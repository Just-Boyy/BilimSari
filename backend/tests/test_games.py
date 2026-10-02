# -*- coding: utf-8 -*-
"""Game Hub backend testi: bir necha o'yinchi, boshqariladigan soat."""
import json
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
from games import clock, engine, rooms  # noqa: E402

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


def mk_user(name, grade=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO users (name, email, password_hash, onboarded) VALUES (%s, NULL, NULL, TRUE) RETURNING id', (name,))
    uid = cur.fetchone()['id']
    if grade:
        cur.execute('UPDATE users SET grade = %s WHERE id = %s', (grade, uid))
    conn.commit()
    cur.close(); conn.close()
    return {'id': uid, 'h': {'Authorization': 'Bearer ' + create_token(uid)}, 'name': name}


def req(method, path, u, **kw):
    r = getattr(c, method)(path, headers=u['h'], **kw)
    return r.status_code, (r.get_json() or {})


def st(u, code, since=None):
    s, d = req('get', f'/api/games/rooms/{code}' + (f'?since={since}' if since else ''), u)
    return s, d.get('state') or d


def correct_answer(code, q_index):
    conn = get_connection(); cur = conn.cursor()
    room = rooms.load_room(cur, code)
    q = engine.questions_for(cur, room['session_id'])[q_index]
    cur.close(); conn.close()
    return q


def wrong_of(q):
    return (q['answer'] + 1) % len(q['options'])


def wait(ms, code, *users):
    """Vaqt o'tadi, ilova kabi o'yinchilar har soniyada so'rov yuboradi."""
    while ms > 0:
        step = min(1000, ms)
        adv(step)
        ms -= step
        for u in users:
            st(u, code)


ali, bek, sam, dil = mk_user('Ali Valiyev', grade=7), mk_user('Bek Karimov', grade=7), mk_user('Sam'), mk_user('Ali Karimov')

print('\n=== Katalog ===')
s, d = req('get', '/api/games/catalog', ali)
check('6 ta o\'yin', s == 200 and len(d['games']) == 6, d)
check('Memory/Match renderer=match', any(g['key'] == 'memory_match' and g['renderer'] == 'match' for g in d['games']))
s, d = req('get', '/api/games/topics?game=quiz_battle&subject=math', ali)
check('Matematika: 40 mavzu, darajalar bilan', s == 200 and len(d['topics']) == 40 and d['topics'][0]['difficulty'] == 'oson' and d['topics'][-1]['difficulty'] == 'qiyin', d)
s, d = req('get', '/api/games/topics?game=math_battle&subject=math', ali)
check('Math Battle: 6 tur', len(d.get('topics', [])) == 6, d)
s, d = req('get', '/api/games/topics?game=math_battle&subject=history', ali)
check('Noto\'g\'ri fan -> 400', s == 400, (s, d))
s, _ = c.get('/api/games/catalog').status_code, None
check('Tokensiz -> 401', s == 401)

print('\n=== Room yaratish / qo\'shilish ===')
s, d = req('post', '/api/games/rooms', ali, json={'game': 'quiz_battle', 'subject': 'math', 'difficulty': 'orta', 'count': 5, 'max_players': 2, 'public': True})
code = d.get('code', '')
check('Room yaratildi, 6 belgili kod', s == 200 and len(code) == 6 and all(ch in rooms.ALPHABET for ch in code), d)
check('Host tayyor, 1 o\'yinchi', d['state']['me']['host'] and len(d['state']['players']) == 1)
s, d = req('post', '/api/games/rooms', ali, json={'game': 'nope'})
check('Noto\'g\'ri o\'yin -> 400', s == 400 and d['code'] == 'bad_settings', d)
s, d = req('post', '/api/games/rooms', ali, json={'game': 'quiz_battle', 'max_players': 3})
check('max_players=3 -> 400', s == 400, d)
s, d = req('post', '/api/games/rooms', ali, json={'game': 'quiz_battle', 'subject': 'math', 'topic': 'geometry-7-x'})
check('Boshqa fan mavzusi -> 400', s == 400, d)
# Ali yangi room yaratmoqchi bo'lsa, eskisidan chiqadi — keyin qaytadan asl roomni yaratamiz
s, d = req('get', '/api/games/lobby', bek)
check('Lobby: public room ko\'rinadi', any(r['code'] == code for r in d.get('rooms', [])), d)
check('Lobby: onlayn soni >= 1', d.get('online', 0) >= 1, d)
s, d = req('post', '/api/games/rooms/join', bek, json={'code': ' ' + code.lower()[:3] + '-' + code.lower()[3:] + ' '})
check('Kichik harf va tire bilan qo\'shildi', s == 200 and d['code'] == code, d)
check('2 o\'yinchi', len(d['state']['players']) == 2)
s, d = req('post', '/api/games/rooms/join', sam, json={'code': code})
check('To\'la room -> 409 room_full', s == 409 and d['code'] == 'room_full', d)
s, d = req('post', '/api/games/rooms/join', sam, json={'code': 'ZZZZZZ'})
check('Yo\'q kod -> 404', s == 404 and d['code'] == 'room_not_found', d)
s, d = req('post', '/api/games/rooms/join', sam, json={'code': 'ab'})
check('Qisqa kod -> 400 invalid_code', s == 400 and d['code'] == 'invalid_code', d)
s, d = st(sam, code)
check('A\'zo bo\'lmagan poll -> 403', s == 403 and d.get('code') == 'not_member', (s, d))
s, d = req('get', '/api/games/lobby', sam)
check('To\'la room lobbyda yo\'q', not any(r['code'] == code for r in d.get('rooms', [])), d)

print('\n=== Host huquqlari va start ===')
s, d = req('post', f'/api/games/rooms/{code}/start', bek)
check('Host emas -> 403 not_host', s == 403 and d['code'] == 'not_host', d)
s, d = req('post', f'/api/games/rooms/{code}/start', ali)
check('Bek tayyor emas -> 409', s == 409 and 'tayyor emas' in d['error'], d)
s, d = req('post', f'/api/games/rooms/{code}/settings', bek, json={'difficulty': 'qiyin'})
check('Host emas sozlay olmaydi', s == 403, d)
s, d = req('post', f'/api/games/rooms/{code}/settings', ali, json={'difficulty': 'qiyin', 'count': 5, 'max_players': 2, 'subject': 'math'})
check('Host sozlamani o\'zgartirdi', s == 200 and d['state']['settings']['difficulty'] == 'qiyin', d)
s, d = req('post', f'/api/games/rooms/{code}/ready', bek, json={'ready': True})
check('Bek tayyor', s == 200 and d['state']['can_start'], d)
etag = d['state']['etag']
s, d = st(bek, code, etag)
check('ETag: o\'zgarish yo\'q -> same', d.get('same') is True, d)
s, d = req('post', f'/api/games/rooms/{code}/start', ali)
check('O\'yin boshlandi (countdown)', s == 200 and d['state']['status'] == 'playing' and d['state']['session']['phase'] == 'countdown', d)
s, d = req('post', f'/api/games/rooms/{code}/settings', ali, json={'difficulty': 'oson'})
check('O\'yin davomida sozlash -> 409', s == 409, d)
s, d = req('post', '/api/games/rooms/join', sam, json={'code': code})
check('Boshlangan roomga qo\'shilish -> 409', s == 409, d)

print('\n=== O\'yin: savol, javob, ball ===')
adv(4100)
s, d = st(ali, code)
sess = d['session']
check('Countdown tugadi -> 1-savol', sess['phase'] == 'question' and sess['q_index'] == 0, sess)
check('To\'g\'ri javob mijozga ketmaydi', 'answer' not in sess['question'] and 'explain' not in sess['question'], sess['question'])
q0 = correct_answer(code, 0)
adv(1000)
s, d = req('post', f'/api/games/rooms/{code}/answer', ali, json={'q': 0, 'answer': q0['answer']})
check('Ali javob berdi', s == 200 and d.get('accepted'), d)
s, d = req('post', f'/api/games/rooms/{code}/answer', ali, json={'q': 0, 'answer': q0['answer']})
check('Ikkinchi javob -> 409 already_answered', s == 409 and d['code'] == 'already_answered', d)
s, d = req('post', f'/api/games/rooms/{code}/answer', bek, json={'q': 0, 'answer': 99})
check('Yo\'q variant -> 400', s == 400 and d['code'] == 'bad_answer', d)
s, d = req('post', f'/api/games/rooms/{code}/answer', bek, json={'q': 0, 'answer': True})
check('bool javob -> 400', s == 400, d)
s, d = req('post', f'/api/games/rooms/{code}/answer', bek, json={'q': 3, 'answer': 0})
check('Boshqa savol raqami -> 409', s == 409 and d['code'] == 'too_late', d)
s, d = req('post', f'/api/games/rooms/{code}/answer', bek, json={'q': 0, 'answer': wrong_of(q0)})
sess = d['state']['session']
check('Hamma javob berdi -> darhol reveal', sess['phase'] == 'reveal', sess)
check('Reveal: to\'g\'ri javob va tushuntirish', sess['reveal']['answer'] == q0['answer'] and 'explain' in sess['reveal'], sess['reveal'])
me_b = next(p for p in d['state']['players'] if p['me'])
me_a = next(p for p in d['state']['players'] if not p['me'])
check('Ali +15 (tez), Bek 0', me_a['score'] == 15 and me_b['score'] == 0, d['state']['players'])

adv(4100)
s, d = st(bek, code)
check('Reveal tugadi -> 2-savol', d['session']['phase'] == 'question' and d['session']['q_index'] == 1, d['session'])
q1 = correct_answer(code, 1)
wait(12000, code, ali, bek)  # sekin javob — tez bonus yo'q
req('post', f'/api/games/rooms/{code}/answer', bek, json={'q': 1, 'answer': q1['answer']})
s, d = st(ali, code)
check('Ali onlayn, javob bermagan -> savol davom etadi', d['session']['phase'] == 'question' and d['session']['answered_count'] == 1, d['session'].get('phase'))
wait(9000, code, ali, bek)   # Ali javob bermaydi — muddat tugaydi (20 s + 0.8 s)
s, d = st(ali, code)
check('Muddat tugadi -> reveal', d['session']['phase'] == 'reveal', d['session'])
s, d = req('post', f'/api/games/rooms/{code}/answer', ali, json={'q': 1, 'answer': 0})
check('Kech javob -> 409 too_late', s == 409 and d['code'] == 'too_late', d)
scores = {p['name']: p['score'] for p in d.get('state', st(ali, code)[1])['players']} if False else {p['name']: p['score'] for p in st(ali, code)[1]['players']}
check('Bek sekin to\'g\'ri: +10', scores.get('Bek') == 10, scores)

for qi in (2, 3, 4):
    adv(4100)
    st(ali, code); st(bek, code)
    q = correct_answer(code, qi)
    adv(500)
    req('post', f'/api/games/rooms/{code}/answer', ali, json={'q': qi, 'answer': q['answer']})
    req('post', f'/api/games/rooms/{code}/answer', bek, json={'q': qi, 'answer': wrong_of(q)})
adv(4100)
s, d = st(ali, code)
res = d['session'].get('results') or {}
check('O\'yin tugadi', d['status'] == 'finished' and d['session']['phase'] == 'finished', d.get('status'))
check('Natija: Ali 1-o\'rin', res['rows'][0]['name'] == 'Ali' and res['rows'][0]['rank'] == 1, res.get('rows'))
me = res['me']
check('Ali: 4 to\'g\'ri, 1 javobsiz, 80%', me['correct'] == 4 and me['unanswered'] == 1 and me['accuracy'] == 80, me)
check('Ali: ball 60, bonus +50 (yakun+g\'alaba), xp 110', me['score'] == 60 and me['bonus'] == 50 and me['xp'] == 110, me)
check("Ali: chaqmoq +30 (1-o'rin, chaqmoqli o'yin)", me['chaqmoq'] == 30, me)
learn = res['learning']
check('"Nimalarni o\'rgandingiz" bor', learn['summary'].startswith('Siz 5 ta savoldan 4') and len(learn['review']) == 5, learn['summary'])
check('Zaif mavzu havolasi (dars)', all('link' in t for t in learn['strong'] + learn['weak']), learn)
s, d = st(bek, code)
bme = d['session']['results']['me']
check('Bek: 2-o\'rin, g\'alaba bonusi yo\'q, yakun +20', bme['rank'] == 2 and bme['bonus'] == 20 and bme['xp'] == 30, bme)

print('\n=== Chaqmoq, statistika, reyting ===')
s, d = req('get', '/api/study/dashboard', ali)
check("Dashboard chaqmoq = 30 (o'yindan)", d.get('chaqmoq') == 30, d.get('chaqmoq'))
s, d = req('get', '/api/study/leaderboard', ali)
check('Umumiy reytingda Ali birinchi', d['top'] and d['top'][0]['name'].startswith('Ali') and d['top'][0]['chaqmoq'] == 30, d.get('top'))
s, d = req('get', '/api/games/me', ali)
ms = d['stats']
check('Profil: 1 o\'yin, 1 g\'alaba, 110 ball, streak 1', ms['games'] == 1 and ms['wins'] == 1 and ms['xp'] == 110 and ms['streak'] == 1, ms)
check('Sevimli fan: Matematika', ms['favorite_subjects'] == ['Matematika'], ms)
for period in ('day', 'week', 'month', 'all'):
    s, d = req('get', f'/api/games/leaderboard?period={period}', bek)
    check(f'O\'yin reytingi ({period}): Ali 1, Bek 2', [e['name'] for e in d['top']][:2] == ['Ali Valiyev', 'Bek Karimov'] and d['me']['rank'] == 2, d)
s, d = req('get', '/api/games/leaderboard?period=week&scope=subject&subject=history', ali)
check('Fan bo\'yicha (tarix) — bo\'sh', d['top'] == [], d)
s, d = req('get', '/api/games/leaderboard?period=week&scope=grade', ali)
check("Sinf bo'yicha reyting yo'q — umumiyga qaytadi", d['scope'] == 'global' and 'grade' not in d and not d.get('notice'), d)

print('\n=== Rematch, kick, host o\'tishi ===')
s, d = req('post', f'/api/games/rooms/{code}/rematch', bek)
check('Rematch faqat host', s == 403, d)
s, d = req('post', f'/api/games/rooms/{code}/rematch', ali)
check('Rematch -> waiting, Bek tayyor emas', d['state']['status'] == 'waiting' and not d['state']['can_start'] and d['state']['session'] is None, d['state'])
bek_pid = next(p['pid'] for p in d['state']['players'] if p['name'] == 'Bek')
s, d = req('post', f'/api/games/rooms/{code}/kick', ali, json={'pid': bek_pid})
check('Ali Bekni chiqardi', s == 200 and len(d['state']['players']) == 1, d)
s, d = st(bek, code)
check('Chiqarilgan -> 403 kicked', s == 403 and d.get('code') == 'kicked', d)
s, d = req('post', '/api/games/rooms/join', bek, json={'code': code})
check('Chiqarilgan qayta kira olmaydi', s == 403 and d['code'] == 'kicked', d)

s, d = req('post', '/api/games/rooms', sam, json={'game': 'quiz_battle', 'subject': 'history', 'max_players': 4})
code2 = d['code']
check("Har bir room ochiq — lobbyda ko'rinadi", any(r['code'] == code2 for r in req('get', '/api/games/lobby', bek)[1]['rooms']))
req('post', '/api/games/rooms/join', bek, json={'code': code2})
req('post', '/api/games/rooms/join', dil, json={'code': code2})
s, d = req('post', '/api/games/rooms/join', ali, json={'code': code2})
names = sorted(p['name'] for p in d['state']['players'])
check('Bir xil ismlar farqlanadi: Ali, Ali (2)', names == ['Ali', 'Ali (2)', 'Bek', 'Sam'], names)
s, d = req('get', '/api/games/lobby', ali)
check('Ali eski roomdan chiqdi (bitta faol room)', d['my_room']['code'] == code2, d['my_room'])
s, d = req('post', f'/api/games/rooms/{code2}/leave', sam)
s, d = st(bek, code2)
check('Host chiqdi -> hostlik Bekka (eng oldin kirgan) o\'tdi', d['me']['host'], d['players'])

print('\n=== Quick Answer ===')
s, d = req('post', '/api/games/rooms', ali, json={'game': 'quick_answer', 'subject': 'history', 'count': 5, 'max_players': 4})
code3 = d['code']
req('post', '/api/games/rooms/join', bek, json={'code': code3})
req('post', '/api/games/rooms/join', sam, json={'code': code3})
req('post', f'/api/games/rooms/{code3}/ready', bek, json={'ready': True})
req('post', f'/api/games/rooms/{code3}/ready', sam, json={'ready': True})
s, d = req('post', f'/api/games/rooms/{code3}/start', ali)
check('Quick Answer boshlandi (3 o\'yinchi)', s == 200 and d['state']['status'] == 'playing', d)
adv(4100)
st(ali, code3)
q = correct_answer(code3, 0)
req('post', f'/api/games/rooms/{code3}/answer', sam, json={'q': 0, 'answer': wrong_of(q)})
s, d = st(ali, code3)
check('Noto\'g\'ri javobdan keyin savol davom etadi', d['session']['phase'] == 'question', d['session']['phase'])
adv(300)
s, d = req('post', f'/api/games/rooms/{code3}/answer', bek, json={'q': 0, 'answer': q['answer']})
check('Birinchi to\'g\'ri javob -> darhol reveal', d['state']['session']['phase'] == 'reveal', d['state']['session']['phase'])
check('Reveal: birinchi to\'g\'ri — Bek', d['state']['session']['reveal']['first_name'] == 'Bek', d['state']['session']['reveal'])
s, d = req('post', f'/api/games/rooms/{code3}/answer', ali, json={'q': 0, 'answer': q['answer']})
check('Reveal paytida javob -> too_late', s == 409, d)
sc = {p['name']: p['score'] for p in st(ali, code3)[1]['players']}
check('Faqat Bek ball oldi (+15)', sc == {'Ali': 0, 'Bek': 15, 'Sam': 0}, sc)

print('\n=== O\'yinchi chiqib ketsa ===')
req('post', f'/api/games/rooms/{code3}/leave', sam)
req('post', f'/api/games/rooms/{code3}/leave', bek)
s, d = st(ali, code3)
check('Bitta o\'yinchi qoldi -> o\'yin tugadi (players_left)', d['status'] == 'finished' and d['session']['end_reason'] == 'players_left', (d['status'], d['session'].get('end_reason')))
res = d['session']['results']
check("Chiqib ketganlar natijada yo'q, qolgan Ali 1-o'rin", [r['name'] for r in res['rows']] == ['Ali'] and res['rows'][0]['rank'] == 1, res['rows'])
check("Qolgan Ali +30 chaqmoq", res['me']['chaqmoq'] == 30, res['me'])

print('\n=== Memory / Match ===')
s, d = req('post', '/api/games/rooms', ali, json={'game': 'memory_match', 'subject': 'history', 'count': 5, 'max_players': 2})
code4 = d['code']
check('Match: count=15 ruxsat etilmaydi', req('post', f'/api/games/rooms/{code4}/settings', ali, json={'count': 15})[0] == 400)
req('post', '/api/games/rooms/join', bek, json={'code': code4})
req('post', f'/api/games/rooms/{code4}/ready', bek, json={'ready': True})
req('post', f'/api/games/rooms/{code4}/start', ali)
adv(4100)
s, d = st(ali, code4)
pq = d['session']['question']
check('Match savoli: 4 chap, 4 o\'ng, javobsiz', pq['kind'] == 'match' and len(pq['left']) == 4 and len(pq['right']) == 4 and 'answer' not in pq, pq)
q = correct_answer(code4, 0)
s, d = req('post', f'/api/games/rooms/{code4}/answer', bek, json={'q': 0, 'answer': [0, 0, 1, 2]})
check('Takroriy moslash -> 400', s == 400 and d['code'] == 'bad_answer', d)
partial = list(q['answer'])
partial[0], partial[1] = partial[1], partial[0]
req('post', f'/api/games/rooms/{code4}/answer', bek, json={'q': 0, 'answer': partial})
s, d = req('post', f'/api/games/rooms/{code4}/answer', ali, json={'q': 0, 'answer': q['answer']})
rv = d['state']['session']
sc = {p['name']: p['score'] for p in d['state']['players']}
check('Match: Ali to\'liq (+15), Bek qisman 2 juft (+4)', sc == {'Ali': 15, 'Bek': 4}, sc)
check('Match reveal: juftliklar va tushuntirishlar', rv['phase'] == 'reveal' and rv['reveal']['answer'] == q['answer'], rv.get('reveal'))

print('\n=== Oflayn raqib ===')
adv(4100); st(ali, code4)
adv(46000)
s, d = st(ali, code4)
check('Raqib 45 s yo\'q -> o\'yin yakunlandi', d['status'] == 'finished' and d['session']['end_reason'] == 'players_left', (d['status'], d['session'].get('end_reason')))

print('\n=== Matchmaking ===')
s, d = req('post', '/api/games/matchmaking', ali, json={'game': 'math_battle', 'subject': 'math', 'difficulty': 'orta', 'count': 5})
check('Ali qidiruvda', s == 200 and d['result'] == 'searching', d)
s, d = req('post', '/api/games/matchmaking', bek, json={'game': 'math_battle', 'subject': 'math', 'difficulty': 'qiyin', 'count': 5})
check('Boshqa qiyinlik — hali mos emas', d['result'] == 'searching', d)
adv(16000)
req('get', '/api/games/matchmaking', ali)
s, d = req('get', '/api/games/matchmaking', bek)
check('15 s dan keyin talab yumshadi -> topildi', d['result'] == 'matched' and len(d.get('code', '')) == 6, d)
mcode = d.get('code')
s, d = req('get', '/api/games/matchmaking', ali)
check('Ali ham o\'sha roomga', d['result'] == 'matched' and d['code'] == mcode, d)
s, d = st(ali, mcode)
check('Random room: 2 o\'yinchi, countdown, yopiq', d['status'] == 'playing' and len(d['players']) == 2 and d['source'] == 'random' and not d['settings']['is_public'], d)
check('Random room: uzoq kutgan (Ali) sozlamasi', d['settings']['difficulty'] == 'orta' and d['me']['host'], d['settings'])
s, d = req('post', '/api/games/matchmaking', sam, json={'game': 'word_battle', 'subject': 'english'})
s, d = req('delete', '/api/games/matchmaking', sam)
check('Qidiruvni bekor qilish', d['result'] == 'cancelled', d)
req('post', '/api/games/matchmaking', sam, json={'game': 'word_battle', 'subject': 'english'})
adv(91000)
s, d = req('get', '/api/games/matchmaking', sam)
check('90 s -> timeout', d['result'] == 'timeout', d)

print('\n=== Rate limit ===')
codes = [req('post', '/api/games/rooms', sam, json={'game': 'quiz_battle', 'subject': 'math'})[0] for _ in range(14)]
check('10 daqiqada 12 tadan ortiq room -> 429', codes.count(429) >= 1 and codes[0] == 200, codes)

print('\n=== Kunlik limit (600 ball) ===')
for i in range(4):
    s, d = req('post', '/api/games/rooms', dil, json={'game': 'math_battle', 'subject': 'math', 'count': 10, 'max_players': 2})
    cc = d['code']
    req('post', '/api/games/rooms/join', ali, json={'code': cc})
    req('post', f'/api/games/rooms/{cc}/ready', ali, json={'ready': True})
    s, d = req('post', f'/api/games/rooms/{cc}/start', dil)
    check(f'{i + 1}-o\'yin boshlandi', s == 200, d)
    for qi in range(10):
        adv(4100); st(ali, cc); st(dil, cc)
        q = correct_answer(cc, qi)
        req('post', f'/api/games/rooms/{cc}/answer', ali, json={'q': qi, 'answer': q['answer']})
        req('post', f'/api/games/rooms/{cc}/answer', dil, json={'q': qi, 'answer': wrong_of(q)})
    adv(4100); st(ali, cc)
s, d = req('get', '/api/games/me', ali)
conn = get_connection(); cur = conn.cursor()
cur.execute('SELECT COALESCE(SUM(xp),0) AS x FROM game_results WHERE user_id = %s AND created_ms >= %s', (ali['id'], clock.period_start_ms('day', T[0])))
today = int(cur.fetchone()['x']); cur.close(); conn.close()
check('Bugungi hisobga o\'tgan ball <= 600', today <= 600, today)
check('Limitga yetdi (600)', today == 600, today)

print('\n=== Muddat tugashi ===')
s, d = req('post', '/api/games/rooms', bek, json={'game': 'quiz_battle', 'subject': 'math', 'public': True})
old = d['code']
adv(21 * 60 * 1000)
s, d = req('post', '/api/games/rooms/join', sam, json={'code': old})
check('20 daqiqa harakatsiz room -> 410 room_expired', s == 410 and d['code'] == 'room_expired', d)

print(f'\n{"HAMMASI OK" if not fails else str(len(fails)) + " ta XATO: " + ", ".join(fails)}')
sys.exit(1 if fails else 0)
