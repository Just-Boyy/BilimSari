# -*- coding: utf-8 -*-
"""Production: ramkalar — fayllar, katalog, tanlash (sinov o'quvchisiga 1 kunlik Premium, keyin o'chiriladi)."""
import os
import re

import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-3ac9d.up.railway.app'
at = requests.post(B + '/api/admin/login', json={'password': os.environ['ADMIN_PW']}, timeout=30).json()['token']
H = {'Authorization': 'Bearer ' + at}
KEYS = ('oltin-chaqmoq', 'kok-chaqmoq', 'yashil-chaqmoq', 'binafsha-chaqmoq', 'qizil-chaqmoq', 'oq-chaqmoq')
for k in KEYS:
    r = requests.get(f'{B}/assets/ramka/{k}.webp', timeout=30)
    print(f'{k}.webp:', r.status_code, r.headers.get('Content-Type'), round(len(r.content) / 1024), 'KB')
g = requests.post(B + '/api/guest', headers=_prod.admin_headers(), json={'name': 'Ramka Sinov'}, timeout=30).json()
tok, uid = g['token'], g['user']['id']
h = {'Authorization': 'Bearer ' + tok}
try:
    r = requests.post(B + '/api/premium/frame', headers=h, json={'frame': 'oltin-chaqmoq'}, timeout=30)
    print('Premiumsiz tanlash:', r.status_code)
    requests.post(B + '/api/admin/premium/grant', headers=H, json={'who': str(uid), 'days': 1}, timeout=30)
    p = requests.get(B + '/api/premium', headers=h, timeout=30).json()
    print('katalog:', [f['key'] for f in p['frames']], '| standart:', p['premium']['frame'])
    r = requests.post(B + '/api/premium/frame', headers=h, json={'frame': 'qizil-chaqmoq'}, timeout=30).json()
    me = requests.get(B + '/api/me', headers=h, timeout=30).json()['user']['premium']
    print('tanlandi:', r.get('ok'), '| /api/me:', me['frame'])
finally:
    print("sinov o'quvchisi o'chirildi:", requests.delete(B + f'/api/admin/users/{uid}', headers=H, timeout=30).status_code)
s = requests.get(B + '/api/admin/system', headers=H, timeout=30).json()
print('xatolar:', s.get('error_counts'))
css = requests.get(B + '/css/app.css', timeout=30).text
print('css ramkalar:', all('.ramka.r-%s {' % k in css for k in KEYS), '| sw:', re.search(r'bilimsari-v\d+', requests.get(B + '/sw.js', timeout=30).text).group(0))
ui = requests.get(B + '/js/ui.js', timeout=30).text
i18n = requests.get(B + '/js/i18n.js', timeout=30).text
print('ui.js kalitlar:', all("'%s': 1" % k in ui for k in KEYS), '| ruscha nomlar:', all(n in i18n for n in ('Фиолетовая молния', 'Красная молния', 'Белая молния')),
      '| sonli qoida:', 'xil ramkadan birini' in i18n)
