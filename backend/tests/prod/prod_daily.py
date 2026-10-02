# -*- coding: utf-8 -*-
"""Production smoke: kun savoli va yutuqlar (1 vaqtinchalik mehmon, keyin o'chiriladi)."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-ec58b.up.railway.app'
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
    check('Mehmon yaratildi', s == 200 and d.get('token'), (s, d))
    user = {'token': d['token'], 'id': d['user']['id']}
    t = user['token']

    s, d = call('GET', '/api/study/dashboard', t)
    check('Dashboard: daily holati va new_achievements', s == 200 and 'daily' in d and 'new_achievements' in d, (s, list(d)))
    s, d = call('GET', '/api/study/daily?peek=1', t)
    check('peek: hali ochilmagan, fan nomi bor', s == 200 and d.get('opened') is False and d.get('subject_name') and 'prompt' not in d, (s, d))
    print('     Bugungi fan:', d.get('subject_name'), '| keyingi savolgacha', d.get('next_in_s'), 's')
    s, d = call('GET', '/api/study/daily', t)
    check('Savol ochildi (javobsiz)', s == 200 and d.get('prompt') and len(d.get('options', [])) >= 2 and 'result' not in d, (s, d))
    s, d = call('POST', '/api/study/daily/answer', t, json={'answer': 0})
    check('Javob qabul qilindi, natija va reyting', s == 200 and 'correct' in d.get('result', {}) and 'ranking' in d, (s, d))
    check('"Kun savoli" nishoni', 'kun_1' in [a['key'] for a in d.get('new_achievements', [])], d.get('new_achievements'))
    s, d = call('POST', '/api/study/daily/answer', t, json={'answer': 0})
    check('Ikkinchi urinish -> 409', s == 409, (s, d))
    s, d = call('GET', '/api/study/achievements', t)
    check('Yutuqlar: 16 ta', s == 200 and d.get('total') == 16, (s, d.get('total')))
    r = requests.get(B + '/daily.html', timeout=30)
    check('daily.html sahifasi', r.status_code == 200 and 'Kun savoli' in r.text, r.status_code)
    r = requests.get(B + '/sw.js', timeout=30)
    check('Service worker v10', "bilimsari-v10" in r.text)
finally:
    pw = os.environ.get('ADMIN_PW', '')
    if user and pw:
        s, d = call('POST', '/api/admin/login', json={'password': pw})
        at = d.get('token')
        s2, d2 = call('DELETE', f"/api/admin/users/{user['id']}", at)
        check(f"Vaqtinchalik hisob o'chirildi (#{user['id']})", s2 == 200, (s2, d2))
    elif user:
        print('  (ADMIN_PW yo\'q — mehmon o\'chirilmadi)')

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: ' + ', '.join(fails)))
sys.exit(1 if fails else 0)
