# -*- coding: utf-8 -*-
"""O'yin xonasida o'yinchilarning profil rasmi keladi (rasmsizda — yo'q)."""
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
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


def mk(name, photo):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO users (name, onboarded, chosen_subject_key, grade, photo_url) VALUES (%s, TRUE, 'math', 7, %s) "
                "RETURNING id", (name, photo))
    uid = cur.fetchone()['id']
    conn.commit(); cur.close(); conn.close()
    return {'id': uid, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


ali = mk('Ali', 'https://t.me/i/userpic/320/ali.jpg')
vali = mk('Vali', None)
r = c.post('/api/games/rooms', headers=ali['h'], json={'game': 'quiz_battle', 'subject': 'math', 'difficulty': 'orta',
                                                       'count': 5, 'max_players': 4, 'public': True}).get_json()
print('create:', str(r)[:300]); code = r['code']
j = c.post('/api/games/rooms/join', headers=vali['h'], json={'code': code}); print('join:', j.status_code, str(j.get_json())[:300])
g = c.get(f'/api/games/rooms/{code}', headers=vali['h']); print('state:', g.status_code, str(g.get_json())[:200]); st = g.get_json()['state']
by = {p['name']: p for p in st['players']}
check('Rasmli o\'yinchi — photo_url keladi', by['Ali'].get('photo_url') == 'https://t.me/i/userpic/320/ali.jpg', by.get('Ali'))
check('Rasmsiz o\'yinchi — photo_url yo\'q', by['Vali'].get('photo_url') is None, by.get('Vali'))
r = c.post(f'/api/games/rooms/{code}/bot', headers=ali['h'], json={'level': 3})
st = c.get(f'/api/games/rooms/{code}', headers=ali['h']).get_json()['state']
bots = [p for p in st['players'] if p['bot']]
check('Kompyuter raqibda rasm yo\'q', not bots or bots[0].get('photo_url') is None, bots)
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
