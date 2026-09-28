# -*- coding: utf-8 -*-
"""
To'lovlar — admin orqali, Telegram bot chatida (avtomatik to'lov tizimi yo'q).

Jarayon:
  1. O'quvchi ilovada fan(lar)ni tanlaydi (shop.html) → buyurtma yaratiladi,
     bot unga karta raqami, summa va buyurtma kodini (BS-4821) yuboradi.
  2. O'quvchi kartaga pul o'tkazib, chek rasmini botga yuboradi.
  3. Chek adminga "Tasdiqlash / Rad etish" tugmalari bilan boradi.
  4. Admin tasdiqlasa — fanlar ochiladi (subject_purchases), rad etsa —
     o'quvchiga sabab boradi va u qayta urinishi mumkin.

Holatlar: awaiting_receipt → pending → approved | rejected;
          awaiting_receipt → cancelled | expired (24 soatda chek kelmasa).

Narx: har bir fan price_single; "3 ta fan" paketi (price_three) va "barcha
fanlar" paketi (price_all) avtomatik qo'llanadi — o'quvchi uchun eng arzoni.
Promo-kod foizli chegirma beradi. Narxlar va karta admin panelda sozlanadi.
"""

import html
import json
import os
import random
from datetime import datetime

import requests

import admin_auth
import curriculum as cur_mod
import study
import tgbot
from db import TASHKENT_TZ, add_column_if_missing, get_connection
from games import clock

AWAITING, PENDING, APPROVED, REJECTED = 'awaiting_receipt', 'pending', 'approved', 'rejected'
CANCELLED, EXPIRED = 'cancelled', 'expired'
AWAITING_STARS = 'awaiting_stars'        # Telegram Stars invoysi ochildi, to'lov kutilmoqda
OPEN = (AWAITING, PENDING)
CARD, STARS = 'card', 'stars'            # to'lov usuli

ORDER_TTL_MS = 24 * 3600 * 1000          # chek shu vaqt ichida yuborilishi kerak
REMIND_AFTER_MS = 30 * 60 * 1000         # tekshirilmagan chek haqida adminga eslatma
RECEIPTS_PER_DAY = 5                     # bitta o'quvchidan sutkada ko'pi bilan
STATUS_SHOW_MS = 7 * 24 * 3600 * 1000    # ilovada holat ko'rsatiladigan muddat

REJECT_REASONS = {
    'kam': "To'lov summasi kam",
    'oqilmaydi': "Chek rasmi o'qilmaydi",
    'topilmadi': "To'lov kartaga kelib tushmagan",
    'soxta': "Chek haqiqiy emas",
}

DEFAULT_SETTINGS = {
    'card_number': '',
    'card_holder': '',
    'price_single': study.SUBJECT_PRICE,
    'price_three': 30000,
    'price_all': 80000,
    # Telegram Stars narxlari (0 — Stars orqali to'lov o'chiq)
    'stars_single': 100,
    'stars_three': 250,
    'stars_all': 1000,
}
_INT_SETTINGS = ('price_single', 'price_three', 'price_all', 'stars_single', 'stars_three', 'stars_all')


class PayError(Exception):
    def __init__(self, message, code='bad_request', http_status=400):
        super().__init__(message)
        self.message, self.code, self.http_status = message, code, http_status


def ensure_tables(cur, conn):
    cur.execute('CREATE TABLE IF NOT EXISTS pay_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pay_orders (
            id SERIAL PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            chat_id BIGINT NOT NULL,
            items TEXT NOT NULL,
            base_amount INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            promo_code TEXT,
            promo_percent INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            receipt_file_id TEXT,
            receipt_unique_id TEXT,
            receipt_kind TEXT,
            reject_reason TEXT,
            decided_by TEXT,
            admin_msgs TEXT,
            created_ms BIGINT NOT NULL,
            receipt_ms BIGINT,
            decided_ms BIGINT,
            reminded_ms BIGINT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            percent INTEGER NOT NULL,
            max_uses INTEGER,
            used INTEGER NOT NULL DEFAULT 0,
            expires_ms BIGINT,
            active INTEGER NOT NULL DEFAULT 1,
            created_ms BIGINT NOT NULL
        )
    ''')
    # Admin chatidagi xabar → qaysi o'quvchiga tegishli ("Reply" orqali javob uchun)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bot_chat_links (
            admin_chat_id BIGINT NOT NULL,
            admin_message_id BIGINT NOT NULL,
            user_chat_id BIGINT NOT NULL,
            order_id INTEGER,
            created_ms BIGINT NOT NULL,
            PRIMARY KEY (admin_chat_id, admin_message_id)
        )
    ''')
    # Bot suhbatidagi kutilayotgan javob (masalan, promo-kod kiritish)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bot_state (
            chat_id BIGINT PRIMARY KEY,
            state TEXT NOT NULL,
            updated_ms BIGINT NOT NULL
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_pay_orders_user ON pay_orders (user_id, created_ms)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_pay_orders_status ON pay_orders (status, created_ms)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_pay_orders_receipt ON pay_orders (receipt_unique_id)')
    conn.commit()
    # To'lov usuli: card (admin tasdiqlaydi) yoki stars (Telegram Stars — avtomatik).
    # Stars buyurtmalarida amount — Stars soni, charge_id — Telegram to'lov identifikatori.
    add_column_if_missing(cur, conn, 'pay_orders', 'method', "TEXT NOT NULL DEFAULT 'card'")
    add_column_if_missing(cur, conn, 'pay_orders', 'charge_id', 'TEXT')


# ───────────────────────── Yordamchilar ─────────────────────────

def som(n) -> str:
    return f'{int(n or 0):,}'.replace(',', ' ') + " so'm"


def _hhmm(ms) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, TASHKENT_TZ).strftime('%H:%M')


def _date(ms) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, TASHKENT_TZ).strftime('%d.%m.%Y %H:%M')


def _items(order) -> list:
    try:
        return [k for k in json.loads(order['items'] or '[]') if isinstance(k, str)]
    except (TypeError, ValueError):
        return []


def subject_names(keys) -> str:
    return ', '.join(cur_mod.subject_meta(k)['name'] for k in keys)


def _tg_result(res):
    return (res or {}).get('result') if (res or {}).get('ok') else None


def admin_ids() -> list:
    return admin_auth.admin_ids()


def is_admin(telegram_id) -> bool:
    return admin_auth.is_admin_telegram(telegram_id)


# ───────────────────────── Sozlamalar ─────────────────────────

def get_settings(cur) -> dict:
    cur.execute('SELECT key, value FROM pay_settings')
    data = dict(DEFAULT_SETTINGS)
    for r in cur.fetchall():
        if r['key'] in data:
            data[r['key']] = int(r['value']) if r['key'] in _INT_SETTINGS else r['value']
    return data


def save_settings(cur, conn, body) -> dict:
    current = get_settings(cur)
    card = ''.join(ch for ch in str(body.get('card_number', current['card_number']) or '') if ch.isdigit())
    if card and not 16 <= len(card) <= 19:
        raise PayError("Karta raqami 16 ta raqamdan iborat bo'lishi kerak.")
    new = {
        'card_number': ' '.join(card[i:i + 4] for i in range(0, len(card), 4)),
        'card_holder': ' '.join(str(body.get('card_holder', current['card_holder']) or '').split())[:60],
    }
    for key in _INT_SETTINGS:
        try:
            value = int(body.get(key, current[key]))
        except (TypeError, ValueError):
            raise PayError("Narx butun son bo'lishi kerak.")
        if key.startswith('stars_'):
            if value < 0 or value > 100_000:
                raise PayError("Stars narxi 0 dan 100 000 gacha bo'lishi kerak (0 — o'chiq).")
        elif value < 0 or value > 10_000_000 or (key == 'price_single' and value < 1000):
            raise PayError("Narx noto'g'ri (bitta fan kamida 1 000 so'm).")
        new[key] = value
    for key, value in new.items():
        cur.execute('DELETE FROM pay_settings WHERE key = %s', (key,))
        cur.execute('INSERT INTO pay_settings (key, value) VALUES (%s, %s)', (key, str(value)))
    conn.commit()
    return get_settings(cur)


# ───────────────────────── Narx ─────────────────────────

def locked_subjects(cur, user_id) -> list:
    """O'quvchi uchun hali yopiq fanlar (katalog tartibida)."""
    cur.execute('SELECT DISTINCT subject_key FROM topics')
    present = {r['subject_key'] for r in cur.fetchall()}
    chosen = study.get_chosen_subject(cur, user_id)
    cur.execute('SELECT subject_key FROM subject_purchases WHERE user_id = %s', (user_id,))
    bought = {r['subject_key'] for r in cur.fetchall()}
    return [k for k in cur_mod.SUBJECT_CATALOG if k in present and k != chosen and k not in bought]


def bundle_price(settings, n, locked_total, prefix='price'):
    """(eng arzon narx, paket nomi yoki None). prefix='stars' — Telegram Stars narxlari."""
    single, three, whole = settings[f'{prefix}_single'], settings[f'{prefix}_three'], settings[f'{prefix}_all']
    best, label = n * single, None
    if three and n >= 3:
        price = (n // 3) * three + (n % 3) * single
        if price < best:
            best, label = price, '3 ta fan paketi'
    if whole and n == locked_total and n >= 2 and whole < best:
        best, label = whole, 'Barcha fanlar paketi'
    return best, label


def _promo_row(cur, code, user_id, now):
    code = str(code or '').strip().upper()
    if not code:
        return None
    cur.execute('SELECT * FROM promo_codes WHERE code = %s', (code,))
    row = cur.fetchone()
    if not row or not row['active']:
        raise PayError("Bunday promo-kod yo'q.", 'bad_promo')
    if row['expires_ms'] and now > int(row['expires_ms']):
        raise PayError("Promo-kod muddati tugagan.", 'bad_promo')
    if row['max_uses'] is not None and int(row['used']) >= int(row['max_uses']):
        raise PayError("Promo-kod limiti tugagan.", 'bad_promo')
    cur.execute('SELECT 1 FROM pay_orders WHERE user_id = %s AND promo_code = %s AND status = %s',
                (user_id, code, APPROVED))
    if cur.fetchone():
        raise PayError("Siz bu promo-koddan allaqachon foydalangansiz.", 'bad_promo')
    return row


def quote(cur, user_id, keys, promo_code=None, now=None) -> dict:
    now = now or clock.now_ms()
    if not isinstance(keys, list) or not keys or not all(isinstance(k, str) for k in keys):
        raise PayError("Kamida bitta fan tanlang.", 'no_items')
    locked = locked_subjects(cur, user_id)
    wanted = set(keys)
    if not wanted <= set(locked):
        raise PayError("Tanlangan fan allaqachon ochiq yoki mavjud emas.", 'bad_items')
    items = [k for k in locked if k in wanted]
    settings = get_settings(cur)
    base = len(items) * settings['price_single']
    bundled, label = bundle_price(settings, len(items), len(locked))
    promo = _promo_row(cur, promo_code, user_id, now)
    percent = int(promo['percent']) if promo else 0
    amount = int(round(bundled * (100 - percent) / 100 / 100.0)) * 100 if percent else bundled
    stars = None
    if settings['stars_single'] > 0:
        stars_bundled, _ = bundle_price(settings, len(items), len(locked), 'stars')
        stars = max(1, int(round(stars_bundled * (100 - percent) / 100))) if percent else stars_bundled
    return {
        'items': [{'key': k, 'name': cur_mod.subject_meta(k)['name']} for k in items],
        'keys': items,
        'base': base,
        'bundle': label,
        'bundled': bundled,
        'promo': {'code': promo['code'], 'percent': percent} if promo else None,
        'discount': bundled - amount,
        'amount': amount,
        'saving': base - amount,
        'stars': stars,                  # Telegram Stars narxi (None — o'chiq)
    }


# ───────────────────────── Buyurtma ─────────────────────────

def _new_code(cur) -> str:
    for attempt in range(40):
        digits = 4 if attempt < 20 else 6
        code = 'BS-' + str(random.randint(10 ** (digits - 1), 10 ** digits - 1))
        cur.execute('SELECT 1 FROM pay_orders WHERE code = %s', (code,))
        if not cur.fetchone():
            return code
    raise PayError("Buyurtma yaratib bo'lmadi, qayta urinib ko'ring.", 'code_failed', 500)


def order_public(order) -> dict:
    keys = _items(order)
    return {
        'id': order['id'], 'code': order['code'], 'status': order['status'],
        'method': order['method'] or CARD,
        'items': [{'key': k, 'name': cur_mod.subject_meta(k)['name']} for k in keys],
        'amount': int(order['amount']), 'base_amount': int(order['base_amount']),
        'promo_code': order['promo_code'], 'promo_percent': int(order['promo_percent'] or 0),
        'reject_reason': order['reject_reason'],
        'created_ms': int(order['created_ms']),
        'decided_ms': int(order['decided_ms']) if order['decided_ms'] else None,
    }


def _order(cur, order_id):
    cur.execute('SELECT * FROM pay_orders WHERE id = %s', (order_id,))
    return cur.fetchone()


def active_order(cur, user_id):
    cur.execute('SELECT * FROM pay_orders WHERE user_id = %s AND status IN (%s, %s) ORDER BY created_ms DESC',
                (user_id, AWAITING, PENDING))
    return cur.fetchone()


def instructions_text(order, settings) -> str:
    keys = _items(order)
    lines = [f"🧾 <b>Buyurtma {order['code']}</b>", f"📚 {html.escape(subject_names(keys))}"]
    if int(order['promo_percent'] or 0):
        lines.append(f"🎟 Promo-kod {html.escape(order['promo_code'])}: −{order['promo_percent']}%")
    lines.append(f"💰 To'lov summasi: <b>{som(order['amount'])}</b>")
    lines += [
        '',
        "<b>Qanday to'lanadi:</b>",
        f"1. Click, Payme yoki bank ilovasi orqali quyidagi kartaga <b>{som(order['amount'])}</b> o'tkazing:",
        f"💳 <code>{html.escape(settings['card_number'])}</code>",
    ]
    if settings['card_holder']:
        lines.append(f"👤 {html.escape(settings['card_holder'])}")
    lines += [
        f"2. Imkon bo'lsa, to'lov izohiga <code>{order['code']}</code> deb yozing.",
        "3. To'lov chekining rasmini (skrinshot) shu chatga yuboring.",
        '',
        "Admin chekni tekshirib, fanni ochib beradi. Buyurtma 24 soat amal qiladi.",
    ]
    return '\n'.join(lines)


def _order_keyboard(order):
    row = []
    if not order['promo_code']:
        row.append({'text': '🎟 Promo-kod', 'callback_data': f"ord:promo:{order['id']}"})
    row.append({'text': '❌ Bekor qilish', 'callback_data': f"ord:cancel:{order['id']}"})
    return {'inline_keyboard': [row]}


def send_instructions(cur, order) -> bool:
    res = tgbot.tg_api('sendMessage', {
        'chat_id': order['chat_id'], 'text': instructions_text(order, get_settings(cur)),
        'parse_mode': 'HTML', 'reply_markup': _order_keyboard(order),
    })
    return bool(_tg_result(res))


def create_order(cur, conn, user, keys, promo_code=None, now=None) -> tuple:
    """(buyurtma, bot xabari yetib bordimi)."""
    now = now or clock.now_ms()
    if not user.get('telegram_id'):
        raise PayError("To'lov Telegram bot orqali amalga oshiriladi. BilimSari'ni Telegram'dan oching.",
                       'no_telegram')
    if not get_settings(cur)['card_number']:
        raise PayError("To'lov vaqtincha ishlamayapti. Birozdan keyin urinib ko'ring.", 'not_configured', 503)
    current = active_order(cur, user['id'])
    if current and current['status'] == PENDING:
        raise PayError(f"Oldingi chekingiz ({current['code']}) tekshirilmoqda. Natijani kuting.", 'pending_exists', 409)
    q = quote(cur, user['id'], keys, promo_code, now)
    cur.execute('UPDATE pay_orders SET status = %s WHERE user_id = %s AND status = %s',
                (CANCELLED, user['id'], AWAITING))
    code = _new_code(cur)
    cur.execute(
        '''INSERT INTO pay_orders (code, user_id, chat_id, items, base_amount, amount, promo_code, promo_percent,
                                   status, created_ms)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
        (code, user['id'], int(user['telegram_id']), json.dumps(q['keys']), q['base'], q['amount'],
         q['promo']['code'] if q['promo'] else None, q['promo']['percent'] if q['promo'] else 0, AWAITING, now),
    )
    order_id = cur.fetchone()['id']
    conn.commit()
    order = _order(cur, order_id)
    return order, send_instructions(cur, order)


def cancel_order(cur, conn, order_id, user_id) -> bool:
    cur.execute('UPDATE pay_orders SET status = %s WHERE id = %s AND user_id = %s AND status = %s',
                (CANCELLED, order_id, user_id, AWAITING))
    ok = cur.rowcount == 1
    conn.commit()
    return ok


def apply_promo(cur, conn, order, code, now=None):
    """Bot orqali kiritilgan promo-kod — summani qayta hisoblab yangilaydi."""
    now = now or clock.now_ms()
    if order['status'] != AWAITING:
        raise PayError("Bu buyurtmaga promo-kod qo'llab bo'lmaydi.", 'bad_state')
    q = quote(cur, order['user_id'], _items(order), code, now)
    cur.execute('UPDATE pay_orders SET amount = %s, promo_code = %s, promo_percent = %s WHERE id = %s AND status = %s',
                (q['amount'], q['promo']['code'], q['promo']['percent'], order['id'], AWAITING))
    conn.commit()
    return _order(cur, order['id'])


def user_orders(cur, user_id, limit=20) -> list:
    cur.execute('SELECT * FROM pay_orders WHERE user_id = %s AND status NOT IN (%s, %s) ORDER BY created_ms DESC LIMIT %s',
                (user_id, CANCELLED, AWAITING_STARS, limit))
    return [order_public(o) for o in cur.fetchall()]


def subject_statuses(cur, user_id, now=None) -> dict:
    """Yopiq fanlar uchun oxirgi buyurtma holati: {fan: {'status', 'code', 'reason'}}."""
    now = now or clock.now_ms()
    cur.execute('SELECT * FROM pay_orders WHERE user_id = %s AND created_ms >= %s ORDER BY created_ms DESC',
                (user_id, now - STATUS_SHOW_MS))
    out = {}
    for o in cur.fetchall():
        for k in _items(o):
            if k not in out:
                out[k] = {'status': o['status'], 'code': o['code'], 'reason': o['reject_reason']}
    return {k: v for k, v in out.items() if v['status'] in (AWAITING, PENDING, REJECTED)}


def annotate_subjects(cur, user_id, subjects):
    """Fan kartalariga joriy narx va to'lov holatini qo'shadi."""
    price = get_settings(cur)['price_single']
    statuses = subject_statuses(cur, user_id)
    for s in subjects or []:
        if s.get('locked'):
            s['price'] = price
            st = statuses.get(s['key'])
            s['pay_status'] = st['status'] if st else None
    return subjects


# ───────────────────────── Chek ─────────────────────────

def _user_by_tg(cur, telegram_id):
    cur.execute('SELECT id, name, username, telegram_id FROM users WHERE telegram_id = %s', (telegram_id,))
    return cur.fetchone()


def admin_caption(cur, order, note='') -> str:
    cur.execute('SELECT name, username FROM users WHERE id = %s', (order['user_id'],))
    u = cur.fetchone() or {}
    who = html.escape(u.get('name') or "O'quvchi") + f" (ID {order['user_id']}" + \
        (f", @{html.escape(u['username'])}" if u.get('username') else '') + ')'
    lines = [
        f"🧾 <b>To'lov — {order['code']}</b>",
        f"👤 {who}",
        f"📚 {html.escape(subject_names(_items(order)))}",
        f"💰 <b>{som(order['amount'])}</b>" + (
            f" (promo {html.escape(order['promo_code'])} −{order['promo_percent']}%)" if order['promo_code'] else ''),
        f"🕒 {_hhmm(order['receipt_ms'] or order['created_ms'])}",
    ]
    cur.execute('''SELECT o.code, u.name FROM pay_orders o LEFT JOIN users u ON u.id = o.user_id
                   WHERE o.receipt_unique_id = %s AND o.id != %s ORDER BY o.created_ms''',
                (order['receipt_unique_id'], order['id']))
    dups = cur.fetchall() if order['receipt_unique_id'] else []
    if dups:
        lines.append('⚠️ <b>Diqqat: bu chek avval yuborilgan</b> — ' + ', '.join(
            f"{d['code']} ({html.escape(d['name'] or '?')})" for d in dups[:3]))
    if note:
        lines += ['', note]
    return '\n'.join(lines)


DECIDE_KEYBOARD = lambda oid: {'inline_keyboard': [[  # noqa: E731
    {'text': '✅ Tasdiqlash', 'callback_data': f'pay:ok:{oid}'},
    {'text': '❌ Rad etish', 'callback_data': f'pay:no:{oid}'},
]]}


def reasons_keyboard(order_id):
    rows = [[{'text': text, 'callback_data': f'pay:rj:{order_id}:{key}'}] for key, text in REJECT_REASONS.items()]
    rows.append([{'text': '⬅️ Orqaga', 'callback_data': f'pay:back:{order_id}'}])
    return {'inline_keyboard': rows}


def link_message(cur, admin_chat_id, message_id, user_chat_id, order_id=None, now=None):
    cur.execute('DELETE FROM bot_chat_links WHERE admin_chat_id = %s AND admin_message_id = %s',
                (admin_chat_id, message_id))
    cur.execute('INSERT INTO bot_chat_links (admin_chat_id, admin_message_id, user_chat_id, order_id, created_ms) '
                'VALUES (%s, %s, %s, %s, %s)', (admin_chat_id, message_id, user_chat_id, order_id, now or clock.now_ms()))


def attach_receipt(cur, conn, chat_id, file_id, unique_id, kind, now=None):
    """O'quvchi chek yubordi. Javob matnini qaytaradi; faol buyurtma bo'lmasa None
    (xabar jonli chat sifatida adminga boradi)."""
    now = now or clock.now_ms()
    user = _user_by_tg(cur, chat_id)
    if not user:
        return None
    order = active_order(cur, user['id'])
    if not order:
        return None
    if order['status'] == PENDING:
        return (f"Chekingiz ({order['code']}) allaqachon tekshirilmoqda. Natija shu yerga keladi. "
                "Savolingiz bo'lsa, matn bilan yozing.")
    if int(order['created_ms']) < now - ORDER_TTL_MS:
        cur.execute('UPDATE pay_orders SET status = %s WHERE id = %s', (EXPIRED, order['id']))
        conn.commit()
        return "Bu buyurtmaning muddati tugagan. Ilovada qaytadan «Sotib olish»ni bosing."
    cur.execute('SELECT COUNT(*) AS n FROM pay_orders WHERE user_id = %s AND receipt_ms >= %s',
                (user['id'], now - 24 * 3600 * 1000))
    if int(cur.fetchone()['n']) >= RECEIPTS_PER_DAY:
        return "Bugun juda ko'p chek yuborildi. Ertaga qayta urinib ko'ring yoki adminga yozing."

    cur.execute('''UPDATE pay_orders SET status = %s, receipt_file_id = %s, receipt_unique_id = %s,
                                         receipt_kind = %s, receipt_ms = %s
                   WHERE id = %s AND status = %s''',
                (PENDING, file_id, unique_id, kind, now, order['id'], AWAITING))
    if cur.rowcount != 1:
        conn.rollback()
        return "Buyurtma holati o'zgargan. Qaytadan urinib ko'ring."
    conn.commit()
    order = _order(cur, order['id'])
    send_to_admins(cur, conn, order)
    return (f"✅ Chek qabul qilindi! Buyurtma <b>{order['code']}</b> adminga yuborildi.\n"
            "Odatda 5–30 daqiqada tekshiriladi — natija shu yerga keladi.")


def send_to_admins(cur, conn, order):
    caption = admin_caption(cur, order)
    method, field = ('sendPhoto', 'photo') if order['receipt_kind'] == 'photo' else ('sendDocument', 'document')
    sent = []
    for admin in admin_ids():
        res = _tg_result(tgbot.tg_api(method, {
            'chat_id': admin, field: order['receipt_file_id'], 'caption': caption,
            'parse_mode': 'HTML', 'reply_markup': DECIDE_KEYBOARD(order['id']),
        }))
        if res:
            sent.append([admin, res['message_id']])
            link_message(cur, admin, res['message_id'], order['chat_id'], order['id'])
    cur.execute('UPDATE pay_orders SET admin_msgs = %s WHERE id = %s', (json.dumps(sent), order['id']))
    conn.commit()


# ───────────────────────── Admin qarori ─────────────────────────

def decide(cur, conn, order_id, approve, by, reason_key=None, now=None) -> tuple:
    """(bajarildimi, izoh). Ikki admin bir vaqtda bossa ham faqat bittasi o'tadi."""
    now = now or clock.now_ms()
    order = _order(cur, order_id)
    if not order:
        return False, "Buyurtma topilmadi."
    if order['status'] != PENDING:
        return False, "Bu to'lov allaqachon hal qilingan."
    reason = None
    if not approve:
        reason = REJECT_REASONS.get(reason_key)
        if not reason:
            return False, "Sababni tanlang."
    cur.execute('''UPDATE pay_orders SET status = %s, decided_ms = %s, decided_by = %s, reject_reason = %s
                   WHERE id = %s AND status = %s''',
                (APPROVED if approve else REJECTED, now, by, reason, order_id, PENDING))
    if cur.rowcount != 1:
        conn.rollback()
        return False, "Bu to'lov allaqachon hal qilingan."
    keys = _items(order)
    if approve:
        for k in keys:
            cur.execute('INSERT INTO subject_purchases (user_id, subject_key) VALUES (%s, %s) '
                        'ON CONFLICT (user_id, subject_key) DO NOTHING', (order['user_id'], k))
        if order['promo_code']:
            cur.execute('UPDATE promo_codes SET used = used + 1 WHERE code = %s', (order['promo_code'],))
    conn.commit()
    order = _order(cur, order_id)

    if approve:
        tgbot.send(order['chat_id'],
                   f"🎉 <b>To'lov tasdiqlandi!</b> ({order['code']})\n"
                   f"{html.escape(subject_names(keys))} — ochildi. Omad!",
                   'Darsni boshlash', f'topics.html?fan={keys[0]}' if keys else 'dashboard.html')
    else:
        tgbot.tg_api('sendMessage', {
            'chat_id': order['chat_id'], 'parse_mode': 'HTML',
            'text': (f"❌ <b>To'lov tasdiqlanmadi</b> ({order['code']})\nSabab: {html.escape(reason)}\n\n"
                     "To'g'ri chek bilan qayta urinib ko'ring. Savolingiz bo'lsa, shu yerga yozing — admin javob beradi."),
            'reply_markup': {'inline_keyboard': [[{'text': '🔄 Qayta urinish', 'callback_data': f'ord:retry:{order_id}'}]]},
        })
    status = (f"✅ <b>Tasdiqlandi</b> — {html.escape(by)}, {_hhmm(now)}" if approve
              else f"❌ <b>Rad etildi</b> ({html.escape(reason)}) — {html.escape(by)}, {_hhmm(now)}")
    caption = admin_caption(cur, order, status)
    for chat, message_id in json.loads(order['admin_msgs'] or '[]'):
        tgbot.tg_api('editMessageCaption', {
            'chat_id': chat, 'message_id': message_id, 'caption': caption, 'parse_mode': 'HTML',
            'reply_markup': {'inline_keyboard': []},
        })
    return True, 'Tasdiqlandi' if approve else 'Rad etildi'


def retry_order(cur, conn, order_id, chat_id, now=None):
    """Rad etilgan buyurtma o'rniga xuddi shu fanlar bilan yangisi."""
    order = _order(cur, order_id)
    if not order or int(order['chat_id']) != int(chat_id) or order['status'] != REJECTED:
        raise PayError("Bu buyurtmani qayta ochib bo'lmaydi.", 'bad_state')
    cur.execute('SELECT id, name, telegram_id FROM users WHERE id = %s', (order['user_id'],))
    user = cur.fetchone()
    keys = [k for k in _items(order) if k in locked_subjects(cur, order['user_id'])]
    promo = order['promo_code']
    try:
        return create_order(cur, conn, user, keys, promo, now)
    except PayError as exc:
        if exc.code != 'bad_promo':
            raise
        return create_order(cur, conn, user, keys, None, now)


# ───────────────────────── Telegram Stars ─────────────────────────
# Raqamli mahsulot uchun Telegram tavsiya qiladigan yo'l: to'lov Telegram'ning
# o'z oynasida bo'ladi (openInvoice), tasdiq webhook orqali keladi va fan
# admin aralashuvisiz darhol ochiladi.

def create_stars_order(cur, conn, user, keys, promo_code=None, now=None) -> tuple:
    """(buyurtma, invoys havolasi)."""
    now = now or clock.now_ms()
    q = quote(cur, user['id'], keys, promo_code, now)
    if not q['stars']:
        raise PayError("Telegram Stars orqali to'lov hozircha o'chiq.", 'stars_off')
    code = _new_code(cur)
    names = subject_names(q['keys'])
    cur.execute(
        '''INSERT INTO pay_orders (code, user_id, chat_id, items, base_amount, amount, promo_code, promo_percent,
                                   status, created_ms, method)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
        (code, user['id'], int(user.get('telegram_id') or 0), json.dumps(q['keys']), q['stars'], q['stars'],
         q['promo']['code'] if q['promo'] else None, q['promo']['percent'] if q['promo'] else 0,
         AWAITING_STARS, now, STARS),
    )
    order_id = cur.fetchone()['id']
    conn.commit()
    title = ('BilimSari: ' + (names if len(q['keys']) == 1 else f"{len(q['keys'])} ta fan"))[:32]
    res = _tg_result(tgbot.tg_api('createInvoiceLink', {
        'title': title,
        'description': (f"{names} — fan(lar)ga to'liq kirish. Buyurtma {code}.")[:255],
        'payload': code,
        'currency': 'XTR',
        'prices': [{'label': title, 'amount': q['stars']}],
    }))
    if not res:
        cur.execute('UPDATE pay_orders SET status = %s WHERE id = %s', (CANCELLED, order_id))
        conn.commit()
        raise PayError("Telegram to'lov oynasini ochib bo'lmadi. Birozdan keyin urinib ko'ring.", 'invoice_failed', 502)
    return _order(cur, order_id), res


def _stars_order(cur, payload):
    cur.execute('SELECT * FROM pay_orders WHERE code = %s AND method = %s', (str(payload or ''), STARS))
    return cur.fetchone()


def answer_pre_checkout(pcq):
    """Telegram to'lovdan oldin so'raydi: buyurtma hali amaldami? 10 soniyada javob kerak."""
    conn = get_connection()
    cur = conn.cursor()
    error = None
    try:
        order = _stars_order(cur, pcq.get('invoice_payload'))
        if not order or order['status'] != AWAITING_STARS:
            error = "Buyurtma topilmadi yoki muddati tugagan. Do'kondan qaytadan urinib ko'ring."
        elif pcq.get('currency') != 'XTR' or int(pcq.get('total_amount') or 0) != int(order['amount']):
            error = "To'lov summasi mos kelmadi. Do'kondan qaytadan urinib ko'ring."
        elif any(k not in locked_subjects(cur, order['user_id']) for k in _items(order)):
            error = "Bu fan allaqachon ochilgan."
    finally:
        cur.close()
        conn.close()
    payload = {'pre_checkout_query_id': pcq.get('id'), 'ok': error is None}
    if error:
        payload['error_message'] = error
    tgbot.tg_api('answerPreCheckoutQuery', payload)
    return error is None


def stars_paid(message, now=None):
    """Muvaffaqiyatli Stars to'lovi: fanlar ochiladi, o'quvchi va adminlarga xabar."""
    now = now or clock.now_ms()
    sp = message.get('successful_payment') or {}
    conn = get_connection()
    cur = conn.cursor()
    try:
        order = _stars_order(cur, sp.get('invoice_payload'))
        if not order:
            return False
        cur.execute('''UPDATE pay_orders SET status = %s, decided_ms = %s, decided_by = %s, charge_id = %s
                       WHERE id = %s AND status != %s''',
                    (APPROVED, now, 'Telegram Stars', sp.get('telegram_payment_charge_id'), order['id'], APPROVED))
        if cur.rowcount != 1:
            conn.rollback()
            return False                      # allaqachon ishlangan
        keys = _items(order)
        for k in keys:
            cur.execute('INSERT INTO subject_purchases (user_id, subject_key) VALUES (%s, %s) '
                        'ON CONFLICT (user_id, subject_key) DO NOTHING', (order['user_id'], k))
        if order['promo_code']:
            cur.execute('UPDATE promo_codes SET used = used + 1 WHERE code = %s', (order['promo_code'],))
        conn.commit()
        chat = (message.get('chat') or {}).get('id') or order['chat_id']
        tgbot.send(chat, f"🎉 <b>To'lov qabul qilindi!</b> ({order['code']})\n"
                         f"{html.escape(subject_names(keys))} — ochildi. Omad!",
                   'Darsni boshlash', f'topics.html?fan={keys[0]}' if keys else 'dashboard.html')
        cur.execute('SELECT name FROM users WHERE id = %s', (order['user_id'],))
        who = html.escape((cur.fetchone() or {}).get('name') or "O'quvchi")
        for admin in admin_ids():
            tgbot.tg_api('sendMessage', {'chat_id': admin, 'parse_mode': 'HTML', 'text': (
                f"⭐ <b>Stars to'lovi</b> — {order['code']}\n👤 {who} (ID {order['user_id']})\n"
                f"📚 {html.escape(subject_names(keys))}\n💰 {int(order['amount'])} Stars — fan avtomatik ochildi.")})
        return True
    finally:
        cur.close()
        conn.close()


# ───────────────────────── Promo-kodlar ─────────────────────────

def list_promos(cur) -> list:
    cur.execute('SELECT * FROM promo_codes ORDER BY created_ms DESC')
    return [{
        'code': r['code'], 'percent': int(r['percent']), 'max_uses': r['max_uses'], 'used': int(r['used']),
        'expires_ms': int(r['expires_ms']) if r['expires_ms'] else None, 'active': bool(r['active']),
    } for r in cur.fetchall()]


def create_promo(cur, conn, body, now=None):
    now = now or clock.now_ms()
    code = str(body.get('code') or '').strip().upper()
    if not code.isalnum() or not 3 <= len(code) <= 20:
        raise PayError("Promo-kod 3–20 ta lotin harfi yoki raqamdan iborat bo'lsin.")
    try:
        percent = int(body.get('percent'))
        max_uses = int(body['max_uses']) if body.get('max_uses') not in (None, '') else None
        days = int(body['days']) if body.get('days') not in (None, '') else None
    except (TypeError, ValueError):
        raise PayError("Qiymatlar butun son bo'lishi kerak.")
    if not 1 <= percent <= 90:
        raise PayError("Chegirma 1% dan 90% gacha bo'lishi mumkin.")
    if (max_uses is not None and max_uses < 1) or (days is not None and days < 1):
        raise PayError("Limit va muddat musbat son bo'lishi kerak.")
    cur.execute('SELECT 1 FROM promo_codes WHERE code = %s', (code,))
    if cur.fetchone():
        raise PayError("Bunday promo-kod allaqachon bor.", 'exists', 409)
    cur.execute('INSERT INTO promo_codes (code, percent, max_uses, used, expires_ms, active, created_ms) '
                'VALUES (%s, %s, %s, 0, %s, 1, %s)',
                (code, percent, max_uses, now + days * 24 * 3600 * 1000 if days else None, now))
    conn.commit()
    return code


def toggle_promo(cur, conn, code):
    cur.execute('UPDATE promo_codes SET active = 1 - active WHERE code = %s', (str(code).upper(),))
    ok = cur.rowcount == 1
    conn.commit()
    return ok


# ───────────────────────── Admin panel ─────────────────────────

def overview(cur, now=None) -> dict:
    now = now or clock.now_ms()
    day = clock.period_start_ms('day', now)
    month = clock.period_start_ms('month', now)

    def total(since, method=CARD):
        cur.execute('SELECT COUNT(*) AS n, COALESCE(SUM(amount), 0) AS s FROM pay_orders '
                    'WHERE status = %s AND decided_ms >= %s AND method = %s', (APPROVED, since, method))
        r = cur.fetchone()
        return {'count': int(r['n']), 'sum': int(r['s'])}

    cur.execute('SELECT COUNT(*) AS n FROM pay_orders WHERE status = %s', (PENDING,))
    pending = int(cur.fetchone()['n'])
    # so'mdagi tushum — faqat karta orqali; Stars alohida hisoblanadi
    return {'today': total(day), 'month': total(month), 'all': total(0), 'pending': pending,
            'stars_month': total(month, STARS), 'stars_all': total(0, STARS)}


# Telegram qoidalari: bot olgan Stars 21 kundan keyin yechib olinadi (Fragment
# orqali, TON'ga), bir martada kamida 1000 Stars; egasiga 1 Star ≈ 0.013 $.
STARS_HOLD_DAYS = 21
STARS_MIN_WITHDRAW = 1000
STARS_USD = 0.013
USD_UZS = int(os.environ.get('USD_UZS', '12700'))   # taxminiy kurs — faqat ko'rsatish uchun
STARS_CACHE_MS = 60 * 1000
_stars_cache = {'at': 0, 'data': None}


def _star_transactions(max_pages=10) -> list:
    txs, offset = [], 0
    for _ in range(max_pages):
        res = _tg_result(tgbot.tg_api('getStarTransactions', {'offset': offset, 'limit': 100}))
        batch = (res or {}).get('transactions') or []
        txs += batch
        if len(batch) < 100:
            break
        offset += len(batch)
    return txs


def stars_balance(now=None, refresh=False) -> dict:
    """Botning Stars balansi (Telegram'dan) va qachon yechib olish mumkinligi."""
    now = now or clock.now_ms()
    cached = _stars_cache['data']
    if cached and not refresh and now - _stars_cache['at'] < STARS_CACHE_MS:
        return cached
    bal = _tg_result(tgbot.tg_api('getMyStarBalance', {}))
    if bal is None:
        return {'ok': False, 'error': "Telegram'dan balansni olib bo'lmadi."}
    balance = int(bal.get('amount') or 0)
    hold_from = now // 1000 - STARS_HOLD_DAYS * 86400
    held, releases, received, withdrawn, refunded = 0, {}, 0, 0, 0
    for t in _star_transactions():
        amount, when = int(t.get('amount') or 0), int(t.get('date') or 0)
        if t.get('source'):                                   # kirim
            received += amount
            if when > hold_from:
                held += amount
                day = datetime.fromtimestamp(when + STARS_HOLD_DAYS * 86400, TASHKENT_TZ).date().isoformat()
                releases[day] = releases.get(day, 0) + amount
        elif (t.get('receiver') or {}).get('type') == 'fragment':
            withdrawn += amount                               # yechib olingan
        elif t.get('receiver'):
            refunded += amount                                # qaytarilgan (refund)
    ready = max(0, balance - held)
    data = {
        'ok': True, 'balance': balance, 'held': min(held, balance), 'ready': ready,
        'can_withdraw': ready >= STARS_MIN_WITHDRAW, 'min_withdraw': STARS_MIN_WITHDRAW,
        'hold_days': STARS_HOLD_DAYS,
        'releases': [{'date': d, 'amount': a} for d, a in sorted(releases.items())][:10],
        'received': received, 'withdrawn': withdrawn, 'refunded': refunded,
        'usd': round(balance * STARS_USD, 2), 'uzs': int(round(balance * STARS_USD * USD_UZS, -2)),
        'usd_rate': STARS_USD, 'checked_ms': now,
    }
    _stars_cache.update(at=now, data=data)
    return data


def admin_orders(cur, status=None, page=1, per_page=30) -> dict:
    where, params = (("WHERE o.status = %s", [status]) if status
                     else ("WHERE o.status NOT IN (%s, %s)", [CANCELLED, AWAITING_STARS]))
    cur.execute(f'SELECT COUNT(*) AS n FROM pay_orders o {where}', params)
    count = int(cur.fetchone()['n'])
    cur.execute(f'''SELECT o.*, u.name AS user_name, u.username FROM pay_orders o
                    LEFT JOIN users u ON u.id = o.user_id {where}
                    ORDER BY o.created_ms DESC LIMIT %s OFFSET %s''',
                params + [per_page, (page - 1) * per_page])
    rows = cur.fetchall()
    out = []
    for o in rows:
        item = order_public(o)
        item.update({
            'user_id': o['user_id'], 'user_name': o['user_name'], 'username': o['username'],
            'has_receipt': bool(o['receipt_file_id']), 'receipt_kind': o['receipt_kind'],
            'receipt_ms': int(o['receipt_ms']) if o['receipt_ms'] else None, 'decided_by': o['decided_by'],
        })
        if o['receipt_unique_id']:
            cur.execute('SELECT code FROM pay_orders WHERE receipt_unique_id = %s AND id != %s',
                        (o['receipt_unique_id'], o['id']))
            item['duplicate_of'] = [r['code'] for r in cur.fetchall()]
        out.append(item)
    return {'orders': out, 'total': count, 'page': page, 'per_page': per_page}


def receipt_file(cur, order_id):
    """Chek faylini Telegram'dan olib beradi: (mime, baytlar) yoki None. Bot tokeni
    faqat serverda qoladi."""
    order = _order(cur, order_id)
    if not order or not order['receipt_file_id'] or not tgbot.BOT_TOKEN:
        return None
    info = _tg_result(tgbot.tg_api('getFile', {'file_id': order['receipt_file_id']}))
    if not info or not info.get('file_path'):
        return None
    try:
        r = requests.get(f"https://api.telegram.org/file/bot{tgbot.BOT_TOKEN}/{info['file_path']}", timeout=20)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    path = info['file_path'].lower()
    mime = ('application/pdf' if path.endswith('.pdf') else 'image/png' if path.endswith('.png')
            else 'image/webp' if path.endswith('.webp') else 'image/jpeg')
    return mime, r.content


# ───────────────────────── Rejalashtiruvchi ─────────────────────────

def housekeeping(cur, conn, now=None) -> dict:
    """Muddati o'tgan buyurtmalarni yopadi va 30 daqiqadan beri tekshirilmagan
    cheklar haqida adminlarga bir marta eslatadi."""
    now = now or clock.now_ms()
    cur.execute('UPDATE pay_orders SET status = %s WHERE status = %s AND created_ms < %s',
                (EXPIRED, AWAITING, now - ORDER_TTL_MS))
    expired = cur.rowcount
    # To'lanmay qolgan Stars invoyslari — tarixda ko'rinmasligi uchun bekor qilinadi
    cur.execute('UPDATE pay_orders SET status = %s WHERE status = %s AND created_ms < %s',
                (CANCELLED, AWAITING_STARS, now - ORDER_TTL_MS))
    conn.commit()
    cur.execute('SELECT id, code, amount FROM pay_orders WHERE status = %s AND receipt_ms < %s AND reminded_ms IS NULL '
                'ORDER BY receipt_ms', (PENDING, now - REMIND_AFTER_MS))
    late = cur.fetchall()
    if late:
        text = (f"⏰ <b>{len(late)} ta chek</b> 30 daqiqadan beri tekshirilmay turibdi:\n" +
                '\n'.join(f"• {o['code']} — {som(o['amount'])}" for o in late[:15]))
        for admin in admin_ids():
            tgbot.send(admin, text, 'Admin panel', 'admin.html')
        marks = ', '.join(['%s'] * len(late))
        cur.execute(f'UPDATE pay_orders SET reminded_ms = %s WHERE id IN ({marks})', [now] + [o['id'] for o in late])
        conn.commit()
    return {'expired': expired, 'reminded': len(late)}


def daily_summary(cur, now=None):
    """Kechki hisobot matni (bugun hech narsa bo'lmagan bo'lsa — None)."""
    now = now or clock.now_ms()
    day = clock.period_start_ms('day', now)
    cur.execute('SELECT status, COUNT(*) AS n, COALESCE(SUM(amount), 0) AS s FROM pay_orders '
                'WHERE (decided_ms >= %s OR receipt_ms >= %s) GROUP BY status', (day, day))
    by = {r['status']: (int(r['n']), int(r['s'])) for r in cur.fetchall()}
    cur.execute('SELECT COUNT(*) AS n FROM pay_orders WHERE status = %s', (PENDING,))
    pending = int(cur.fetchone()['n'])
    if not by and not pending:
        return None
    ok_n, ok_s = by.get(APPROVED, (0, 0))
    return (f"📊 <b>Bugungi to'lovlar</b>\n"
            f"✅ Tasdiqlangan: {ok_n} ta — <b>{som(ok_s)}</b>\n"
            f"❌ Rad etilgan: {by.get(REJECTED, (0, 0))[0]} ta\n"
            f"⏳ Kutilmoqda: {pending} ta")
