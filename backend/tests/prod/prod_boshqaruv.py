# -*- coding: utf-8 -*-
"""Production: admin boshqaruvi — faqat o'qish va SINOV o'quvchisi ustidagi amallar.

Bot/ilovani to'xtatish, bo'limlarni o'chirish va e'lon bu yerda SINALMAYDI — ular barcha o'quvchilarga
darhol ta'sir qiladi (lokal tests/test_boshqaruv.py da to'liq tekshiriladi)."""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = _prod.B if hasattr(_prod, 'B') else 'https://backend-production-3ac9d.up.railway.app'
H = _prod.admin_headers()
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:400]}'))
    if not cond:
        fails.append(name)


r = requests.get(B + '/api/admin/control?bot=1', headers=H, timeout=60).json()
check('Boshqaruv holati', r.get('ok') and len(r['features']) == 9, r)
print('     tanaffus:', {k: bool(v and v.get('active')) for k, v in r['pause'].items()},
      "| o'chiq bo'limlar:", [f['key'] for f in r['features'] if not f['on']], "| e'lon:", bool(r.get('announcement')),
      '| bloklanganlar:', len(r['banned']))
b = r.get('bot') or {}
check('Bot holati (webhook ulangan)', b.get('url', '').endswith('/telegram/webhook'), b)
print('     navbatda:', b.get('pending'), '| oxirgi xato:', b.get('last_error') or "yo'q")

g = requests.post(B + '/api/guest', headers=H, json={'name': 'Boshqaruv Sinov'}, timeout=60).json()
uid, gh = g['user']['id'], {'Authorization': 'Bearer ' + g['token']}
try:
    d = requests.get(B + '/api/study/dashboard', headers=gh, timeout=60).json()
    check("Bosh sahifa: e'lon maydoni va bonus qismi", 'announcement' in d and 'bonus' in d.get('chaqmoq_parts', {}), d.keys())
    c = requests.get(B + f'/api/admin/users/{uid}/control', headers=H, timeout=60).json()
    check("O'quvchi boshqaruvi", c.get('ok') and c['chaqmoq'] == 0 and c['ban'] is None and c['chances']['left'] == 3, c)

    c = requests.post(B + f'/api/admin/users/{uid}/bonus', headers=H, json={'amount': 25, 'note': 'sinov', 'notify': False},
                      timeout=60).json()
    check('Bonus +25', c.get('ok') and c['parts']['bonus'] == 25 and c['chaqmoq'] == 25, c)
    c = requests.post(B + f'/api/admin/users/{uid}/rename', headers=H, json={'name': 'Boshqaruv Sinov 2'}, timeout=60).json()
    check('Ism', c.get('ok') and c['name'] == 'Boshqaruv Sinov 2', c)
    c = requests.post(B + f'/api/admin/users/{uid}/reset-chances', headers=H, timeout=60).json()
    check("O'yin imkoniyatlari", c.get('ok') and c['chances']['left'] == 3, c)

    c = requests.post(B + f'/api/admin/users/{uid}/ban', headers=H, json={'minutes': 60, 'reason': 'sinov', 'notify': False},
                      timeout=60).json()
    check('Bloklash (1 soat)', c.get('ok') and c['ban'] and c['ban']['reason'] == 'sinov' and c['sessions'] == 0, c)
    s = requests.get(B + '/api/study/dashboard', headers=gh, timeout=60).status_code
    check('Eski seans yopildi (401)', s == 401, s)
    ov = requests.get(B + '/api/admin/control', headers=H, timeout=60).json()
    check("Bloklanganlar ro'yxatida", any(x['id'] == uid for x in ov['banned']), ov['banned'])
    c = requests.post(B + f'/api/admin/users/{uid}/unban', headers=H, json={'notify': False}, timeout=60).json()
    check('Blokdan chiqarish', c.get('ok') and c['ban'] is None, c)

    ad = requests.get(B + '/admin.html', timeout=60).text
    check("admin.html: Boshqaruv bo'limi", 'id="bolim-boshqaruv"' in ad and 'data-bolim="boshqaruv"' in ad)
    audit = [i['action'] for i in requests.get(B + '/api/admin/audit?limit=50', headers=H, timeout=60).json()['items']]
    check('Audit jurnali', {'user_bonus', 'user_ban', 'user_unban', 'user_rename'} <= set(audit), audit[:10])
finally:
    print("sinov o'quvchisi o'chirildi:", requests.delete(B + f'/api/admin/users/{uid}', headers=H, timeout=60).status_code)
s = requests.get(B + '/api/admin/system', headers=H, timeout=60).json()
print('     xatolar:', s.get('error_counts'))
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
sys.exit(1 if fails else 0)
