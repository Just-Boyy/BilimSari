# -*- coding: utf-8 -*-
"""Kun savoli va yutuqlar testi."""
import os
import sys
import time
from datetime import date, timedelta

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import achievements  # noqa: E402
import daily  # noqa: E402
import notify  # noqa: E402
import study  # noqa: E402
import curriculum as cur_mod  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402
from games import clock, engine, rooms  # noqa: E402

c = A.app.test_client()
fails = []
# Toshkent 08:00 atrofidagi vaqtdan boshlaymiz (kun o'rtasida kun almashib qolmasin)
_base = int(time.time() * 1000)
T = [_base - (_base + 5 * 3600 * 1000) % (24 * 3600 * 1000) + 8 * 3600 * 1000]
clock.now_ms = lambda: T[0]


def adv(ms):
    T[0] += ms


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


def with_cur(fn):
    conn = get_connection(); cur = conn.cursor()
    try:
        return fn(cur, conn)
    finally:
        cur.close(); conn.close()


def mk_user(name, tg=None):
    rows = db('INSERT INTO users (name, email, password_hash, onboarded) VALUES (%s, NULL, NULL, TRUE) RETURNING id', (name,), True)
    uid = rows[0]['id']
    if tg:
        db('UPDATE users SET telegram_id = %s WHERE id = %s', (tg, uid))
    return {'id': uid, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


def req(method, path, u, **kw):
    r = getattr(c, method)(path, headers=u['h'], **kw)
    return r.status_code, (r.get_json() or {})


def sub(x, keys=('answered', 'correct', 'streak')):
    return {k: x.get(k) for k in keys}


def right_answer():
    return with_cur(lambda cur, conn: daily._question(cur, conn, daily.today(T[0]), T[0])['answer'])


ali, bek, sar, dil = mk_user('Ali Valiyev', 1001), mk_user('Bek', 1002), mk_user('Sardor'), mk_user('Dilnoza', 1004)

print('\n=== Kun savoli ===')
s, d = req('get', '/api/study/dashboard', ali)
check('Dashboard: kun savoli holati (hali javob yo\'q)', s == 200 and sub(d['daily']) == {'answered': False, 'correct': False, 'streak': 0}, d.get('daily'))
check('Dashboard savolni ochmaydi (vaqt boshlanmaydi)', not db('SELECT 1 FROM daily_answers WHERE user_id = %s', (ali['id'],), True))

s, d = req('get', '/api/study/daily?peek=1', ali)
check('peek: savol matnisiz, vaqt boshlanmaydi', s == 200 and d['opened'] is False and 'prompt' not in d and d['subject_name']
      and d['bot'] and 0 < d['next_in_s'] <= 86400 and not db('SELECT 1 FROM daily_answers WHERE user_id = %s', (ali['id'],), True), d)
s, d = req('get', '/api/study/daily', ali)
check('Ochildi: kind, elapsed 0', d['opened'] and d['kind'] in ('mc', 'tf') and d['elapsed_ms'] == 0, d)
s, d = req('get', '/api/study/daily?peek=1', ali)
check('Ochilgandan keyin peek savolni qaytaradi', d['opened'] and d['prompt'], d)
s, d = req('get', '/api/study/daily', ali)
check('Savol keldi',s == 200 and d['prompt'] and len(d['options']) >= 2 and d['subject_name'] and not d['answered'], d)
check('To\'g\'ri javob oshkor qilinmaydi', 'answer' not in d and 'result' not in d and 'explain' not in d, list(d))
prompt = d['prompt']
adv(2000)
s, d2 = req('get', '/api/study/daily', bek)
check('Hamma uchun bir xil savol', d2['prompt'] == prompt and d2['options'] == d['options'])
adv(1000)
s, d = req('get', '/api/study/daily', ali)
opened = db('SELECT opened_ms FROM daily_answers WHERE user_id = %s', (ali['id'],), True)[0]['opened_ms']
check('Qayta ochish vaqtni qayta boshlamaydi', int(opened) == T[0] - 3000, (opened, T[0]))

ans = right_answer()
s, d = req('post', '/api/study/daily/answer', dil, json={'answer': ans})
check('Ochmasdan javob -> 409', s == 409 and d['code'] == 'not_opened', (s, d))
for bad in ('x', 99, -1, True, None):
    s, d = req('post', '/api/study/daily/answer', ali, json={'answer': bad})
    check(f'Noto\'g\'ri format ({bad!r}) -> 400', s == 400, (s, d))

s, d = req('post', '/api/study/daily/answer', ali, json={'answer': ans})
r = d.get('result') or {}
check('Ali to\'g\'ri javob berdi: +5 chaqmoq, 3.0 s', s == 200 and r.get('correct') and r.get('chaqmoq') == 5 and r.get('seconds') == 3.0, d)
check('Javobdan keyin to\'g\'ri variant va izoh', r.get('right_answer') == ans and 'explain' in r, r)
check('Reyting: Ali 1-o\'rin, streak 1', d['ranking']['me'] == {'rank': 1, 'seconds': 3.0} and d['streak'] == 1, d)
check('Yangi yutuq: "Kun savoli"', [a['key'] for a in d['new_achievements']] == ['kun_1'], d['new_achievements'])
s, d = req('post', '/api/study/daily/answer', ali, json={'answer': ans})
check('Ikkinchi urinish -> 409', s == 409 and d['code'] == 'already_answered', (s, d))
s, d = req('get', '/api/study/daily', ali)
check('Qayta ochganda natija saqlangan', d['answered'] and d['result']['correct'], d)

s, d = req('post', '/api/study/daily/answer', bek, json={'answer': ans})
check('Bek tezroq (0 s? yo\'q — 3 s oldin ochgan)', d['ranking']['me']['rank'] in (1, 2), d['ranking'])
s, d = req('get', '/api/study/daily', sar)
adv(500)
s, d = req('post', '/api/study/daily/answer', sar, json={'answer': ans})
check('Sardor eng tez (0.5 s) -> 1-o\'rin', d['ranking']['me'] == {'rank': 1, 'seconds': 0.5}, d['ranking'])
s, d = req('get', '/api/study/daily', dil)
wrong = (ans + 1) % len(d['options'])
s, d = req('post', '/api/study/daily/answer', dil, json={'answer': wrong})
check('Dilnoza xato: chaqmoq yo\'q, reytingda yo\'q', not d['result']['correct'] and d['result']['chaqmoq'] == 0 and d['ranking']['me'] is None, d)
check('Hisob: 3 to\'g\'ri, 4 javob', d['ranking']['correct_count'] == 3 and d['ranking']['answered_count'] == 4, d['ranking'])
check('Reytingda faqat ism (familiyasiz)', any(t['name'] == 'Ali' for t in d['ranking']['top']), d['ranking']['top'])

base = with_cur(lambda cur, conn: study.compute_chaqmoq(cur, ali['id']))
check('Chaqmoqqa +5 qo\'shildi', base == 5, base)
lb = with_cur(lambda cur, conn: study.leaderboard(cur, ali['id']))
check('Umumiy reytingda kun savoli chaqmoqlari', lb['me'] and lb['me']['chaqmoq'] == 5, lb['me'])

s, d = req('get', '/api/study/dashboard', ali)
check('Dashboard: javob berilgan', sub(d['daily']) == {'answered': True, 'correct': True, 'streak': 1}, d['daily'])

print('\n=== Keyingi kunlar va streak ===')
day1 = daily.today(T[0])
adv(24 * 3600 * 1000)
s, d = req('get', '/api/study/dashboard', ali)
check('Ertasi kuni streak saqlanadi (bugun hali javob yo\'q)', sub(d['daily']) == {'answered': False, 'correct': False, 'streak': 1}, d['daily'])
s, d = req('get', '/api/study/daily', ali)
check('Yangi kun — yangi savol yozuvi', daily.today(T[0]) != day1 and db('SELECT COUNT(*) AS n FROM daily_questions', fetch=True)[0]['n'] == 2)
s, d = req('post', '/api/study/daily/answer', ali, json={'answer': right_answer()})
check('2-kun: streak 2, chaqmoq 10', d['streak'] == 2 and with_cur(lambda cur, conn: study.compute_chaqmoq(cur, ali['id'])) == 10, d['streak'])
adv(2 * 24 * 3600 * 1000)
s, d = req('get', '/api/study/dashboard', ali)
check('Bir kun o\'tkazib yuborilsa streak 0', d['daily']['streak'] == 0, d['daily'])

# Har bir fan uchun savol tanlanadi (12 kun ketma-ket)
def all_subjects(cur, conn):
    got = set()
    for i in range(len(cur_mod.SUBJECT_CATALOG)):
        day = (date.fromisoformat(daily.today(T[0])) + timedelta(days=100 + i)).isoformat()
        q = daily._question(cur, conn, day, T[0])
        got.add(q['subject_name'])
        assert q['prompt'] and 0 <= q['answer'] < len(q['options'])
    return got
names = with_cur(all_subjects)
check('Har bir fandan kun savoli chiqadi', len(names) == len(cur_mod.SUBJECT_CATALOG), names)
again = with_cur(lambda cur, conn: daily._pick(cur, '2030-01-05'))
check('Tanlov deterministik', again == with_cur(lambda cur, conn: daily._pick(cur, '2030-01-05')))

print('\n=== Yutuqlar ===')
s, d = req('get', '/api/study/achievements', ali)
keys = {i['key']: i for i in d['items']}
check("Ro'yxat: 19 ta nishon (premium va marafon bilan)", s == 200 and d['total'] == 19 and len(d['items']) == 19, d.get('total'))
tiers = {i['key']: i['tier'] for i in d['items']}
check('Darajalar: bronza/kumush/oltin/brilyant/premium', tiers['mavzu_1'] == 'bronza' and tiers['mavzu_10'] == 'kumush'
      and tiers['mavzu_50'] == 'oltin' and tiers['mavzu_100'] == 'brilyant' and tiers['premium'] == 'premium', tiers)
check('"Kun savoli" ochilgan, allaqachon tabriklangan', keys['kun_1']['unlocked'] and not d['new'], d['new'])
check('Jarayon: 7 kunlik streak 0/7', keys['streak_7']['progress'] == 0 and keys['streak_7']['goal'] == 7)

# 7 kun ketma-ket kun savoli
today = date.fromisoformat(daily.today(T[0]))
for k in range(7):
    day = (today - timedelta(days=k)).isoformat()
    db('INSERT INTO daily_answers (day, user_id, opened_ms, answered_ms, answer, correct, chaqmoq) VALUES (%s, %s, %s, %s, 0, 0, 0) '
       'ON CONFLICT (day, user_id) DO NOTHING', (day, bek['id'], T[0], T[0]))
s, d = req('get', '/api/study/achievements', bek)
check('7 kun ketma-ket -> "Har kuni savol"', 'kun_7' in [n['key'] for n in d['new']], d['new'])
s, d = req('get', '/api/study/achievements', bek)
check('Tabrik bir marta ko\'rsatiladi', d['new'] == [], d['new'])

# Mavzular + chaqmoq
tids = [r['id'] for r in db('SELECT id FROM topics ORDER BY id LIMIT 12', fetch=True)]
for t in tids:
    db("INSERT INTO user_progress (user_id, topic_id, status, completed_at) VALUES (%s, %s, 'completed', NOW())", (sar['id'], t))
s, d = req('get', '/api/study/dashboard', sar)
got = [n['key'] for n in d['new_achievements']]
check('12 mavzu -> "Birinchi qadam", "Bilim izlovchi" (dashboard orqali)', 'mavzu_1' in got and 'mavzu_10' in got and 'mavzu_50' not in got, got)

# Turnir medallari
db('INSERT INTO game_awards (week_start_ms, place, user_id, xp, created_ms) VALUES (1, 1, %s, 500, 1)', (dil['id'],))
db('INSERT INTO game_awards (week_start_ms, place, user_id, xp, created_ms) VALUES (1, 2, %s, 300, 1)', (bek['id'],))
s, d = req('get', '/api/study/achievements', dil)
got = [n['key'] for n in d['new']]
check('Turnirda 1-o\'rin -> sovrindor + g\'olib', 'turnir_1' in got and 'turnir_3' in got, got)
s, d = req('get', '/api/study/achievements', bek)
got = [n['key'] for n in d['new']]
check('Turnirda 2-o\'rin -> faqat sovrindor', got == ['turnir_3'], got)

print('\n=== Qiyin kompyuterni yutish ===')
s, d = req('post', '/api/games/rooms', ali, json={'game': 'quiz_battle', 'subject': 'math', 'difficulty': 'oson', 'count': 5, 'max_players': 2})
print('CREATE', s, d); code = d['code']
req('post', f'/api/games/rooms/{code}/bot', ali, json={'level': 'qiyin'})
s, d = req('post', f'/api/games/rooms/{code}/start', ali)
check('O\'yin boshlandi', s == 200, d)


def q_of(i):
    def f(cur, conn):
        room = rooms.load_room(cur, code)
        return engine.questions_for(cur, room['session_id'])[i]
    return with_cur(f)


def st():
    return req('get', f'/api/games/rooms/{code}', ali)[1].get('state') or {}


for qi in range(5):
    for _ in range(60):
        d = st()
        if d['session'] and d['session']['phase'] == 'question' and d['session']['q_index'] == qi:
            break
        adv(500)
    req('post', f'/api/games/rooms/{code}/answer', ali, json={'q': qi, 'answer': q_of(qi)['answer']})
for _ in range(80):
    d = st()
    if d['status'] == 'finished':
        break
    adv(1000)
row = db('SELECT won, bot_level FROM game_results WHERE user_id = %s', (ali['id'],), True)
check('Natijada eng kuchli kompyuter darajasi (5) saqlandi', row and row[0]['bot_level'] == 5, row)
check('Ali yutdi', row and row[0]['won'] == 1, row)
s, d = req('get', '/api/study/achievements', ali)
got = [n['key'] for n in d['new']]
check('"Birinchi o\'yin", "Birinchi g\'alaba", "Kompyuter ustasi"', {'oyin_1', 'galaba_1', 'bot_qiyin'} <= set(got), got)
# Room o'chirilgandan keyin ham saqlanadi
db('DELETE FROM game_room_players')
db('DELETE FROM user_achievements WHERE user_id = %s AND key = %s', (ali['id'], 'bot_qiyin'))
s, d = req('get', '/api/study/achievements', ali)
check('Room tozalangach ham "Kompyuter ustasi" aniqlanadi', 'bot_qiyin' in [n['key'] for n in d['new']], d['new'])

print('\n=== Ertalabki xabar (09:00) ===')
sent = []
notify.send = lambda chat, text, button=None, path='', lang=None: (sent.append((chat, text, path)) or (True, None))
notify.time = type('TezVaqt', (), {'sleep': staticmethod(lambda s: None)})()
adv(24 * 3600 * 1000)       # yangi kun, hali hech kim ochmagan
new_user = mk_user('Yangi', 1005)
s, d = req('get', '/api/study/daily', bek)          # Bek bugun ochib bo'lgan
n = with_cur(lambda cur, conn: notify.question_ready(cur, conn, T[0]))
chats = sorted(x[0] for x in sent)
check('Faol, bugun ochmaganlarga yuborildi (Bek ochgan)', 1001 in chats and 1004 in chats and 1005 in chats and 1002 not in chats, chats)
check('Havola daily.html, matnda fan nomi', all(p == 'daily.html' and 'bugungi savol tayyor' in t for _, t, p in sent), sent)
check('Streak bo\'lsa eslatiladi (Ali: 0 — bir kun o\'tkazgan)', not any('streak' in t for c_, t, _ in sent if c_ == 1001), sent)
sent.clear()
with_cur(lambda cur, conn: notify.question_ready(cur, conn, T[0]))
check('Bir kunda ikki marta yuborilmaydi', sent == [], sent)
# tick: soat 9 dan oldin yubormaydi, 9 da yuboradi
sent.clear()
db("DELETE FROM notify_log WHERE kind = 'question'")
local_h = (T[0] + 5 * 3600 * 1000) // 3600000 % 24
check('Test soati 08:xx', local_h == 8, local_h)
notify.tick(T[0])
check('08:xx da xabar yo\'q', not any(p == 'daily.html' for _, _, p in sent), sent)
adv(3600 * 1000)
notify.tick(T[0])
check('09:xx da tick orqali yuborildi', any(p == 'daily.html' for _, _, p in sent), sent)

print('\n=== Bot: /start kun ===')
calls = []
A.tg_api = lambda method, payload: calls.append((method, payload))
hdr = {'X-Telegram-Bot-Api-Secret-Token': A.WEBHOOK_SECRET}
c.post('/telegram/webhook', headers=hdr, json={'message': {'text': '/start kun', 'chat': {'id': 77}, 'from': {'first_name': '<b>X</b>'}}})
c.post('/telegram/webhook', headers=hdr, json={'message': {'text': '/kun', 'chat': {'id': 78}, 'from': {'first_name': 'Y'}}})
urls = [p['reply_markup']['inline_keyboard'][0][0]['web_app']['url'] for _, p in calls]
check('/start kun va /kun -> daily.html tugmasi', len(urls) == 2 and all(u.endswith('/daily.html') for u in urls), urls)
check('Ism HTML-escape qilingan', '&lt;b&gt;X' in calls[0][1]['text'], calls[0][1]['text'])
s = c.get('/daily.html')
check('daily.html sahifasi ochiladi', s.status_code == 200)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))

print('\n=== Bosh sahifa: yangi maydonlar ===')
s, d = req('get', '/api/study/dashboard', ali)
k = d['daily']
check('Kun savoli: taymer, mini reyting, hafta', 0 < k['next_in_s'] <= 86400 and len(k['week']) == 7
      and sum(1 for w in k['week'] if w['today']) == 1 and isinstance(k['top'], list), k)
check('Bugungi reja maydonlari', set(d['plan']) >= {'daily', 'topic', 'game', 'done', 'total'} and d['plan']['total'] == 3, d['plan'])
check('Reyting o\'rni va chaqmoq manbalari', 'rank' in d['rank'] and set(d['chaqmoq_parts']) == {'topics', 'games', 'daily', 'bonus'}
      and sum(d['chaqmoq_parts'].values()) == d['chaqmoq'], (d['rank'], d['chaqmoq_parts'], d['chaqmoq']))
print('\n' + ('HAMMASI OK (2)' if not fails else f'{len(fails)} ta XATO: {fails}'))
