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


def _to_sqlite(sql: str) -> str:
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


# ───────────────────────── Ulanish ─────────────────────────

def get_connection():
    """Postgres (prod) yoki SQLite (lokal) ulanishi."""
    url = database_url()
    if url:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        return psycopg2.connect(url, cursor_factory=RealDictCursor)

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
