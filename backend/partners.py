# -*- coding: utf-8 -*-
"""
Hamkorlik dasturi — promo-kod egasi (hamkor) o'z kodi bilan qilingan xariddan foiz oladi.

  * Admin hamkorni tanlaydi (ilovadagi ID, Telegram ID yoki @username) va unga
    bitta promo-kod beradi: komissiya foizi (standart 20%) va xaridorga chegirma
    (0 — chegirmasiz). Kod oddiy promo-kodlar jadvalida (promo_codes.partner_user_id).
  * Komissiya faqat kod shu xaridda qo'llangan va admin chekni tasdiqlagan bo'lsa
    yoziladi — haqiqatda to'langan summadan (chegirmadan keyin). Rad etilgan yoki
    bekor qilingan buyurtmaga hech narsa yozilmaydi. Fanlar ham, Premium ham.
  * Pog'onali komissiya: N ta sotuvdan keyin +X% (admin sozlaydi).
  * Hamkor o'z kodini ishlata olmaydi; har o'quvchi kodni bir marta ishlatadi;
    admin hamkorni to'xtatib qo'yishi mumkin — kod ishlamay qoladi.
  * Har sotuvda hamkorga botda xabar boradi; profilida statistika va ulashish matni.
  * Pul: admin istalgan vaqtda "To'landi" bosib summani yozib qo'yadi — tarix saqlanadi.
  * Havola t.me/<bot>?start=<KOD> — kod saqlanadi va do'konda avtomatik qo'llanadi.
"""

import html
from datetime import datetime

import tgbot
from db import TASHKENT_TZ, add_column_if_missing
from games import clock

DEFAULT_COMMISSION = 20
DEFAULT_TIERS = {'tier1_sales': 10, 'tier1_bonus': 5, 'tier2_sales': 50, 'tier2_bonus': 10}
MAX_PERCENT = 90
REFERRAL_TTL_MS = 30 * 24 * 3600 * 1000      # havola orqali saqlangan kod shu muddat amal qiladi
RESERVED = ('KUN', 'PAY')                      # /start buyrug'idagi boshqa so'zlar bilan to'qnashmasin
PREMIUM_ITEM = 'premium'


class PartnerError(Exception):
    def __init__(self, message, code='bad_request', http_status=400):
        super().__init__(message)
        self.message, self.code, self.http_status = message, code, http_status


def ensure_tables(cur, conn):
    add_column_if_missing(cur, conn, 'promo_codes', 'partner_user_id', 'INTEGER')
    add_column_if_missing(cur, conn, 'promo_codes', 'commission', 'INTEGER')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS partner_earnings (
            id SERIAL PRIMARY KEY,
            partner_user_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL UNIQUE,
            order_code TEXT NOT NULL,
            promo_code TEXT NOT NULL,
            buyer_id INTEGER NOT NULL,
            items TEXT NOT NULL,
            paid_amount INTEGER NOT NULL,
            percent INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            created_ms BIGINT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS partner_payouts (
            id SERIAL PRIMARY KEY,
            partner_user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            note TEXT,
            created_by TEXT,
            created_ms BIGINT NOT NULL
        )
    ''')
    # t.me/<bot>?start=<KOD> orqali kelganlar — o'quvchi hali ro'yxatdan o'tmagan bo'lishi mumkin
    cur.execute('''
        CREATE TABLE IF NOT EXISTS promo_referrals (
            telegram_id BIGINT PRIMARY KEY,
            code TEXT NOT NULL,
            created_ms BIGINT NOT NULL
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_partner_earnings_partner ON partner_earnings (partner_user_id, created_ms)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_partner_payouts_partner ON partner_payouts (partner_user_id, created_ms)')
    conn.commit()


# ───────────────────────── Yordamchilar ─────────────────────────

def som(n) -> str:
    return f'{int(n or 0):,}'.replace(',', ' ') + " so'm"


def som_ru(n) -> str:
    return f'{int(n or 0):,}'.replace(',', ' ') + ' сум'


def _date(ms) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, TASHKENT_TZ).strftime('%d.%m.%Y')


def _int(value, name, lo, hi, default=None):
    if value in (None, '') and default is not None:
        return default
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise PartnerError(f"{name} butun son bo'lishi kerak.")
    if not lo <= value <= hi:
        raise PartnerError(f"{name} {lo} dan {hi} gacha bo'lishi kerak.")
    return value


def share_link(code) -> str:
    return f'https://t.me/{tgbot.BOT_USERNAME}?start={code}'


def share_texts(code, discount) -> dict:
    """Hamkor do'stlariga yuboradigan tayyor matn (o'zbekcha va ruscha)."""
    link = share_link(code)
    uz = ("📚 BilimSari — maktab fanlarini o'rganish uchun qulay ilova: har kuni yangi dars, test, "
          "kun savoli va bilim o'yinlari!\n\n")
    ru = ("📚 BilimSari — удобное приложение для изучения школьных предметов: каждый день новый урок, тест, "
          "вопрос дня и игры на знания!\n\n")
    if discount:
        uz += f"🎟 Mening promo-kodim: {code} — fan yoki Bilim Premium xaridida −{discount}% chegirma.\n"
        ru += f"🎟 Мой промокод: {code} — скидка −{discount}% на предметы и Bilim Premium.\n"
    else:
        uz += f"🎟 Xarid qilayotganda mening promo-kodimni kiriting: {code}\n"
        ru += f"🎟 При покупке введите мой промокод: {code}\n"
    return {'uz': uz + f"👉 {link}", 'ru': ru + f"👉 {link}"}


def _items_label(items_json) -> str:
    import json
    import curriculum as cur_mod
    try:
        keys = [k for k in json.loads(items_json or '[]') if isinstance(k, str)]
    except (TypeError, ValueError):
        keys = []
    if keys == [PREMIUM_ITEM]:
        return 'Bilim Premium'
    if len(keys) == 1:
        return cur_mod.subject_meta(keys[0])['name']
    return f'{len(keys)} ta fan'


# ───────────────────────── Pog'onalar ─────────────────────────

def tiers(cur) -> dict:
    data = dict(DEFAULT_TIERS)
    cur.execute('SELECT key, value FROM pay_settings')
    for r in cur.fetchall():
        key = r['key'][len('partner_'):] if r['key'].startswith('partner_') else None
        if key in data:
            try:
                data[key] = int(r['value'])
            except (TypeError, ValueError):
                pass
    return data


def save_tiers(cur, conn, body) -> dict:
    cur_t = tiers(cur)
    new = {
        'tier1_sales': _int(body.get('tier1_sales', cur_t['tier1_sales']), "1-pog'ona sotuvlar soni", 0, 100_000),
        'tier1_bonus': _int(body.get('tier1_bonus', cur_t['tier1_bonus']), "1-pog'ona qo'shimcha foizi", 0, 50),
        'tier2_sales': _int(body.get('tier2_sales', cur_t['tier2_sales']), "2-pog'ona sotuvlar soni", 0, 100_000),
        'tier2_bonus': _int(body.get('tier2_bonus', cur_t['tier2_bonus']), "2-pog'ona qo'shimcha foizi", 0, 50),
    }
    if new['tier1_sales'] and new['tier2_sales'] and new['tier2_sales'] <= new['tier1_sales']:
        raise PartnerError("2-pog'ona sotuvlar soni 1-pog'onadan katta bo'lishi kerak.")
    for key, value in new.items():
        cur.execute('DELETE FROM pay_settings WHERE key = %s', ('partner_' + key,))
        cur.execute('INSERT INTO pay_settings (key, value) VALUES (%s, %s)', ('partner_' + key, str(value)))
    conn.commit()
    return new


def effective_percent(base, sales_before, t) -> int:
    """Navbatdagi sotuv uchun foiz: asosiy foiz + pog'ona qo'shimchasi."""
    bonus = 0
    if t['tier2_sales'] and t['tier2_bonus'] and sales_before >= t['tier2_sales']:
        bonus = t['tier2_bonus']
    elif t['tier1_sales'] and t['tier1_bonus'] and sales_before >= t['tier1_sales']:
        bonus = t['tier1_bonus']
    return min(MAX_PERCENT, int(base) + bonus)


def next_tier(base, sales, t):
    """Keyingi pog'ona: {'sales_left', 'percent'} yoki None."""
    for n, b in ((t['tier1_sales'], t['tier1_bonus']), (t['tier2_sales'], t['tier2_bonus'])):
        if n and b and sales < n:
            return {'sales_left': n - sales, 'percent': min(MAX_PERCENT, int(base) + b), 'at': n}
    return None


# ───────────────────────── Hamkorlar ─────────────────────────

def partner_code(cur, user_id):
    cur.execute('SELECT * FROM promo_codes WHERE partner_user_id = %s ORDER BY created_ms LIMIT 1', (user_id,))
    return cur.fetchone()


def _totals(cur, user_id) -> dict:
    cur.execute('SELECT COUNT(*) AS n, COALESCE(SUM(amount), 0) AS s, COALESCE(SUM(paid_amount), 0) AS t '
                'FROM partner_earnings WHERE partner_user_id = %s', (user_id,))
    e = cur.fetchone()
    cur.execute('SELECT COALESCE(SUM(amount), 0) AS s FROM partner_payouts WHERE partner_user_id = %s', (user_id,))
    paid = int(cur.fetchone()['s'])
    earned = int(e['s'])
    return {'sales': int(e['n']), 'revenue': int(e['t']), 'earned': earned, 'paid': paid, 'due': earned - paid}


def _view(cur, row, t) -> dict:
    """Hamkor haqida umumiy ma'lumot (admin ro'yxati va profil uchun)."""
    uid = int(row['partner_user_id'])
    tot = _totals(cur, uid)
    base = int(row['commission'] or DEFAULT_COMMISSION)
    return dict(tot, **{
        'user_id': uid, 'code': row['code'], 'active': bool(row['active']),
        'discount': int(row['percent']), 'commission': base,
        'percent_now': effective_percent(base, tot['sales'], t),
        'next_tier': next_tier(base, tot['sales'], t),
        'link': share_link(row['code']), 'created_ms': int(row['created_ms']),
    })


def create(cur, conn, user, code, commission=None, discount=None, now=None) -> str:
    now = now or clock.now_ms()
    code = str(code or '').strip().upper()
    if not code.isalnum() or not code.isascii() or not 3 <= len(code) <= 20:
        raise PartnerError("Kod 3–20 ta lotin harfi yoki raqamdan iborat bo'lsin.")
    if code in RESERVED or code.startswith('ROOM'):
        raise PartnerError("Bu so'zni kod qilib bo'lmaydi — boshqasini tanlang.")
    commission = _int(commission, 'Komissiya', 1, MAX_PERCENT, DEFAULT_COMMISSION)
    discount = _int(discount, 'Xaridorga chegirma', 0, MAX_PERCENT, 0)
    if partner_code(cur, user['id']):
        raise PartnerError("Bu foydalanuvchi allaqachon hamkor.", 'exists', 409)
    cur.execute('SELECT 1 FROM promo_codes WHERE code = %s', (code,))
    if cur.fetchone():
        raise PartnerError("Bunday promo-kod allaqachon bor.", 'exists', 409)
    cur.execute('INSERT INTO promo_codes (code, percent, max_uses, used, expires_ms, active, created_ms, '
                'partner_user_id, commission) VALUES (%s, %s, NULL, 0, NULL, 1, %s, %s, %s)',
                (code, discount, now, user['id'], commission))
    conn.commit()
    return code


def update(cur, conn, user_id, body):
    row = partner_code(cur, user_id)
    if not row:
        raise PartnerError('Hamkor topilmadi.', 'not_found', 404)
    commission = _int(body.get('commission', row['commission']), 'Komissiya', 1, MAX_PERCENT, DEFAULT_COMMISSION)
    discount = _int(body.get('discount', row['percent']), 'Xaridorga chegirma', 0, MAX_PERCENT, 0)
    cur.execute('UPDATE promo_codes SET commission = %s, percent = %s WHERE code = %s',
                (commission, discount, row['code']))
    conn.commit()


def toggle(cur, conn, user_id) -> bool:
    """To'xtatish / qayta yoqish. Yangi holatni qaytaradi (True — faol)."""
    row = partner_code(cur, user_id)
    if not row:
        raise PartnerError('Hamkor topilmadi.', 'not_found', 404)
    cur.execute('UPDATE promo_codes SET active = %s WHERE code = %s', (0 if row['active'] else 1, row['code']))
    conn.commit()
    return not row['active']


def delete(cur, conn, user_id):
    """Faqat hali sotuvi bo'lmagan hamkorni o'chirish mumkin (xato qo'shilganda)."""
    row = partner_code(cur, user_id)
    if not row:
        raise PartnerError('Hamkor topilmadi.', 'not_found', 404)
    if _totals(cur, user_id)['sales']:
        raise PartnerError("Sotuvi bor hamkorni o'chirib bo'lmaydi — to'xtatib qo'ying.", 'has_sales', 409)
    cur.execute('SELECT 1 FROM pay_orders WHERE promo_code = %s LIMIT 1', (row['code'],))
    if cur.fetchone():
        # Kod ochiq buyurtmada ishlatilgan — o'chirsak, tasdiqlanganda komissiya yozilmay qoladi
        raise PartnerError("Bu kod buyurtmalarda ishlatilgan — o'chirib bo'lmaydi, to'xtatib qo'ying.", 'has_orders', 409)
    cur.execute('DELETE FROM promo_codes WHERE code = %s', (row['code'],))
    cur.execute('DELETE FROM promo_referrals WHERE code = %s', (row['code'],))
    conn.commit()


# ───────────────────────── Sotuv va to'lov ─────────────────────────

def credit(cur, order, now=None):
    """Tasdiqlangan buyurtma hamkor kodi bilan bo'lsa — komissiya yoziladi (commit chaqiruvchida).
    Yozilgan daromad (dict) yoki None."""
    code = order['promo_code']
    if not code:
        return None
    cur.execute('SELECT * FROM promo_codes WHERE code = %s', (code,))
    row = cur.fetchone()
    if not row or row['partner_user_id'] is None:
        return None
    partner = int(row['partner_user_id'])
    if partner == int(order['user_id']):
        return None                                       # o'z kodi (qo'lda o'tib ketgan bo'lsa ham)
    now = now or clock.now_ms()
    t = tiers(cur)
    sales_before = _totals(cur, partner)['sales']
    percent = effective_percent(row['commission'] or DEFAULT_COMMISSION, sales_before, t)
    paid = int(order['amount'])
    amount = int(round(paid * percent / 100))
    cur.execute('SELECT 1 FROM partner_earnings WHERE order_id = %s', (order['id'],))
    if cur.fetchone():
        return None
    cur.execute('''INSERT INTO partner_earnings (partner_user_id, order_id, order_code, promo_code, buyer_id, items,
                                                 paid_amount, percent, amount, created_ms)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (partner, order['id'], order['code'], code, order['user_id'], order['items'], paid, percent,
                 amount, now))
    return {'partner_user_id': partner, 'items': order['items'], 'paid': paid, 'percent': percent,
            'amount': amount, 'sales_before': sales_before, 'base': int(row['commission'] or DEFAULT_COMMISSION)}


def notify_sale(cur, earning):
    """Hamkorga bot orqali xabar: yangi sotuv, komissiya va hisobidagi summa."""
    if not earning:
        return
    uid = earning['partner_user_id']
    cur.execute('SELECT telegram_id FROM users WHERE id = %s', (uid,))
    u = cur.fetchone()
    if not u or not u['telegram_id']:
        return
    tot = _totals(cur, uid)
    t = tiers(cur)
    lines = [
        "🎉 <b>Kodingiz orqali yangi xarid!</b>",
        f"📦 {html.escape(_items_label(earning['items']))} — {som(earning['paid'])}",
        f"💰 Sizga: <b>+{som(earning['amount'])}</b> ({earning['percent']}%)",
        '',
        f"Jami sotuvlar: {tot['sales']} ta • To'lanishi kerak: <b>{som(tot['due'])}</b>",
    ]
    before = effective_percent(earning['base'], earning['sales_before'], t)
    after = effective_percent(earning['base'], tot['sales'], t)
    label_ru = ', '.join(tgbot.fan_ru(x.strip()) for x in _items_label(earning['items']).split(','))
    lines_ru = [
        "🎉 <b>Новая покупка по вашему коду!</b>",
        f"📦 {html.escape(label_ru)} — {som_ru(earning['paid'])}",
        f"💰 Вам: <b>+{som_ru(earning['amount'])}</b> ({earning['percent']}%)",
        '',
        f"Всего продаж: {tot['sales']} • К выплате: <b>{som_ru(tot['due'])}</b>",
    ]
    if after > before:
        lines += ['', f"🚀 Tabriklaymiz! {tot['sales']} ta sotuvdan o'tdingiz — endi komissiyangiz <b>{after}%</b>."]
        lines_ru += ['', f"🚀 Поздравляем! Вы прошли отметку {tot['sales']} продаж — теперь ваша комиссия <b>{after}%</b>."]
    tgbot.send(u['telegram_id'], tgbot.L('\n'.join(lines), '\n'.join(lines_ru)), tgbot.L('Hamkorlik', 'Партнёрство'),
               'hamkor.html')


def record_payout(cur, conn, user_id, amount, note, by, now=None) -> dict:
    """Admin hamkorga pul o'tkazdi — yozib qo'yiladi va hamkorga xabar boradi."""
    now = now or clock.now_ms()
    if not partner_code(cur, user_id):
        raise PartnerError('Hamkor topilmadi.', 'not_found', 404)
    due = _totals(cur, user_id)['due']
    if due <= 0:
        raise PartnerError("Bu hamkorga to'lanadigan summa yo'q.", 'nothing_due', 409)
    amount = _int(amount, "Summa", 1, due, due)
    note = ' '.join(str(note or '').split())[:120] or None
    cur.execute('INSERT INTO partner_payouts (partner_user_id, amount, note, created_by, created_ms) '
                'VALUES (%s, %s, %s, %s, %s)', (user_id, amount, note, by, now))
    conn.commit()
    cur.execute('SELECT telegram_id FROM users WHERE id = %s', (user_id,))
    u = cur.fetchone()
    if u and u['telegram_id']:
        left = _totals(cur, user_id)['due']
        tgbot.send(u['telegram_id'], tgbot.L(
            f"💸 <b>Hamkorlik mukofoti to'landi: {som(amount)}</b>\n"
            + (f"Izoh: {html.escape(note)}\n" if note else '')
            + f"Qolgan hisob: {som(left)}. Rahmat!",
            f"💸 <b>Партнёрское вознаграждение выплачено: {som_ru(amount)}</b>\n"
            + (f"Комментарий: {html.escape(note)}\n" if note else '')
            + f"Остаток: {som_ru(left)}. Спасибо!"), tgbot.L('Hamkorlik', 'Партнёрство'), 'hamkor.html')
    return {'amount': amount}


def delete_payout(cur, conn, payout_id):
    cur.execute('DELETE FROM partner_payouts WHERE id = %s', (payout_id,))
    ok = cur.rowcount == 1
    conn.commit()
    if not ok:
        raise PartnerError("To'lov yozuvi topilmadi.", 'not_found', 404)


# ───────────────────────── Ko'rinishlar ─────────────────────────

def _sales(cur, user_id, limit):
    cur.execute('SELECT * FROM partner_earnings WHERE partner_user_id = %s ORDER BY created_ms DESC LIMIT %s',
                (user_id, limit))
    return [{'id': r['id'], 'order_code': r['order_code'], 'item': _items_label(r['items']),
             'paid': int(r['paid_amount']), 'percent': int(r['percent']), 'amount': int(r['amount']),
             'created_ms': int(r['created_ms']), 'buyer_id': int(r['buyer_id'])} for r in cur.fetchall()]


def _payouts(cur, user_id, limit):
    cur.execute('SELECT * FROM partner_payouts WHERE partner_user_id = %s ORDER BY created_ms DESC LIMIT %s',
                (user_id, limit))
    return [{'id': r['id'], 'amount': int(r['amount']), 'note': r['note'], 'by': r['created_by'],
             'created_ms': int(r['created_ms'])} for r in cur.fetchall()]


def mine(cur, user_id):
    """Profil uchun: foydalanuvchi hamkor bo'lsa — statistika, aks holda None."""
    row = partner_code(cur, user_id)
    if not row:
        return None
    data = _view(cur, row, tiers(cur))
    data['share'] = share_texts(row['code'], data['discount'])
    data['sales_list'] = [{k: s[k] for k in ('item', 'paid', 'percent', 'amount', 'created_ms')}
                          for s in _sales(cur, user_id, 10)]
    data['payouts'] = [{k: p[k] for k in ('amount', 'note', 'created_ms')} for p in _payouts(cur, user_id, 10)]
    return data


def admin_list(cur) -> dict:
    t = tiers(cur)
    cur.execute('''SELECT p.*, u.name, u.username, u.telegram_id FROM promo_codes p
                   LEFT JOIN users u ON u.id = p.partner_user_id
                   WHERE p.partner_user_id IS NOT NULL ORDER BY p.created_ms DESC''')
    out = []
    for r in cur.fetchall():
        v = _view(cur, r, t)
        v.update({'name': r['name'], 'username': r['username'], 'has_telegram': bool(r['telegram_id'])})
        out.append(v)
    totals = {k: sum(p[k] for p in out) for k in ('sales', 'revenue', 'earned', 'paid', 'due')}
    totals['count'] = len(out)
    totals['active'] = sum(1 for p in out if p['active'])
    return {'partners': out, 'totals': totals, 'tiers': t}


def admin_detail(cur, user_id) -> dict:
    if not partner_code(cur, user_id):
        raise PartnerError('Hamkor topilmadi.', 'not_found', 404)
    sales = _sales(cur, user_id, 100)
    ids = sorted({s['buyer_id'] for s in sales})
    names = {}
    if ids:
        cur.execute(f"SELECT id, name FROM users WHERE id IN ({', '.join(['%s'] * len(ids))})", ids)
        names = {r['id']: r['name'] for r in cur.fetchall()}
    for s in sales:
        s['buyer'] = names.get(s['buyer_id'])
    return {'sales': sales, 'payouts': _payouts(cur, user_id, 100)}


# ───────────────────────── Havola orqali kelganlar ─────────────────────────

def active_code(cur, code):
    """Faol hamkor kodi (katta-kichik harf farqsiz) yoki None."""
    code = str(code or '').strip().upper()
    if not code.isalnum() or len(code) > 20:
        return None
    cur.execute('SELECT * FROM promo_codes WHERE code = %s AND partner_user_id IS NOT NULL AND active = 1', (code,))
    return cur.fetchone()


def remember(cur, conn, telegram_id, code, now=None):
    cur.execute('DELETE FROM promo_referrals WHERE telegram_id = %s', (telegram_id,))
    cur.execute('INSERT INTO promo_referrals (telegram_id, code, created_ms) VALUES (%s, %s, %s)',
                (telegram_id, code, now or clock.now_ms()))
    conn.commit()


def saved_promo(cur, user, now=None):
    """Havola orqali saqlangan kod — hali ishlatsa bo'ladigan bo'lsa {'code', 'percent'}, aks holda None."""
    import payments
    now = now or clock.now_ms()
    if not user.get('telegram_id'):
        return None
    cur.execute('SELECT code, created_ms FROM promo_referrals WHERE telegram_id = %s', (int(user['telegram_id']),))
    row = cur.fetchone()
    if not row or int(row['created_ms']) < now - REFERRAL_TTL_MS:
        return None
    try:
        promo = payments._promo_row(cur, row['code'], user['id'], now)
    except payments.PayError:
        return None
    return {'code': promo['code'], 'percent': int(promo['percent'])} if promo else None


def start_link(cur, conn, chat_id, code_row):
    """/start <KOD>: kod saqlanadi va o'quvchiga xabar boradi. Hamkorning o'zi bossa — eslatma."""
    cur.execute('SELECT id FROM users WHERE telegram_id = %s', (chat_id,))
    me = cur.fetchone()
    code = code_row['code']
    if me and int(me['id']) == int(code_row['partner_user_id']):
        tgbot.send(chat_id, tgbot.L(
            f"🤝 <b>{code}</b> — bu sizning hamkorlik kodingiz. Uni do'stlaringizga yuboring: "
            f"ular xarid qilganda sizga foiz tushadi.",
            f"🤝 <b>{code}</b> — это ваш партнёрский код. Отправьте его друзьям: "
            f"когда они сделают покупку, вы получите процент."), tgbot.L('Hamkorlik', 'Партнёрство'), 'hamkor.html')
        return
    remember(cur, conn, chat_id, code)
    percent = int(code_row['percent'])
    tgbot.send(chat_id, tgbot.L(
        f"🎟 <b>{code}</b> promo-kodi saqlandi!\n"
        + (f"Fan yoki Bilim Premium sotib olayotganingizda u avtomatik qo'llanadi — "
           f"<b>−{percent}%</b> chegirma." if percent else
           "Fan yoki Bilim Premium sotib olayotganingizda u avtomatik qo'llanadi."),
        f"🎟 Промокод <b>{code}</b> сохранён!\n"
        + (f"Он применится автоматически при покупке предмета или Bilim Premium — "
           f"скидка <b>−{percent}%</b>." if percent else
           "Он применится автоматически при покупке предмета или Bilim Premium.")),
        tgbot.L("Do'konni ochish", 'Открыть магазин'), 'shop.html')
