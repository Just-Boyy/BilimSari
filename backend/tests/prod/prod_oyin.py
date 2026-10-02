# -*- coding: utf-8 -*-
"""Production: chaqmoqli o'yinlar — imkoniyatlar, chiqib ketish, +30. Ikki sinov o'quvchisi, oxirida o'chiriladi."""
import os
import time

import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-ec58b.up.railway.app'
at = requests.post(B + '/api/admin/login', json={'password': os.environ['ADMIN_PW']}, timeout=30).json()['token']
H = {'Authorization': 'Bearer ' + at}


def guest(name):
    g = requests.post(B + '/api/guest', headers=_prod.admin_headers(), json={'name': name}, timeout=30).json()
    return g['user']['id'], {'Authorization': 'Bearer ' + g['token']}


ids = []
try:
    a, ha = guest('Oyin Sinov A'); ids.append(a)
    b, hb = guest('Oyin Sinov B'); ids.append(b)
    ch = requests.get(B + '/api/games/lobby', headers=ha, timeout=30).json()['chances']
    print('lobby imkoniyat:', ch['left'], '/', ch['max'], '| +', ch['win'], '/ +', ch['play'])
    code = requests.post(B + '/api/games/rooms', headers=ha, json={'game': 'quiz_battle', 'subject': 'math', 'count': 5,
                                                                   'max_players': 2}, timeout=30).json()['code']
    requests.post(B + '/api/games/rooms/join', headers=hb, json={'code': code}, timeout=30)
    requests.post(B + f'/api/games/rooms/{code}/ready', headers=hb, json={'ready': True}, timeout=30)
    st = requests.get(B + f'/api/games/rooms/{code}', headers=ha, timeout=30).json()['state']
    print('lobbida kind:', st['chaqmoq']['kind'])
    r = requests.post(B + f'/api/games/rooms/{code}/start', headers=ha, timeout=30).json()
    print('start:', r.get('ok'))
    st = requests.get(B + f'/api/games/rooms/{code}', headers=hb, timeout=30).json()['state']
    print("o'yinda kind:", st['chaqmoq']['kind'], '| qolgan:', st['chaqmoq']['left'])
    time.sleep(5)
    requests.post(B + f'/api/games/rooms/{code}/leave', headers=hb, timeout=30)
    st = requests.get(B + f'/api/games/rooms/{code}', headers=ha, timeout=30).json()['state']
    res = st['session']['results']
    print('holat:', st['status'], st['session']['end_reason'], '| chiqqanlar:', st['left_players'],
          '| natija:', [(x['name'], x['rank']) for x in res['rows']], '| chaqmoq:', res['me']['chaqmoq'])
    print('B imkoniyati:', requests.get(B + '/api/games/lobby', headers=hb, timeout=30).json()['chances']['left'],
          '| A dashboard chaqmoq:', requests.get(B + '/api/study/dashboard', headers=ha, timeout=30).json().get('chaqmoq'))
    s, e = requests.post(B + '/api/games/rooms/join', headers=hb, json={'code': code}, timeout=30), None
    print("tugagach qaytish:", s.status_code)
finally:
    for u in ids:
        print("sinov o'quvchisi o'chirildi:", u, requests.delete(B + f'/api/admin/users/{u}', headers=H, timeout=30).status_code)
lb = requests.get(B + '/api/study/leaderboard', headers=H, timeout=30)
print('umumiy reyting ishlaydi:', lb.status_code)
s = requests.get(B + '/api/admin/system', headers=H, timeout=30).json()
print('xatolar:', s.get('error_counts'))
print('sw v41:', 'bilimsari-v41' in requests.get(B + '/sw.js', timeout=30).text)
