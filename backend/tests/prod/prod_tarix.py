# -*- coding: utf-8 -*-
"""Production: tugagan marafon tepada yo'q, tarixda bor (sinov o'quvchisi bilan, oxirida o'chiriladi)."""
import os
import re

import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-3ac9d.up.railway.app'
at = requests.post(B + '/api/admin/login', json={'password': os.environ['ADMIN_PW']}, timeout=30).json()['token']
H = {'Authorization': 'Bearer ' + at}
g = requests.post(B + '/api/guest', headers=_prod.admin_headers(), json={'name': 'Tarix Sinov'}, timeout=30).json()
gh = {'Authorization': 'Bearer ' + g['token']}
try:
    d = requests.get(B + '/api/marathon', headers=gh, timeout=30).json()
    print('tepada marafon:', d['marathon'] and d['marathon']['title'], '| tarix:', [(x['title'], x['prize_fund']) for x in d['history']])
    if d['history']:
        h = requests.get(B + f"/api/marathon/history/{d['history'][0]['id']}", headers=gh, timeout=30).json()
        print('tarix ichi:', h['ok'], h['marathon']['title'], '| g\'oliblar:', len(h['winners']))
finally:
    print("sinov o'quvchisi o'chirildi:", requests.delete(B + f"/api/admin/users/{g['user']['id']}", headers=H, timeout=30).status_code)
print('sw:', re.search(r'bilimsari-v\d+', requests.get(B + '/sw.js', timeout=30).text).group(0),
      '| sahifa:', 'tarixJoy' in requests.get(B + '/leaderboard.html', timeout=30).text)
print('xatolar:', requests.get(B + '/api/admin/system', headers=H, timeout=30).json().get('error_counts'))
