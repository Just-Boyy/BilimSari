# -*- coding: utf-8 -*-
"""Production: marafon — faqat qoralama (hech kimga e'lon yuborilmaydi), keyin o'chiriladi. Jurnal jadvali tekshiriladi."""
import base64
import json
import os
import time
from datetime import datetime, timedelta, timezone

import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-ec58b.up.railway.app'
at = requests.post(B + '/api/admin/login', json={'password': os.environ['ADMIN_PW']}, timeout=30).json()['token']
H = {'Authorization': 'Bearer ' + at}
d = requests.get(B + '/api/admin/marathon', headers=H, timeout=30).json()
print('admin marafon:', d['ok'], '| ochiq marafon:', d['marathon'], '| kanal:', d.get('channel'))
start = (datetime.now(timezone(timedelta(hours=5))) + timedelta(days=3)).strftime('%Y-%m-%dT%H:00')
body = {'title': 'Sinov qoralama', 'start': start, 'days': 7, 'top_n': 2, 'audience': 'all', 'contact': '@bilimsari_admin',
        'prizes': [{'place': 1, 'amount': 100000}, {'place': 2, 'amount': 50000, 'note': 'sinov'}]}
mid = None
g = requests.post(B + '/api/guest', headers=_prod.admin_headers(), json={'name': 'Marafon Sinov'}, timeout=30).json()
gh = {'Authorization': 'Bearer ' + g['token']}
try:
    r = requests.post(B + '/api/admin/marathon', headers=H, json=body, timeout=30).json()
    mid = r['marathon']['id']
    print('qoralama:', r['marathon']['status'], '| fond:', r['marathon']['prize_fund'])
    png = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uitest', 'sovrin.png'), 'rb').read()
    r = requests.post(B + f'/api/admin/marathon/{mid}/image', headers=H,
                      json={'place': 1, 'image': 'data:image/png;base64,' + base64.b64encode(png).decode()}, timeout=30).json()
    img = r.get('image_url')
    ri = requests.get(B + img, timeout=30)
    print('rasm:', ri.status_code, ri.headers.get('Content-Type'), '| kesh:', ri.headers.get('Cache-Control'))
    s = requests.get(B + '/api/marathon', headers=gh, timeout=30).json()
    print("o'quvchiga qoralama ko'rinmaydi:", s['marathon'] is None,
          '| banner:', requests.get(B + '/api/marathon/banner', headers=gh, timeout=30).json()['banner'])
finally:
    if mid:
        print("qoralama o'chirildi:", requests.post(B + f'/api/admin/marathon/{mid}/delete', headers=H, timeout=30).json()['ok'])
    print("sinov o'quvchisi o'chirildi:", requests.delete(B + f"/api/admin/users/{g['user']['id']}", headers=H, timeout=30).status_code)
lb = requests.get(B + '/leaderboard.html', timeout=30).text
ad = requests.get(B + '/admin.html', timeout=30).text
print('sahifalar:', 'reyting-tablar' in lb, 'bolim-marafon' in ad, '| sw v42:', 'bilimsari-v42' in requests.get(B + '/sw.js', timeout=30).text)
s = requests.get(B + '/api/admin/system', headers=H, timeout=30).json()
print('xatolar:', s.get('error_counts'))
