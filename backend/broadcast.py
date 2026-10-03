# -*- coding: utf-8 -*-
"""
Ommaviy xabar (admin panel → "Xabar") — fonda yuboriladi.

Oldin xabar bitta HTTP so'rov ichida hammaga ketma-ket yuborilardi: 60 soniyalik
gunicorn chegarasidan oshsa uzilib qolardi va shu vaqt ichida ishchi jarayon
band bo'lib, sayt sekinlashardi. Endi:

  * so'rov darhol javob qaytaradi, yuborish alohida oqimda boradi;
  * jarayon broadcasts jadvalida saqlanadi (yuborildi / xato / bloklagan) —
    admin panel uni jonli ko'rsatadi;
  * worker qayta ishga tushsa (gunicorn --max-requests), rejalashtiruvchi
    "osilib qolgan" tarqatishni topib, qolgan joyidan davom ettiradi;
  * eslatmalarni o'chirgan (users.notify = 0) o'quvchilarga yuborilmaydi;
  * botni bloklagan (403) o'quvchilar belgilanadi — keyin ularga urinilmaydi;
  * Telegram "juda tez" (429) desa, aytilgan vaqt kutiladi.

Tizim xabarlari (masalan, yutuqli marafon e'loni) HTML matn va ilovani ochadigan
tugma bilan, "hammaga" (everyone — eslatmani o'chirganlarga ham) yuborilishi mumkin.
Bir tarqatish ketayotganda yangisi navbatga (queued) qo'yiladi va keyin boshlanadi.
"""

import logging
import threading
import time

import boshqaruv
import tgbot
from db import add_column_if_missing, get_connection
from games import clock

logger = logging.getLogger('bilimsari.broadcast')

BATCH = 50
PAUSE_S = 0.04            # Telegram: sekundiga ~30 xabardan oshmaslik
STALE_MS = 2 * 60 * 1000  # shuncha vaqt yangilanmagan "running" — osilib qolgan


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS broadcasts (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            status TEXT NOT NULL,
            total INTEGER NOT NULL DEFAULT 0,
            sent INTEGER NOT NULL DEFAULT 0,
            failed INTEGER NOT NULL DEFAULT 0,
            blocked INTEGER NOT NULL DEFAULT 0,
            last_user_id INTEGER NOT NULL DEFAULT 0,
            created_ms BIGINT NOT NULL,
            heartbeat_ms BIGINT NOT NULL,
            finished_ms BIGINT
        )
    ''')
    conn.commit()
    add_column_if_missing(cur, conn, 'broadcasts', 'html', 'INTEGER NOT NULL DEFAULT 0')
    add_column_if_missing(cur, conn, 'broadcasts', 'button_text', 'TEXT')
    add_column_if_missing(cur, conn, 'broadcasts', 'button_path', 'TEXT')
    add_column_if_missing(cur, conn, 'broadcasts', 'everyone', 'INTEGER NOT NULL DEFAULT 0')
    # Tizim xabarlari (marafon e'loni) ruscha interfeysdagi o'quvchilarga ruscha ketadi
    add_column_if_missing(cur, conn, 'broadcasts', 'text_ru', 'TEXT')
    add_column_if_missing(cur, conn, 'broadcasts', 'button_ru', 'TEXT')


class BroadcastError(Exception):
    def __init__(self, message, http_status=400):
        super().__init__(message)
        self.message, self.http_status = message, http_status


def _public(row) -> dict:
    # "state" (status emas) — frontend so'rov yordamchilari javobdagi "status"ni HTTP kodi bilan almashtiradi
    return {k: row[k] for k in ('id', 'total', 'sent', 'failed', 'blocked')} | {
        'state': row['status'], 'done': int(row['sent']) + int(row['failed']) + int(row['blocked'])}


def get(cur, bid):
    cur.execute('SELECT * FROM broadcasts WHERE id = %s', (bid,))
    row = cur.fetchone()
    return _public(row) if row else None


def _recipients_sql(everyone) -> str:
    return 'telegram_id IS NOT NULL' + ('' if everyone else ' AND notify = 1')


def start(cur, conn, text, now=None, html=False, button=None, path='', everyone=False, queue=False,
          text_ru=None, button_ru=None) -> dict:
    """Tarqatishni yaratadi va fonda boshlaydi. queue=True — boshqasi ketayotgan bo'lsa navbatga qo'yiladi.
    text_ru / button_ru — ruscha interfeysdagi o'quvchilar uchun (berilmasa hammaga text)."""
    now = now or clock.now_ms()
    text = str(text or '').strip()
    if not text:
        raise BroadcastError("Xabar matni bo'sh")
    if len(text) > 3500:
        raise BroadcastError('Xabar juda uzun (3500 belgigacha)')
    cur.execute("SELECT id FROM broadcasts WHERE status IN ('running', 'queued')")
    busy = cur.fetchone() is not None
    if busy and not queue:
        raise BroadcastError("Oldingi xabar hali yuborilmoqda. U tugashini kuting.", 409)
    cur.execute(f'SELECT COUNT(*) AS n FROM users WHERE {_recipients_sql(everyone)}')
    total = int(cur.fetchone()['n'])
    cur.execute('''INSERT INTO broadcasts (text, status, total, created_ms, heartbeat_ms, html, button_text, button_path,
                                           everyone, text_ru, button_ru)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
                (text, 'queued' if busy else 'running', total, now, now, int(bool(html)), button, path or None,
                 int(bool(everyone)), (str(text_ru).strip() or None) if text_ru else None, button_ru))
    bid = cur.fetchone()['id']
    conn.commit()
    if not busy:
        _spawn(bid)
    return get(cur, bid)


def _spawn(bid):
    threading.Thread(target=run, args=(bid,), name=f'bilimsari-broadcast-{bid}', daemon=True).start()


def _send(chat_id, text, b=None, ru=False):
    """(natija, retry_after): 'ok' | 'blocked' | 'failed'. ru=True — ruscha tugma (bo'lsa)."""
    payload = {'chat_id': chat_id, 'text': text}
    if b and b['html']:
        payload['parse_mode'] = 'HTML'
    if b and b['button_text']:
        label = (b.get('button_ru') if ru else None) or b['button_text']
        payload['reply_markup'] = {'inline_keyboard': [[
            {'text': label, 'web_app': {'url': tgbot.app_url(b['button_path'] or '')}}]]}
    res = tgbot.tg_api('sendMessage', payload)
    if res and res.get('ok'):
        return 'ok', 0
    code = (res or {}).get('error_code')
    if code == 403:
        return 'blocked', 0
    if code == 429:
        return 'failed', int(((res or {}).get('parameters') or {}).get('retry_after') or 1)
    return 'failed', 0


def run(bid):
    """Tarqatishni last_user_id dan davom ettiradi (bir necha marta chaqirish xavfsiz)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM broadcasts WHERE id = %s', (bid,))
        b = cur.fetchone()
        if not b or b['status'] != 'running':
            return
        text, last = b['text'], int(b['last_user_id'])
        sent, failed, blocked = int(b['sent']), int(b['failed']), int(b['blocked'])
        while True:
            if boshqaruv.notifications_off():
                # Admin botni to'xtatgan — tarqatish to'xtab turadi; resume_stale keyinroq shu joydan davom ettiradi
                conn.commit()
                return
            cur.execute(f'''SELECT id, telegram_id, lang FROM users
                            WHERE {_recipients_sql(b['everyone'])} AND id > %s
                            ORDER BY id LIMIT %s''', (last, BATCH))
            batch = cur.fetchall()
            if not batch:
                break
            for u in batch:
                ru = u.get('lang') == 'ru' and bool(b.get('text_ru'))
                matn = b['text_ru'] if ru else text
                result, wait = _send(u['telegram_id'], matn, b, ru)
                if wait:                                   # 429 — kutib, bir marta qayta urinamiz
                    time.sleep(min(wait, 30))
                    result, _ = _send(u['telegram_id'], matn, b, ru)
                if result == 'ok':
                    sent += 1
                elif result == 'blocked':
                    blocked += 1
                    cur.execute('UPDATE users SET notify = 0 WHERE id = %s', (u['id'],))
                else:
                    failed += 1
                last = u['id']
                time.sleep(PAUSE_S)
            cur.execute('''UPDATE broadcasts SET sent = %s, failed = %s, blocked = %s, last_user_id = %s,
                                                 heartbeat_ms = %s WHERE id = %s''',
                        (sent, failed, blocked, last, clock.now_ms(), bid))
            conn.commit()
        now = clock.now_ms()
        cur.execute('''UPDATE broadcasts SET status = 'done', sent = %s, failed = %s, blocked = %s,
                                             last_user_id = %s, heartbeat_ms = %s, finished_ms = %s
                       WHERE id = %s''', (sent, failed, blocked, last, now, now, bid))
        conn.commit()
        logger.info('Ommaviy xabar #%s tugadi: %s ta yuborildi, %s xato, %s bloklagan', bid, sent, failed, blocked)
        _next_queued(cur, conn)
    except Exception:  # noqa: BLE001
        conn.rollback()
        logger.exception('Ommaviy xabar #%s xatosi', bid)
    finally:
        cur.close()
        conn.close()


def _next_queued(cur, conn, now=None):
    """Navbatdagi tarqatishni boshlaydi (hech biri ketmayotgan bo'lsa). CAS — bitta worker oladi."""
    now = now or clock.now_ms()
    cur.execute("SELECT id FROM broadcasts WHERE status = 'running'")
    if cur.fetchone():
        return None
    cur.execute("SELECT id FROM broadcasts WHERE status = 'queued' ORDER BY id LIMIT 1")
    row = cur.fetchone()
    if not row:
        return None
    cur.execute("UPDATE broadcasts SET status = 'running', heartbeat_ms = %s WHERE id = %s AND status = 'queued'",
                (now, row['id']))
    took = cur.rowcount == 1
    conn.commit()
    if took:
        _spawn(row['id'])
        return row['id']
    return None


def resume_stale(cur, conn, now=None) -> list:
    """Worker o'lib qolib, yangilanmay qolgan tarqatishlarni davom ettiradi
    (rejalashtiruvchi chaqiradi). heartbeat CAS — faqat bitta worker oladi."""
    now = now or clock.now_ms()
    cur.execute("SELECT id, heartbeat_ms FROM broadcasts WHERE status = 'running' AND heartbeat_ms < %s",
                (now - STALE_MS,))
    resumed = []
    for row in cur.fetchall():
        cur.execute('UPDATE broadcasts SET heartbeat_ms = %s WHERE id = %s AND heartbeat_ms = %s',
                    (now, row['id'], row['heartbeat_ms']))
        if cur.rowcount == 1:
            resumed.append(row['id'])
    conn.commit()
    for bid in resumed:
        _spawn(bid)
    if not resumed:
        nxt = _next_queued(cur, conn, now)
        if nxt:
            resumed.append(nxt)
    return resumed
