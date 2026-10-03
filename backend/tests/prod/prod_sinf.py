# -*- coding: utf-8 -*-
"""Production: sinf olib tashlangan — admin API, profil, o'yinlar reytingi, sahifalar."""
import os

import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-3ac9d.up.railway.app'
at = requests.post(B + '/api/admin/login', json={'password': os.environ['ADMIN_PW']}, timeout=30).json()['token']
H = {'Authorization': 'Bearer ' + at}
u = requests.get(B + '/api/admin/users', headers=H, timeout=30).json()
print("admin ro'yxat:", u['ok'], "| grade bor:", any('grade' in x for x in u['users']))
print("sinf yo'li:", requests.post(B + '/api/admin/users/1/grade', headers=H, json={'grade': 5}, timeout=30).status_code)
st = requests.get(B + '/api/admin/stats', headers=H, timeout=30).json()
print('statistika:', st['ok'], '| by_grade:', 'by_grade' in st)
t = requests.get(B + '/api/admin/subjects/math/topics', headers=H, timeout=30).json()['topics']
print('mavzular:', len(t), '| ketma-ket:', [x['seq'] for x in t] == list(range(1, len(t) + 1)))
csv = requests.get(B + '/api/admin/users/export.csv', headers=H, timeout=30).text.splitlines()[0]
print('CSV sarlavha:', csv)
g = requests.post(B + '/api/guest', headers=_prod.admin_headers(), json={'name': 'Sinf Sinov'}, timeout=30).json()
h = {'Authorization': 'Bearer ' + g['token']}
try:
    lb = requests.get(B + '/api/games/leaderboard?scope=grade', headers=h, timeout=30).json()
    print("o'yin reytingi scope=grade ->", lb['scope'], '| grade maydoni:', 'grade' in lb)
    pr = requests.get(B + f"/api/study/profile/{u['users'][0]['id']}", headers=h, timeout=30).json()
    print('profil ok:', pr['ok'], '| grade maydoni:', 'grade' in pr['profile'])
finally:
    print("sinov o'quvchisi o'chirildi:", requests.delete(B + f"/api/admin/users/{g['user']['id']}", headers=H, timeout=30).status_code)
for p in ('profile.html', 'foydalanuvchi.html', 'dostlar.html', 'admin.html', 'js/games/hub.js'):
    body = requests.get(B + '/' + p, timeout=30).text
    print(p, '| sinf qoldiqlari:', [w for w in ("-sinf'", 'Sinfim', 'sinfFiltr', 'sinfTanlov', 'Sinfdosh') if w in body])
s = requests.get(B + '/api/admin/system', headers=H, timeout=30).json()
print('xatolar:', s.get('error_counts'))
