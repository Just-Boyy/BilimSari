# -*- coding: utf-8 -*-
"""Production smoke: to'lov tizimi (o'qish so'rovlari; karta/narxlarni o'zgartirmaydi)."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-3ac9d.up.railway.app'
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:300]}'))
    if not cond:
        fails.append(name)


def call(method, path, tok=None, **kw):
    h = {'Authorization': 'Bearer ' + tok} if tok else {}
    r = requests.request(method, B + path, headers=h, timeout=30, **kw)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


user = None
at = None
try:
    pw = os.environ.get('ADMIN_PW', '')
    s, d = call('POST', '/api/admin/login', json={'password': pw})
    at = d.get('token')
    check('Admin kirish', s == 200 and at, s)
    s, d = call('GET', '/api/admin/pay/overview', at)
    check('Admin: to\'lov umumiy (Postgres jadvallari)', s == 200 and 'pending' in d.get('stats', {}), (s, d))
    print('     Karta kiritilganmi:', bool(d.get('settings', {}).get('card_number')), '| narxlar:',
          {k: d['settings'][k] for k in ('price_single', 'price_three', 'price_all')})
    s, d = call('GET', '/api/admin/pay/orders?status=pending', at)
    check('Admin: cheklar ro\'yxati', s == 200 and 'orders' in d, (s, d))

    s, d = call('POST', '/api/guest', _prod.admin_token(), json={'name': 'Smoke Testchi'})
    user = {'token': d['token'], 'id': d['user']['id']}
    t = user['token']
    s, d = call('GET', '/api/pay/shop', t)
    check('Do\'kon', s == 200 and len(d['subjects']) >= 11 and d['telegram'] is False, (s, d))
    s, d = call('POST', '/api/pay/quote', t, json={'keys': ['english', 'history', 'biology']})
    check('Narx: 3 ta fan paketi', s == 200 and d.get('bundle') == '3 ta fan paketi', (s, d))
    s, d = call('POST', '/api/pay/orders', t, json={'keys': ['english']})
    check('Telegram\'siz buyurtma -> no_telegram', s == 400 and d.get('code') in ('no_telegram', 'not_configured'), (s, d))
    s, d = call('POST', '/api/study/subjects/english/unlock', t)
    check('Eski pulsiz ochish yopilgan', s == 402, (s, d))
    for page in ('shop.html', 'settings.html', 'admin.html'):
        r = requests.get(f'{B}/{page}', timeout=30)
        check(f'{page} ochiladi', r.status_code == 200, r.status_code)
    r = requests.get(B + '/sw.js', timeout=30)
    check('Service worker', r.status_code == 200 and 'bilimsari-v' in r.text)
finally:
    if user and at:
        s2, d2 = call('DELETE', f"/api/admin/users/{user['id']}", at)
        check(f"Vaqtinchalik hisob o'chirildi (#{user['id']})", s2 == 200, (s2, d2))

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: ' + ', '.join(fails)))
sys.exit(1 if fails else 0)
