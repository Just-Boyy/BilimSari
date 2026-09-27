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


def app_url(path=''):
    return WEBAPP_URL.rstrip('/') + '/' + path.lstrip('/')


def send(chat_id, text, button_text=None, path=''):
    """HTML matnli xabar va (ixtiyoriy) ilovani ochadigan tugma.
    (yuborildimi, xato_kodi) qaytaradi — 403 foydalanuvchi botni bloklagan
    yoki hech qachon /start bosmaganini bildiradi."""
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    if button_text:
        payload['reply_markup'] = {'inline_keyboard': [[
            {'text': button_text, 'web_app': {'url': app_url(path)}},
        ]]}
    res = tg_api('sendMessage', payload)
    if not res:
        return False, None
    return bool(res.get('ok')), res.get('error_code')
