# -*- coding: utf-8 -*-
"""
Bilim Premium — 1 oylik obuna.

Imkoniyatlar: AI tushuntirish, shaxsiy darslar yaratish (personal.py), ism
yonida emoji va avatar atrofida oltin halqa. Premium fanlarni ochmaydi — fanlar
alohida sotiladi.

Sotib olish fanlar kabi (payments.py): karta orqali, admin chekni tasdiqlaydi.
Buyurtmada items = ["premium"]. Muddat tugamaguncha qayta
sotib olib bo'lmaydi; tugagach — yana 30 kun. Admin paneldan qo'lda berish yoki
olib qo'yish mumkin (premium_log'da qayd etiladi).

users.premium_until — tugash vaqti (epoch ms). users.emoji_status — tanlangan
emoji (assets/emoji/<kalit>.png); premium tugasa yashiriladi, lekin saqlanadi.
"""

import os
import re

from db import add_column_if_missing
from games import clock

ITEM = 'premium'                     # pay_orders.items dagi kalit
NAME = 'Bilim Premium (1 oy)'
DAYS = 30
DAY_MS = 24 * 3600 * 1000
EMOJI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'emoji')
_KEY_RE = re.compile(r'^[a-z0-9_-]{1,40}$')
_emoji_cache = {'mtime': None, 'keys': []}


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS premium_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            until_ms BIGINT NOT NULL,
            days INTEGER NOT NULL,
            source TEXT NOT NULL,
            note TEXT,
            created_ms BIGINT NOT NULL
        )
    ''')
    conn.commit()
    add_column_if_missing(cur, conn, 'users', 'premium_until', 'BIGINT')
    add_column_if_missing(cur, conn, 'users', 'emoji_status', 'TEXT')


# ───────────────────────── Holat ─────────────────────────

def is_active(until_ms, now=None) -> bool:
    now = now or clock.now_ms()
    try:
        return bool(until_ms) and int(until_ms) > now
    except (TypeError, ValueError):
        return False


def until(cur, user_id) -> int:
    cur.execute('SELECT premium_until FROM users WHERE id = %s', (user_id,))
    row = cur.fetchone() or {}
    return int(row.get('premium_until') or 0)


def status(cur, user_id, now=None) -> dict:
    now = now or clock.now_ms()
    cur.execute('SELECT premium_until, emoji_status FROM users WHERE id = %s', (user_id,))
    row = cur.fetchone() or {}
    u = int(row.get('premium_until') or 0)
    active = is_active(u, now)
    return {
        'active': active,
        'until_ms': u or None,
        'days_left': max(0, -(-(u - now) // DAY_MS)) if active else 0,
        'emoji': row.get('emoji_status') if active and row.get('emoji_status') in emoji_catalog() else None,
        'emoji_saved': row.get('emoji_status'),
    }


def grant(cur, user_id, days, source, now=None, note=None) -> int:
    """Premium beradi yoki uzaytiradi (faol bo'lsa — qolgan kunlar ustiga). Commit — chaqiruvchida."""
    now = now or clock.now_ms()
    base = max(now, until(cur, user_id))
    new_until = base + int(days) * DAY_MS
    cur.execute('UPDATE users SET premium_until = %s WHERE id = %s', (new_until, user_id))
    cur.execute('INSERT INTO premium_log (user_id, until_ms, days, source, note, created_ms) VALUES (%s, %s, %s, %s, %s, %s)',
                (user_id, new_until, int(days), source, note, now))
    return new_until


def revoke(cur, user_id, now=None, note=None):
    now = now or clock.now_ms()
    cur.execute('UPDATE users SET premium_until = NULL WHERE id = %s', (user_id,))
    cur.execute('INSERT INTO premium_log (user_id, until_ms, days, source, note, created_ms) VALUES (%s, %s, %s, %s, %s, %s)',
                (user_id, now, 0, 'revoke', note, now))


# ───────────────────────── Emoji ─────────────────────────

def emoji_catalog() -> list:
    """assets/emoji/*.png — fayl nomi (kengaytmasiz) kalit. Papka o'zgarsa qayta o'qiladi."""
    try:
        mtime = os.path.getmtime(EMOJI_DIR)
    except OSError:
        return []
    if _emoji_cache['mtime'] != mtime:
        keys = []
        for name in sorted(os.listdir(EMOJI_DIR)):
            base, ext = os.path.splitext(name)
            if ext.lower() == '.png' and _KEY_RE.match(base):
                keys.append(base)
        _emoji_cache.update(mtime=mtime, keys=keys)
    return list(_emoji_cache['keys'])


def set_emoji(cur, conn, user_id, key, now=None):
    if not is_active(until(cur, user_id), now):
        raise ValueError("Emoji faqat Bilim Premium bilan ishlaydi.")
    if key is not None and key not in emoji_catalog():
        raise ValueError("Bunday emoji yo'q.")
    cur.execute('UPDATE users SET emoji_status = %s WHERE id = %s', (key, user_id))
    conn.commit()


def badges(cur, user_ids, now=None) -> dict:
    """{user_id: {'premium': True, 'emoji': kalit|None}} — faqat premium'i faol bo'lganlar."""
    ids = sorted({int(i) for i in user_ids if i and int(i) > 0})
    if not ids:
        return {}
    now = now or clock.now_ms()
    catalog = set(emoji_catalog())
    marks = ', '.join(['%s'] * len(ids))
    cur.execute(f'SELECT id, premium_until, emoji_status FROM users WHERE id IN ({marks}) AND premium_until > %s',
                ids + [now])
    return {int(r['id']): {'premium': True, 'emoji': r['emoji_status'] if r['emoji_status'] in catalog else None}
            for r in cur.fetchall()}


def decorate(cur, rows, id_key='user_id', now=None):
    """Ro'yxatdagi har bir qatorga 'premium' va 'emoji' qo'shadi (reyting, o'yinchilar va h.k.)."""
    rows = list(rows or [])
    b = badges(cur, [r.get(id_key) for r in rows if isinstance(r, dict)], now)
    for r in rows:
        info = b.get(int(r.get(id_key) or 0)) if isinstance(r, dict) else None
        r['premium'] = bool(info)
        r['emoji'] = info['emoji'] if info else None
    return rows


# ───────────────────────── Admin ─────────────────────────

def admin_overview(cur, now=None) -> dict:
    now = now or clock.now_ms()
    cur.execute('''SELECT id, name, username, telegram_id, premium_until FROM users
                   WHERE premium_until IS NOT NULL AND premium_until > %s ORDER BY premium_until''', (now,))
    active = [{'id': r['id'], 'name': r['name'], 'username': r['username'], 'until_ms': int(r['premium_until']),
               'days_left': max(0, -(-(int(r['premium_until']) - now) // DAY_MS))} for r in cur.fetchall()]
    cur.execute('''SELECT l.*, u.name FROM premium_log l LEFT JOIN users u ON u.id = l.user_id
                   ORDER BY l.created_ms DESC LIMIT 30''')
    log = [{'user_id': r['user_id'], 'name': r['name'], 'until_ms': int(r['until_ms']), 'days': int(r['days']),
            'source': r['source'], 'note': r['note'], 'created_ms': int(r['created_ms'])} for r in cur.fetchall()]
    month = clock.period_start_ms('month', now)
    cur.execute("SELECT COUNT(*) AS n, COALESCE(SUM(amount), 0) AS s FROM pay_orders "
                "WHERE status = 'approved' AND items = %s AND decided_ms >= %s", ('["premium"]', month))
    r = cur.fetchone()
    cur.execute("SELECT COUNT(*) AS n FROM personal_topics WHERE status = 'ready'")
    lessons = int(cur.fetchone()['n'])
    return {'active': active, 'active_count': len(active), 'log': log, 'lessons': lessons,
            'month': {'count': int(r['n']), 'sum': int(r['s'])}}
