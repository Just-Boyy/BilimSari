# -*- coding: utf-8 -*-
"""Production: Bilim Premium va shaxsiy darslar (haqiqiy Gemini bilan). Sinov o'quvchisi oxirida o'chiriladi."""
import os
import time

import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402

B = 'https://backend-production-ec58b.up.railway.app'
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:400]}'))
    if not cond:
        fails.append(name)


def call(method, path, tok=None, **kw):
    h = {'Authorization': 'Bearer ' + tok} if tok else {}
    r = requests.request(method, B + path, headers=h, timeout=90, **kw)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, r.text


for p in ('/premium.html', '/shaxsiy.html', '/assets/emoji/20-kubok.png'):
    s, _ = call('GET', p)
    check('Fayl: ' + p, s == 200, s)

s, d = call('POST', '/api/admin/login', json={'password': os.environ.get('ADMIN_PW', '')})
at = d.get('token')
check('Admin kirish', s == 200 and at, s)
s, d = call('GET', '/api/admin/premium', at)
# Narxni admin o'zgartiradi; Stars narxi 2026-09-29 dan beri yo'q
check("Admin: Premium bo'limi, narx so'mda", s == 200 and (d['settings'].get('premium_price') or 0) >= 1000
      and 'premium_stars' not in d['settings'], (s, d.get('settings')))
print('     premium narxi:', d['settings'].get('premium_price'))

s, d = call('POST', '/api/guest', _prod.admin_token(), json={'name': 'Premium Sinov'})
tok, uid = d.get('token'), (d.get('user') or {}).get('id')
try:
    check('Sinov o\'quvchisi', s == 201 and tok, (s, d))
    s, d = call('POST', '/api/study/subjects/math/choose', tok)
    check('Matematika tanlandi', s == 200, (s, d))
    s, d = call('GET', '/api/premium', tok)
    check('Premium: faol emas, 23 emoji', s == 200 and not d['premium']['active'] and len(d['emoji']) == 23, d)
    s, d = call('POST', '/api/ai/explain', tok, json={'subject_key': 'math', 'slug': 'x', 'grade': 7, 'mode': 'full'})
    check('Premiumsiz AI — 403', s == 403 and d.get('code') == 'premium_required', (s, d))
    s, d = call('POST', '/api/personal/suggest', tok, json={'subject_key': 'math', 'text': 'kasr'})
    check('Premiumsiz shaxsiy dars — 403', s == 403, (s, d))

    s, d = call('POST', '/api/admin/premium/grant', at, json={'who': str(uid), 'days': 1})
    check('Admin 1 kunga Premium berdi', s == 200 and d['ok'], (s, d))
    s, d = call('POST', '/api/personal/suggest', tok, json={'subject_key': 'math', 'text': 'futbol jamoalari'})
    check('Haqiqiy AI: fanga aloqasiz mavzu rad etildi', s == 400 and d.get('code') == 'off_topic', (s, d))
    s, d = call('POST', '/api/personal/suggest', tok, json={'subject_key': 'math', 'text': 'kasrlrni qushish'})
    check('Haqiqiy AI: 3 ta variant', s == 200 and len(d.get('options') or []) == 3, (s, d))
    print('     variantlar:', d.get('options'))
    title = (d.get('options') or ['Kasrlarni qo\'shish'])[0]
    t0 = time.time()
    s, d = call('POST', '/api/personal/generate', tok, json={'subject_key': 'math', 'title': title})
    check('Yaratish boshlandi', s == 200 and d['topic']['status'] == 'generating', (s, d))
    pid = d.get('topic', {}).get('id')
    status = 'generating'
    while status == 'generating' and time.time() - t0 < 240:
        time.sleep(6)
        s, d = call('GET', '/api/personal', tok)
        found = [t for g in d.get('groups', []) for t in g['topics'] if t['id'] == pid]
        status = found[0]['status'] if found else ('failed' if not d.get('generating') else 'generating')
    print(f'     holat: {status}, {int(time.time() - t0)} soniya')
    check('Haqiqiy AI: dars tayyor bo\'ldi', status == 'ready', status)
    if status == 'ready':
        s, p = call('GET', f'/api/personal/{pid}', tok)
        check('Dars: bloklar, 3 savol, 3 topshiriq', s == 200 and len(p['lesson']) >= 3 and len(p['quiz']) == 3
              and len(p['homework']['tasks']) == 3, (s, str(p)[:300]))
        print('     sarlavha:', p.get('title'), '| bloklar:', len(p.get('lesson', [])))
        s, d = call('POST', '/api/ai/explain', tok, json={'personal_id': pid, 'mode': 'examples'})
        check('Premium AI shaxsiy darsda ishlaydi', s == 200 and d.get('reply'), (s, str(d)[:200]))
        s, d = call('POST', '/api/personal/generate', tok, json={'subject_key': 'math', 'title': 'Boshqa'})
        check('24 soatda bitta — 429', s == 429, (s, d))
finally:
    if uid:
        s2, _ = call('DELETE', f'/api/admin/users/{uid}', at)
        check("Sinov o'quvchisi o'chirildi", s2 == 200, s2)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
