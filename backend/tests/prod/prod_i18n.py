# -*- coding: utf-8 -*-
"""Production: ruscha interfeys (til saqlash) va mavzu tahrirlagichi (faqat o'qish)."""
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
        return r.status_code, r.text


s, js = call('GET', '/js/i18n.js')
check('js/i18n.js yuklanadi', s == 200 and 'window.I18N' in js and 'Настройки' in js, s)
s, html = call('GET', '/settings.html')
check("Sozlamalarda til tanlovi", s == 200 and 'js/i18n.js' in html and 'data-til="ru"' in html, s)
s, sw = call('GET', '/sw.js')
check('Service worker (i18n.js keshda)', 'bilimsari-v' in sw and '/js/i18n.js' in sw)

s, d = call('POST', '/api/admin/login', json={'password': os.environ.get('ADMIN_PW', '')})
at = d.get('token')
check('Admin kirish', s == 200 and at, s)

s, d = call('POST', '/api/guest', _prod.admin_token(), json={'name': 'Til Testchi'})
tok, uid = d.get('token'), (d.get('user') or {}).get('id')
try:
    check('Sinov foydalanuvchi', s == 201 and tok, (s, d))
    s, d = call('GET', '/api/me', tok)
    check("Standart til — uz", s == 200 and d['user']['lang'] == 'uz', d)
    s, d = call('POST', '/api/profile/lang', tok, json={'lang': 'ru'})
    check('Til saqlandi (ru)', s == 200 and d.get('lang') == 'ru', (s, d))
    s, d = call('GET', '/api/me', tok)
    check('/api/me — lang=ru', d['user']['lang'] == 'ru', d)
    s, d = call('POST', '/api/profile/lang', tok, json={'lang': 'en'})
    check("Noto'g'ri til — 400", s == 400, (s, d))
finally:
    if uid:
        s2, _ = call('DELETE', f'/api/admin/users/{uid}', at)
        check("Sinov foydalanuvchi o'chirildi", s2 == 200, s2)

s, d = call('GET', '/api/admin/subjects/math/topics', at)
check("Admin: mavzular ro'yxati (edited belgisi bilan)", s == 200 and d['topics'] and 'edited' in d['topics'][0], (s, str(d)[:200]))
if s == 200 and d['topics']:
    tid = d['topics'][0]['id']
    s, t = call('GET', f'/api/admin/topics/{tid}', at)
    check('Admin: mavzuni tahrirlash uchun ochish', s == 200 and t['topic']['lesson'] and t['topic']['quiz'], (s, str(t)[:200]))
    print('     tahrirlangan mavzular soni:', sum(1 for x in d['topics'] if x['edited']))

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
