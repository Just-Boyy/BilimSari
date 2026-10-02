# -*- coding: utf-8 -*-
"""Premium avatar ramkalari: katalog, standart, tanlash, himoya, reyting va o'yinlarda."""
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
import premium  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402

tgbot.tg_api = lambda m, p: {'ok': True, 'result': {'message_id': 1}}
c = A.app.test_client()
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:400]}'))
    if not cond:
        fails.append(name)


def db(sql, params=(), fetch=False):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall() if fetch else None
    conn.commit(); cur.close(); conn.close()
    return rows


def mk(name, tg):
    db('DELETE FROM users WHERE telegram_id = %s', (tg,))  # oldingi uzilgan ishga tushirishdan qolgan bo'lsa
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id, grade) VALUES (%s, TRUE, 'math', %s, 7) "
             "RETURNING id", (name, tg), True)[0]['id']
    return {'id': uid, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
p = mk('Premiumli', 91001)
o = mk('Oddiy', 91002)
c.post('/api/admin/premium/grant', headers=ADM, json={'who': str(p['id']), 'days': 30})

r = c.get('/api/premium', headers=p['h']).get_json()
KEYS = ['oltin-chaqmoq', 'kok-chaqmoq', 'yashil-chaqmoq', 'binafsha-chaqmoq', 'qizil-chaqmoq', 'oq-chaqmoq']
check('Katalog: 6 ta ramka', [f['key'] for f in r['frames']] == KEYS, r.get('frames'))
check('Fayllar bor', all(os.path.exists(os.path.join(BACKEND, 'assets', 'ramka', f['key'] + '.webp')) for f in r['frames']))
_css = open(os.path.join(BACKEND, 'css', 'app.css'), encoding='utf-8').read()
_ui = open(os.path.join(BACKEND, 'js', 'ui.js'), encoding='utf-8').read()
_i18n = open(os.path.join(BACKEND, 'js', 'i18n.js'), encoding='utf-8').read()
check('Har ramkaga CSS klassi', all('.ramka.r-%s {' % k in _css for k in KEYS), [k for k in KEYS if '.ramka.r-%s {' % k not in _css])
check("Har ramka ui.js RAMKALAR da", all("'%s': 1" % k in _ui for k in KEYS), [k for k in KEYS if "'%s': 1" % k not in _ui])
check('Har ramka nomining ruschasi bor', all(("'%s':" % f['name']) in _i18n or ('"%s":' % f['name']) in _i18n for f in r['frames']),
      [f['name'] for f in r['frames'] if ("'%s':" % f['name']) not in _i18n and ('"%s":' % f['name']) not in _i18n])
check('Standart ramka — oltin chaqmoq', r['premium']['frame'] == 'oltin-chaqmoq', r['premium'])
r = c.post('/api/premium/frame', headers=p['h'], json={'frame': 'qizil-chaqmoq'}).get_json()
check('Yangi ramka (qizil) tanlanadi', r['ok'] and r['frame'] == 'qizil-chaqmoq', r)
r = c.post('/api/premium/frame', headers=p['h'], json={'frame': 'yashil-chaqmoq'}).get_json()
check('Ramka tanlandi', r['ok'] and r['frame'] == 'yashil-chaqmoq', r)
st = c.get('/api/me', headers=p['h']).get_json()['user']['premium']
check('/api/me da tanlangan ramka', st['frame'] == 'yashil-chaqmoq' and st['frame_saved'] == 'yashil-chaqmoq', st)
r = c.post('/api/premium/frame', headers=p['h'], json={'frame': '../../etc'})
check("Noto'g'ri kalit — rad", r.status_code == 403 and 'yo\'q' in r.get_json()['error'], r.get_json())
r = c.post('/api/premium/frame', headers=o['h'], json={'frame': 'oltin-chaqmoq'})
check('Premiumsiz — 403', r.status_code == 403, r.get_json())
check("Premiumsizda ramka yo'q", c.get('/api/me', headers=o['h']).get_json()['user']['premium']['frame'] is None)

conn = get_connection(); cur = conn.cursor()
b = premium.badges(cur, [p['id'], o['id']])
cur.close(); conn.close()
check('badges: ramka faqat premiumlida', b.get(p['id'], {}).get('frame') == 'yashil-chaqmoq' and o['id'] not in b, b)
lb = c.get('/api/study/leaderboard', headers=o['h'])
if lb.status_code == 200:
    rows = lb.get_json().get('items') or lb.get_json().get('leaderboard') or lb.get_json().get('rows') or []
    me = [x for x in rows if x.get('user_id') == p['id'] or x.get('id') == p['id']]
    check('Reytingda ramka', not me or me[0].get('frame') == 'yashil-chaqmoq', me[:1])

c.post('/api/admin/premium/revoke', headers=ADM, json={'user_id': p['id']})
st = c.get('/api/me', headers=p['h']).get_json()['user']['premium']
check("Premium tugasa ramka yashirinadi, tanlov saqlanadi", st['frame'] is None and st['frame_saved'] == 'yashil-chaqmoq', st)
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
