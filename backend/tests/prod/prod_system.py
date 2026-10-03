# -*- coding: utf-8 -*-
"""Production: Stars olib tashlangani, zaxira nusxa, xatolar jurnali (faqat o'qish)."""
import os
import time

import requests

B = 'https://backend-production-3ac9d.up.railway.app'
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:400]}'))
    if not cond:
        fails.append(name)


def call(method, path, tok=None, **kw):
    h = {'Authorization': 'Bearer ' + tok} if tok else {}
    r = requests.request(method, B + path, headers=h, timeout=60, **kw)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


s, d = call('POST', '/api/admin/login', json={'password': os.environ.get('ADMIN_PW', '')})
at = d.get('token')
check('Admin kirish', s == 200 and at, s)

s, d = call('GET', '/api/admin/pay/stars', at)
check("Stars to'lovi olib tashlangan (2026-09-29) — 404", s == 404, (s, d))

for _ in range(12):
    s, d = call('GET', '/api/admin/system', at)
    if d.get('backups'):
        break
    time.sleep(10)
check('Tizim endpoint', s == 200 and d.get('ok'), (s, d))
b = (d.get('backups') or [None])[0]
check("Bugungi avtomatik zaxira olindi va egaga yuborildi", b and b['origin'] == 'auto' and b['sent'] >= 1, d.get('backups'))
if b:
    print(f"     zaxira: {b['size']} bayt, {b['row_count']} qator, {b['table_count']} jadval, note={b['note']}")
print('     xatolar (24 soat):', d.get('error_counts'))
for e in (d.get('errors') or [])[:5]:
    print('     -', e['source'], '|', e['message'][:150].replace('\n', ' '))

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
