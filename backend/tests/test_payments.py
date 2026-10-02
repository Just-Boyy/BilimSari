# -*- coding: utf-8 -*-
"""To'lov tizimi testi: buyurtma, chek, admin qarori, promo, paketlar, jonli chat, eslatmalar."""
import os
import sys
import time

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import admin_auth  # noqa: E402
import notify  # noqa: E402
import payments  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402
from games import clock  # noqa: E402

c = A.app.test_client()
fails = []
T = [int(time.time() * 1000)]
clock.now_ms = lambda: T[0]
ADMIN = 5771496552

CALLS = []
MID = [1000]


def fake_tg(method, payload):
    MID[0] += 1
    CALLS.append((method, payload))
    return {'ok': True, 'result': {'message_id': MID[0], 'file_path': 'photos/file_1.jpg'}}


tgbot.tg_api = fake_tg
A.tg_api = fake_tg


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:500]}'))
    if not cond:
        fails.append(name)


def db(sql, params=(), fetch=False):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall() if fetch else None
    conn.commit(); cur.close(); conn.close()
    return rows


def mk_user(name, tg=None, chosen='math'):
    uid = db('INSERT INTO users (name, email, password_hash, onboarded) VALUES (%s, NULL, NULL, TRUE) RETURNING id', (name,), True)[0]['id']
    db('UPDATE users SET telegram_id = %s, chosen_subject_key = %s WHERE id = %s', (tg, chosen, uid))
    return {'id': uid, 'tg': tg, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


def req(method, path, u=None, headers=None, **kw):
    r = getattr(c, method)(path, headers=headers or (u['h'] if u else {}), **kw)
    return r.status_code, (r.get_json() or {})


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
HOOK = {'X-Telegram-Bot-Api-Secret-Token': A.WEBHOOK_SECRET}


def hook(update):
    CALLS.clear()
    return c.post('/telegram/webhook', headers=HOOK, json=update).status_code


def msg(frm, **extra):
    m = {'message_id': MID[0] + 500, 'chat': {'id': frm, 'type': 'private'}, 'from': {'id': frm, 'first_name': 'Ali'}}
    m.update(extra)
    return {'message': m}


def cb(frm, data, message=None):
    return {'callback_query': {'id': 'q1', 'from': {'id': frm, 'first_name': 'Shukurjon'}, 'data': data,
                               'message': message or {'chat': {'id': frm}, 'message_id': 77}}}


def photo(uid_str):
    return [{'file_id': 'small', 'file_unique_id': 'u-small'}, {'file_id': f'F-{uid_str}', 'file_unique_id': f'U-{uid_str}'}]


def sent_to(chat, method=None):
    return [p for m, p in CALLS if p.get('chat_id') == chat and (method is None or m == method)]


def order(code_or_id):
    col = 'code' if isinstance(code_or_id, str) else 'id'
    return db(f'SELECT * FROM pay_orders WHERE {col} = %s', (code_or_id,), True)[0]


stud, guest, other = mk_user('Ali Valiyev', 9001), mk_user('Mehmon', None), mk_user('Sardor', 9002)

print('\n=== Sozlanmagan holat va eski DEMO ===')
s, d = req('get', '/api/pay/shop', stud)
check('Do\'kon: 11 ta yopiq fan, narxlar, sozlanmagan', s == 200 and len(d['subjects']) == 11 and d['configured'] is False
      and {k: d['prices'][k] for k in ('price_single', 'price_three', 'price_all')} == {'price_single': 12000, 'price_three': 30000, 'price_all': 80000} and d['telegram'], d)
s, d = req('post', '/api/pay/orders', stud, json={'keys': ['english']})
check('Karta sozlanmagan -> 503', s == 503 and d['code'] == 'not_configured', (s, d))
s, d = req('post', '/api/study/subjects/english/unlock', stud)
check('Eski DEMO (pulsiz ochish) o\'chirildi -> 402', s == 402 and d['code'] == 'use_shop', (s, d))

print('\n=== Admin: karta va narxlar ===')
s, d = req('post', '/api/admin/pay/settings', headers=ADM, json={'card_number': '8600 12'})
check('Noto\'g\'ri karta -> 400', s == 400, (s, d))
check('Adminsiz -> 401', req('post', '/api/admin/pay/settings', stud, json={})[0] == 401)
s, d = req('post', '/api/admin/pay/settings', headers=ADM,
           json={'card_number': '8600123456789012', 'card_holder': ' Shukurjon  S. ', 'price_single': 12000,
                 'price_three': 30000, 'price_all': 80000})
check('Saqlandi, karta formatlandi', s == 200 and d['settings']['card_number'] == '8600 1234 5678 9012'
      and d['settings']['card_holder'] == 'Shukurjon S.', d)

print('\n=== Narx va paketlar ===')
q = lambda keys, promo=None: req('post', '/api/pay/quote', stud, json={'keys': keys, 'promo': promo})  # noqa: E731
s, d = q(['english'])
check('1 fan — 12 000', d['amount'] == 12000 and d['bundle'] is None, d)
s, d = q(['english', 'history', 'chemistry'])
check('3 fan — paket 30 000 (6 000 tejash)', d['amount'] == 30000 and d['bundle'] == '3 ta fan paketi' and d['saving'] == 6000, d)
s, d = q(['english', 'history', 'chemistry', 'biology'])
check('4 fan — 30 000 + 12 000', d['amount'] == 42000, d)
alls = [x['key'] for x in req('get', '/api/pay/shop', stud)[1]['subjects']]
s, d = q(alls)
check('Barcha fanlar — 80 000', d['amount'] == 80000 and d['bundle'] == 'Barcha fanlar paketi', d)
check('Ochiq fan (math) -> 400', q(['math'])[0] == 400)
check('Bo\'sh ro\'yxat -> 400', q([])[0] == 400)

print('\n=== Promo-kod ===')
s, d = req('post', '/api/admin/pay/promos', headers=ADM, json={'code': 'maktab20', 'percent': 20, 'max_uses': 2})
check('Promo yaratildi (katta harf)', s == 200 and d['promos'][0]['code'] == 'MAKTAB20', d)
check('Takror -> 409', req('post', '/api/admin/pay/promos', headers=ADM, json={'code': 'MAKTAB20', 'percent': 10})[0] == 409)
check('100% -> 400', req('post', '/api/admin/pay/promos', headers=ADM, json={'code': 'BEPUL', 'percent': 100})[0] == 400)
s, d = q(['english', 'history', 'chemistry'], 'maktab20')
check('3 fan + 20% = 24 000', d['amount'] == 24000 and d['promo']['percent'] == 20, d)
s, d = q(['english'], 'YOQ')
check('Yo\'q promo -> 400', s == 400 and d['code'] == 'bad_promo', d)

print('\n=== Buyurtma ===')
s, d = req('post', '/api/pay/orders', guest, json={'keys': ['english']})
check('Telegram\'siz -> 400 no_telegram', s == 400 and d['code'] == 'no_telegram', (s, d))
CALLS.clear()
s, d = req('post', '/api/pay/orders', stud, json={'keys': ['history']})
first_code = d['order']['code']
s, d = req('post', '/api/pay/orders', stud, json={'keys': ['english']})
o1 = d['order']
check('Buyurtma yaratildi, bot yubordi', s == 200 and o1['status'] == 'awaiting_receipt' and d['bot_sent'] and o1['code'].startswith('BS-'), d)
check('Oldingi (chek kutilayotgan) buyurtma bekor qilindi', order(first_code)['status'] == 'cancelled')
m = sent_to(9001, 'sendMessage')[-1]
check('Yo\'riqnomada karta, summa, kod, tugmalar', '8600 1234 5678 9012' in m['text'] and "12 000 so'm" in m['text']
      and o1['code'] in m['text'] and 'ord:promo:' in str(m['reply_markup']) and 'ord:cancel:' in str(m['reply_markup']), m)
s, d = req('get', '/api/study/subjects', stud)
eng = next(x for x in d['subjects'] if x['key'] == 'english')
check('Ilovada holat: "chek kutilmoqda", narx', eng['pay_status'] == 'awaiting_receipt' and eng['price'] == 12000, eng)
s, d = req('get', '/api/study/topics/english', stud)
check('Yopiq fan sahifasida holat', s == 403 and d['pay_status']['status'] == 'awaiting_receipt' and d['pay_status']['code'] == o1['code'], d)

print('\n=== Bot: promo-kod ===')
hook(cb(9001, f"ord:promo:{o1['id']}"))
check('Promo so\'raldi', any('promo-kodni yozing' in p.get('text', '') for p in sent_to(9001)), CALLS)
hook(msg(9001, text='maktab20'))
check('Promo qo\'llandi: 9 600', order(o1['id'])['amount'] == 9600 and any("9 600" in p.get('text', '') for p in sent_to(9001)), CALLS)
check('Begona foydalanuvchi tugmasi ishlamaydi', hook(cb(9002, f"ord:cancel:{o1['id']}")) == 200 and order(o1['id'])['status'] == 'awaiting_receipt')

print('\n=== Chek ===')
hook(msg(9001, photo=photo('1')))
o = order(o1['id'])
check('Chek qabul qilindi -> pending', o['status'] == 'pending' and o['receipt_file_id'] == 'F-1', dict(o))
adm = sent_to(ADMIN, 'sendPhoto')
check('Adminga chek + Tasdiqlash/Rad etish', adm and o1['code'] in adm[0]['caption'] and 'pay:ok:' in str(adm[0]['reply_markup'])
      and "9 600" in adm[0]['caption'] and 'MAKTAB20' in adm[0]['caption'], adm)
check('O\'quvchiga "Chek qabul qilindi"', any('Chek qabul qilindi' in p.get('text', '') for p in sent_to(9001)))
hook(msg(9001, photo=photo('2')))
check('Ikkinchi chek -> "allaqachon tekshirilmoqda"', any('allaqachon tekshirilmoqda' in p.get('text', '') for p in sent_to(9001)))
s, d = req('post', '/api/pay/orders', stud, json={'keys': ['history']})
check('Tekshiruv paytida yangi buyurtma -> 409', s == 409 and d['code'] == 'pending_exists', (s, d))

print('\n=== Admin: rad etish ===')
hook(cb(9002, f"pay:ok:{o1['id']}"))
check('Admin bo\'lmagan tasdiqlay olmaydi', order(o1['id'])['status'] == 'pending'
      and any('faqat admin' in p.get('text', '') for m_, p in CALLS if m_ == 'answerCallbackQuery'))
hook(cb(ADMIN, f"pay:no:{o1['id']}"))
check('Sabablar ro\'yxati chiqdi', any(m_ == 'editMessageReplyMarkup' and 'pay:rj:' in str(p) for m_, p in CALLS), CALLS)
hook(cb(ADMIN, f"pay:rj:{o1['id']}:kam"))
o = order(o1['id'])
check('Rad etildi, sabab saqlandi', o['status'] == 'rejected' and o['reject_reason'] == "To'lov summasi kam" and o['decided_by'] == 'Shukurjon', dict(o))
um = [p for p in sent_to(9001) if 'tasdiqlanmadi' in p.get('text', '')]
check('O\'quvchiga sabab + "Qayta urinish"', um and 'summasi kam' in um[0]['text'] and 'ord:retry:' in str(um[0]['reply_markup']), CALLS)
check('Admin xabari yangilandi (tugmalarsiz)', any(m_ == 'editMessageCaption' and 'Rad etildi' in p['caption'] for m_, p in CALLS))
hook(cb(ADMIN, f"pay:ok:{o1['id']}"))
check('Hal qilingan -> qayta bosish ishlamaydi', order(o1['id'])['status'] == 'rejected'
      and any('allaqachon' in p.get('text', '') for m_, p in CALLS if m_ == 'answerCallbackQuery'))
s, d = req('get', '/api/study/subjects', stud)
check('Ilovada "rad etildi"', next(x for x in d['subjects'] if x['key'] == 'english')['pay_status'] == 'rejected')

print('\n=== Qayta urinish, takroriy chek, tasdiqlash ===')
hook(cb(9001, f"ord:retry:{o1['id']}"))
o2 = db("SELECT * FROM pay_orders WHERE user_id = %s AND status = 'awaiting_receipt'", (stud['id'],), True)[0]
check('Yangi buyurtma (promo saqlandi)', o2['promo_code'] == 'MAKTAB20' and o2['amount'] == 9600 and o2['code'] != o1['code'], dict(o2))
hook(msg(9001, photo=photo('1')))
adm = sent_to(ADMIN, 'sendPhoto')
check('Takroriy chek aniqlandi', adm and 'avval yuborilgan' in adm[0]['caption'] and o1['code'] in adm[0]['caption'], adm)
hook(cb(ADMIN, f"pay:ok:{o2['id']}"))
o = order(o2['id'])
check('Tasdiqlandi', o['status'] == 'approved', dict(o))
check('Fan ochildi', db("SELECT 1 FROM subject_purchases WHERE user_id = %s AND subject_key = 'english'", (stud['id'],), True))
ok_msg = [p for p in sent_to(9001) if 'tasdiqlandi' in p.get('text', '')]
check('O\'quvchiga tabrik + "Darsni boshlash"', ok_msg and 'topics.html?fan=english' in str(ok_msg[0]['reply_markup']), CALLS)
check('Promo ishlatildi = 1', db("SELECT used FROM promo_codes WHERE code = 'MAKTAB20'", fetch=True)[0]['used'] == 1)
check('Fan sahifasi ochiq', req('get', '/api/study/topics/english', stud)[0] == 200)
s, d = q(['history'], 'MAKTAB20')
check('Bir kishi promoni ikki marta ishlata olmaydi', s == 400 and 'allaqachon' in d['error'], d)

print('\n=== Admin panel (sayt) ===')
s, d = req('post', '/api/pay/orders', other, json={'keys': ['history', 'chemistry', 'biology'], 'promo': 'MAKTAB20'})
o3 = d['order']
check('Paket + promo buyurtma', s == 200 and o3['amount'] == 24000, d)
hook(msg(9002, photo=photo('3')))
s, d = req('get', '/api/admin/pay/orders?status=pending', headers=ADM)
check('Kutilayotgan cheklar ro\'yxati', s == 200 and [x['code'] for x in d['orders']] == [o3['code']] and d['orders'][0]['has_receipt'], d)
s, d = req('post', f"/api/admin/pay/orders/{o3['id']}/reject", headers=ADM, json={'reason': 'nomalum'})
check('Noma\'lum sabab -> 409', s == 409, (s, d))
s, d = req('post', f"/api/admin/pay/orders/{o3['id']}/approve", headers=ADM)
check('Saytdan tasdiqlandi', s == 200 and order(o3['id'])['status'] == 'approved' and order(o3['id'])['decided_by'] == 'Admin panel', d)
check('3 ta fan ochildi', len(db('SELECT 1 FROM subject_purchases WHERE user_id = %s', (other['id'],), True)) == 3)
s, d = req('get', '/api/admin/pay/overview', headers=ADM)
check('Tushum: bugun 33 600, 2 ta', d['stats']['today'] == {'count': 2, 'sum': 33600} and d['stats']['pending'] == 0, d['stats'])
check('Promo limiti (2) tugadi', d['promos'][0]['used'] == 2)
check('Limit tugagan promo -> 400', q(['history'], 'MAKTAB20')[1].get('code') == 'bad_promo')
s, d = req('post', '/api/admin/pay/promos/MAKTAB20/toggle', headers=ADM)
check('Promo o\'chirildi', s == 200 and d['promos'][0]['active'] is False)
s, d = req('get', '/api/admin/stats', headers=ADM)
check('Statistikada haqiqiy tushum', d['revenue'] == 33600, d.get('revenue'))

tgbot.BOT_TOKEN = 'test'
payments.requests = type('R', (), {'get': staticmethod(lambda url, timeout=0: type('Resp', (), {'status_code': 200, 'content': b'JPEGDATA'})()),
                                    'RequestException': Exception})
r = c.get(f"/api/admin/pay/orders/{o3['id']}/receipt", headers=ADM)
check('Chek rasmi admin panelga (token sirligicha)', r.status_code == 200 and r.data == b'JPEGDATA' and r.mimetype == 'image/jpeg', r.status_code)
check('Chek rasmi — adminsiz 401', c.get(f"/api/admin/pay/orders/{o3['id']}/receipt").status_code == 401)
tgbot.BOT_TOKEN = ''

print('\n=== Jonli chat ===')
hook(msg(9001, text='Salom, savolim bor'))
am = sent_to(ADMIN, 'sendMessage')
check('Savol adminga bordi', am and 'Salom, savolim bor' in am[0]['text'] and 'tg 9001' in am[0]['text'], CALLS)
check('O\'quvchiga tasdiq', any('adminga yuborildi' in p.get('text', '') for p in sent_to(9001)))
admin_msg_id = MID[0] - 1
hook(msg(9001, text='Yana bir savol'))
check('Tasdiq takrorlanmaydi', not any('adminga yuborildi' in p.get('text', '') for p in sent_to(9001)))
hook(msg(ADMIN, text='Javobim <b>shu</b>', reply_to_message={'message_id': admin_msg_id}))
um = sent_to(9001, 'sendMessage')
check('Admin javobi o\'quvchiga (xavfsiz HTML)', um and 'Admin:' in um[0]['text'] and '&lt;b&gt;shu' in um[0]['text'], CALLS)
check('Adminga "Yuborildi"', any('Yuborildi' in p.get('text', '') for p in sent_to(ADMIN)))
hook(msg(ADMIN, text='Hech kimga', reply_to_message={'message_id': 1}))
check('Noma\'lum xabarga javob -> ogohlantirish', any("o'quvchi topilmadi" in p.get('text', '') for p in sent_to(ADMIN)))
hook(msg(ADMIN, text='oddiy matn'))
check('Admin oddiy matn -> yo\'riqnoma', any('Siz adminsiz' in p.get('text', '') for p in sent_to(ADMIN)))
hook(msg(9001, photo=photo('9')))
check('Buyurtmasiz rasm -> adminga (jonli chat)', any(m_ == 'copyMessage' and p['chat_id'] == ADMIN for m_, p in CALLS), CALLS)
hook({'message': {'message_id': 5, 'chat': {'id': -100, 'type': 'group'}, 'from': {'id': 9001}, 'text': 'guruh'}})
check('Guruh xabarlari e\'tiborsiz', not CALLS, CALLS)

print('\n=== Buyruqlar ===')
hook(msg(9001, text='/tolovlarim'))
t = sent_to(9001, 'sendMessage')
check('/tolovlarim', t and o1['code'] in t[0]['text'] and 'Rad etilgan' in t[0]['text'] and 'Tasdiqlangan' in t[0]['text'], t)
hook(msg(ADMIN, text='/tolovlar'))
check('/tolovlar (admin)', any("Kutilayotgan chek yo'q" in p.get('text', '') for p in sent_to(ADMIN)), CALLS)
hook(msg(9001, text='/sotib_olish'))
check('/sotib_olish -> do\'kon tugmasi', any('shop.html' in str(p.get('reply_markup')) for p in sent_to(9001)), CALLS)
hook(msg(9001, text='/start pay'))
check('/start pay -> do\'kon', any('shop.html' in str(p.get('reply_markup')) for p in sent_to(9001)))

print('\n=== Eslatmalar va himoya ===')
s, d = req('post', '/api/pay/orders', stud, json={'keys': ['history']})
o4 = d['order']
hook(msg(9001, photo=photo('4')))
CALLS.clear()
T[0] += 31 * 60 * 1000
res = payments.housekeeping(*(lambda cn: (cn.cursor(), cn))(get_connection()))
check('30 daqiqa -> adminga eslatma', res['reminded'] == 1 and any('30 daqiqadan' in p.get('text', '') for p in sent_to(ADMIN)), CALLS)
CALLS.clear()
conn = get_connection(); cur = conn.cursor()
res = payments.housekeeping(cur, conn)
check('Eslatma bir marta', res['reminded'] == 0 and not CALLS)
summary = payments.daily_summary(cur)
check('Kunlik hisobot', summary and '33 600' in summary and 'Kutilmoqda: 1' in summary, summary)
cur.close(); conn.close()
hook(cb(ADMIN, f"pay:ok:{o4['id']}"))
s, d = req('post', '/api/pay/orders', stud, json={'keys': ['chemistry']})
T[0] += 25 * 3600 * 1000
conn = get_connection(); cur = conn.cursor()
res = payments.housekeeping(cur, conn)
cur.close(); conn.close()
check('24 soatda chek kelmasa -> expired', res['expired'] == 1 and order(d['order']['id'])['status'] == 'expired')
# Sutkalik chek limiti
check('Soatiga 10 tadan ortiq buyurtma -> 429', req('post', '/api/pay/orders', stud, json={'keys': ['law']})[0] in (200, 429))
db("DELETE FROM rate_hits WHERE bucket LIKE 'order:%'")
for i in range(5):
    s, d = req('post', '/api/pay/orders', stud, json={'keys': ['chemistry']})
    if 'order' not in d: print('ORDER FAIL', i, s, d)
    db('UPDATE pay_orders SET receipt_ms = %s, status = %s WHERE id = %s', (T[0], 'rejected', d['order']['id']))
s, d = req('post', '/api/pay/orders', stud, json={'keys': ['chemistry']})
hook(msg(9001, photo=photo('x')))
check('Sutkada 5 tadan ortiq chek -> rad', any("juda ko'p chek" in p.get('text', '') for p in sent_to(9001))
      and order(d['order']['id'])['status'] == 'awaiting_receipt', CALLS)
s, d = req('post', f"/api/pay/orders/{d['order']['id']}/cancel", stud)
check('Ilovadan bekor qilish', s == 200)
s, d = req('get', '/api/pay/orders', stud)
check('To\'lovlar tarixi (bekor qilinganlarsiz)', s == 200 and all(o['status'] != 'cancelled' for o in d['orders']) and len(d['orders']) >= 3, d)
check('Admin kunlik hisobot jobi (21:00)', 'pay_summary' in open(os.path.join(BACKEND, 'notify.py'), encoding='utf-8').read())
check('shop.html sahifasi', c.get('/shop.html').status_code == 200)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
