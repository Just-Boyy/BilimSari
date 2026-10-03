# -*- coding: utf-8 -*-
"""Production: admin panelning qoidalar, matnlar, dizayn, baza, xabarlar, ishlar, kun savoli bo'limlari.

Faqat o'qish va SINOV o'quvchisi ustida yozish. Qoidalar, matnlar, ranglar va kun savolini bu yerda
O'ZGARTIRMAYMIZ — ular barcha o'quvchilarga darhol ta'sir qiladi (lokal tests/test_admin_kuch.py da tekshiriladi)."""
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = _prod.B if hasattr(_prod, 'B') else 'https://backend-production-ec58b.up.railway.app'
H = _prod.admin_headers()
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:400]}'))
    if not cond:
        fails.append(name)


def get(path, auth=True):
    r = requests.get(B + path, headers=H if auth else {}, timeout=60)
    return r.status_code, (r.json() if 'json' in r.headers.get('Content-Type', '') else r.text)


s, d = get('/api/site/config', auth=False)
check("Ochiq sayt sozlamalari", s == 200 and d['ok'] and 'texts' in d and 'theme' in d and 'hide' in d, d)
print("     o'zgartirilgan matnlar:", len(d['texts']['uz']), '/', len(d['texts']['ru']), '| ranglar:', d['theme'], '| yashirin:', d['hide'])
s, d = get('/api/admin/rules')
check('Qoidalar', s == 200 and len(d['rules']) >= 20, d)
print("     standartdan farqli:", [(r['key'], r['value']) for r in d['rules'] if r['value'] != r['default']])
s, d = get('/api/admin/texts/search?q=Kun%20savoli')
check('Matnlar katalogi (qidiruv)', s == 200 and any(x['uz'] == 'Kun savoli' for x in d['items']), d)
s, d = get('/api/admin/texts')
check('Matnlar va bot matnlari', s == 200 and len(d['bot']) == 4 and all(b['default']['uz'] for b in d['bot']), d)
s, d = get('/api/admin/design')
check('Dizayn', s == 200 and len(d['colors']) >= 5 and len(d['blocks']) >= 10, d)
s, d = get('/api/admin/db/tables')
names = [t['name'] for t in d.get('tables', [])]
check("Baza: jadvallar (maxfiylarsiz)", s == 200 and 'users' in names and 'tokens' not in names and 'admin_settings' not in names, names)
s, d = get('/api/admin/db/rows?table=users&page=1')
check("Baza: o'quvchilar jadvali", s == 200 and d['total'] > 0 and all(c['name'] != 'password_hash' for c in d['columns']), str(d)[:300])
s, d = get('/api/admin/broadcasts')
check('Xabarlar: guruhlar va tarix', s == 200 and any(x['key'] == 'ru' for x in d['segments']), d)
print('     guruhlar:', {x['key']: x['count'] for x in d['segments']})
s, d = get('/api/admin/jobs')
check('Rejalashtirilgan ishlar', s == 200 and any(j['key'] == 'question' and j['last_ms'] for j in d['jobs']), d)
s, d = get('/api/admin/subjects/math/admin-topics')
check("Yangi mavzular ro'yxati (faqat o'qish)", s == 200 and isinstance(d.get('items'), list), d)
s, d = get('/api/admin/subjects/math/topics')
check("Fan mavzulari «siz qo'shgan» belgisi bilan", s == 200 and d['topics'] and all('admin' in t for t in d['topics']), str(d)[:300])
s, d = get('/api/admin/daily-plan')
check('Kun savoli rejasi (7 kun)', s == 200 and len(d['days']) == 7 and all(x.get('question') for x in d['days']), d)

r = requests.post(B + '/api/admin/handoff', json={'initData': 'soxta'}, timeout=60)
check("Brauzerga o'tish: soxta initData — 403", r.status_code == 403, r.text[:200])
r = requests.post(B + '/api/admin/handoff/redeem', json={'code': 'soxta'}, timeout=60)
check('Soxta kod — 403', r.status_code == 403, r.text[:200])

g = requests.post(B + '/api/guest', headers=H, json={'name': 'Baza Sinov'}, timeout=60).json()
uid = g['user']['id']
try:
    r = requests.post(B + '/api/admin/db/update', headers=H, timeout=60,
                      json={'table': 'users', 'key': {'id': uid}, 'changes': {'name': 'Baza Sinov 2'}}).json()
    check('Baza: sinov o\'quvchisi tahrirlandi', r.get('ok') and r['row']['name'] == 'Baza Sinov 2', r)
    s, d = get('/api/admin/db/row?table=users&key=' + json.dumps({'id': uid}))
    check('Baza: qator o\'qildi', s == 200 and d['row']['name'] == 'Baza Sinov 2', d)
finally:
    print("sinov o'quvchisi o'chirildi:", requests.delete(B + f'/api/admin/users/{uid}', headers=H, timeout=60).status_code)

ad = requests.get(B + '/admin.html', timeout=60).text
check("admin.html: yangi bo'limlar", all(f'id="bolim-{b}"' in ad for b in ('qoidalar', 'matnlar', 'dizayn', 'baza')))
ui = requests.get(B + '/js/ui.js', timeout=60).text
check("ui.js: admin panel tashqi brauzerda", 'tg.openLink(url' in ui)
s = requests.get(B + '/api/admin/system', headers=H, timeout=60).json()
print('     xatolar:', s.get('error_counts'))
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
sys.exit(1 if fails else 0)
