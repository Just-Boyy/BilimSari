# -*- coding: utf-8 -*-
"""Jonli yangilanish: /api/site/live versiyalari har bir o'zgarishda yangilanadi (sahifa qayta yuklanmasdan
ko'rinishi uchun), bloklangan / tanaffusdagi o'quvchiga darhol 403/423 qaytaradi."""
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import admin_auth  # noqa: E402
import sayt  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402

tgbot.tg_api = lambda method, payload: {'ok': True, 'result': {'message_id': 1}}
A.tg_api = tgbot.tg_api
c = A.app.test_client()
fails = []
ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:500]}'))
    if not cond:
        fails.append(name)


def db(sql, params=(), fetch=False):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall() if fetch else None
    conn.commit(); cur.close(); conn.close()
    return rows


uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id) VALUES ('Jonli', TRUE, 'math', 9500001) "
         "RETURNING id", fetch=True)[0]['id']
H = {'Authorization': 'Bearer ' + create_token(uid)}


def live(h=None):
    sayt._cache['t'] = 0.0          # testda keshni kutmaymiz
    sayt._content['t'] = 0.0
    r = c.get('/api/site/live', headers=h or {})
    return r.status_code, r.get_json()


print('\n=== Versiyalar ===')
s, d = live()
check('Kirmagan sahifa uchun: site, control, content', s == 200 and set(d['v']) == {'site', 'control', 'content'}, d)
s, base = live(H)
check("Kirgan o'quvchi uchun: me ham", s == 200 and 'me' in base['v'], base)
s, d = live(H)
check("O'zgarish bo'lmasa — versiyalar bir xil", d['v'] == base['v'], (base, d))


def changed(after, before):
    return {k for k in before['v'] if after['v'].get(k) != before['v'][k]}


c.post('/api/admin/texts', headers=ADM, json={'orig': 'Kun savoli', 'uz': 'Bugungi savol'})
s, d = live(H)
check("Matn o'zgardi → site", changed(d, base) == {'site'}, changed(d, base))
base = d
c.post('/api/admin/design', headers=ADM, json={'colors': {'primary': '#7c3aed'}})
s, d = live(H)
check('Rang o\'zgardi → site', changed(d, base) == {'site'}, changed(d, base))
base = d
c.post('/api/admin/rules', headers=ADM, json={'values': {'daily.reward': 9}})
s, d = live(H)
check("Qoida o'zgardi → site (tushuntirish matnlari)", 'site' in changed(d, base), changed(d, base))
base = d
c.post('/api/admin/control/announcement', headers=ADM, json={'text': "Yangi e'lon", 'minutes': 60})
s, d = live(H)
check("E'lon → control", changed(d, base) == {'control'}, changed(d, base))
base = d
c.post('/api/admin/control/features', headers=ADM, json={'features': {'games': False}})
s, d = live(H)
check("Bo'lim o'chirildi → control", changed(d, base) == {'control'}, changed(d, base))
base = d

tid = db("SELECT id FROM topics WHERE subject_key = 'math' ORDER BY seq LIMIT 1", fetch=True)[0]['id']
t = c.get(f'/api/admin/topics/{tid}', headers=ADM).get_json()['topic']
body = {k: t[k] for k in ('title', 'summary', 'duration', 'lesson', 'quiz', 'homework')}
body['title'] = t['title'] + ' (yangi)'
c.put(f'/api/admin/topics/{tid}', headers=ADM, json=body)
s, d = live(H)
check('Mavzu tahrirlandi → content', changed(d, base) == {'content'}, changed(d, base))
base = d
c.post('/api/admin/subjects/math/admin-topics', headers=ADM, json={'title': 'Jonli mavzu', 'mode': 'manual'})
s, d = live(H)
check("Yangi mavzu → content", 'content' in changed(d, base), changed(d, base))
base = d

c.post(f'/api/admin/users/{uid}/bonus', headers=ADM, json={'amount': 25, 'notify': False})
s, d = live(H)
check('Bonus chaqmoq → me', changed(d, base) == {'me'}, changed(d, base))
base = d
c.post('/api/admin/premium/grant', headers=ADM, json={'who': str(uid), 'days': 30})
s, d = live(H)
check('Premium berildi → me', changed(d, base) == {'me'}, changed(d, base))
base = d
c.post(f'/api/admin/users/{uid}/unlock', headers=ADM, json={'subject_key': 'history'})
s, d = live(H)
check('Fan ochildi → me', changed(d, base) == {'me'}, changed(d, base))
base = d
other = db("INSERT INTO users (name, onboarded, chosen_subject_key) VALUES ('Boshqa', TRUE, 'math') RETURNING id", fetch=True)[0]['id']
db("INSERT INTO friend_requests (from_id, to_id, status, created_ms) VALUES (%s, %s, 'pending', 1)", (other, uid))
s, d = live(H)
check("Do'stlik so'rovi keldi → me", changed(d, base) == {'me'}, changed(d, base))
base = d
s2, d2 = live({'Authorization': 'Bearer ' + create_token(other)})
check("Boshqa o'quvchining me versiyasi alohida", d2['v']['me'] != base['v']['me'])

print("\n=== Tanaffus va blok darhol ===")
c.post('/api/admin/control/pause', headers=ADM, json={'targets': ['app'], 'minutes': 30})
s, d = live(H)
check("Ilova to'xtatildi → 423 (oyna darhol chiqadi)", s == 423 and d['code'] == 'maintenance', (s, d))
s, d = live()
check("Kirmagan sahifaga (kirish oynasi) 200", s == 200)
c.post('/api/admin/control/resume', headers=ADM, json={'targets': ['app']})
s, d = live(H)
check('Qayta yoqildi → 200', s == 200)
c.post(f'/api/admin/users/{uid}/ban', headers=ADM, json={'minutes': 60, 'reason': 'test', 'notify': False})
H = {'Authorization': 'Bearer ' + create_token(uid)}
s, d = live(H)
check('Bloklandi → 403', s == 403 and d['code'] == 'banned', (s, d))
c.post(f'/api/admin/users/{uid}/unban', headers=ADM, json={'notify': False})
check('Blokdan chiqarildi → 200', live(H)[0] == 200)

print('\n=== Sahifalar ===')
ui_js = open(os.path.join(BACKEND, 'js', 'ui.js'), encoding='utf-8').read()
i18n = open(os.path.join(BACKEND, 'js', 'i18n.js'), encoding='utf-8').read()
check("ui.js: jonli tekshiruvchi", "API.get('/api/site/live')" in ui_js and 'jonli: jonli' in ui_js and 'location.reload()' in ui_js)
check("i18n.js: matn aslidan qayta hisoblanadi (o'zgartirish olib tashlansa — asliga qaytadi)",
      'new WeakMap()' in i18n and 'saytYangila: saytYangila' in i18n)
for page in ('dashboard', 'subjects', 'topics', 'shop', 'dostlar', 'shaxsiy', 'premium', 'hamkor', 'leaderboard',
             'profile', 'settings', 'foydalanuvchi'):
    html = open(os.path.join(BACKEND, page + '.html'), encoding='utf-8').read()
    check(f'{page}.html jonli', 'UI.jonli(' in html)
adm = open(os.path.join(BACKEND, 'admin.html'), encoding='utf-8').read()
check('Admin panel ham jonli', 'JONLI_BOLIMLAR' in adm)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
sys.exit(1 if fails else 0)
