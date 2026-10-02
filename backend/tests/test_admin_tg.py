# -*- coding: utf-8 -*-
"""Admin Telegram SSO lokal testi (Flask test client, soxta bot token, alohida SQLite)."""
import hashlib
import hmac
import json
import os
import sys
import time
from urllib.parse import urlencode

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

BOT_TOKEN = os.environ['BOT_TOKEN']
assert BOT_TOKEN.startswith('000000:'), 'faqat soxta token bilan ishga tushiring!'

from app import app  # noqa: E402
import admin_auth  # noqa: E402

c = app.test_client()
fails = 0


def check(name, cond, extra=''):
    global fails
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {extra}'))
    if not cond:
        fails += 1


def init_data(tg_id, age=0, first_name='Test'):
    fields = {
        'auth_date': str(int(time.time()) - age),
        'query_id': 'AAHtest',
        'user': json.dumps({'id': tg_id, 'first_name': first_name, 'username': f'u{tg_id}'},
                           separators=(',', ':')),
    }
    dcs = '\n'.join(f'{k}={v}' for k, v in sorted(fields.items()))
    secret = hmac.new(b'WebAppData', BOT_TOKEN.encode(), hashlib.sha256).digest()
    fields['hash'] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


ADMIN_ID = 5771496552
OTHER_ID = 111222333

print('\n=== is_admin_telegram ===')
check('int ID', admin_auth.is_admin_telegram(ADMIN_ID))
check('str ID', admin_auth.is_admin_telegram(str(ADMIN_ID)))
check('boshqa ID', not admin_auth.is_admin_telegram(OTHER_ID))
check('None', not admin_auth.is_admin_telegram(None))
check('matn', not admin_auth.is_admin_telegram('abc'))

print('\n=== /api/admin/telegram-login ===')
r = c.post('/api/admin/telegram-login', json={'initData': init_data(ADMIN_ID)})
d = r.get_json()
check('admin -> 200 + token', r.status_code == 200 and d.get('ok') and d.get('token'), (r.status_code, d))
admin_token = d.get('token')

r = c.get('/api/admin/stats', headers={'Authorization': f'Bearer {admin_token}'})
check('token bilan /stats ishlaydi', r.status_code == 200 and r.get_json().get('ok'), r.status_code)

r = c.get('/api/admin/audit', headers={'Authorization': f'Bearer {admin_token}'})
items = r.get_json().get('items', [])
check('audit: login_telegram yozildi',
      any(i['action'] == 'login_telegram' and str(ADMIN_ID) in (i.get('detail') or '') for i in items),
      items[:3])

r = c.post('/api/admin/telegram-login', json={'initData': init_data(OTHER_ID)})
d = r.get_json()
check('boshqa user -> 403 not_admin', r.status_code == 403 and d.get('code') == 'not_admin' and not d.get('token'),
      (r.status_code, d))

# Soxtalashtirish: boshqa user uchun imzolangan initData'da ID'ni admin ID'ga almashtiramiz
forged = init_data(OTHER_ID).replace(str(OTHER_ID), str(ADMIN_ID))
r = c.post('/api/admin/telegram-login', json={'initData': forged})
d = r.get_json()
check('soxta ID -> 403 bad_init_data', r.status_code == 403 and d.get('code') == 'bad_init_data', (r.status_code, d))

r = c.post('/api/admin/telegram-login', json={'initData': init_data(ADMIN_ID, age=2 * 3600)})
d = r.get_json()
check('2 soatlik eski initData -> 403', r.status_code == 403 and d.get('code') == 'bad_init_data', (r.status_code, d))

r = c.post('/api/admin/telegram-login', json={})
check('initData yo\'q -> 403', r.status_code == 403, r.status_code)

print('\n=== Parol bilan kirish hali ishlaydi va SSO xatolari uni bloklamaydi ===')
for _ in range(7):
    c.post('/api/admin/telegram-login', json={'initData': forged})
r = c.post('/api/admin/login', json={'password': os.environ['ADMIN_PASSWORD']})
check('parol login -> 200 (7 ta SSO xatosidan keyin ham)', r.status_code == 200 and r.get_json().get('token'),
      (r.status_code, r.get_json()))

print('\n=== /api/me is_admin ===')
r = c.post('/api/telegram/auth', json={'initData': init_data(ADMIN_ID, first_name='Admin')})
d = r.get_json()
check('admin talaba sifatida kiradi', r.status_code == 200 and d.get('token'), (r.status_code, d))
me = c.get('/api/me', headers={'Authorization': f"Bearer {d.get('token')}"}).get_json()
check('admin: is_admin = true', me.get('ok') and me['user'].get('is_admin') is True, me)

r = c.post('/api/telegram/auth', json={'initData': init_data(OTHER_ID, first_name='Oddiy')})
d = r.get_json()
me = c.get('/api/me', headers={'Authorization': f"Bearer {d.get('token')}"}).get_json()
check('oddiy user: is_admin = false', me.get('ok') and me['user'].get('is_admin') is False, me)

r = c.post('/api/guest', json={'name': 'Mehmon Bola'})
d = r.get_json() or {}
if d.get('token'):
    me = c.get('/api/me', headers={'Authorization': f"Bearer {d['token']}"}).get_json()
    check('mehmon: is_admin = false', me.get('ok') and me['user'].get('is_admin') is False, me)

print('\n=== Sahifalar ===')
html = c.get('/settings.html').get_data(as_text=True)
check('settings.html: adminQator bor, boshida yashirin, faqat adminga ochiladi',
      'id="adminQator"' in html and 'style="display:none"' in html and 'u.is_admin' in html)
html = c.get('/admin.html').get_data(as_text=True)
check('admin.html: telegram-web-app.js + telegramKirish',
      'telegram-web-app.js' in html and 'AdminAPI.telegramKirish' in html)
js = c.get('/js/admin.js').get_data(as_text=True)
check('admin.js: telegramKirish', 'telegramKirish' in js and '/api/admin/telegram-login' in js)

print('\n=== Mehmon hisobi (prod rejimi) ===')
import app as A  # noqa: E402
_asl = A.database_url
A.database_url = lambda: 'postgresql://prod-taqlidi'   # faqat /api/guest dagi tekshiruv uchun
try:
    r = c.post('/api/guest', json={'name': 'Begona Skript'})
    check("prod'da tokensiz mehmon — 403 telegram_required", r.status_code == 403
          and (r.get_json() or {}).get('code') == 'telegram_required', (r.status_code, r.get_json()))
    r = c.post('/api/guest', json={'name': 'Sinov Admin'},
               headers={'Authorization': 'Bearer ' + admin_auth.make_admin_token()})
    check("prod'da admin tokeni bilan — ochiladi (prod tekshiruvlari uchun)", r.status_code in (200, 201), r.status_code)
finally:
    A.database_url = _asl

print(f'\n{"HAMMASI OK" if not fails else f"{fails} ta XATO"}')
sys.exit(1 if fails else 0)
