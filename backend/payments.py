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
import random
from datetime import datetime

import requests

import admin_auth
import curriculum as cur_mod
import partners
import premium
import study
import tgbot
from db import TASHKENT_TZ, add_column_if_missing, get_connection
from games import clock

AWAITING, PENDING, APPROVED, REJECTED = 'awaiting_receipt', 'pending', 'approved', 'rejected'
CANCELLED, EXPIRED = 'cancelled', 'expired'
OPEN = (AWAITING, PENDING)

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
    # Bilim Premium: 1 oy; 3 oy va 1 yil — admin narx qo'ymaguncha (0) sotilmaydi
    'premium_price': 34900,
    'premium_price_3': 0,
    'premium_price_12': 0,
}
_INT_SETTINGS = ('price_single', 'price_three', 'price_all', 'premium_price', 'premium_price_3', 'premium_price_12')


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
    # Eski ustunlar (Telegram Stars davridan) — endi faqat karta, lekin eski bazalar bilan mos bo'lsin
    add_column_if_missing(cur, conn, 'pay_orders', 'method', "TEXT NOT NULL DEFAULT 'card'")
    add_column_if_missing(cur, conn, 'pay_orders', 'charge_id', 'TEXT')
    # Telegram Stars to'lovi olib tashlandi: ochiq qolgan Stars invoyslari va narx sozlamalari tozalanadi
    cur.execute("UPDATE pay_orders SET status = %s WHERE status = 'awaiting_stars'", (CANCELLED,))
    cur.execute("DELETE FROM pay_settings WHERE key IN ('stars_single', 'stars_three', 'stars_all', 'premium_stars')")
    conn.commit()


# ───────────────────────── Yordamchilar ─────────────────────────

def som(n, lang='uz') -> str:
    return f'{int(n or 0):,}'.replace(',', ' ') + (' сум' if lang == 'ru' else " so'm")


def _hhmm(ms) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, TASHKENT_TZ).strftime('%H:%M')


def _date(ms) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, TASHKENT_TZ).strftime('%d.%m.%Y %H:%M')


def _items(order) -> list:
    try:
        return [k for k in json.loads(order['items'] or '[]') if isinstance(k, str)]
    except (TypeError, ValueError):
        return []


def item_name(key, lang='uz') -> str:
    if key in premium.PLANS:
        return premium.PLANS[key][3] if lang == 'ru' else premium.PLANS[key][2]
    name = cur_mod.subject_meta(key)['name']
    return tgbot.fan_ru(name) if lang == 'ru' else name


def is_premium(order_or_keys) -> bool:
    keys = order_or_keys if isinstance(order_or_keys, list) else _items(order_or_keys)
    return premium.plan_of(keys) is not None


def subject_names(keys, lang='uz') -> str:
    return ', '.join(item_name(k, lang) for k in keys)


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
        if key == 'premium_price':
            if value < 1000 or value > 10_000_000:
                raise PayError("Premium narxi kamida 1 000 so'm bo'lishi kerak.")
        elif key in ('premium_price_3', 'premium_price_12'):
            if value and (value < 1000 or value > 50_000_000):
                raise PayError("Premium 3 oy / 1 yil narxi 0 (sotilmaydi) yoki kamida 1 000 so'm bo'lsin.")
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


def bundle_price(settings, n, locked_total):
    """(eng arzon narx, paket nomi yoki None)."""
    single, three, whole = settings['price_single'], settings['price_three'], settings['price_all']
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
    if row['partner_user_id'] is not None and int(row['partner_user_id']) == int(user_id):
        raise PayError("O'zingizning hamkorlik kodingizdan foydalana olmaysiz — uni do'stlaringizga ulashing.",
                       'bad_promo')
    cur.execute('SELECT 1 FROM pay_orders WHERE user_id = %s AND promo_code = %s AND status = %s',
                (user_id, code, APPROVED))
    if cur.fetchone():
        raise PayError("Siz bu promo-koddan allaqachon foydalangansiz.", 'bad_promo')
    return row


def premium_quote(cur, user_id, promo_code=None, now=None, plan=None) -> dict:
    """Bilim Premium narxi (tarif bo'yicha). Faol bo'lsa — sotib olinmaydi (tugagach yana ochiladi)."""
    now = now or clock.now_ms()
    plan = plan if plan in premium.PLANS else premium.ITEM
    if premium.is_active(premium.until(cur, user_id), now):
        raise PayError("Premium hali faol — muddati tugagach qayta olish mumkin.", 'premium_active', 409)
    settings = get_settings(cur)
    base = int(settings.get(premium.PLANS[plan][4]) or 0)
    if base <= 0:
        raise PayError("Bu tarif hozircha sotilmaydi.", 'plan_off')
    promo = _promo_row(cur, promo_code, user_id, now)
    percent = int(promo['percent']) if promo else 0
    amount = int(round(base * (100 - percent) / 100 / 100.0)) * 100 if percent else base
    return {
        'items': [{'key': plan, 'name': premium.PLANS[plan][2]}], 'keys': [plan],
        'base': base, 'bundle': None, 'bundled': base,
        'promo': {'code': promo['code'], 'percent': percent} if promo else None,
        'discount': base - amount, 'amount': amount, 'saving': base - amount,
    }


def quote(cur, user_id, keys, promo_code=None, now=None) -> dict:
    now = now or clock.now_ms()
    if premium.plan_of(keys):
        return premium_quote(cur, user_id, promo_code, now, premium.plan_of(keys))
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
        'items': [{'key': k, 'name': item_name(k)} for k in keys],
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


def instructions_text(order, settings, lang='uz') -> str:
    if lang == 'ru':
        return _instructions_ru(order, settings)
    keys = _items(order)
    lines = [f"🧾 <b>Buyurtma {order['code']}</b>", f"📚 {html.escape(subject_names(keys))}"]
    if int(order['promo_percent'] or 0):
        lines.append(f"🎟 Promo-kod {html.escape(order['promo_code'])}: −{order['promo_percent']}%")
    elif order['promo_code']:
        lines.append(f"🎟 Promo-kod {html.escape(order['promo_code'])}")
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
        ("Admin chekni tekshirib, Premium'ni faollashtiradi. Buyurtma 24 soat amal qiladi." if is_premium(keys)
         else "Admin chekni tekshirib, fanni ochib beradi. Buyurtma 24 soat amal qiladi."),
    ]
    return '\n'.join(lines)


def _instructions_ru(order, settings) -> str:
    keys = _items(order)
    lines = [f"🧾 <b>Заказ {order['code']}</b>", f"📚 {html.escape(subject_names(keys, 'ru'))}"]
    if int(order['promo_percent'] or 0):
        lines.append(f"🎟 Промокод {html.escape(order['promo_code'])}: −{order['promo_percent']}%")
    elif order['promo_code']:
        lines.append(f"🎟 Промокод {html.escape(order['promo_code'])}")
    lines.append(f"💰 Сумма оплаты: <b>{som(order['amount'], 'ru')}</b>")
    lines += [
        '',
        '<b>Как оплатить:</b>',
        f"1. Переведите <b>{som(order['amount'], 'ru')}</b> на эту карту через Click, Payme или банковское приложение:",
        f"💳 <code>{html.escape(settings['card_number'])}</code>",
    ]
    if settings['card_holder']:
        lines.append(f"👤 {html.escape(settings['card_holder'])}")
    lines += [
        f"2. Если возможно, укажите в комментарии к платежу <code>{order['code']}</code>.",
        '3. Отправьте в этот чат фото (скриншот) чека об оплате.',
        '',
        ('Админ проверит чек и активирует Premium. Заказ действует 24 часа.' if is_premium(keys)
         else 'Админ проверит чек и откроет предмет. Заказ действует 24 часа.'),
    ]
    return '\n'.join(lines)


def _order_keyboard(order, lang='uz'):
    row = []
    if not order['promo_code']:
        row.append({'text': '🎟 Промокод' if lang == 'ru' else '🎟 Promo-kod', 'callback_data': f"ord:promo:{order['id']}"})
    row.append({'text': '❌ Отменить' if lang == 'ru' else '❌ Bekor qilish', 'callback_data': f"ord:cancel:{order['id']}"})
    return {'inline_keyboard': [row]}


def send_instructions(cur, order) -> bool:
    lang = tgbot.lang_of(order['chat_id'])
    res = tgbot.tg_api('sendMessage', {
        'chat_id': order['chat_id'], 'text': instructions_text(order, get_settings(cur), lang),
        'parse_mode': 'HTML', 'reply_markup': _order_keyboard(order, lang),
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
    cur.execute('SELECT * FROM pay_orders WHERE user_id = %s AND status != %s ORDER BY created_ms DESC LIMIT %s',
                (user_id, CANCELLED, limit))
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
    partner = _partner_name(cur, order['promo_code'])
    if partner:
        lines.insert(4, f"🤝 Hamkor kodi — {html.escape(partner)}")
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
    earning = None
    if approve:
        _deliver_items(cur, order, keys, now)
        earning = partners.credit(cur, order, now)      # hamkor kodi bo'lsa — komissiya
    conn.commit()
    order = _order(cur, order_id)

    if approve:
        _notify_paid(cur, order['chat_id'], order, keys, tgbot.L("To'lov tasdiqlandi!", 'Оплата подтверждена!'))
        partners.notify_sale(cur, earning)
    else:
        ru = tgbot.lang_of(order['chat_id']) == 'ru'
        tgbot.tg_api('sendMessage', {
            'chat_id': order['chat_id'], 'parse_mode': 'HTML',
            'text': (f"❌ <b>Оплата не подтверждена</b> ({order['code']})\nПричина: {html.escape(reason)}\n\n"
                     "Попробуйте снова с правильным чеком. Если есть вопрос, напишите сюда — админ ответит." if ru else
                     f"❌ <b>To'lov tasdiqlanmadi</b> ({order['code']})\nSabab: {html.escape(reason)}\n\n"
                     "To'g'ri chek bilan qayta urinib ko'ring. Savolingiz bo'lsa, shu yerga yozing — admin javob beradi."),
            'reply_markup': {'inline_keyboard': [[{'text': '🔄 Повторить' if ru else '🔄 Qayta urinish',
                                                   'callback_data': f'ord:retry:{order_id}'}]]},
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


def _deliver_items(cur, order, keys, now):
    """To'lov tasdiqlandi: fanlar ochiladi yoki Premium beriladi (commit — chaqiruvchida)."""
    if is_premium(keys):
        premium.grant(cur, order['user_id'], premium.PLANS[premium.plan_of(keys)][0], 'card', now, note=order['code'])
    else:
        for k in keys:
            cur.execute('INSERT INTO subject_purchases (user_id, subject_key) VALUES (%s, %s) '
                        'ON CONFLICT (user_id, subject_key) DO NOTHING', (order['user_id'], k))
    if order['promo_code']:
        cur.execute('UPDATE promo_codes SET used = used + 1 WHERE code = %s', (order['promo_code'],))


def _notify_paid(cur, chat_id, order, keys, head):
    lang = tgbot.lang_of(chat_id)
    head = tgbot.pick(head, lang)
    if is_premium(keys):
        u = premium.until(cur, order['user_id'])
        till = datetime.fromtimestamp(u / 1000, TASHKENT_TZ).strftime('%d.%m.%Y') if u else ''
        tgbot.send(chat_id, tgbot.L(
            f"🎉 <b>{head}</b> ({order['code']})\n💎 <b>Bilim Premium</b> faollashdi — {till} gacha.\n"
            f"AI tushuntirish, shaxsiy darslar, emoji va chaqmoqli avatar ramkasi endi sizniki!",
            f"🎉 <b>{head}</b> ({order['code']})\n💎 <b>Bilim Premium</b> активирован — до {till}.\n"
            f"Объяснения ИИ, личные уроки, эмодзи и рамка аватара с молниями теперь ваши!"),
            tgbot.L('Shaxsiy darslarim', 'Мои личные уроки'), 'shaxsiy.html', lang=lang)
    else:
        tgbot.send(chat_id, tgbot.L(
            f"🎉 <b>{head}</b> ({order['code']})\n{html.escape(subject_names(keys))} — ochildi. Omad!",
            f"🎉 <b>{head}</b> ({order['code']})\n{html.escape(subject_names(keys, 'ru'))} — открыт. Удачи!"),
            tgbot.L('Darsni boshlash', 'Начать урок'), f'topics.html?fan={keys[0]}' if keys else 'dashboard.html',
            lang=lang)


def still_available(cur, user_id, keys, now=None) -> bool:
    """Buyurtma hali bajarilishi mumkinmi (fan yopiq / premium faol emas)."""
    if is_premium(keys):
        return not premium.is_active(premium.until(cur, user_id), now)
    locked = locked_subjects(cur, user_id)
    return bool(keys) and all(k in locked for k in keys)


def retry_order(cur, conn, order_id, chat_id, now=None):
    """Rad etilgan buyurtma o'rniga xuddi shu fanlar bilan yangisi."""
    order = _order(cur, order_id)
    if not order or int(order['chat_id']) != int(chat_id) or order['status'] != REJECTED:
        raise PayError("Bu buyurtmani qayta ochib bo'lmaydi.", 'bad_state')
    cur.execute('SELECT id, name, telegram_id FROM users WHERE id = %s', (order['user_id'],))
    user = cur.fetchone()
    keys = (_items(order) if is_premium(order)
            else [k for k in _items(order) if k in locked_subjects(cur, order['user_id'])])
    promo = order['promo_code']
    try:
        return create_order(cur, conn, user, keys, promo, now)
    except PayError as exc:
        if exc.code != 'bad_promo':
            raise
        return create_order(cur, conn, user, keys, None, now)


# ───────────────────────── Promo-kodlar ─────────────────────────

def _partner_name(cur, code):
    """Promo-kod hamkorniki bo'lsa — hamkor ismi (admin xabari uchun)."""
    if not code:
        return None
    cur.execute('SELECT u.name, p.partner_user_id FROM promo_codes p LEFT JOIN users u ON u.id = p.partner_user_id '
                'WHERE p.code = %s AND p.partner_user_id IS NOT NULL', (code,))
    r = cur.fetchone()
    return (r['name'] or f"ID {r['partner_user_id']}") if r else None


def list_promos(cur) -> list:
    """Oddiy promo-kodlar (hamkorlarniki — alohida, "Hamkorlar" bo'limida)."""
    cur.execute('SELECT * FROM promo_codes WHERE partner_user_id IS NULL ORDER BY created_ms DESC')
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
    cur.execute('UPDATE promo_codes SET active = 1 - active WHERE code = %s AND partner_user_id IS NULL',
                (str(code).upper(),))
    ok = cur.rowcount == 1
    conn.commit()
    return ok


# ───────────────────────── Admin panel ─────────────────────────

def overview(cur, now=None) -> dict:
    now = now or clock.now_ms()
    day = clock.period_start_ms('day', now)
    month = clock.period_start_ms('month', now)

    def total(since):
        cur.execute('SELECT COUNT(*) AS n, COALESCE(SUM(amount), 0) AS s FROM pay_orders '
                    'WHERE status = %s AND decided_ms >= %s', (APPROVED, since))
        r = cur.fetchone()
        return {'count': int(r['n']), 'sum': int(r['s'])}

    cur.execute('SELECT COUNT(*) AS n FROM pay_orders WHERE status = %s', (PENDING,))
    pending = int(cur.fetchone()['n'])
    return {'today': total(day), 'month': total(month), 'all': total(0), 'pending': pending}


def admin_orders(cur, status=None, page=1, per_page=30) -> dict:
    where, params = (("WHERE o.status = %s", [status]) if status
                     else ("WHERE o.status != %s", [CANCELLED]))
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
