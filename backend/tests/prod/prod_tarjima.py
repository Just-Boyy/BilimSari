# -*- coding: utf-8 -*-
"""Production: mavzular ruscha (X-Lang: ru) keladimi. python prod_tarjima.py math geometry ..."""
import os, re, sys
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-ec58b.up.railway.app'
CYR = re.compile('[А-Яа-яЁё]')
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:300]}'))
    if not cond:
        fails.append(name)


def get(path, tok, lang):
    r = requests.get(B + path, headers={'Authorization': 'Bearer ' + tok, 'X-Lang': lang}, timeout=60)
    return r.status_code, r.json()


at = requests.post(B + '/api/admin/login', json={'password': os.environ.get('ADMIN_PW', '')}, timeout=30).json().get('token')
d = requests.post(B + '/api/guest', headers=_prod.admin_headers(), json={'name': 'Tarjima Testchi'}, timeout=30).json()
tok, uid = d['token'], d['user']['id']
try:
    for fan in sys.argv[1:]:
        requests.post(B + f'/api/admin/users/{uid}/unlock', json={'subject_key': fan},
                      headers={'Authorization': 'Bearer ' + at}, timeout=30)
        s, d = get(f'/api/study/topics/{fan}', tok, 'ru')
        tops = d.get('topics') or []
        ru = sum(1 for t in tops if CYR.search(t.get('title') or ''))
        check(f'{fan}: ruscha sarlavhalar {ru}/{len(tops)}', s == 200 and tops and ru == len(tops), (s, str(d)[:200]))
        s, du = get(f'/api/study/topics/{fan}', tok, 'uz')
        uz = sum(1 for t in du.get('topics') or [] if not CYR.search(t.get('title') or ''))
        check(f"{fan}: o'zbekcha sarlavhalar {uz}/{len(tops)}", uz == len(tops))
        if tops:
            slug = tops[0]['slug']
            s, t = get(f"/api/study/topic/{fan}/{slug}?grade={tops[0].get('grade', 1)}", tok, 'ru')
            tp = t.get('topic') or t
            body = ' '.join(str(b.get('body') or b.get('items') or '') for b in tp.get('lesson') or [])
            qz = ' '.join(q.get('q', '') for q in tp.get('quiz') or [])
            check(f'{fan}/{slug}: dars va test ruscha', s == 200 and CYR.search(body) and CYR.search(qz), (s, str(t)[:300]))
finally:
    for old in [int(x) for x in os.environ.get('OLD_UIDS', '').split(',') if x]:
        requests.delete(B + f'/api/admin/users/{old}', headers={'Authorization': 'Bearer ' + at}, timeout=30)
    if at:
        s2 = requests.delete(B + f'/api/admin/users/{uid}', headers={'Authorization': 'Bearer ' + at}, timeout=30).status_code
        check("Sinov foydalanuvchi o'chirildi", s2 == 200, s2)
    else:
        print('  (admin parol yo\'q — sinov foydalanuvchi qoldi:', uid, ')')
print('FAIL:', len(fails))
