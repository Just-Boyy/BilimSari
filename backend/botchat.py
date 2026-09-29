# -*- coding: utf-8 -*-
"""
Bot chatidagi suhbat: to'lov cheklari, admin tugmalari va jonli chat.

  * O'quvchi chek rasmini yuborsa — payments.attach_receipt (faol buyurtma bo'lsa).
  * Admin tugmalari (callback_query): pay:ok / pay:no / pay:rj / pay:back.
  * O'quvchi tugmalari: ord:promo / ord:cancel / ord:retry.
  * Boshqa xabarlar — jonli chat: adminga boradi; admin shu xabarga "Reply"
    qilib yozgan javob o'quvchiga yetkaziladi (bot_chat_links orqali).

Buyruqlar (/start, /kun, ...) app.py'da; bu yerga faqat qolgan xabarlar keladi.
"""

import html
import logging

import partners
import payments
import rate_limit
import tgbot
from db import get_connection
from games import clock

logger = logging.getLogger('bilimsari.botchat')

STATE_TTL_MS = 10 * 60 * 1000
SUPPORT_LIMIT = 30            # soatiga o'quvchidan adminga xabar
ACK_EVERY_S = 30 * 60         # "adminga yuborildi" tasdig'i shu oraliqda bir marta
UPDATES_KEEP_MS = 2 * 24 * 3600 * 1000

# Bot chatining pastidagi doimiy menyu (reply keyboard)
BTN_APP = '📚 Ilovani ochish'
BTN_DAILY = '❓ Kun savoli'
BTN_SHOP = "🛒 Do'kon"
BTN_ORDERS = "🧾 To'lovlarim"
BTN_SUPPORT = "💬 Admin bilan bog'lanish"


def menu_keyboard():
    """Tugmalar matn yuboradi, bot esa inline "Ochish" tugmasi bilan javob beradi.
    Pastki menyudagi web_app tugmasidan ochilgan Mini App'ga Telegram initData
    bermaydi — yangi o'quvchi kira olmasdi."""
    return {
        'keyboard': [
            [{'text': BTN_APP}],
            [{'text': BTN_DAILY}, {'text': BTN_SHOP}],
            [{'text': BTN_ORDERS}, {'text': BTN_SUPPORT}],
        ],
        'resize_keyboard': True,
        'is_persistent': True,
    }


def ensure_tables(cur, conn):
    # Telegram bir yangilanishni qayta yuborsa (server sekin javob berganda) —
    # ikkinchi marta ishlanmasligi uchun
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bot_updates (
            update_id BIGINT PRIMARY KEY,
            received_ms BIGINT NOT NULL
        )
    ''')
    conn.commit()


def first_time(update_id) -> bool:
    """Yangilanish birinchi marta kelganmi (update_id bo'yicha)."""
    try:
        update_id = int(update_id)
    except (TypeError, ValueError):
        return True
    conn, cur = _db()
    try:
        cur.execute('INSERT INTO bot_updates (update_id, received_ms) VALUES (%s, %s) ON CONFLICT DO NOTHING',
                    (update_id, clock.now_ms()))
        fresh = cur.rowcount == 1
        conn.commit()
        return fresh
    except Exception:  # noqa: BLE001
        conn.rollback()
        return True
    finally:
        _close(conn, cur)


def cleanup_updates(cur, conn, now=None):
    cur.execute('DELETE FROM bot_updates WHERE received_ms < %s', ((now or clock.now_ms()) - UPDATES_KEEP_MS,))
    conn.commit()


def handle_group(message):
    """Guruhda buyruq yozilsa — Mini App tugmasi guruhda ishlamaydi, shuning
    uchun botning shaxsiy chatiga havola beriladi. Oddiy xabarlar e'tiborsiz."""
    text = (message.get('text') or '').strip()
    if not text.startswith('/'):
        return
    tgbot.tg_api('sendMessage', {
        'chat_id': (message.get('chat') or {}).get('id'),
        'text': "📚 BilimSari'dan foydalanish uchun botga shaxsiy chatda yozing.",
        'reply_markup': {'inline_keyboard': [[{'text': 'Botni ochish', 'url': f'https://t.me/{tgbot.BOT_USERNAME}'}]]},
    })


def _send(chat_id, text, markup=None):
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    if markup:
        payload['reply_markup'] = markup
    return tgbot.tg_api('sendMessage', payload)


def _db():
    conn = get_connection()
    return conn, conn.cursor()


def _close(conn, cur):
    try:
        cur.close()
        conn.close()
    except Exception:  # noqa: BLE001
        pass


def _set_state(cur, conn, chat_id, state):
    cur.execute('DELETE FROM bot_state WHERE chat_id = %s', (chat_id,))
    if state:
        cur.execute('INSERT INTO bot_state (chat_id, state, updated_ms) VALUES (%s, %s, %s)',
                    (chat_id, state, clock.now_ms()))
    conn.commit()


def _get_state(cur, chat_id):
    cur.execute('SELECT state, updated_ms FROM bot_state WHERE chat_id = %s', (chat_id,))
    row = cur.fetchone()
    if not row or int(row['updated_ms']) < clock.now_ms() - STATE_TTL_MS:
        return None
    return row['state']


def _who(frm) -> str:
    name = ' '.join(x for x in (frm.get('first_name'), frm.get('last_name')) if x) or "O'quvchi"
    extra = f", @{frm['username']}" if frm.get('username') else ''
    return f"<b>{html.escape(name)}</b> (tg {frm.get('id')}{html.escape(extra)})"


# ───────────────────────── Tugmalar ─────────────────────────

def handle_callback(cq):
    data = str(cq.get('data') or '')
    frm = cq.get('from') or {}
    chat_id = frm.get('id')
    answer = None
    conn, cur = _db()
    try:
        parts = data.split(':')
        if parts[0] == 'pay' and len(parts) >= 3:
            answer = _admin_callback(cur, conn, cq, parts)
        elif parts[0] == 'ord' and len(parts) == 3:
            answer = _order_callback(cur, conn, chat_id, parts[1], parts[2])
    except payments.PayError as exc:
        answer = exc.message
    except Exception:  # noqa: BLE001
        conn.rollback()
        logger.exception('Callback xatosi: %s', data)
        answer = "Xatolik yuz berdi, qayta urinib ko'ring."
    finally:
        _close(conn, cur)
    tgbot.tg_api('answerCallbackQuery', {'callback_query_id': cq.get('id'), 'text': answer or ''})


def _admin_callback(cur, conn, cq, parts):
    frm = cq.get('from') or {}
    if not payments.is_admin(frm.get('id')):
        return "Bu tugma faqat admin uchun."
    action, order_id = parts[1], parts[2]
    try:
        order_id = int(order_id)
    except ValueError:
        return None
    msg = cq.get('message') or {}
    by = ' '.join(x for x in (frm.get('first_name'), frm.get('last_name')) if x) or 'Admin'
    if action == 'ok':
        return payments.decide(cur, conn, order_id, True, by)[1]
    if action == 'rj' and len(parts) == 4:
        return payments.decide(cur, conn, order_id, False, by, parts[3])[1]
    if action in ('no', 'back'):
        keyboard = payments.reasons_keyboard(order_id) if action == 'no' else payments.DECIDE_KEYBOARD(order_id)
        tgbot.tg_api('editMessageReplyMarkup', {
            'chat_id': (msg.get('chat') or {}).get('id'), 'message_id': msg.get('message_id'),
            'reply_markup': keyboard,
        })
        return 'Sababni tanlang' if action == 'no' else None
    return None


def _order_callback(cur, conn, chat_id, action, order_id):
    try:
        order_id = int(order_id)
    except ValueError:
        return None
    cur.execute('SELECT * FROM pay_orders WHERE id = %s', (order_id,))
    order = cur.fetchone()
    if not order or int(order['chat_id']) != int(chat_id or 0):
        return 'Buyurtma topilmadi.'
    if action == 'promo':
        if order['status'] != payments.AWAITING:
            return "Bu buyurtmaga endi promo-kod qo'llab bo'lmaydi."
        _set_state(cur, conn, chat_id, f'promo:{order_id}')
        _send(chat_id, f"🎟 Buyurtma {order['code']} uchun promo-kodni yozing:")
        return None
    if action == 'cancel':
        if payments.cancel_order(cur, conn, order_id, order['user_id']):
            _send(chat_id, f"Buyurtma {order['code']} bekor qilindi.")
            return 'Bekor qilindi'
        return "Bu buyurtmani bekor qilib bo'lmaydi."
    if action == 'retry':
        payments.retry_order(cur, conn, order_id, chat_id)
        return 'Yangi buyurtma yuborildi'
    return None


# ───────────────────────── Xabarlar ─────────────────────────

def handle_message(message):
    """Buyruq bo'lmagan xabar: chek, promo-kod, admin javobi yoki jonli chat."""
    chat = message.get('chat') or {}
    if chat.get('type', 'private') != 'private':
        return
    frm = message.get('from') or {}
    chat_id = chat.get('id')
    conn, cur = _db()
    try:
        if payments.is_admin(frm.get('id')):
            if message.get('reply_to_message'):
                _admin_reply(cur, chat_id, message)
                return
        text = (message.get('text') or '').strip()
        # Pastki menyu tugmalari (matn yuboradi) — adminga savol sifatida ketmaydi
        if text == BTN_ORDERS:
            send_my_orders(chat_id)
            return
        if text == BTN_APP:
            tgbot.send(chat_id, "📚 BilimSari'ni ochish uchun tugmani bosing:", 'Ilovani ochish', 'dashboard.html')
            return
        if text == BTN_DAILY:
            tgbot.send(chat_id, "❓ <b>Kun savoli</b> — bugun hamma uchun bitta savol. To'g'ri va tez javob bering, "
                                "kunlik reytingga chiqing!", 'Savolni ochish', 'daily.html')
            return
        if text == BTN_SHOP:
            send_shop(chat_id)
            return
        if text == BTN_SUPPORT:
            _send(chat_id, "💬 Savolingizni shu yerga yozing — admin javob beradi. Rasm yoki skrinshot ham yuborishingiz mumkin.")
            return
        state = _get_state(cur, chat_id)
        if text and state and state.startswith('promo:'):
            _promo_input(cur, conn, chat_id, int(state.split(':')[1]), text)
            return

        receipt = _receipt_of(message)
        if receipt:
            reply = payments.attach_receipt(cur, conn, chat_id, *receipt)
            if reply:
                _send(chat_id, reply)
                return
        if payments.is_admin(frm.get('id')):
            _send(chat_id, "👨‍💼 Siz adminsiz. O'quvchiga javob berish uchun uning xabariga <b>Reply</b> qiling.\n"
                           "/tolovlar — kutilayotgan cheklar")
            return
        _support(cur, conn, chat_id, frm, message, text)
    except Exception:  # noqa: BLE001
        conn.rollback()
        logger.exception('Bot xabari xatosi')
    finally:
        _close(conn, cur)


def _receipt_of(message):
    """(file_id, file_unique_id, tur) — rasm yoki rasm/PDF hujjat bo'lsa."""
    if message.get('photo'):
        p = message['photo'][-1]          # eng katta o'lcham
        return p.get('file_id'), p.get('file_unique_id'), 'photo'
    doc = message.get('document') or {}
    mime = str(doc.get('mime_type') or '')
    if doc and (mime.startswith('image/') or mime == 'application/pdf'):
        return doc.get('file_id'), doc.get('file_unique_id'), 'document'
    return None


def _promo_input(cur, conn, chat_id, order_id, text):
    _set_state(cur, conn, chat_id, None)
    cur.execute('SELECT * FROM pay_orders WHERE id = %s AND chat_id = %s', (order_id, chat_id))
    order = cur.fetchone()
    if not order:
        return
    try:
        order = payments.apply_promo(cur, conn, order, text)
    except payments.PayError as exc:
        _send(chat_id, f"❌ {html.escape(exc.message)}\nQayta urinish uchun «🎟 Promo-kod» tugmasini bosing.")
        return
    percent = int(order['promo_percent'] or 0)
    _send(chat_id, f"✅ Promo-kod qo'llandi" + (f": −{percent}%" if percent else '') +
          f". Summa: <b>{payments.som(order['amount'])}</b>")
    payments.send_instructions(cur, order)


def _support(cur, conn, chat_id, frm, message, text):
    if not rate_limit.hit(f'support:{chat_id}', SUPPORT_LIMIT, 3600):
        _send(chat_id, "Juda ko'p xabar yuborildi. Birozdan keyin yozing.")
        return
    header = f"💬 {_who(frm)}:"
    media = message.get('photo') or message.get('document') or message.get('video') or message.get('voice')
    if not text and not media:
        _send(chat_id, "Hozircha adminga faqat matn, rasm, video yoki ovozli xabar yuborish mumkin.")
        return
    delivered = False
    for admin in payments.admin_ids():
        if text:
            res = _send(admin, f"{header}\n{html.escape(text)}")
        else:
            caption = header + ('\n' + html.escape(message['caption']) if message.get('caption') else '')
            res = tgbot.tg_api('copyMessage', {'chat_id': admin, 'from_chat_id': chat_id,
                                               'message_id': message.get('message_id'),
                                               'caption': caption, 'parse_mode': 'HTML'})
        result = (res or {}).get('result') if (res or {}).get('ok') else None
        if result:
            payments.link_message(cur, admin, result['message_id'], chat_id)
            delivered = True
    conn.commit()
    if delivered and rate_limit.hit(f'support_ack:{chat_id}', 1, ACK_EVERY_S):
        _send(chat_id, "✅ Xabaringiz adminga yuborildi. Javob shu chatga keladi.")


def _admin_reply(cur, chat_id, message):
    replied = message['reply_to_message'].get('message_id')
    cur.execute('SELECT user_chat_id FROM bot_chat_links WHERE admin_chat_id = %s AND admin_message_id = %s',
                (chat_id, replied))
    row = cur.fetchone()
    if not row:
        _send(chat_id, "Bu xabarga javob yuborib bo'lmaydi — o'quvchi topilmadi. O'quvchi xabariga Reply qiling.")
        return
    user_chat = row['user_chat_id']
    text = (message.get('text') or '').strip()
    if text:
        res = _send(user_chat, f"👨‍💼 <b>Admin:</b>\n{html.escape(text)}")
    else:
        caption = '👨‍💼 <b>Admin</b>' + ('\n' + html.escape(message['caption']) if message.get('caption') else '')
        res = tgbot.tg_api('copyMessage', {'chat_id': user_chat, 'from_chat_id': chat_id,
                                           'message_id': message.get('message_id'),
                                           'caption': caption, 'parse_mode': 'HTML'})
    ok = bool((res or {}).get('ok'))
    tgbot.tg_api('sendMessage', {
        'chat_id': chat_id, 'reply_to_message_id': message.get('message_id'),
        'text': '✅ Yuborildi' if ok else "❌ Yuborilmadi (o'quvchi botni bloklagan bo'lishi mumkin)",
    })


# ───────────────────────── Buyruqlar ─────────────────────────

def partner_start(chat_id, payload):
    """/start <KOD> — hamkor havolasi: kod saqlanadi va do'konda avtomatik qo'llanadi."""
    conn, cur = _db()
    try:
        row = partners.active_code(cur, payload)
        if row:
            partners.start_link(cur, conn, chat_id, row)
    except Exception:  # noqa: BLE001
        conn.rollback()
        logger.exception('Hamkor havolasi xatosi')
    finally:
        _close(conn, cur)


def send_shop(chat_id):
    """/sotib_olish va /start pay — faol buyurtma bo'lsa uni, aks holda do'konni ko'rsatadi."""
    conn, cur = _db()
    try:
        cur.execute('SELECT id FROM users WHERE telegram_id = %s', (chat_id,))
        user = cur.fetchone()
        order = payments.active_order(cur, user['id']) if user else None
        if order and order['status'] == payments.AWAITING:
            payments.send_instructions(cur, order)
            return
        if order:
            _send(chat_id, f"⏳ Chekingiz ({order['code']}) tekshirilmoqda. Natija shu yerga keladi.")
            return
    finally:
        _close(conn, cur)
    tgbot.send(chat_id, "🛒 <b>Fan sotib olish</b>\nFanlarni tanlang — 3 ta fan va barcha fanlar paketlari arzonroq.\n\n"
                        "To'lov karta orqali: kartaga o'tkazasiz, chek rasmini shu chatga yuborasiz — "
                        "admin tasdiqlagach fan ochiladi.", "Do'konni ochish", 'shop.html')


STATUS_LABELS = {
    payments.AWAITING: '🕐 Chek kutilmoqda', payments.PENDING: '⏳ Tekshirilmoqda',
    payments.APPROVED: '✅ Tasdiqlangan', payments.REJECTED: '❌ Rad etilgan', payments.EXPIRED: '⌛ Muddati tugagan',
}


def send_my_orders(chat_id):
    conn, cur = _db()
    try:
        cur.execute('SELECT id FROM users WHERE telegram_id = %s', (chat_id,))
        user = cur.fetchone()
        orders = payments.user_orders(cur, user['id'], 10) if user else []
    finally:
        _close(conn, cur)
    if not orders:
        _send(chat_id, "Sizda hali to'lovlar yo'q. Fan sotib olish: /sotib_olish")
        return
    lines = ["🧾 <b>To'lovlarim</b>"]
    for o in orders:
        names = ', '.join(i['name'] for i in o['items'])
        lines.append(f"\n<b>{o['code']}</b> — {payments.som(o['amount'])}\n{html.escape(names)}\n"
                     f"{STATUS_LABELS.get(o['status'], o['status'])} • {payments._date(o['created_ms'])}"
                     + (f"\nSabab: {html.escape(o['reject_reason'])}" if o['reject_reason'] else ''))
    _send(chat_id, '\n'.join(lines))


def send_pending(chat_id):
    """Admin: /tolovlar — kutilayotgan cheklar."""
    conn, cur = _db()
    try:
        data = payments.admin_orders(cur, payments.PENDING, 1, 20)
    finally:
        _close(conn, cur)
    if not data['orders']:
        _send(chat_id, "✅ Kutilayotgan chek yo'q.")
        return
    now = clock.now_ms()
    lines = [f"⏳ <b>Kutilayotgan cheklar: {data['total']}</b>"]
    for o in data['orders']:
        mins = max(0, (now - (o['receipt_ms'] or o['created_ms'])) // 60000)
        lines.append(f"• {o['code']} — {html.escape(o['user_name'] or '?')} — {payments.som(o['amount'])} ({mins} daq.)")
    tgbot.send(chat_id, '\n'.join(lines), 'Admin panel', 'admin.html')
