# -*- coding: utf-8 -*-
"""Production smoke: sozlamalar (ism, rasm, avatar nishonlari). Vaqtinchalik mehmon keyin o'chiriladi."""
import base64
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
try:
    s, d = call('POST', '/api/guest', _prod.admin_token(), json={'name': 'Smoke Testchi'})
    check('Mehmon yaratildi', s in (200, 201) and d.get('token'), (s, d))
    user = {'token': d['token'], 'id': d['user']['id']}
    t = user['token']

    r = requests.get(B + '/settings.html', timeout=30)
    check('settings.html sahifasi', r.status_code == 200 and 'Sozlamalar' in r.text, r.status_code)
    r = requests.get(B + '/profile.html', timeout=30)
    check('Profilda sozlama tugmasi', 'sozlama-tugma' in r.text and 'settings.html' in r.text)

    s, d = call('POST', '/api/profile/name', t, json={'name': '  Smoke   Yangi  '})
    check('Ism o\'zgardi', s == 200 and d['user']['name'] == 'Smoke Yangi', (s, d))
    s, d = call('GET', '/api/me', t)
    check('/api/me: yangi ism, bot, custom_photo', d['user']['name'] == 'Smoke Yangi' and d.get('bot') and d['user']['custom_photo'] is False, d)

    png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 64
    s, d = call('POST', '/api/profile/photo', t, json={'image': 'data:image/png;base64,' + base64.b64encode(png).decode()})
    url = d.get('photo_url') or ''
    check('Rasm yuklandi (Postgres)', s == 200 and url.startswith(f"/api/photo/{user['id']}?v="), (s, d))
    r = requests.get(B + url, timeout=30)
    check('Rasm beriladi', r.status_code == 200 and r.content == png and r.headers.get('Content-Type') == 'image/png', (r.status_code, r.headers.get('Content-Type')))
    s, d = call('POST', '/api/profile/photo', t, json={'image': 'data:image/gif;base64,R0lGODlh'})
    check('Noto\'g\'ri format rad etiladi', s == 400, (s, d))

    s, d = call('GET', '/api/study/achievements', t)
    check('Yutuqlar: pinned va max_pinned', s == 200 and d.get('pinned') == [] and d.get('max_pinned') == 6, d.get('pinned'))
    s, d = call('POST', '/api/study/achievements/pin', t, json={'keys': ['kun_1']})
    check('Olinmagan nishonni tanlab bo\'lmaydi', s == 400 and d.get('code') == 'not_unlocked', (s, d))

    s, d = call('POST', '/api/profile/photo/remove', t, json={})
    check('Rasm o\'chirildi', s == 200 and d.get('photo_url') is None, (s, d))
    check('Eski rasm manzili 404', requests.get(B + url, timeout=30).status_code == 404)
finally:
    pw = os.environ.get('ADMIN_PW', '')
    if user and pw:
        s, d = call('POST', '/api/admin/login', json={'password': pw})
        s2, d2 = call('DELETE', f"/api/admin/users/{user['id']}", d.get('token'))
        check(f"Vaqtinchalik hisob o'chirildi (#{user['id']})", s2 == 200, (s2, d2))
    elif user:
        print("  (ADMIN_PW yo'q — mehmon o'chirilmadi)")

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: ' + ', '.join(fails)))
sys.exit(1 if fails else 0)
