# -*- coding: utf-8 -*-
"""Boshqa o'quvchining ochiq profili: ma'lumotlar, maxfiylik, ro'yxatlarda user_id."""
import json
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


def mk(name, tg, username, photo=None):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, grade, telegram_id, username, photo_url) "
             "VALUES (%s, TRUE, 'math', 7, %s, %s, %s) RETURNING id", (name, tg, username, photo), True)[0]['id']
    return {'id': uid, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
ali = mk('Ali Valiyev', 93001, 'ali_secret', 'https://t.me/i/userpic/ali.jpg')
vali = mk('Vali', 93002, 'vali_x')
c.post('/api/admin/premium/grant', headers=ADM, json={'who': str(ali['id']), 'days': 30})
c.post('/api/premium/frame', headers=ali['h'], json={'frame': 'kok-chaqmoq'})
db("INSERT INTO user_achievements (user_id, key, unlocked_ms, seen_ms) VALUES (%s, 'mavzu_1', 1, 1)", (ali['id'],))

r = c.get(f"/api/study/profile/{ali['id']}", headers=vali['h'])
d = r.get_json()
p = d.get('profile') or {}
check('Profil ochiladi', r.status_code == 200 and d['ok'] and p['name'] == 'Ali Valiyev' and p['me'] is False, d)
check("Rasm va Premium ramka, sinf yo'q", p['photo_url'] and 'grade' not in p and p['premium'] == {'active': True, 'emoji': None, 'frame': 'kok-chaqmoq'}, p)
check('Statistika maydonlari', all(k in p for k in ('chaqmoq', 'rank', 'streak', 'topics', 'games', 'badges')), list(p))
check('Nishonlar: olingani darajasi bilan', p['badges']['unlocked'] >= 1
      and any(b['key'] == 'mavzu_1' and b['tier'] == 'bronza' for b in p['badges']['items']), p['badges'])
raw = json.dumps(d)
check("Shaxsiy ma'lumot chiqmaydi (telegram id, username, premium muddati)",
      '93001' not in raw and 'ali_secret' not in raw and 'until' not in raw and 'telegram' not in raw, raw[:300])
check("O'zini ko'rsa — me=True", c.get(f"/api/study/profile/{ali['id']}", headers=ali['h']).get_json()['profile']['me'] is True)
check("Yo'q o'quvchi — 404", c.get('/api/study/profile/999999', headers=vali['h']).status_code == 404)
check('Kirmagan — 401', c.get(f"/api/study/profile/{ali['id']}").status_code == 401)
n0 = db('SELECT COUNT(*) AS n FROM user_achievements WHERE user_id = %s', (vali['id'],), True)[0]['n']
c.get(f"/api/study/profile/{vali['id']}", headers=ali['h'])
n1 = db('SELECT COUNT(*) AS n FROM user_achievements WHERE user_id = %s', (vali['id'],), True)[0]['n']
check("Profilni ko'rish boshqaning nishonlarini o'zgartirmaydi", n0 == n1, (n0, n1))
check("Sahifa beriladi", c.get('/foydalanuvchi.html').status_code == 200)
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
