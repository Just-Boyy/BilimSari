# -*- coding: utf-8 -*-
"""
Telegram Bot API bilan ishlash — bitta joyda.

app.py (webhook, /start javoblari) ham, notify.py (eslatmalar) ham shu
moduldan foydalanadi. BOT_TOKEN faqat muhit o'zgaruvchisidan olinadi.
"""

import logging
import os

import requests

logger = logging.getLogger('bilimsari.tgbot')

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://bilimsari-production.up.railway.app')
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'bilimsaribot').lstrip('@')


def tg_api(method, payload):
    """Bot API chaqiruvi. Token bo'lmasa yoki tarmoq xatosida None qaytaradi."""
    if not BOT_TOKEN:
        return None
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/{method}'
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.json()
    except Exception:  # noqa: BLE001
        logger.exception('Telegram API xato (%s)', method)
        return None


def tg_upload(method, data, files, timeout=120):
    """Fayl yuboradigan Bot API chaqiruvi (multipart), masalan sendDocument."""
    if not BOT_TOKEN:
        return None
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/{method}'
    try:
        r = requests.post(url, data=data, files=files, timeout=timeout)
        return r.json()
    except Exception:  # noqa: BLE001
        logger.exception('Telegram API xato (%s)', method)
        return None


def app_url(path=''):
    return WEBAPP_URL.rstrip('/') + '/' + path.lstrip('/')


def L(uz, ru):
    """Ikki tilli matn: tgbot.send / pick o'quvchi tiliga qarab birini tanlaydi."""
    return {'uz': uz, 'ru': ru}


def pick(value, lang):
    """L(...) bo'lsa — o'quvchi tilidagisi (ruschasi bo'lmasa o'zbekcha), oddiy matn — o'zi."""
    if isinstance(value, dict):
        return value.get(lang) or value.get('uz') or ''
    return value


SUBJECT_RU = {
    'Matematika': 'Математика', 'Geometriya': 'Геометрия', 'Ona tili': 'Родной язык', 'Adabiyot': 'Литература',
    'Ingliz tili': 'Английский язык', 'Rus tili': 'Русский язык', 'Tarix': 'История', 'Geografiya': 'География',
    'Kimyo': 'Химия', 'Biologiya': 'Биология', 'Huquq': 'Право', 'Informatika': 'Информатика',
}


def fan_ru(name):
    """Fan nomining ruschasi (topilmasa — o'zi)."""
    return SUBJECT_RU.get(name, name)


def kun_ru(n):
    """1 день, 2 дня, 5 дней."""
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return 'день'
    return 'дня' if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else 'дней'


def lang_of(chat_id, tg_lang=None) -> str:
    """O'quvchining tili — 'ru' yoki 'uz'. Ilovada tanlagani (users.lang) birinchi; tanlamagan yoki
    hali ilovaga kirmagan bo'lsa — Telegram ilovasining tili (message.from.language_code)."""
    saved = None
    try:
        from db import get_connection   # noqa: PLC0415 — tgbot bazasiz ham ishlatiladi
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute('SELECT lang FROM users WHERE telegram_id = %s ORDER BY id DESC LIMIT 1', (chat_id,))
            row = cur.fetchone()
            saved = row.get('lang') if row else None
        finally:
            cur.close()
            conn.close()
    except Exception:  # noqa: BLE001 — til aniqlanmasa o'zbekcha yuboriladi
        saved = None
    if saved in ('uz', 'ru'):
        return saved
    return 'ru' if str(tg_lang or '').lower().startswith('ru') else 'uz'


def send(chat_id, text, button_text=None, path='', lang=None):
    """HTML matnli xabar va (ixtiyoriy) ilovani ochadigan tugma.
    text / button_text — oddiy matn yoki L(uz, ru); lang berilmasa o'quvchi tili bazadan olinadi.
    (yuborildimi, xato_kodi) qaytaradi — 403 foydalanuvchi botni bloklagan
    yoki hech qachon /start bosmaganini bildiradi."""
    if isinstance(text, dict) or isinstance(button_text, dict):
        lang = lang or lang_of(chat_id)
        text, button_text = pick(text, lang), pick(button_text, lang)
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    if button_text:
        payload['reply_markup'] = {'inline_keyboard': [[
            {'text': button_text, 'web_app': {'url': app_url(path)}},
        ]]}
    res = tg_api('sendMessage', payload)
    if not res:
        return False, None
    return bool(res.get('ok')), res.get('error_code')
