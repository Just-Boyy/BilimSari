# -*- coding: utf-8 -*-
"""Production: do'stlar — qidiruv, so'rov, qabul, reyting, lenta, o'yinga chaqirish, shikoyat, admin.
Ikki sinov o'quvchisi yaratiladi va oxirida o'chiriladi."""
import os
import re

import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-ec58b.up.railway.app'
at = requests.post(B + '/api/admin/login', json={'password': os.environ['ADMIN_PW']}, timeout=30).json()['token']
H = {'Authorization': 'Bearer ' + at}


def guest(name):
    g = requests.post(B + '/api/guest', headers=_prod.admin_headers(), json={'name': name}, timeout=30).json()
    h = {'Authorization': 'Bearer ' + g['token']}
    requests.post(B + '/api/profile/onboarded', headers=h, timeout=30)
    return g['user']['id'], h


ids = []
try:
    a, ha = guest('Dostsinov Birinchi'); ids.append(a)
    b, hb = guest('Dostsinov Ikkinchi'); ids.append(b)
    r = requests.get(B + f'/api/friends/search?q={b}', headers=ha, timeout=30).json()
    print('ID qidiruv:', [x['name'] for x in r['results']])
    r = requests.get(B + '/api/friends/search?q=Dostsinov', headers=ha, timeout=30).json()
    print('ism qidiruv:', [x['name'] for x in r['results']])
    r = requests.post(B + '/api/friends/request', headers=ha, json={'user_id': b}, timeout=30).json()
    print("so'rov:", r.get('ok'), r.get('state'))
    ov = requests.get(B + '/api/friends', headers=hb, timeout=30).json()
    print('kelgan:', len(ov['incoming']))
    r = requests.post(B + '/api/friends/respond', headers=hb, json={'request_id': ov['incoming'][0]['request_id'], 'accept': True}, timeout=30).json()
    print('qabul:', r.get('ok'), r.get('state'), '| soni:', requests.get(B + '/api/friends', headers=ha, timeout=30).json()['count'])
    p = requests.get(B + f'/api/study/profile/{b}', headers=ha, timeout=30).json()['profile']
    print('profil:', p['friend'], p['friends_count'])
    print('reyting:', len(requests.get(B + '/api/friends/leaderboard', headers=ha, timeout=30).json()['rows']),
          '| lenta ok:', requests.get(B + '/api/friends/feed', headers=ha, timeout=30).json()['ok'])
    room = requests.post(B + '/api/games/rooms', headers=ha, json={'game': 'quiz_battle', 'subject': 'math', 'difficulty': 'orta',
                                                                  'count': 5, 'max_players': 2, 'public': False}, timeout=30).json()
    r = requests.post(B + '/api/friends/invite', headers=ha, json={'user_id': b, 'code': room['code']}, timeout=30).json()
    print('chaqiruv:', r.get('ok'), '| B da:', len(requests.get(B + '/api/friends/invites', headers=hb, timeout=30).json()['invites']))
    lob = requests.get(B + '/api/games/lobby', headers=hb, timeout=30).json()
    print("B lobbysida 'Sizni chaqirishdi':", [(i['from']['name'], i['game'], i['code'] == room['code']) for i in lob.get('invites') or []])
    requests.post(B + f"/api/games/rooms/{room['code']}/leave", headers=ha, timeout=30)
    r = requests.post(B + '/api/friends/report', headers=hb, json={'user_id': a, 'reason': 'boshqa', 'note': 'prod sinov'}, timeout=30).json()
    print('shikoyat:', r.get('ok'))
    ar = requests.get(B + '/api/admin/reports', headers=H, timeout=30).json()
    mine = [x for x in ar['reports'] if x['target_id'] == a]
    print('admin: ochiq', ar['open'], '| sinov shikoyati:', len(mine))
    if mine:
        print('dismiss:', requests.post(B + f"/api/admin/reports/{mine[0]['id']}/dismiss", headers=H, timeout=30).json().get('ok'))
    print('sahifa:', requests.get(B + '/dostlar.html', timeout=30).status_code,
          '| sw:', (re.search(r"bilimsari-v\d+", requests.get(B + '/sw.js', timeout=30).text) or [''])[0],
          '| chaqiruv oynasi (ui.js):', 'chaqiruvKuzat' in requests.get(B + '/js/ui.js', timeout=30).text)
finally:
    for u in ids:
        print("sinov o'quvchisi o'chirildi:", u, requests.delete(B + f'/api/admin/users/{u}', headers=H, timeout=30).status_code)
s = requests.get(B + '/api/admin/system', headers=H, timeout=30).json()
print('xatolar:', s.get('error_counts'))
