# -*- coding: utf-8 -*-
"""
Profil rasmi — o'quvchi o'zi yuklagan avatar.

Railway diski har deployda tozalanadi, shuning uchun rasm bazada (base64)
saqlanadi va /api/photo/<user_id>?v=<vaqt> orqali beriladi. Brauzer rasmni
yuklashdan oldin o'zi kichraytiradi (320×320 JPEG, ~30 KB), server esa
faqat haqiqiy JPEG/PNG/WebP va MAX_BYTES gacha bo'lgan faylni qabul qiladi.

users.custom_photo = 1 bo'lsa Telegram orqali kirish rasmni qayta yozmaydi;
Telegram rasmi users.tg_photo_url'da alohida saqlanadi (o'chirilganda unga qaytiladi).
"""

import base64
import binascii
import re

from games import clock

MAX_BYTES = 300 * 1024
_DATA_URL = re.compile(r'^data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/=\s]+)$')
_MAGIC = {
    'jpeg': lambda b: b[:3] == b'\xff\xd8\xff',
    'png': lambda b: b[:8] == b'\x89PNG\r\n\x1a\n',
    'webp': lambda b: b[:4] == b'RIFF' and b[8:12] == b'WEBP',
}


class PhotoError(Exception):
    pass


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_photos (
            user_id INTEGER PRIMARY KEY,
            mime TEXT NOT NULL,
            data TEXT NOT NULL,
            updated_ms BIGINT NOT NULL
        )
    ''')
    conn.commit()


def _decode(data_url):
    m = _DATA_URL.match(str(data_url or '').strip())
    if not m:
        raise PhotoError("Rasm formati noto'g'ri (JPG, PNG yoki WebP bo'lishi kerak).")
    kind, payload = m.group(1), re.sub(r'\s', '', m.group(2))
    if len(payload) > MAX_BYTES * 4 // 3 + 8:
        raise PhotoError('Rasm juda katta.')
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        raise PhotoError("Rasm formati noto'g'ri.")
    if not raw or len(raw) > MAX_BYTES:
        raise PhotoError('Rasm juda katta.')
    if not _MAGIC[kind](raw):
        raise PhotoError("Rasm formati noto'g'ri.")
    return 'image/' + kind, base64.b64encode(raw).decode('ascii')


def save(cur, conn, user_id, data_url) -> str:
    """Rasmni saqlaydi va yangi photo_url'ni qaytaradi."""
    mime, data = _decode(data_url)
    now = clock.now_ms()
    cur.execute('DELETE FROM user_photos WHERE user_id = %s', (user_id,))
    cur.execute('INSERT INTO user_photos (user_id, mime, data, updated_ms) VALUES (%s, %s, %s, %s)',
                (user_id, mime, data, now))
    url = f'/api/photo/{user_id}?v={now}'
    cur.execute('UPDATE users SET photo_url = %s, custom_photo = 1 WHERE id = %s', (url, user_id))
    conn.commit()
    return url


def remove(cur, conn, user_id):
    """O'zi yuklagan rasmni o'chiradi — Telegram rasmi (bo'lsa) qaytadi."""
    cur.execute('DELETE FROM user_photos WHERE user_id = %s', (user_id,))
    cur.execute('UPDATE users SET photo_url = tg_photo_url, custom_photo = 0 WHERE id = %s', (user_id,))
    cur.execute('SELECT photo_url FROM users WHERE id = %s', (user_id,))
    row = cur.fetchone()
    conn.commit()
    return row['photo_url'] if row else None


def load(cur, user_id):
    """(mime, bytes) yoki None."""
    cur.execute('SELECT mime, data FROM user_photos WHERE user_id = %s', (user_id,))
    row = cur.fetchone()
    if not row:
        return None
    return row['mime'], base64.b64decode(row['data'])
