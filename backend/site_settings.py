# -*- coding: utf-8 -*-
"""
Sayt sozlamalari (admin panelda o'zgartiriladi): hozircha "Biz haqimizda" uchun
Telegram kanal havolasi. Qiymatlar pay_settings kalit-qiymat jadvalida saqlanadi.
"""

import re

CHANNEL_KEY = 'channel_url'
_USERNAME = re.compile(r'^[A-Za-z][A-Za-z0-9_]{3,31}$')
_INVITE = re.compile(r'^\+[A-Za-z0-9_-]{8,64}$')


def get(cur, key, default=''):
    cur.execute('SELECT value FROM pay_settings WHERE key = %s', (key,))
    row = cur.fetchone()
    return row['value'] if row else default


def put(cur, conn, key, value):
    cur.execute('DELETE FROM pay_settings WHERE key = %s', (key,))
    if value:
        cur.execute('INSERT INTO pay_settings (key, value) VALUES (%s, %s)', (key, value))
    conn.commit()


def normalize_channel(raw) -> str:
    """@kanal, t.me/kanal, https://t.me/kanal yoki https://t.me/+taklif → https://t.me/...
    Bo'sh qiymat — havola o'chiriladi. Noto'g'ri bo'lsa ValueError."""
    s = str(raw or '').strip()
    if not s:
        return ''
    s = re.sub(r'^(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/', '', s)
    s = s.lstrip('@').split('?')[0].rstrip('/')
    if _USERNAME.match(s) or _INVITE.match(s):
        return 'https://t.me/' + s
    raise ValueError("Kanal havolasi noto'g'ri. Masalan: @bilimsari yoki https://t.me/bilimsari")


def channel_url(cur) -> str:
    return get(cur, CHANNEL_KEY)
