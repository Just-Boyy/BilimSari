# -*- coding: utf-8 -*-
"""Hamkorlik dasturi: hamkor kodi, komissiya, pog'onalar, himoya, havola, to'lovlar, admin."""
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import admin_auth  # noqa: E402
import partners  # noqa: E402
import payments  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402

c = A.app.test_client()
fails = []
CALLS = []


def fake_tg(method, payload):
    CALLS.append((method, payload))
    return {'ok': True, 'result': {'message_id': 1}}


tgbot.tg_api = fake_tg
A.tg_api = fake_tg


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:600]}'))
    if not cond:
        fails.append(name)


def db(sql, params=(), fetch=False):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall() if fetch else None
    conn.commit(); cur.close(); conn.close()
    return rows


def withcur(fn):
    conn = get_connection(); cur = conn.cursor()
    try:
        return fn(cur, conn)
    finally:
        cur.close(); conn.close()


def mk(name, tg, username=None, chosen='math'):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id, username, grade) "
             "VALUES (%s, TRUE, %s, %s, %s, 7) RETURNING id", (name, chosen, tg, username), True)[0]['id']
    return {'id': uid, 'tg': tg, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


def sent_to(chat):
    return [p.get('text', '') for m, p in CALLS if m == 'sendMessage' and p.get('chat_id') == chat]


def buy(u, keys, promo=None, approve=True):
    """Buyurtma → chek → admin qarori. (buyurtma id, create javobi)."""
    if keys == ['premium']:
        r = c.post('/api/premium/order', headers=u['h'], json={'promo': promo})
    else:
        r = c.post('/api/pay/orders', headers=u['h'], json={'keys': keys, 'promo': promo})
    d = r.get_json()
    if not d.get('ok'):
        return None, d
    oid = d['order']['id']
    withcur(lambda cur, conn: payments.attach_receipt(cur, conn, u['tg'], f'f{oid}', f'u{oid}', 'photo'))
    withcur(lambda cur, conn: payments.decide(cur, conn, oid, approve, 'Admin', None if approve else 'kam'))
    return oid, d


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
withcur(lambda cur, conn: payments.save_settings(cur, conn, {'card_number': '8600123412341234', 'card_holder': 'Test',
                                                              'price_single': 24000, 'price_three': 60000}))
ali = mk('Ali Hamkor', 81001, 'ali_h')
s1 = mk('Sardor', 81002)
s2 = mk('Madina', 81003)
s3 = mk('Bekzod', 81004)
nop = mk('Telegramsiz', None)

print('=== 1) Admin hamkor qo\'shadi ===')
r = c.post('/api/admin/partners', headers=ADM, json={'who': '@ali_h', 'code': 'ali20', 'commission': 20, 'discount': 10}).get_json()
check('Hamkor qo\'shildi (kod katta harfda)', r['ok'] and r['code'] == 'ALI20' and r['totals']['count'] == 1, r)
p = r['partners'][0]
check("Ro'yxatda: 20%, −10%, faol, havola", p['commission'] == 20 and p['discount'] == 10 and p['active']
      and p['link'].endswith('?start=ALI20') and p['due'] == 0, p)
r = c.post('/api/admin/partners', headers=ADM, json={'who': str(ali['id']), 'code': 'ALI2'})
check('Bir odam ikki marta hamkor bo\'lmaydi (409)', r.status_code == 409)
r = c.post('/api/admin/partners', headers=ADM, json={'who': '@yoq_odam', 'code': 'XYZ1'})
check('Topilmagan foydalanuvchi — 404', r.status_code == 404)
r = c.post('/api/admin/partners', headers=ADM, json={'who': str(s3['id']), 'code': 'PAY'})
check('Band so\'z (PAY) kod bo\'lmaydi', r.status_code == 400, r.get_json())
r = c.post('/api/admin/partners', headers=ADM, json={'who': str(s3['id']), 'code': 'ALI20'})
check('Mavjud kod — 409', r.status_code == 409)
r = c.post('/api/admin/partners', headers=ADM, json={'who': str(s3['id']), 'code': 'BEK', 'commission': 0})
check('Komissiya 0 — 400', r.status_code == 400)
check('Himoyalangan', c.get('/api/admin/partners').status_code == 401)
promos = c.get('/api/admin/pay/overview', headers=ADM).get_json()['promos']
check('Hamkor kodi oddiy promo-kodlar ro\'yxatida chiqmaydi', all(x['code'] != 'ALI20' for x in promos), promos)

print('\n=== 2) O\'z kodini ishlata olmaydi ===')
r = c.post('/api/pay/quote', headers=ali['h'], json={'keys': ['history'], 'promo': 'ALI20'})
check('Hamkor o\'z kodini kiritsa — rad', r.status_code == 400 and 'hamkorlik kodingiz' in r.get_json()['error'], r.get_json())

print('\n=== 3) Sotuv va komissiya ===')
q = c.post('/api/pay/quote', headers=s1['h'], json={'keys': ['history'], 'promo': 'ali20'}).get_json()
check("Xaridorga −10%: 24 000 → 21 600", q['ok'] and q['amount'] == 21600 and q['promo']['percent'] == 10, q)
CALLS.clear()
oid, d = buy(s1, ['history'], 'ALI20')
e = db('SELECT * FROM partner_earnings WHERE order_id = %s', (oid,), True)
check('Komissiya to\'langan summadan: 21 600 × 20% = 4 320', e and e[0]['amount'] == 4320 and e[0]['percent'] == 20
      and e[0]['paid_amount'] == 21600, e and dict(e[0]))
msg = sent_to(81001)
check("Hamkorga botda xabar: +4 320 so'm", any('Kodingiz orqali yangi xarid' in t and "+4 320 so'm" in t for t in msg), msg)
check("Xabarda xaridor ismi yo'q (maxfiylik)", not any('Sardor' in t for t in msg), msg)
adm = [p for m, p in CALLS if m in ('sendPhoto', 'editMessageCaption')]
check('Admin chek xabarida "Hamkor kodi — Ali Hamkor"', any('Hamkor kodi — Ali Hamkor' in (p.get('caption') or '') for p in adm), adm[:1])
oid2, _ = buy(s1, ['biology'], 'ALI20')
check('Bir o\'quvchi kodni ikkinchi marta ishlata olmaydi', oid2 is None and _['code'] == 'bad_promo', _)

print('\n=== 4) Rad etilgan — komissiya yo\'q; Premium ham ishlaydi ===')
oid, _ = buy(s2, ['history'], 'ALI20', approve=False)
check('Rad etilgan buyurtma — komissiya yozilmadi', not db('SELECT 1 FROM partner_earnings WHERE order_id = %s', (oid,), True))
CALLS.clear()
oid, d = buy(s2, ['premium'], 'ALI20')
e = db('SELECT * FROM partner_earnings WHERE order_id = %s', (oid,), True)
check("Premium: 34 900 −10% = 31 400 → 20% = 6 280", d['order']['amount'] == 31400 and e and e[0]['amount'] == 6280, (d, e and dict(e[0])))
check("Xabarda: Bilim Premium", any('Bilim Premium' in t for t in sent_to(81001)), sent_to(81001))
oid, _ = buy(s3, ['history'])
check('Kodsiz xarid — komissiya yo\'q (faqat kod qo\'llanganda)',
      not db('SELECT 1 FROM partner_earnings WHERE order_id = %s', (oid,), True))

print('\n=== 5) Hamkor profili ===')
r = c.get('/api/partner', headers=ali['h']).get_json()
h = r['partner']
check("Profil: 2 sotuv, 10 600 so'm ishlangan, hammasi to'lanishi kerak", h and h['sales'] == 2 and h['earned'] == 10600
      and h['paid'] == 0 and h['due'] == 10600, h)
check('Ulashish matni (uz/ru) kod va havola bilan', 'ALI20' in h['share']['uz'] and '−10%' in h['share']['uz']
      and '?start=ALI20' in h['share']['ru'] and 'промокод' in h['share']['ru'], h['share'])
check("Sotuvlar ro'yxati xaridor ma'lumotisiz", len(h['sales_list']) == 2 and 'buyer_id' not in h['sales_list'][0], h['sales_list'])
check('Keyingi pog\'ona: yana 8 ta → 25%', h['next_tier'] == {'sales_left': 8, 'percent': 25, 'at': 10}, h['next_tier'])
check('Oddiy o\'quvchida hamkorlik yo\'q', c.get('/api/partner', headers=s1['h']).get_json()['partner'] is None)

print('\n=== 6) To\'lovni yozib borish ===')
CALLS.clear()
r = c.post(f"/api/admin/partners/{ali['id']}/payout", headers=ADM, json={'amount': 20000})
check("Qarzdan ko'p yozib bo'lmaydi", r.status_code == 400, r.get_json())
r = c.post(f"/api/admin/partners/{ali['id']}/payout", headers=ADM, json={'amount': 6000, 'note': 'Click'}).get_json()
p = r['partners'][0]
check("6 000 to'landi → qarz 4 600", r['ok'] and p['paid'] == 6000 and p['due'] == 4600, p)
check("Hamkorga xabar: mukofot to'landi", any("mukofoti to'landi: 6 000 so'm" in t for t in sent_to(81001)), sent_to(81001))
r = c.post(f"/api/admin/partners/{ali['id']}/payout", headers=ADM, json={}).get_json()
check("Summasiz — butun qarz to'lanadi", r['partners'][0]['due'] == 0 and r['totals']['paid'] == 10600, r['totals'])
r = c.post(f"/api/admin/partners/{ali['id']}/payout", headers=ADM, json={})
check("Qarz yo'q — 409", r.status_code == 409)
det = c.get(f"/api/admin/partners/{ali['id']}", headers=ADM).get_json()
check('Tarix: 2 sotuv (xaridor ismi bilan), 2 to\'lov', len(det['sales']) == 2 and det['sales'][0]['buyer'] == 'Madina'
      and len(det['payouts']) == 2 and det['payouts'][-1]['note'] == 'Click', det)
r = c.post(f"/api/admin/partners/payouts/{det['payouts'][0]['id']}/delete", headers=ADM).get_json()
check("Xato yozilgan to'lovni o'chirish → qarz qaytadi", r['ok'] and r['partners'][0]['due'] == 4600, r['partners'][0])

print('\n=== 7) Pog\'onali komissiya ===')
r = c.post('/api/admin/partners/tiers', headers=ADM, json={'tier1_sales': 2, 'tier1_bonus': 5, 'tier2_sales': 3, 'tier2_bonus': 10}).get_json()
check("Pog'onalar saqlandi, joriy foiz 25%", r['ok'] and r['tiers']['tier1_sales'] == 2 and r['partners'][0]['percent_now'] == 25, r.get('tiers'))
r = c.post('/api/admin/partners/tiers', headers=ADM, json={'tier1_sales': 5, 'tier2_sales': 3})
check("2-pog'ona 1-dan kichik — 400", r.status_code == 400)
s4 = mk('Nodira', 81005)
CALLS.clear()
oid, d = buy(s4, ['history', 'biology', 'chemistry'], 'ALI20')
e = db('SELECT * FROM partner_earnings WHERE order_id = %s', (oid,), True)[0]
check("3-sotuv: 60 000 −10% = 54 000 × 25% = 13 500", e['percent'] == 25 and e['amount'] == 13500, dict(e))
check("Pog'ona oshgani haqida tabrik (endi 30%)", any('endi komissiyangiz <b>30%</b>' in t for t in sent_to(81001)), sent_to(81001))
check("Paket va chegirma bilan to'g'ri summa", d['order']['amount'] == 54000, d['order'])

print('\n=== 8) Tahrirlash, to\'xtatish, o\'chirish ===')
r = c.post(f"/api/admin/partners/{ali['id']}/update", headers=ADM, json={'commission': 15, 'discount': 0}).get_json()
check('Foizlar o\'zgardi (15% + 10% pog\'ona = 25%)', r['partners'][0]['commission'] == 15 and r['partners'][0]['discount'] == 0
      and r['partners'][0]['percent_now'] == 25, r['partners'][0])
s5 = mk('Olim', 81006)
q = c.post('/api/pay/quote', headers=s5['h'], json={'keys': ['history'], 'promo': 'ALI20'}).get_json()
check("Chegirmasiz kod: narx o'zgarmaydi, lekin kod qo'llanadi", q['ok'] and q['amount'] == 24000 and q['promo']['percent'] == 0, q)
CALLS.clear()
oid, d = buy(s5, ['history'], 'ALI20')
txt = [p['text'] for m, p in CALLS if m == 'sendMessage' and p.get('chat_id') == 81006]
check("Botdagi yo'riqnomada: Promo-kod ALI20 (foizsiz)", any('Promo-kod ALI20' in t and '−0%' not in t for t in txt), txt)
r = c.post(f"/api/admin/partners/{ali['id']}/toggle", headers=ADM).get_json()
check("To'xtatildi", r['partners'][0]['active'] is False)
s6 = mk('Kamola', 81007)
r = c.post('/api/pay/quote', headers=s6['h'], json={'keys': ['history'], 'promo': 'ALI20'})
check("To'xtatilgan kod ishlamaydi", r.status_code == 400 and r.get_json()['code'] == 'bad_promo')
r = c.post(f"/api/admin/partners/{ali['id']}/delete", headers=ADM)
check("Sotuvi bor hamkorni o'chirib bo'lmaydi", r.status_code == 409)
c.post(f"/api/admin/partners/{ali['id']}/toggle", headers=ADM)
r = c.post('/api/admin/partners', headers=ADM, json={'who': str(nop['id']), 'code': 'NOTG', 'commission': 30}).get_json()
check("Telegramsiz hamkor — ogohlantirish belgisi", any(x['code'] == 'NOTG' and not x['has_telegram'] for x in r['partners']))
r = c.post(f"/api/admin/partners/{nop['id']}/delete", headers=ADM).get_json()
check("Sotuvsiz hamkorni o'chirish mumkin", r['ok'] and all(x['code'] != 'NOTG' for x in r['partners']), r)

print('\n=== 9) Havola: t.me/bot?start=KOD ===')
HOOK = {'X-Telegram-Bot-Api-Secret-Token': A.WEBHOOK_SECRET}
UPD = [9000]


def start(tg, payload):
    CALLS.clear()
    UPD[0] += 1
    c.post('/telegram/webhook', headers=HOOK, json={'update_id': UPD[0], 'message': {
        'message_id': 1, 'text': f'/start {payload}', 'chat': {'id': tg, 'type': 'private'},
        'from': {'id': tg, 'first_name': 'X'}}})


c.post(f"/api/admin/partners/{ali['id']}/update", headers=ADM, json={'commission': 20, 'discount': 10})
start(81008, 'ali20')
check("Yangi odam: kod saqlandi xabari (−10%)", any('ALI20</b> promo-kodi saqlandi' in t and '−10%' in t for t in sent_to(81008)),
      sent_to(81008))
s8 = mk('Yangi', 81008)
shop = c.get('/api/pay/shop', headers=s8['h']).get_json()
check("Do'konda saqlangan kod avtomatik: ALI20 (−10%)", shop['saved_promo'] == {'code': 'ALI20', 'percent': 10}, shop.get('saved_promo'))
pr = c.get('/api/premium', headers=s8['h']).get_json()
check("Premium sahifasida ham", pr['saved_promo'] == {'code': 'ALI20', 'percent': 10}, pr.get('saved_promo'))
buy(s8, ['history'], 'ALI20')
check("Ishlatilgach — boshqa taklif qilinmaydi", c.get('/api/pay/shop', headers=s8['h']).get_json()['saved_promo'] is None)
start(81001, 'ALI20')
check("Hamkorning o'zi bossa — 'bu sizning kodingiz', saqlanmaydi",
      any('sizning hamkorlik kodingiz' in t for t in sent_to(81001))
      and not db('SELECT 1 FROM promo_referrals WHERE telegram_id = 81001', fetch=True), sent_to(81001))
start(81009, 'NOCODE')
check("Noma'lum so'z — oddiy salom, kod saqlanmaydi", sent_to(81009)
      and not db('SELECT 1 FROM promo_referrals WHERE telegram_id = 81009', fetch=True))
start(81010, 'kun')
check("/start kun o'zgarmadi", any('Kun savoli' in t for t in sent_to(81010)), sent_to(81010))

print('\n=== 10) Jami ===')
r = c.get('/api/admin/partners', headers=ADM).get_json()
t = r['totals']
e_sum = db('SELECT SUM(amount) AS s FROM partner_earnings', fetch=True)[0]['s']
check("Jami ishlangan = daromadlar yig'indisi", t['earned'] == e_sum and t['due'] == t['earned'] - t['paid'] and t['sales'] == 5, t)
check('Admin jurnalida yozuvlar', db("SELECT COUNT(*) AS n FROM admin_audit_log WHERE action LIKE 'partner_%%'", fetch=True)[0]['n'] >= 8)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
