"""
BilimSari — ma'lumotlar bazasi qatlami.

Ishlab chiqarishda (Railway) PostgreSQL ishlatiladi: DATABASE_URL orqali.
Lokal ishlab chiqishda DATABASE_URL bo'lmasa — SQLite ga tushadi, shunda
loyihani hech qanday tashqi baza o'rnatmasdan ishga tushirish mumkin.

Kod bir xil SQL yozadi (PostgreSQL dialekti, %s placeholder).
SQLite uchun quyidagi shim so'rovni tarjima qiladi.
"""

import os
import re
import sqlite3
import threading
import time
from datetime import datetime, timezone, timedelta

# O'zbekiston vaqti — UTC+5, yozgi/qishki o'zgarish yo'q
TASHKENT_TZ = timezone(timedelta(hours=5), 'Asia/Tashkent')


def database_url():
    url = os.environ.get('DATABASE_URL') or ''
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


def is_postgres():
    return bool(database_url())


# ───────────────────────── SQLite shim ─────────────────────────

sqlite3.register_adapter(datetime, lambda d: d.strftime('%Y-%m-%d %H:%M:%S'))

_SQLITE_RULES = [
    (re.compile(r'\bSERIAL\s+PRIMARY\s+KEY\b', re.I), 'INTEGER PRIMARY KEY AUTOINCREMENT'),
    (re.compile(r'\bBIGSERIAL\s+PRIMARY\s+KEY\b', re.I), 'INTEGER PRIMARY KEY AUTOINCREMENT'),
    # PostgreSQL castlari (::jsonb, ::text) — SQLite da kerak emas.
    # Bu qoida JSONB → TEXT almashtirishidan OLDIN turishi shart, aks holda
    # '[]'::jsonb → '[]'::TEXT bo'lib qoladi va SQLite uni tushunmaydi.
    (re.compile(r'::\s*[A-Za-z_][A-Za-z0-9_]*'), ''),
    (re.compile(r'\bJSONB\b', re.I), 'TEXT'),
    (re.compile(r'\bBIGINT\b', re.I), 'INTEGER'),
    (re.compile(r'\bDOUBLE\s+PRECISION\b', re.I), 'REAL'),
    (re.compile(r'\bNOW\(\)'), "CURRENT_TIMESTAMP"),
]


_EMPTY_IN = re.compile(r'\bIN\s*\(\s*\)', re.I)


def _to_sqlite(sql: str) -> str:
    # Postgres "IN ()" ni sintaksis xatosi deb rad etadi, SQLite esa jim o'tkazadi —
    # lokal testlarda ham xato bo'lsin, aks holda bunday bug faqat prod'da chiqadi
    if _EMPTY_IN.search(sql):
        raise sqlite3.OperationalError("IN () — bo'sh ro'yxat (Postgres buni sintaksis xatosi deb rad etadi)")
    for pattern, repl in _SQLITE_RULES:
        sql = pattern.sub(repl, sql)
    # %s → ?  (lekin LIKE '%s%' kabi holatlarga tegmaymiz: bizda bunday yo'q)
    sql = sql.replace('%s', '?')
    return sql


class _SqliteCursor:
    """psycopg2 RealDictCursor ga o'xshash interfeys."""

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql, params=None):
        return self._raw.execute(_to_sqlite(sql), tuple(params or ()))

    def executemany(self, sql, seq):
        return self._raw.executemany(_to_sqlite(sql), [tuple(p) for p in seq])

    def fetchone(self):
        row = self._raw.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        return [dict(r) for r in self._raw.fetchall()]

    @property
    def rowcount(self):
        return self._raw.rowcount

    @property
    def lastrowid(self):
        return self._raw.lastrowid

    def close(self):
        self._raw.close()


class _SqliteConnection:
    def __init__(self, raw):
        self._raw = raw

    def cursor(self, *args, **kwargs):
        return _SqliteCursor(self._raw.cursor())

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()


def sqlite_path():
    return os.environ.get(
        'SQLITE_PATH',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bilimsari.db'),
    )


# ───────────────────────── Postgres ulanish hovuzi ─────────────────────────
#
# Oldin har bir so'rov (har bir API chaqiruvi, ba'zan bittasida bir nechta
# marta) psycopg2.connect() bilan YANGI TCP+autentifikatsiya ulanishi
# ochardi — bu Railway'dagi Postgres'gacha bo'lgan tarmoq safari tufayli har
# bir so'rovga sezilarli kechikish qo'shadi. Endi ulanishlar hovuzda qayta
# ishlatiladi; har bir gunicorn worker o'zining alohida hovuzini birinchi
# so'rovda yaratadi (fork qilingandan keyin, shuning uchun xavfsiz).

_pg_pool = None
# Bir vaqtda nechta oqim bazadan ulanish olishi mumkin (gthread rejimi). Hovuz bo'sh qolmasa ThreadedConnectionPool
# darhol xato beradi — semafor esa oqimni bo'sh ulanish chiqquncha kutdiradi.
_pg_sem = None
_pool_lock = threading.Lock()
# Oqim allaqachon ulanish ushlab turib yana olsa (ichma-ich, masalan onlayn belgisi) — asosiy semaforni
# kutmaydi (aks holda hamma oqim bir-birini kutib qotib qolardi), NESTED_EXTRA o'rinli alohida semaforni kutadi:
# ichma-ich ulanish qisqa va undan keyin boshqa narsa so'ralmaydi — qotib qolish bo'lmaydi.
NESTED_EXTRA = 2
_pg_sem_ichki = None
_ushlagan = {}     # oqim ident → hozir ushlab turgan ulanishlar soni


def _get_pg_pool():
    global _pg_pool, _pg_sem, _pg_sem_ichki
    if _pg_pool is not None:
        return _pg_pool
    with _pool_lock:
        if _pg_pool is not None:
            return _pg_pool
        from psycopg2.extras import RealDictCursor
        from psycopg2.pool import ThreadedConnectionPool
        max_conn = int(os.environ.get('DB_POOL_MAX', '5'))
        # connect_timeout — baza javob bermasa so'rov cheksiz osilib qolmasin (sync worker'lar
        # band bo'lib, butun sayt qotib qolardi); 10 soniyada xato qaytadi va keyingi so'rov qayta uradi
        # keepalives — baza internet orqali (tashqi xizmatda) bo'lganda, jim turgan ulanish
        # tarmoq yoki pooler tomonidan sezdirmasdan uzilib qolmasligi uchun
        _pg_sem = threading.BoundedSemaphore(max_conn)
        _pg_sem_ichki = threading.BoundedSemaphore(NESTED_EXTRA)
        _pg_pool = ThreadedConnectionPool(
            1, max_conn + NESTED_EXTRA + 1, database_url(), cursor_factory=RealDictCursor,
            connect_timeout=int(os.environ.get('DB_CONNECT_TIMEOUT', '10')),
            keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3,
        )
    return _pg_pool


# Ulanish oxirgi marta qachon ishlatilgan (id(raw) → soniya). Uzoq jim turgan ulanish
# berishdan oldin "SELECT 1" bilan tekshiriladi — o'lik bo'lsa tashlanib, yangisi olinadi.
PING_AFTER_S = 30
_last_used = {}


def _pg_getconn(pool):
    for _ in range(3):
        raw = pool.getconn()
        if raw.closed:
            pool.putconn(raw, close=True)
            continue
        if time.time() - _last_used.get(id(raw), 0) > PING_AFTER_S:
            try:
                with raw.cursor() as c:
                    c.execute('SELECT 1')
                raw.rollback()
            except Exception:  # noqa: BLE001
                _last_used.pop(id(raw), None)
                pool.putconn(raw, close=True)
                continue
        return raw
    return pool.getconn()


class _PooledPgConnection:
    """psycopg2 ulanishini o'raydi — .close() uni haqiqatan yopmaydi,
    hovuzga qaytaradi. Qaytarishdan oldin har doim rollback qilinadi:
    aks holda oldingi so'rovda xato bo'lib, commit/rollback qilinmagan
    tranzaksiya qolib ketsa, keyingi so'rov shu "buzilgan" ulanishni olib,
    "current transaction is aborted" xatosiga uchraydi."""

    def __init__(self, pool, raw, sem=None):
        self._pool = pool
        self._raw = raw
        self._yopiq = False
        self._sem = sem                        # qaysi semafor o'rnini egallagan (asosiy yoki ichma-ich)
        self._oqim = threading.get_ident()
        _ushlagan[self._oqim] = _ushlagan.get(self._oqim, 0) + 1

    def cursor(self, *args, **kwargs):
        return self._raw.cursor(*args, **kwargs)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        if self._yopiq:          # ikki marta yopilsa — hovuz va semafor buzilmasin
            return
        self._yopiq = True
        try:
            self._raw.rollback()
        except Exception:
            pass
        broken = bool(getattr(self._raw, 'closed', 0))
        if broken:
            _last_used.pop(id(self._raw), None)
        else:
            _last_used[id(self._raw)] = time.time()
        try:
            self._pool.putconn(self._raw, close=broken)
        finally:
            n = _ushlagan.get(self._oqim, 1) - 1
            if n > 0:
                _ushlagan[self._oqim] = n
            else:
                _ushlagan.pop(self._oqim, None)
            if self._sem is not None:
                self._sem.release()

    def __del__(self):
        # Yopilmay qolgan ulanish (kod xatosi) — semafor o'rni abadiy band bo'lib qolmasin
        try:
            self.close()
        except Exception:  # noqa: BLE001
            pass


# ───────────────────────── Ulanish ─────────────────────────

def get_connection():
    """Postgres (prod, hovuzdan) yoki SQLite (lokal) ulanishi."""
    url = database_url()
    if url:
        pool = _get_pg_pool()
        ushlagan = _ushlagan.get(threading.get_ident(), 0)
        # 0 — asosiy navbat; 1 — ichma-ich navbat; undan chuqur (juda kam) — navbatsiz
        sem = _pg_sem if ushlagan == 0 else (_pg_sem_ichki if ushlagan == 1 else None)
        if sem is not None and not sem.acquire(timeout=int(os.environ.get('DB_WAIT_S', '25'))):
            raise RuntimeError("Baza band — barcha ulanishlar ishlatilmoqda")
        try:
            return _PooledPgConnection(pool, _pg_getconn(pool), sem)
        except BaseException:
            if sem is not None:
                sem.release()
            raise

    raw = sqlite3.connect(sqlite_path(), timeout=15)
    raw.row_factory = sqlite3.Row
    raw.execute('PRAGMA foreign_keys = ON')
    raw.execute('PRAGMA journal_mode = WAL')
    return _SqliteConnection(raw)


# ───────────────────────── Yordamchilar ─────────────────────────

def add_column_if_missing(cur, conn, table: str, column: str, ddl: str):
    """Ikkala bazada ham ishlaydigan 'ADD COLUMN IF NOT EXISTS'."""
    try:
        cur.execute(f'ALTER TABLE {table} ADD COLUMN {column} {ddl}')
        conn.commit()
    except Exception:
        conn.rollback()  # ustun allaqachon bor


def utc_now() -> datetime:
    """Naive UTC — bazaga yozish uchun (ikkala baza ham naive saqlaydi)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def as_utc(value) -> datetime | None:
    """Bazadan kelgan vaqtni naive UTC datetime ga aylantiradi."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    text = str(value).strip()
    if not text:
        return None
    text = text.replace('T', ' ')
    if text.endswith('Z'):
        text = text[:-1]
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(text[:26], fmt)
        except ValueError:
            continue
    return None


def to_tashkent(dt: datetime | None):
    """Naive UTC → Toshkent vaqti (tzinfo bilan)."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc).astimezone(TASHKENT_TZ)


def iso_utc(dt: datetime | None):
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc).isoformat()
