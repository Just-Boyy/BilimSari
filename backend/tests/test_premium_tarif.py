# -*- coding: utf-8 -*-
"""Bilim Premium tariflari (1 oy / 3 oy / 1 yil): admin narx qo'yadi, sahifada tejash foizi, buyurtma botga
(to'lov oqimi o'zgarmagan), tasdiqlansa tarif muddaticha Premium. Bosh sahifada Premium kartasi."""
import json
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
import premium  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402
from games import clock  # noqa: E402

CALLS = []


def fake_tg(method, payload):
    CALLS.append((method, payload))
    return {'ok': True, 'result': {'message_id': len(CALLS)}}


tgbot.tg_api = fake_tg
A.tg_api = fake_tg
c = A.app.test_client()
fails = []
ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
DAY = 24 * 3600 * 1000


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


uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id) VALUES ('Tarif', TRUE, 'math', 9600001) RETURNING id",
         fetch=True)[0]['id']
H = {'Authorization': 'Bearer ' + create_token(uid)}

print('\n=== Narxlar ===')
r = c.post('/api/admin/pay/settings', headers=ADM, json={'card_number': '8600123412341234', 'card_holder': 'Ega'})
check('Karta kiritildi', r.status_code == 200, r.get_json())
d = c.get('/api/premium', headers=H).get_json()
check("Standart: faqat 1 oylik sotuvda (3 oy / 1 yil narxi qo'yilmagan)", [p['key'] for p in d['plans']] == ['premium'], d['plans'])
r = c.post('/api/admin/pay/settings', headers=ADM, json={'premium_price': 34900, 'premium_price_3': 89900, 'premium_price_12': 299000})
check('Admin 3 oy va 1 yil narxini qo\'ydi', r.status_code == 200 and r.get_json()['settings']['premium_price_12'] == 299000, r.get_json())
check("Noto'g'ri narx — 400", c.post('/api/admin/pay/settings', headers=ADM, json={'premium_price_3': 500}).status_code == 400)
d = c.get('/api/premium', headers=H).get_json()
plans = {p['key']: p for p in d['plans']}
check('Uch tarif', list(plans) == ['premium', 'premium3', 'premium12'], d['plans'])
check('3 oy: oyiga narx va tejash foizi', plans['premium3']['per_month'] == 30000 and plans['premium3']['saving'] == 14
      and plans['premium3']['months'] == 3, plans['premium3'])
check('1 yil: tejash foizi', plans['premium12']['saving'] == 29 and plans['premium12']['days'] == 365, plans['premium12'])
check("Shaxsiy dars oralig'i va a'zolar soni", d['personal_hours'] == 24 and d['members'] == 0, d)

print('\n=== Buyurtma (to\'lov oqimi o\'zgarmagan) ===')
check("Noto'g'ri tarif — 400", c.post('/api/premium/order', headers=H, json={'plan': 'premium99'}).status_code == 400)
CALLS.clear()
r = c.post('/api/premium/order', headers=H, json={'plan': 'premium12'})
o = r.get_json()
check('1 yillik buyurtma: narx va nom', r.status_code == 200 and o['order']['amount'] == 299000
      and o['order']['items'][0]['key'] == 'premium12', o)
text = ' '.join(p.get('text', '') for m, p in CALLS if m == 'sendMessage')
check("Botga karta yo'riqnomasi (1 yil nomi bilan)", 'Bilim Premium (1 yil)' in text and '8600' in text, text[:300])
conn = get_connection(); cur = conn.cursor()
reply = payments.attach_receipt(cur, conn, 9600001, 'file1', 'uniq1', 'photo')
oid = o['order']['id']
ok, msg = payments.decide(cur, conn, oid, True, 'Admin')
until = premium.until(cur, uid)
cur.close(); conn.close()
check('Tasdiqlandi — 365 kunlik Premium', ok and 364 * DAY < until - clock.now_ms() <= 365 * DAY, (ok, msg, until))
check("Hamkor yorlig'i", partners._items_label(json.dumps(['premium12'])) == 'Bilim Premium')
r = c.post('/api/premium/order', headers=H, json={'plan': 'premium3'})
check("Premium faol — yana olib bo'lmaydi (409)", r.status_code == 409 and r.get_json()['code'] == 'premium_active', r.get_json())

db('UPDATE users SET premium_until = NULL WHERE id = %s', (uid,))
c.post('/api/admin/pay/settings', headers=ADM, json={'premium_price_3': 0})
r = c.post('/api/premium/order', headers=H, json={'plan': 'premium3'})
check("Sotuvdan olingan tarif — 400 plan_off", r.status_code == 400 and r.get_json()['code'] == 'plan_off', r.get_json())
r = c.post('/api/premium/order', headers=H, json={})
check("Eski so'rov (tarifsiz) — 1 oylik", r.status_code == 200 and r.get_json()['order']['items'][0]['key'] == 'premium', r.get_json())
conn = get_connection(); cur = conn.cursor()
payments.attach_receipt(cur, conn, 9600001, 'file2', 'uniq2', 'photo')
payments.decide(cur, conn, r.get_json()['order']['id'], True, 'Admin')
until = premium.until(cur, uid)
cur.close(); conn.close()
check('1 oylik — 30 kun', 29 * DAY < until - clock.now_ms() <= 30 * DAY, until)

print('\n=== Sahifalar ===')
dash = open(os.path.join(BACKEND, 'dashboard.html'), encoding='utf-8').read()
check("Bosh sahifa: tezkor tugmalar o'rnida Premium kartasi", 'id="premiumKarta"' in dash and 'href="premium.html"' in dash
      and 'id="tezkor"' not in dash)
pr = open(os.path.join(BACKEND, 'premium.html'), encoding='utf-8').read()
check('Premium sahifasi: tariflar, sotib olish tugmasi, animatsiya', 'data-tarif' in pr and 'id="tolashTugma"' in pr
      and 'API.premiumBuyurtma(promo, tanlangan)' in pr and '@keyframes prTojKir' in pr)
i18n = open(os.path.join(BACKEND, 'js', 'i18n.js'), encoding='utf-8').read()
check('Ruscha tarjimalar', "'Muddatni tanlang': 'Выберите срок'" in i18n and "tejaysiz$/" in i18n)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
sys.exit(1 if fails else 0)
