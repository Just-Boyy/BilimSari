# -*- coding: utf-8 -*-
"""Yangi imkoniyatlar testi: kompyuter raqib, takrorlash, haftalik turnir, eslatmalar."""
import os
import sys
import time
from datetime import timedelta

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import notify  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection, utc_now  # noqa: E402
from games import clock, engine, rooms, stats  # noqa: E402

c = A.app.test_client()
fails = []
T = [int(time.time() * 1000)]
clock.now_ms = lambda: T[0]


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


def mk_user(name, tg=None):
    rows = db('INSERT INTO users (name, email, password_hash, onboarded) VALUES (%s, NULL, NULL, TRUE) RETURNING id', (name,), True)
    uid = rows[0]['id']
    if tg:
        db('UPDATE users SET telegram_id = %s WHERE id = %s', (tg, uid))
    return {'id': uid, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


def req(method, path, u, **kw):
    r = getattr(c, method)(path, headers=u['h'], **kw)
    return r.status_code, (r.get_json() or {})


def st(u, code):
    return req('get', f'/api/games/rooms/{code}', u)[1].get('state') or {}


def wait(ms, code, *users):
    while ms > 0:
        step = min(1000, ms)
        adv(step); ms -= step
        for u in users:
            st(u, code)


def q_of(code, i):
    conn = get_connection(); cur = conn.cursor()
    room = rooms.load_room(cur, code)
    q = engine.questions_for(cur, room['session_id'])[i]
    cur.close(); conn.close()
    return q


ali, bek = mk_user('Ali Valiyev', tg=1001), mk_user('Bek', tg=1002)

print('\n=== Kompyuter raqib ===')
s, d = req('post', '/api/games/rooms', ali, json={'game': 'quiz_battle', 'subject': 'math', 'difficulty': 'oson', 'count': 5, 'max_players': 2})
code = d['code']
check('Yolg\'iz host boshlay olmaydi (maslahat kompyuter haqida)', not d['state']['can_start'] and 'kompyuter' in d['state']['start_hint'], d['state']['start_hint'])
s, d = req('post', f'/api/games/rooms/{code}/bot', bek, json={'level': 'oson'})
check('Host emas kompyuter qo\'sha olmaydi', s == 403, (s, d))
s, d = req('post', f'/api/games/rooms/{code}/bot', ali, json={'level': 'super'})
check('Noto\'g\'ri daraja -> 400', s == 400, (s, d))
s, d = req('post', f'/api/games/rooms/{code}/bot', ali, json={'level': 'qiyin'})
bots = [p for p in d['state']['players'] if p['bot']]
check('Kompyuter qo\'shildi, tayyor, onlayn', s == 200 and len(bots) == 1 and bots[0]['ready'] and bots[0]['online'], d)
check('Endi boshlash mumkin', d['state']['can_start'], d['state'])
s, d = req('post', f'/api/games/rooms/{code}/bot', ali, json={'level': 'oson'})
check('Joy yo\'q (max 2) -> 409', s == 409 and d['code'] == 'room_full', d)
s, d = req('post', f'/api/games/rooms/{code}/start', ali)
check('Kompyuter bilan o\'yin boshlandi', s == 200 and d['state']['status'] == 'playing', d)
adv(4100); st(ali, code)
req('post', f'/api/games/rooms/{code}/answer', ali, json={'q': 0, 'answer': q_of(code, 0)['answer']})
d = st(ali, code)
check('Ali javob berdi, kompyuter hali o\'ylamoqda', d['session']['phase'] == 'question' and d['session']['answered_count'] == 1, d['session'])
wait(12000, code, ali)
d = st(ali, code)
check('Kompyuter o\'z vaqtida javob berdi -> reveal', d['session']['phase'] in ('reveal', 'question') and d['session']['q_index'] >= 0, d['session'])
for qi in range(1, 5):
    for _ in range(40):
        d = st(ali, code)
        if d['session'] and d['session']['phase'] == 'question' and d['session']['q_index'] == qi:
            break
        adv(1000)
    q = q_of(code, qi)
    wrong = (q['answer'] + 1) % len(q['options'])
    req('post', f'/api/games/rooms/{code}/answer', ali, json={'q': qi, 'answer': wrong if qi >= 3 else q['answer']})
for _ in range(60):
    d = st(ali, code)
    if d['status'] == 'finished':
        break
    adv(1000)
res = d['session']['results']
names = [r['name'] for r in res['rows']]
check('O\'yin tugadi, natijada kompyuter ham bor', d['status'] == 'finished' and any('Kompyuter' in n for n in names), names)
check('Ali ball oldi (kompyuterga qarshi ham hisobga o\'tadi)', res['me']['xp'] > 0 and res['me']['multiplayer'], res['me'])
s, d = req('get', '/api/games/leaderboard?period=all', ali)
check('Reytingda kompyuter yo\'q', all('Kompyuter' not in e['name'] for e in d['top']) and d['top'], d['top'])
check('Kompyuterning natijasi bazada manfiy id bilan', db('SELECT COUNT(*) AS n FROM game_results WHERE user_id < 0', fetch=True)[0]['n'] >= 1)

print('\n=== Hostlik kompyuterga o\'tmaydi ===')
s, d = req('post', '/api/games/rooms', ali, json={'game': 'quiz_battle', 'subject': 'history', 'max_players': 4})
code2 = d['code']
req('post', f'/api/games/rooms/{code2}/bot', ali, json={'level': 'orta'})
req('post', '/api/games/rooms/join', bek, json={'code': code2})
req('post', f'/api/games/rooms/{code2}/leave', ali)
d = st(bek, code2)
check('Host chiqdi -> hostlik odamga (Bek)', d['me']['host'], d['players'])
bot_pid = next(p['pid'] for p in d['players'] if p['bot'])
s, d = req('post', f'/api/games/rooms/{code2}/kick', bek, json={'pid': bot_pid})
check('Kompyuterni chiqarish mumkin', s == 200 and not any(p['bot'] for p in d['state']['players']), d)
req('post', f'/api/games/rooms/{code2}/bot', bek, json={'level': 'oson'})
req('post', f'/api/games/rooms/{code2}/leave', bek)
check('Faqat kompyuter qolsa room yopiladi', db('SELECT status FROM game_rooms WHERE code = %s', (code2,), True)[0]['status'] == 'cancelled')

print('\n=== Takrorlash (zaif mavzular) ===')
rows = db('SELECT topic, correct, total FROM game_topic_stats WHERE user_id = %s', (ali['id'],), True)
check('Mavzular bo\'yicha natija saqlandi', len(rows) >= 1 and sum(r['total'] for r in rows) == 5, rows)
s, d = req('get', '/api/study/game/questions?mode=review&count=10', ali)
weak = d.get('weak_topics', [])
check('Zaif mavzular topildi (noto\'g\'ri javob berilganlar)', s == 200 and len(weak) >= 1 and all(w['accuracy'] < 60 for w in weak), d)
check('Takrorlash savollari faqat zaif mavzulardan', d['questions'] and {q['topic_id'] for q in d['questions']} <= {w['topic_id'] for w in weak}, d.get('questions', [])[:2])
s, d = req('get', '/api/study/game/questions?mode=review', bek)
check('Zaif mavzusi yo\'q o\'quvchiga bo\'sh ro\'yxat', d['questions'] == [] and d['weak_topics'] == [], d)

print('\n=== Haftalik turnir ===')
s, d = req('get', '/api/games/leaderboard?period=week', ali)
check('Hafta reytingida turnir ma\'lumoti', d.get('tournament') and d['tournament']['ends_ms'] > T[0], d.get('tournament'))
s, d = req('get', '/api/games/leaderboard?period=day', ali)
check('Kunlik reytingda turnir yo\'q', d.get('tournament') is None)

print('\n=== Eslatmalar ===')
sent = []
notify.send = lambda chat, text, button=None, path='': (sent.append((chat, text, path)) or (True, None))
notify.time = type('TezVaqt', (), {'sleep': staticmethod(lambda s: None)})()   # faqat notify ichidagi kutish

zar = mk_user('Zarina Qodirova', tg=2001)                       # bugun ro'yxatdan o'tgan, hali o'qimagan
old = mk_user('Eski', tg=2002)
db("UPDATE users SET created_at = %s WHERE id = %s", (utc_now() - timedelta(days=40), old['id']))   # uzoq kirmagan
off = mk_user('Ochirgan', tg=2003)
req('post', '/api/profile/notify', off, json={'on': False})
s, d = req('get', '/api/me', off)
check('/api/me: eslatma o\'chirilgan', d['user']['notify'] is False, d['user'])

conn = get_connection(); cur = conn.cursor()
n = notify.daily_reminders(cur, conn, T[0])
cur.close(); conn.close()
chats = [x[0] for x in sent]
check('Kunlik eslatma: yangi o\'quvchiga yuborildi', 2001 in chats, sent)
check('Bugun o\'ynagan Ali, uzoq kirmagan va o\'chirganlarga yuborilmadi', 1001 not in chats and 2002 not in chats and 2003 not in chats, chats)
check('Xabarda ism va tugma', any('Zarina' in t and p == 'dashboard.html' for _, t, p in sent), sent)
conn = get_connection(); cur = conn.cursor()
notify.daily_reminders(cur, conn, T[0])
cur.close(); conn.close()
check('Bir kunda ikki marta yuborilmaydi', [x[0] for x in sent].count(2001) == 1, sent)

sent.clear()
cool = mk_user('Kutuvchi', tg=3001)
db("INSERT INTO user_progress (user_id, topic_id, status, completed_at) VALUES (%s, (SELECT id FROM topics WHERE subject_key = 'math' ORDER BY grade, seq LIMIT 1), 'completed', %s)",
   (cool['id'], notify._utc(T[0]) - timedelta(hours=24, minutes=5)))
conn = get_connection(); cur = conn.cursor()
notify.cooldown_ready(cur, conn, T[0])
notify.cooldown_ready(cur, conn, T[0])
cur.close(); conn.close()
check('"Keyingi mavzu ochildi" — bir marta, fan nomi bilan', [x[0] for x in sent] == [3001] and 'Matematika' in sent[0][1] and sent[0][2] == 'topics.html?fan=math', sent)

sent.clear()
blocked = mk_user('Bloklagan', tg=4001)
notify.send = lambda chat, text, button=None, path='': (sent.append((chat, text, path)) or ((False, 403) if chat == 4001 else (True, None)))
conn = get_connection(); cur = conn.cursor()
notify.daily_reminders(cur, conn, T[0] + 1000)
cur.close(); conn.close()
check('Botni bloklagan (403) -> eslatmalar o\'chdi', db('SELECT notify FROM users WHERE id = %s', (blocked['id'],), True)[0]['notify'] == 0)

sent.clear()
notify.send = lambda chat, text, button=None, path='': (sent.append((chat, text, path)) or (True, None))
conn = get_connection(); cur = conn.cursor()
winners = notify.weekly_awards(cur, conn, T[0] + stats.WEEK_MS)
again = notify.weekly_awards(cur, conn, T[0] + stats.WEEK_MS)
cur.close(); conn.close()
check('Haftalik g\'olib: Ali 1-o\'rin, tabrik xabari', winners and winners[0]['user_id'] == ali['id'] and winners[0]['place'] == 1 and any(x[0] == 1001 and 'Tabriklaymiz' in x[1] for x in sent), (winners, sent))
check('Medallar qayta berilmaydi', again == [], again)
s, d = req('get', '/api/games/me', ali)
check('Profilda oltin medal', d['stats']['medals']['gold'] == 1, d['stats']['medals'])

sent.clear()
notify.BOT_TOKEN = 'test'
db('DELETE FROM game_presence')
for uid in (ali['id'], bek['id']):
    db('''INSERT INTO game_results (session_id, room_id, user_id, game_type, subject, difficulty, score, earned, xp,
          correct, wrong, total, accuracy, rank, players, won, created_ms) VALUES (99999, 1, %s, 'quiz_battle', 'math',
          'orta', 10, 10, 0, 1, 0, 1, 100, 1, 2, 0, %s)''', (uid, T[0]))
notify.invite_co_players(ali['id'], 'Ali Valiyev', 'ABC234', 'Quiz Battle', 'Matematika')
for _ in range(50):
    if sent:
        break
    time.sleep(0.1)
check("Taklif: oldin birga o'ynagan Bekka yuborildi (kod bilan)",
      [x[0] for x in sent] == [1002] and 'ABC234' in sent[0][1] and sent[0][2] == 'games.html?kod=ABC234', sent)

print('\n=== Rejalashtiruvchi: vazifa bir marta egallanadi ===')
conn = get_connection(); cur = conn.cursor()
first = notify._claim(cur, conn, 'test', 'slot-1')
second = notify._claim(cur, conn, 'test', 'slot-1')
cur.close(); conn.close()
check('Bir slotni faqat bitta worker egallaydi', first is True and second is False, (first, second))

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: ' + ', '.join(fails)))
sys.exit(1 if fails else 0)
