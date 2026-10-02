# -*- coding: utf-8 -*-
"""Production: Stars olib tashlangan, hamkorlik dasturi ishlaydi (sinov hamkori yaratilib, o'chiriladi)."""
import os

import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-ec58b.up.railway.app'
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:400]}'))
    if not cond:
        fails.append(name)


def call(method, path, tok=None, **kw):
    h = {'Authorization': 'Bearer ' + tok} if tok else {}
    r = requests.request(method, B + path, headers=h, timeout=60, **kw)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


s, d = call('POST', '/api/admin/login', json={'password': os.environ.get('ADMIN_PW', '')})
at = d.get('token')
check('Admin kirish', s == 200 and at, s)

print('=== Stars olib tashlandi ===')
s, _ = call('GET', '/api/admin/pay/stars', at)
check('/api/admin/pay/stars — 404', s == 404, s)
s, d = call('GET', '/api/admin/pay/overview', at)
check("Statistikada va sozlamalarda Stars yo'q", s == 200 and 'stars_all' not in d['stats']
      and not any('stars' in k for k in d['settings']), d.get('settings'))
print("     tushum (jami):", d['stats']['all'], '| premium narxi:', d['settings']['premium_price'])
s, d = call('GET', '/api/admin/premium', at)
check("Premium bo'limi: narx 34 900, oylik sotuv", s == 200 and d['settings'] == {'premium_price': 34900}
      and 'count' in d['month'], (s, d.get('settings'), d.get('month')))
tok_bot = os.environ.get('BOT_TOKEN', '')
if tok_bot:
    info = requests.get(f'https://api.telegram.org/bot{tok_bot}/getWebhookInfo', timeout=20).json().get('result', {})
    check("Webhook: pre_checkout_query yo'q", 'pre_checkout_query' not in (info.get('allowed_updates') or []),
          info.get('allowed_updates'))
    check('Webhook xatosiz', not info.get('last_error_message'), info.get('last_error_message'))

print('\n=== Hamkorlik ===')
s, d = call('GET', '/api/admin/partners', at)
check("Hamkorlar bo'limi, pog'onalar 10:+5 / 50:+10", s == 200 and d['tiers'] == {
    'tier1_sales': 10, 'tier1_bonus': 5, 'tier2_sales': 50, 'tier2_bonus': 10}, (s, d))
s, d = call('POST', '/api/guest', _prod.admin_token(), json={'name': 'Hamkor Sinov'})
tok, uid = d.get('token'), (d.get('user') or {}).get('id')
try:
    check("Sinov o'quvchisi", s == 201 and tok, (s, d))
    s, d = call('POST', '/api/admin/partners', at, json={'who': str(uid), 'code': 'SINOVHK7', 'commission': 20, 'discount': 10})
    check('Sinov hamkori yaratildi', s == 200 and d.get('code') == 'SINOVHK7', (s, d))
    s, d = call('GET', '/api/partner', tok)
    p = d.get('partner') or {}
    check("Profilda: kod, 20%, ulashish havolasi", s == 200 and p.get('code') == 'SINOVHK7' and p['percent_now'] == 20
          and p['link'] == 'https://t.me/bilimsaribot?start=SINOVHK7' and 'SINOVHK7' in p['share']['uz'], p)
    s, d = call('POST', '/api/pay/quote', tok, json={'keys': ['history'], 'promo': 'SINOVHK7'})
    check("O'z kodini ishlata olmaydi", s == 400 and d.get('code') == 'bad_promo', (s, d))
    s, d = call('GET', '/api/admin/pay/overview', at)
    check("Oddiy promo-kodlar ro'yxatida chiqmaydi", all(x['code'] != 'SINOVHK7' for x in d['promos']))
finally:
    if uid:
        s, d = call('POST', f'/api/admin/partners/{uid}/delete', at)
        check("Sinov hamkori o'chirildi", s == 200 and all(x['code'] != 'SINOVHK7' for x in d['partners']), (s, d))
        s, _ = call('DELETE', f'/api/admin/users/{uid}', at)
        check("Sinov o'quvchisi o'chirildi", s == 200, s)

for page in ('shop.html', 'premium.html', 'profile.html', 'admin.html'):
    r = requests.get(f'{B}/{page}', timeout=30)
    check(f"{page} — Stars yo'q", r.status_code == 200 and 'Stars' not in r.text, r.status_code)
r = requests.get(f'{B}/sw.js', timeout=30)
check('Service worker keshi yangilandi (v22)', "bilimsari-v22" in r.text)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
