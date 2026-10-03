# -*- coding: utf-8 -*-
"""Production: Menyu (/api/menu), hamkor.html, kanal sozlamasi (o'zgartirilmaydi — faqat o'qiladi)."""
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
    r = requests.request(method, B + path, headers=h, timeout=60, **kw)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


s, d = call('POST', '/api/admin/login', json={'password': os.environ.get('ADMIN_PW', '')})
at = d.get('token')
check('Admin kirish', s == 200 and at, s)
s, d = call('GET', '/api/admin/system', at)
check('Tizim: channel_url maydoni bor', s == 200 and 'channel_url' in d, (s, list(d)))
print('     hozirgi kanal:', repr(d.get('channel_url')))
s, d = call('POST', '/api/admin/channel', at, json={'url': 'https://evil.com'})
check("Noto'g'ri kanal havolasi rad etiladi (400)", s == 400, (s, d))

s, d = call('POST', '/api/guest', _prod.admin_token(), json={'name': 'Menyu Sinov'})
tok, uid = d.get('token'), (d.get('user') or {}).get('id')
try:
    s, d = call('GET', '/api/menu', tok)
    check('/api/menu: oddiy o\'quvchi — partner=False', s == 200 and d['partner'] is False and 'channel_url' in d, (s, d))
    check('/api/menu himoyalangan', call('GET', '/api/menu')[0] == 401)
finally:
    if uid:
        check("Sinov o'quvchisi o'chirildi", call('DELETE', f'/api/admin/users/{uid}', at)[0] == 200)

r = requests.get(B + '/hamkor.html', timeout=30)
check('hamkor.html beriladi', r.status_code == 200 and 'Hamkorlik' in r.text, r.status_code)
ui = requests.get(B + '/js/ui.js', timeout=30).text
check("ui.js: Menyu va 'Biz haqimizda'", 'navMenyuTugma' in ui and 'Biz haqimizda' in ui and "matn: 'Profil' }," in ui)
check('sw.js', "bilimsari-v" in requests.get(B + '/sw.js', timeout=30).text)
check('i18n.js: Меню', "'Menyu': 'Меню'" in requests.get(B + '/js/i18n.js', timeout=30).text)
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
