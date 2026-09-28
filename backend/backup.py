# -*- coding: utf-8 -*-
"""
Kunlik zaxira nusxa.

Har kecha (03:00, Toshkent) butun baza — o'quvchilar, progress, to'lovlar,
nishonlar, o'yinlar, rasmlar — bitta siqilgan JSON faylga yoziladi va
egaga (ADMIN_TELEGRAM_IDS) bot orqali hujjat sifatida yuboriladi. Fayl
Railway'dan tashqarida — Telegram'da saqlanadi: baza butunlay yo'qolsa ham,
scripts/restore_backup.py bilan qayta tiklash mumkin.

Nusxaga kirmaydi: kod'dan qayta yaratiladigan darslar (topics, subjects,
curriculum_meta — admin tahrirlari esa topic_overrides'da, u kiradi),
sessiya tokenlari (xavfsizlik uchun; o'quvchilar Telegram orqali avtomatik
qayta kiradi) va vaqtinchalik jadvallar.

Fayl faqat egalarga yuboriladi — panelda qo'shilgan adminlarga emas
(unda barcha o'quvchilarning shaxsiy ma'lumotlari bor).
"""

import base64
import gzip
import io
import json
import logging
from datetime import date, datetime
from decimal import Decimal

import admin_auth
import tgbot
from db import TASHKENT_TZ, get_connection, is_postgres
from games import clock

logger = logging.getLogger('bilimsari.backup')

BACKUP_HOUR = 3                       # Toshkent vaqti
FORMAT = 'bilimsari-backup'
VERSION = 1
TG_LIMIT = 49 * 1024 * 1024          # Telegram bot hujjati — ko'pi bilan 50 MB
SKIP_TABLES = {
    'topics', 'subjects', 'curriculum_meta',          # kod'dan qayta yaratiladi
    'tokens',                                         # sessiyalar — nusxada saqlanmaydi
    'rate_hits', 'bot_updates', 'job_runs', 'error_log', 'game_presence', 'game_queue',  # vaqtinchalik
    'backup_log',
}
BULKY_TABLES = ('user_photos', 'ai_explanations')     # fayl juda katta bo'lsa — tashlab yuboriladi


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS backup_log (
            id SERIAL PRIMARY KEY,
            ms BIGINT NOT NULL,
            size INTEGER NOT NULL,
            table_count INTEGER NOT NULL,
            row_count INTEGER NOT NULL,
            sent INTEGER NOT NULL DEFAULT 0,
            origin TEXT NOT NULL,
            note TEXT
        )
    ''')
    conn.commit()


def table_names(cur) -> list:
    if is_postgres():
        cur.execute("SELECT tablename AS name FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    return [r['name'] for r in cur.fetchall()]


def _value(v):
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, Decimal):
        return int(v) if v == int(v) else float(v)
    if isinstance(v, (bytes, bytearray, memoryview)):
        return {'$b64': base64.b64encode(bytes(v)).decode('ascii')}
    return v


def dump(cur, skip_bulky=False) -> dict:
    """{'format', 'version', 'created', 'tables': {nom: {'columns', 'rows'}}}"""
    skip = SKIP_TABLES | (set(BULKY_TABLES) if skip_bulky else set())
    tables = {}
    for name in table_names(cur):
        if name in skip:
            continue
        cur.execute(f'SELECT * FROM {name}')
        rows = cur.fetchall()
        columns = list(rows[0].keys()) if rows else []
        tables[name] = {'columns': columns, 'rows': [[_value(r[c]) for c in columns] for r in rows]}
    return {
        'format': FORMAT, 'version': VERSION,
        'created': datetime.now(TASHKENT_TZ).isoformat(timespec='seconds'),
        'db': 'postgres' if is_postgres() else 'sqlite',
        'skipped': sorted(skip),
        'tables': tables,
    }


def pack(data: dict) -> bytes:
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return gzip.compress(raw, compresslevel=9)


def unpack(blob: bytes) -> dict:
    data = json.loads(gzip.decompress(blob).decode('utf-8'))
    if data.get('format') != FORMAT:
        raise ValueError('Bu BilimSari zaxira nusxasi emas')
    return data


def _mb(n) -> str:
    return f'{n / 1024 / 1024:.2f} MB' if n >= 1024 * 1024 else f'{max(1, round(n / 1024))} KB'


def make(cur):
    """(fayl baytlari, ma'lumot, izoh). 50 MB'dan oshsa — rasmlar va AI keshi tashlab yuboriladi."""
    data = dump(cur)
    blob = pack(data)
    note = ''
    if len(blob) > TG_LIMIT:
        data = dump(cur, skip_bulky=True)
        blob = pack(data)
        note = "Fayl juda katta bo'lgani uchun profil rasmlari va AI keshi kiritilmadi."
    return blob, data, note


def run(origin='auto', now_ms=None) -> dict:
    """Nusxa oladi, egalarga yuboradi va backup_log'ga yozadi."""
    now_ms = now_ms or clock.now_ms()
    conn = get_connection()
    cur = conn.cursor()
    try:
        blob, data, note = make(cur)
        conn.rollback()                     # faqat o'qildi — tranzaksiyani yopamiz
        rows = sum(len(t['rows']) for t in data['tables'].values())
        stamp = datetime.fromtimestamp(now_ms / 1000, TASHKENT_TZ)
        filename = f'bilimsari-{stamp:%Y-%m-%d-%H%M}.json.gz'
        users = len(data['tables'].get('users', {}).get('rows', []))
        caption = (f"💾 <b>Zaxira nusxa</b> — {stamp:%d.%m.%Y %H:%M}\n"
                   f"{users} o'quvchi, {len(data['tables'])} jadval, {rows} qator, {_mb(len(blob))}.\n"
                   f"Faylni saqlab qo'ying — baza buzilsa, shu fayldan tiklanadi.")
        if note:
            caption += f"\n⚠️ {note}"
        sent = 0
        for owner in sorted(admin_auth.ADMIN_TELEGRAM_IDS):
            res = tgbot.tg_upload('sendDocument', {'chat_id': owner, 'caption': caption, 'parse_mode': 'HTML'},
                                  {'document': (filename, io.BytesIO(blob), 'application/gzip')})
            if res and res.get('ok'):
                sent += 1
            else:
                logger.error('Zaxira nusxa egaga yuborilmadi (%s): %s', owner, (res or {}).get('description'))
        cur.execute('INSERT INTO backup_log (ms, size, table_count, row_count, sent, origin, note) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (now_ms, len(blob), len(data['tables']), rows, sent, origin, note or None))
        conn.commit()
        logger.info('Zaxira nusxa: %s, %d qator, %d egaga yuborildi', _mb(len(blob)), rows, sent)
        return {'size': len(blob), 'rows': rows, 'tables': len(data['tables']), 'sent': sent, 'note': note,
                'users': users}
    finally:
        cur.close()
        conn.close()


def history(cur, limit=10) -> list:
    cur.execute('SELECT ms, size, table_count, row_count, sent, origin, note FROM backup_log '
                'ORDER BY ms DESC LIMIT %s',
                (limit,))
    return [dict(r, ms=int(r['ms'])) for r in cur.fetchall()]


# ───────────────────────── Tiklash ─────────────────────────

def _columns(cur, table) -> list:
    if is_postgres():
        cur.execute('SELECT column_name AS name FROM information_schema.columns '
                    "WHERE table_schema = 'public' AND table_name = %s", (table,))
    else:
        cur.execute(f'PRAGMA table_info({table})')
    return [r['name'] for r in cur.fetchall()]


def _restore_value(v):
    if isinstance(v, dict) and set(v) == {'$b64'}:
        return base64.b64decode(v['$b64'])
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)          # JSONB ustunlar
    return v


def restore(cur, conn, data, replace=False) -> dict:
    """Nusxadagi qatorlarni bazaga yozadi (jadvallar init_db bilan yaratilgan
    bo'lishi kerak). replace=True — nusxadagi jadvallar avval tozalanadi.
    {jadval: yozilgan qatorlar} qaytaradi."""
    existing = set(table_names(cur))
    names = [n for n in data['tables'] if n in existing]
    order = sorted(names, key=lambda n: (n != 'users', n))    # users — birinchi (tokens FK)
    if replace:
        for name in reversed(order):
            cur.execute(f'DELETE FROM {name}')
        conn.commit()
    written = {}
    for name in order:
        table = data['tables'][name]
        have = set(_columns(cur, name))
        cols = [c for c in table['columns'] if c in have]
        if not cols:
            written[name] = 0
            continue
        idx = [table['columns'].index(c) for c in cols]
        sql = (f'INSERT INTO {name} ({", ".join(cols)}) VALUES ({", ".join(["%s"] * len(cols))}) '
               'ON CONFLICT DO NOTHING')
        n = 0
        for row in table['rows']:
            cur.execute(sql, [_restore_value(row[i]) for i in idx])
            n += max(cur.rowcount, 0)
        written[name] = n
        if is_postgres() and 'id' in cols:
            # SERIAL hisoblagichi tiklangan eng katta id'dan davom etsin
            cur.execute("SELECT pg_get_serial_sequence(%s, 'id') AS seq", (name,))
            seq = (cur.fetchone() or {}).get('seq')
            if seq:
                cur.execute(f'SELECT setval(%s, GREATEST(COALESCE(MAX(id), 0), 1)) FROM {name}', (seq,))
        conn.commit()
    return written
