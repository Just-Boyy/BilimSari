# -*- coding: utf-8 -*-
"""Chaqmoqli o'yinlar: 3 ta imkoniyat, 24 soat taymer, +30/+20, kompyuter, chiqib ketish, uzilish, teng ball."""
import os
import sys
import time

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402
from games import chances, clock, engine, rooms  # noqa: E402

c = A.app.test_client()
fails = []
T = [int(time.time() * 1000)]
clock.now_ms = lambda: T[0]
H24 = 24 * 3600 * 1000


def adv(ms):
    T[0] += ms


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


def mk(name):
    uid = db('INSERT INTO users (name, onboarded) VALUES (%s, TRUE) RETURNING id', (name,), True)[0]['id']
    return {'id': uid, 'h': {'Authorization': 'Bearer ' + create_token(uid)}, 'name': name}


def req(method, path, u, **kw):
    r = getattr(c, method)(path, headers=u['h'], **kw)
    return r.status_code, (r.get_json() or {})


def st(u, code):
    s, d = req('get', f'/api/games/rooms/{code}', u)
    return d.get('state') or d


def q_of(code, i):
    conn = get_connection(); cur = conn.cursor()
    room = rooms.load_room(cur, code)
    q = engine.questions_for(cur, room['session_id'])[i]
    cur.close(); conn.close()
    return q


def wrong(q):
    return (q['answer'] + 1) % len(q['options'])


def room_with(host, *others, count=5):
    s, d = req('post', '/api/games/rooms', host, json={'game': 'quiz_battle', 'subject': 'math', 'count': count, 'max_players': 4})
    code = d['code']
    for u in others:
        req('post', '/api/games/rooms/join', u, json={'code': code})
        req('post', f'/api/games/rooms/{code}/ready', u, json={'ready': True})
    return code


def start(host, code):
    s, d = req('post', f'/api/games/rooms/{code}/start', host)
    assert s == 200, d
    adv(4500)                                   # countdown


def play_all(code, plan, count=5):
    """plan: {user: 'right'|'wrong'|None} har savolga. Hamma javob bersa — darhol reveal."""
    users = [u for u, _ in plan]
    for i in range(count):
        for u in users:
            st(u, code)
        q = q_of(code, i)
        adv(300)
        for u, how in plan:
            if how:
                req('post', f'/api/games/rooms/{code}/answer', u, json={'q': i, 'answer': q['answer'] if how == 'right' else wrong(q)})
            adv(100)
        adv(4200)
    for u in users:
        st(u, code)


def my_result(u, code):
    return st(u, code)['session']['results']


def chance(u):
    return req('get', '/api/games/lobby', u)[1]['chances']


ali, bek, sam, dil = mk('Ali'), mk('Bek'), mk('Sam'), mk('Dil')

print('— Boshlang\'ich holat')
ch = chance(ali)
check('Lobby: 3 / 3 imkoniyat, +30 / +20', ch['left'] == 3 and ch['max'] == 3 and ch['win'] == 30 and ch['play'] == 20 and ch['reset_at_ms'] is None, ch)
code = room_with(ali, bek)
info = st(ali, code)['chaqmoq']
check("Lobbida: 2 odam — o'yin chaqmoq beradi", info['kind'] == 'yes' and info['left'] == 3, info)

print("— 1-o'yin: Ali g'olib (+30), Bek +20")
start(ali, code)
info = st(bek, code)['chaqmoq']
check("O'yin boshlandi: imkoniyat ishlatildi (2 qoldi)", info['kind'] == 'yes' and info['left'] == 2, info)
play_all(code, [(ali, 'right'), (bek, 'wrong')])
r = my_result(ali, code)
check('Ali 1-o\'rin +30', r['me']['rank'] == 1 and r['me']['chaqmoq'] == 30, r['me'])
rb = my_result(bek, code)['me']
check('Bek 2-o\'rin +20 (0 to\'g\'ri bo\'lsa ham)', rb['rank'] == 2 and rb['chaqmoq'] == 20 and rb['correct'] == 0, rb)
d = req('get', '/api/study/dashboard', ali)[1]
check('Dashboard: Ali 30 chaqmoq', d['chaqmoq'] == 30, d['chaqmoq'])

print('— Teng ball: tezroq javob bergan 1-o\'rin')
req('post', f'/api/games/rooms/{code}/rematch', ali)
req('post', f'/api/games/rooms/{code}/ready', bek, json={'ready': True})
start(ali, code)
for i in range(5):
    st(ali, code); st(bek, code)
    q = q_of(code, i)
    adv(2000)
    req('post', f'/api/games/rooms/{code}/answer', bek, json={'q': i, 'answer': q['answer']})   # Bek tezroq
    adv(1500)
    req('post', f'/api/games/rooms/{code}/answer', ali, json={'q': i, 'answer': q['answer']})
    adv(4200)
st(ali, code)
rows = my_result(ali, code)['rows']
check("Teng ball — ranklar noyob, Bek (tez) 1-o'rin", [x['name'] for x in rows] == ['Bek', 'Ali']
      and rows[0]['score'] == rows[1]['score'] and [x['rank'] for x in rows] == [1, 2], rows)
check('Bek +30, Ali +20', my_result(bek, code)['me']['chaqmoq'] == 30 and my_result(ali, code)['me']['chaqmoq'] == 20)

print("— 3-o'yin va limit: 4-o'yin chaqmoq bermaydi")
req('post', f'/api/games/rooms/{code}/rematch', ali)
req('post', f'/api/games/rooms/{code}/ready', bek, json={'ready': True})
start(ali, code)
ch = st(ali, code)['chaqmoq']
check("3-imkoniyat ishlatildi, 3-o'yin davom etyapti (taymer hali yo'q)", ch['left'] == 0 and ch['pending'] and ch['reset_at_ms'] is None, ch)
play_all(code, [(ali, 'right'), (bek, 'wrong')])
end3 = T[0]
ch = chance(ali)
check("3-o'yin tugadi: taymer 24 soat", ch['left'] == 0 and not ch['pending'] and abs(ch['reset_at_ms'] - (end3 + H24)) < 10000, (ch, end3 + H24))
req('post', f'/api/games/rooms/{code}/rematch', ali)
req('post', f'/api/games/rooms/{code}/ready', bek, json={'ready': True})
check("Lobbida: imkoniyat tugagan", st(ali, code)['chaqmoq']['kind'] == 'no_chance')
start(ali, code)
play_all(code, [(ali, 'right'), (bek, 'wrong')])
r = my_result(ali, code)['me']
check("4-o'yin: 1-o'rin, lekin chaqmoq 0; ball/xp esa bor", r['chaqmoq'] == 0 and r['rank'] == 1 and r['xp'] > 0, r)
check("Natijada kind = no_chance", st(ali, code)['chaqmoq']['kind'] == 'no_chance')
check('Dashboard o\'zgarmadi (30+20+30=80)', req('get', '/api/study/dashboard', ali)[1]['chaqmoq'] == 80)

print('— 24 soat o\'tgach yana 3 ta')
adv(H24 + 1000)
ch = chance(ali)
check('Taymer tugadi: 3 / 3', ch['left'] == 3 and ch['reset_at_ms'] is None, ch)
ch = chance(bek)
check('Bek ham 3 / 3', ch['left'] == 3, ch)

print('— Kompyuter bilan o\'yin')
code2 = room_with(sam)
req('post', f'/api/games/rooms/{code2}/bot', sam, json={'level': 'oson'})
check("Lobbida: kompyuter bilan — chaqmoq yo'q", st(sam, code2)['chaqmoq']['kind'] == 'bot')
start(sam, code2)
check("O'yinda ham 'bot', imkoniyat ishlatilmadi", st(sam, code2)['chaqmoq']['kind'] == 'bot' and chance(sam)['left'] == 3)
play_all(code2, [(sam, 'right')])
for _ in range(60):                          # kompyuter javobini kutamiz (Sam har 5 s so'raydi)
    if st(sam, code2)['status'] == 'finished':
        break
    adv(5000)
check('Kompyuter bilan: chaqmoq 0', my_result(sam, code2)['me']['chaqmoq'] == 0)

print("— O'rtada chiqib ketish")
code3 = room_with(dil, sam, bek)
start(dil, code3)
st(dil, code3); st(sam, code3); st(bek, code3)
q = q_of(code3, 0)
req('post', f'/api/games/rooms/{code3}/answer', sam, json={'q': 0, 'answer': q['answer']})
req('post', f'/api/games/rooms/{code3}/leave', sam)
check("Chiqqan Sam: imkoniyat baribir ishlatildi", chance(sam)['left'] == 2, chance(sam))
d = st(dil, code3)
check("3 kishidan biri chiqdi — o'yin davom etadi", d['status'] == 'playing' and d.get('left_players') == ['Sam'], (d.get('status'), d.get('left_players')))
s, e = req('post', '/api/games/rooms/join', sam, json={'code': code3})
check("Chiqqan Sam o'yin davomida qaytib kira olmaydi (left_game)", s == 409 and e.get('code') == 'left_game', e)
req('post', f'/api/games/rooms/{code3}/leave', bek)
d = st(dil, code3)
check("Yana biri chiqdi — bitta odam qoldi, o'yin tugadi", d['status'] == 'finished' and d['session']['end_reason'] == 'players_left', d.get('status'))
check("Dil ko'radi: Sam va Bek chiqib ketdi", sorted(d.get('left_players') or []) == ['Bek', 'Sam'], d.get('left_players'))
r = my_result(dil, code3)
check("Natijada faqat Dil, 1-o'rin, +30", [x['name'] for x in r['rows']] == ['Dil'] and r['me']['rank'] == 1 and r['me']['chaqmoq'] == 30, r)
n = db('SELECT COUNT(*) AS n FROM game_results WHERE user_id = %s', (sam['id'],), True)[0]['n']
check("Sam uchun natija yozilmadi (reyting yo'q)", n == 1, n)            # faqat kompyuter bilan o'yin
s, e = req('post', '/api/games/rooms/join', sam, json={'code': code3})
check("O'yin tugagach roomga qaytish mumkin (keyingi o'yin uchun)", s == 200, e)

print('— Aloqa 30 s uzilsa — avtomatik chiqadi')
code4 = room_with(ali, bek, count=10)
start(ali, code4)
for _ in range(8):                          # Bek so'rov yubormaydi (ilova yopilgan)
    adv(5000)
    st(ali, code4)
d = st(ali, code4)
check("Bek chiqarildi, o'yin tugadi, Ali +30", d['status'] == 'finished' and d.get('left_players') == ['Bek']
      and my_result(ali, code4)['me']['chaqmoq'] == 30, (d.get('status'), d.get('left_players')))
check("Bek imkoniyati ishlatildi (3 - 2 = 1), natija yo'q", chance(bek)['left'] == 1
      and not db('SELECT 1 FROM game_results r JOIN game_rooms g ON g.id = r.room_id WHERE g.code = %s AND r.user_id = %s',
                 (code4, bek['id']), True))

print('— Eski natijalar: 10 ball = 1 chaqmoq saqlanadi')
db("INSERT INTO game_results (session_id, room_id, user_id, game_type, subject, difficulty, score, earned, xp, correct, wrong, total, "
   "accuracy, rank, players, won, duration_ms, created_ms) VALUES (999999, 1, %s, 'quiz_battle', 'math', 'orta', 50, 95, 95, 3, 2, 5, 60, 1, 2, 1, 1000, 1)",
   (dil['id'],))
check('Dil: 30 (yangi) + 95//10 = 39', req('get', '/api/study/dashboard', dil)[1]['chaqmoq'] == 39,
      req('get', '/api/study/dashboard', dil)[1]['chaqmoq'])
g = req('get', '/api/games/me', dil)[1]['stats']
check("O'yin profili chaqmoqi ham 39", g['chaqmoq'] == 39, g['chaqmoq'])
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
