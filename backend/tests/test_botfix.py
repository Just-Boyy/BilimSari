# -*- coding: utf-8 -*-
"""Bot kamchiliklari tuzatilganini tekshiradi (10 ta band)."""
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
import botchat  # noqa: E402
import broadcast  # noqa: E402
import payments  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402

c = A.app.test_client()
fails = []
OWNER = 5771496552
CALLS = []
MID = [5000]
BLOCKED = {8003}


def fake_tg(method, payload):
    MID[0] += 1
    CALLS.append((method, payload))
    if method == 'createInvoiceLink':
        return {'ok': True, 'result': 'https://t.me/$invoice' + str(MID[0])}
    if method in ('sendMessage', 'sendPhoto', 'copyMessage') and payload.get('chat_id') in BLOCKED:
        return {'ok': False, 'error_code': 403, 'description': 'Forbidden: bot was blocked by the user'}
    return {'ok': True, 'result': {'message_id': MID[0]}}


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


def mk(name, tg=None, username=None, notify=1):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id, username) VALUES (%s, TRUE, 'math', %s, %s) RETURNING id",
             (name, tg, username), True)[0]['id']
    db('UPDATE users SET notify = %s WHERE id = %s', (notify, uid))
    return {'id': uid, 'tg': tg, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


HOOK = {'X-Telegram-Bot-Api-Secret-Token': A.WEBHOOK_SECRET}
ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
UPD = [100]


def hook(body, update_id=None):
    CALLS.clear()
    UPD[0] += 1
    body = dict(body, update_id=update_id if update_id is not None else UPD[0])
    return c.post('/telegram/webhook', headers=HOOK, json=body).status_code


def msg(frm, text=None, chat_type='private', chat_id=None, **extra):
    m = {'message_id': 1, 'chat': {'id': chat_id or frm, 'type': chat_type}, 'from': {'id': frm, 'first_name': 'Ali'}}
    if text is not None:
        m['text'] = text
    m.update(extra)
    return {'message': m}


def sent(chat=None, method=None):
    return [p for m, p in CALLS if (chat is None or p.get('chat_id') == chat) and (method is None or m == method)]


print('\n=== 9) Takroriy yangilanish ===')
hook(msg(9101, 'Salom, savol bor'), update_id=777)
first = len(sent(OWNER))
hook(msg(9101, 'Salom, savol bor'), update_id=777)
check('Bir xil update_id ikkinchi marta ishlanmaydi', first == 1 and not CALLS, (first, CALLS))

print('\n=== 6) Guruhlar ===')
hook(msg(9101, '/start@bilimsaribot', chat_type='group', chat_id=-100500))
g = sent(-100500)
check('Guruhda /start — oddiy havola tugmasi (web_app emas)', g and 'url' in str(g[0]['reply_markup'])
      and 'web_app' not in str(g[0]['reply_markup']), g)
hook(msg(9101, 'oddiy gap', chat_type='supergroup', chat_id=-100500))
check('Guruhdagi oddiy xabar e\'tiborsiz', not CALLS, CALLS)

print('\n=== 4, 5) Matnlar va menyu ===')
hook(msg(9101, '/start'))
st = sent(9101, 'sendMessage')[0]
kb = str(st['reply_markup'])
check('/start: chaqmoq, XP yo\'q', 'Chaqmoq' in st['text'] and 'XP' not in st['text'], st['text'])
check("/start: pastki menyu (5 ta matnli tugma — initData yo'qolmaydi)", all(b in kb for b in (botchat.BTN_APP, botchat.BTN_DAILY, botchat.BTN_SHOP,
      botchat.BTN_ORDERS, botchat.BTN_SUPPORT)) and 'web_app' not in kb and st['reply_markup'].get('is_persistent'), kb)
hook(msg(9101, botchat.BTN_ORDERS))
check("Menyu: \"To'lovlarim\" — ro'yxat, adminga ketmaydi", sent(9101) and not sent(OWNER), CALLS)
hook(msg(9101, botchat.BTN_SUPPORT))
check('Menyu: "Admin bilan bog\'lanish" — yo\'riqnoma, adminga ketmaydi',
      any('Savolingizni' in p.get('text', '') for p in sent(9101)) and not sent(OWNER), CALLS)
hook(msg(9101, '/help'))
check('/help ham menyuni qaytaradi', 'keyboard' in str(sent(9101)[0].get('reply_markup')))

print('\n=== 8) Bot sozlamasi bir marta ===')
A.BOT_TOKEN = 'test'
CALLS.clear()
A.setup_telegram_bot()
methods = [m for m, p in CALLS]
wh = next((p for m, p in CALLS if m == 'setWebhook'), {})
check('Birinchi worker: webhook, buyruqlar, tavsif', {'setWebhook', 'setMyCommands', 'setMyDescription',
      'setMyShortDescription', 'setChatMenuButton'} <= set(methods) and 'pre_checkout_query' not in wh.get('allowed_updates', []), methods)
desc = next(p for m, p in CALLS if m == 'setMyDescription')['description']
check('Tavsifda chaqmoq/kun savoli, XP yo\'q', 'chaqmoq' in desc and 'kun savoli' in desc and 'XP' not in desc, desc)
CALLS.clear()
A.setup_telegram_bot()
check('Ikkinchi worker: Telegram\'ga qayta yubormaydi (429 yo\'q)', not CALLS, CALLS)
A.BOT_TOKEN = ''

print('\n=== 1, 2) Ommaviy xabar ===')
bu = [mk(f'B{i}', 8000 + i) for i in range(1, 6)]
mk('Ochirgan', 8006, notify=0)
s = c.post('/api/admin/broadcast', headers=ADM, json={'message': 'Yangilik!'})
check('Bot tokeni yo\'q bo\'lsa — 503', s.status_code == 503)
import admin_api  # noqa: E402
admin_api.BOT_TOKEN = 'test'
t0 = time.time()
CALLS.clear()
s = c.post('/api/admin/broadcast', headers=ADM, json={'message': 'Yangilik!'})
d = s.get_json()
check('So\'rov darhol qaytadi (fonda yuboriladi)', s.status_code == 200 and time.time() - t0 < 1.5 and d['state'] == 'running', (s.status_code, d))
s2 = c.post('/api/admin/broadcast', headers=ADM, json={'message': 'Yana'})
check('Oldingisi tugamaguncha yangisi — 409', s2.status_code == 409, s2.get_json())
for _ in range(60):
    st = c.get(f"/api/admin/broadcast/{d['id']}", headers=ADM).get_json()
    if st['state'] == 'done':
        break
    time.sleep(0.2)
got = sorted(p['chat_id'] for m, p in CALLS if m == 'sendMessage' and p.get('text') == 'Yangilik!')
check('Tugadi: eslatmani o\'chirganga bormadi', st['state'] == 'done' and 8006 not in got and 8001 in got, (st, got))
check('Bloklagan belgilandi (notify=0)', st['blocked'] >= 1 and db('SELECT notify FROM users WHERE telegram_id = 8003', fetch=True)[0]['notify'] == 0, st)
# Worker o'lib qolgan tarqatishni davom ettirish
conn = get_connection(); cur = conn.cursor()
cur.execute("INSERT INTO broadcasts (text, status, total, last_user_id, created_ms, heartbeat_ms) VALUES ('Davomi', 'running', 5, %s, 1, 1) RETURNING id",
            (bu[2]['id'],))
bid = cur.fetchone()['id']; conn.commit()
CALLS.clear()
resumed = broadcast.resume_stale(cur, conn)
cur.close(); conn.close()
for _ in range(60):
    st = c.get(f'/api/admin/broadcast/{bid}', headers=ADM).get_json()
    if st['state'] == 'done':
        break
    time.sleep(0.2)
got = sorted(p['chat_id'] for m, p in CALLS if m == 'sendMessage' and p.get('text') == 'Davomi')
check('Osilib qolgan tarqatish qolgan joyidan davom etdi', resumed == [bid] and st['state'] == 'done'
      and 8001 not in got and 8004 in got and 8005 in got, (resumed, st, got))

print('\n=== 3) Ikkinchi admin ===')
ona = mk('Ona', 9200, username='ona_uz')
r = c.post('/api/admin/admins', headers=ADM, json={'who': '@ona_uz'})
d = r.get_json()
check('Admin qo\'shildi va botda xabardor qilindi', r.status_code == 200 and d['notified'] and any(a['telegram_id'] == 9200 for a in d['admins']), d)
check('Yangi admin tan olinadi', admin_auth.is_admin_telegram(9200) and 9200 in payments.admin_ids())
check('/api/me: is_admin', c.get('/api/me', headers=ona['h']).get_json()['user']['is_admin'] is True)
check('Takror — 409', c.post('/api/admin/admins', headers=ADM, json={'who': '9200'}).status_code == 409)
check('Topilmadi — 404', c.post('/api/admin/admins', headers=ADM, json={'who': '@yoq_odam'}).status_code == 404)
check('Asosiy adminni olib bo\'lmaydi', c.delete(f'/api/admin/admins/{OWNER}', headers=ADM).status_code == 400)
# chek ikkala adminga ham boradi
db("INSERT INTO pay_settings (key, value) VALUES ('card_number', '8600 1234 5678 9012')")
stud = mk('Xaridor', 9300)
o = c.post('/api/pay/orders', headers=stud['h'], json={'keys': ['english']}).get_json()['order']
hook(msg(9300, photo=[{'file_id': 'F1', 'file_unique_id': 'U1'}]))
check('Chek ikkala adminga keldi', {p['chat_id'] for p in sent(method='sendPhoto')} == {OWNER, 9200}, sent(method='sendPhoto'))
r = c.delete('/api/admin/admins/9200', headers=ADM)
check('Admin olib tashlandi', r.status_code == 200 and not admin_auth.is_admin_telegram(9200))

print('\n=== 7) Admin o\'quvchiga birinchi yozadi ===')
CALLS.clear()
r = c.post(f"/api/admin/users/{stud['id']}/message", headers=ADM, json={'text': 'Salom <b>'})
m = sent(9300, 'sendMessage')
check('Yuborildi, HTML xavfsiz', r.status_code == 200 and m and 'Admin:' in m[0]['text'] and '&lt;b&gt;' in m[0]['text'], (r.get_json(), m))
nt = mk('Telegramsiz')
check('Telegramsiz o\'quvchi — 400', c.post(f"/api/admin/users/{nt['id']}/message", headers=ADM, json={'text': 'x'}).status_code == 400)
blk = db('SELECT id FROM users WHERE telegram_id = 8003', fetch=True)[0]['id']
check('Bloklagan — 502 va tushunarli xato', c.post(f'/api/admin/users/{blk}/message', headers=ADM, json={'text': 'x'}).status_code == 502)

print('\n=== 10) Telegram Stars olib tashlangan ===')
q = c.post('/api/pay/quote', headers=stud['h'], json={'keys': ['history']}).get_json()
check("Narxda Stars yo'q", q['ok'] and 'stars' not in q, q)
shop = c.get('/api/pay/shop', headers=stud['h']).get_json()
check("Do'konda Stars yo'q", 'stars_enabled' not in shop and set(shop['prices']) == {'price_single', 'price_three', 'price_all'}, shop)
check('/api/pay/stars — 404', c.post('/api/pay/stars', headers=stud['h'], json={'keys': ['law']}).status_code in (404, 405))
check('/api/admin/pay/stars — 404', c.get('/api/admin/pay/stars', headers=ADM).status_code == 404)
CALLS.clear()
hook({'pre_checkout_query': {'id': 'pq1', 'from': {'id': 9300}, 'currency': 'XTR', 'total_amount': 1, 'invoice_payload': 'BS-1'}})
check("pre_checkout_query e'tiborsiz", not any(m == 'answerPreCheckoutQuery' for m, p in CALLS), CALLS)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))

print('\n=== Menyu tugmalari inline "Ochish" tugmasini yuboradi ===')
for btn, page in ((botchat.BTN_APP, 'dashboard.html'), (botchat.BTN_DAILY, 'daily.html'), (botchat.BTN_SHOP, 'shop.html')):
    hook(msg(9101, btn))
    m = sent(9101, 'sendMessage')
    check(f'{btn} -> inline web_app {page}', m and page in str(m[-1].get('reply_markup')) and 'inline_keyboard' in str(m[-1].get('reply_markup'))
          and not sent(OWNER), (m, CALLS))
print('\n' + ('HAMMASI OK (2)' if not fails else f'{len(fails)} ta XATO: {fails}'))
