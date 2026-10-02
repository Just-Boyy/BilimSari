# -*- coding: utf-8 -*-
"""Production (PostgreSQL) smoke testi: 2 vaqtinchalik mehmon, to'liq o'yin, keyin tozalash."""
import os
import sys
import time

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


users = []
try:
    for n in ('Smoke Testchi A', 'Smoke Testchi B'):
        s, d = call('POST', '/api/guest', _prod.admin_token(), json={'name': n})
        check(f'Mehmon yaratildi: {n}', s in (200, 201) and d.get('token'), (s, d))
        users.append({'token': d['token'], 'id': d['user']['id']})
    ta, tb = users[0]['token'], users[1]['token']

    s, d = call('GET', '/api/games/catalog', ta)
    check('Katalog: 6 o\'yin', s == 200 and len(d.get('games', [])) == 6, (s, d))
    s, d = call('GET', '/api/games/topics?game=quiz_battle&subject=history', ta)
    check('Tarix mavzulari (Postgres)', s == 200 and len(d.get('topics', [])) == 40, (s, len(d.get('topics', []))))
    s, d = call('GET', '/api/games/lobby', ta)
    check('Lobby', s == 200 and 'online' in d, (s, d))

    s, d = call('POST', '/api/games/rooms', ta, json={'game': 'quiz_battle', 'subject': 'history', 'difficulty': 'oson', 'count': 5, 'max_players': 2, 'public': False})
    code = d.get('code')
    check('Room yaratildi', s == 200 and code, (s, d))
    s, d = call('POST', '/api/games/rooms/join', tb, json={'code': code})
    check('B qo\'shildi', s == 200, (s, d))
    call('POST', f'/api/games/rooms/{code}/ready', tb, json={'ready': True})
    s, d = call('POST', f'/api/games/rooms/{code}/start', ta)
    check('O\'yin boshlandi', s == 200 and d['state']['status'] == 'playing', (s, d))

    answered = set()
    t_end = time.time() + 150
    while time.time() < t_end:
        s, d = call('GET', f'/api/games/rooms/{code}', ta)
        st = d.get('state') or {}
        sess = st.get('session') or {}
        if st.get('status') == 'finished':
            break
        if sess.get('phase') == 'question' and sess['q_index'] not in answered:
            q = sess['q_index']
            check(f'{q + 1}-savol: javob yashirin', 'answer' not in sess['question'])
            call('POST', f'/api/games/rooms/{code}/answer', ta, json={'q': q, 'answer': 0})
            s2, d2 = call('POST', f'/api/games/rooms/{code}/answer', tb, json={'q': q, 'answer': 1})
            ph = ((d2.get('state') or {}).get('session') or {}).get('phase')
            check(f'{q + 1}-savol: ikkalasi javob berdi -> reveal', s2 == 200 and ph == 'reveal', (s2, ph))
            answered.add(q)
        call('GET', f'/api/games/rooms/{code}', tb)
        time.sleep(0.8)

    s, d = call('GET', f'/api/games/rooms/{code}', ta)
    res = ((d.get('state') or {}).get('session') or {}).get('results') or {}
    check('O\'yin tugadi, natijalar bor', d.get('state', {}).get('status') == 'finished' and len(res.get('rows', [])) == 2, d.get('state', {}).get('status'))
    me = res.get('me') or {}
    check('Natija: ball, aniqlik, o\'rganish xulosasi', 'accuracy' in me and res.get('learning', {}).get('summary'), me)

    s, d = call('GET', '/api/games/me', ta)
    check('Profil statistikasi: 1 o\'yin', s == 200 and d['stats']['games'] == 1, d)
    s, d = call('GET', '/api/games/leaderboard?period=day', ta)
    check('O\'yin reytingi ishlaydi', s == 200 and 'top' in d, d)
    s, d = call('GET', '/api/study/dashboard', ta)
    check('Dashboard (chaqmoq bilan) ishlaydi', s == 200 and 'chaqmoq' in d, (s, d.get('error')))
    s, d = call('GET', '/api/study/leaderboard', ta)
    check('Umumiy reyting ishlaydi', s == 200 and 'top' in d, (s, d.get('error')))

    call('POST', f'/api/games/rooms/{code}/leave', ta)
    call('POST', f'/api/games/rooms/{code}/leave', tb)

    s, d = call('POST', '/api/games/matchmaking', ta, json={'game': 'math_battle', 'subject': 'math'})
    check('Matchmaking: A qidiruvda', d.get('result') == 'searching', d)
    s, d = call('POST', '/api/games/matchmaking', tb, json={'game': 'math_battle', 'subject': 'math'})
    check('Matchmaking: B darhol topildi', d.get('result') == 'matched', d)
    mcode = d.get('code')
    s, d = call('GET', '/api/games/matchmaking', ta)
    check('Matchmaking: A ham o\'sha roomda', d.get('result') == 'matched' and d.get('code') == mcode, d)
    call('POST', f'/api/games/rooms/{mcode}/leave', ta)
    call('POST', f'/api/games/rooms/{mcode}/leave', tb)
finally:
    pw = os.environ.get('ADMIN_PW', '')
    if users and pw:
        s, d = call('POST', '/api/admin/login', json={'password': pw})
        at = d.get('token')
        for u in users:
            s2, d2 = call('DELETE', f"/api/admin/users/{u['id']}", at)
            check(f"Vaqtinchalik hisob o'chirildi (#{u['id']})", s2 == 200, (s2, d2))
        s, d = call('GET', '/api/games/leaderboard?period=day', users[0]['token'])
        check('O\'chirilgan hisob tokeni endi ishlamaydi', s == 401, s)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: ' + ', '.join(fails)))
sys.exit(1 if fails else 0)
