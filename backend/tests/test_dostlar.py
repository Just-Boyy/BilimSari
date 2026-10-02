# -*- coding: utf-8 -*-
"""Do'stlar: qidiruv, so'rovlar, limitlar, reyting, lenta, o'yinga chaqirish, shikoyat, admin, o'chirish."""
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
import dostlar  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402

SENT = []


def fake_tg(method, payload):
    SENT.append((method, payload))
    return {'ok': True, 'result': {'message_id': 1}}


tgbot.tg_api = fake_tg
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


def mk(name, tg, username, onboarded=True):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, grade, telegram_id, username) "
             "VALUES (%s, %s, 'math', 7, %s, %s) RETURNING id", (name, onboarded, tg, username), True)[0]['id']
    return {'id': uid, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


def post(u, action, body):
    r = c.post('/api/friends/' + action, headers=u['h'], json=body)
    return r.status_code, r.get_json()


def get(u, path=''):
    r = c.get('/api/friends' + path, headers=u['h'])
    return r.get_json()


def last_text(chat_id):
    for m, p in reversed(SENT):
        if m == 'sendMessage' and str(p.get('chat_id')) == str(chat_id):
            return p
    return None


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
ali = mk('Ali Valiyev', 94001, 'ali_dost')
vali = mk('Vali Karimov', 94002, 'vali_k')
sami = mk('Sami', 94003, None)
yangi = mk('Onboard emas', 94004, 'yangi_u', onboarded=False)

print('— Qidiruv')
res = get(ali, '/search?q=vali')['results']
check('Ism bo\'yicha topadi', any(x['id'] == vali['id'] for x in res), res)
check("O'zi natijada yo'q", all(x['id'] != ali['id'] for x in get(ali, '/search?q=ali')['results']))
res = get(ali, '/search?q=@vali_k')['results']
check('@username bo\'yicha', len(res) == 1 and res[0]['id'] == vali['id'], res)
res = get(ali, f"/search?q={sami['id']}")['results']
check('ID bo\'yicha', len(res) == 1 and res[0]['id'] == sami['id'], res)
res = get(ali, f"/search?q=%23{sami['id']}")['results']
check('#ID bo\'yicha', len(res) == 1 and res[0]['id'] == sami['id'], res)
check("Onboarding tugatmagan chiqmaydi", not get(ali, '/search?q=Onboard')['results'])
raw = json.dumps(get(ali, '/search?q=vali'))
check("Qidiruvda telegram id/username chiqmaydi", '94002' not in raw and 'vali_k' not in raw, raw[:300])
check('Kirmagan — 401', c.get('/api/friends/search?q=ali').status_code == 401)

print('— So\'rovlar')
SENT.clear()
s, d = post(ali, 'request', {'user_id': vali['id']})
check("So'rov yuboriladi", s == 200 and d['state'] == 'outgoing' and d.get('request_id'), d)
req_id = d['request_id']
m = last_text(94002)
check("Valiga bot xabari (so'rov)", m and "do'stlik so'rovi" in m['text']
      and 'tab=sorovlar' in m['reply_markup']['inline_keyboard'][0][0]['web_app']['url'], m)
s, d = post(ali, 'request', {'user_id': vali['id']})
check('Takroriy so\'rov — xato', s == 400 and d['code'] == 'already', d)
s, d = post(ali, 'request', {'user_id': ali['id']})
check("O'ziga — xato", s == 400, d)
s, d = post(ali, 'request', {'user_id': 999999})
check("Yo'q o'quvchi — 404", s == 404, d)
ov = get(vali)
check("Valida kelgan so'rov", len(ov['incoming']) == 1 and ov['incoming'][0]['id'] == ali['id']
      and ov['incoming'][0]['request_id'] == req_id, ov)
check('Alida yuborilgan', len(get(ali)['outgoing']) == 1)
pr = c.get(f"/api/study/profile/{ali['id']}", headers=vali['h']).get_json()['profile']
check("Profilda holat: incoming", pr['friend']['state'] == 'incoming' and pr['friend']['request_id'] == req_id, pr['friend'])
s, d = post(sami, 'respond', {'request_id': req_id, 'accept': True})
check("Begona so'rovga javob bera olmaydi", s == 404, d)
SENT.clear()
s, d = post(vali, 'respond', {'request_id': req_id, 'accept': True})
check('Qabul qilinadi', s == 200 and d['state'] == 'friend', d)
check("Aliga bot xabari (qabul)", last_text(94001) and 'qabul qildi' in last_text(94001)['text'])
check('Endi do\'st (ikkala tomonda)', get(ali)['count'] == 1 and get(vali)['count'] == 1)
pr = c.get(f"/api/study/profile/{vali['id']}", headers=ali['h']).get_json()['profile']
check('Profilda: friend + friends_count', pr['friend']['state'] == 'friend' and pr['friends_count'] == 1, pr)
s, d = post(ali, 'request', {'user_id': vali['id']})
check("Do'stga yana so'rov — xato", s == 400 and d['code'] == 'already', d)

print('— Qarama-qarshi so\'rov (avto-qabul), rad, bekor')
post(sami, 'request', {'user_id': ali['id']})
s, d = post(ali, 'request', {'user_id': sami['id']})
check("Ikki tomon so'rov — darhol do'st", s == 200 and d['state'] == 'friend', d)
check('Ochiq so\'rov qolmaydi', not get(ali)['incoming'] and not get(sami)['outgoing'], (get(ali), get(sami)))
s, d = post(ali, 'remove', {'user_id': sami['id']})
check("Do'stlikdan chiqarish", s == 200 and get(ali)['count'] == 1, d)
_, d = post(sami, 'request', {'user_id': ali['id']})
s, d2 = post(ali, 'respond', {'request_id': d['request_id'], 'accept': False})
check('Rad etish', s == 200 and d2['state'] == 'none' and not get(ali)['incoming'], d2)
_, d = post(sami, 'request', {'user_id': ali['id']})
s, _ = post(sami, 'cancel', {'request_id': d['request_id']})
check('Bekor qilish', s == 200 and not get(ali)['incoming'] and not get(sami)['outgoing'])

print('— Limitlar')
conn = get_connection(); cur = conn.cursor()
ids = []
for i in range(dostlar.MAX_FRIENDS - 1):         # alida allaqachon 1 do'st (vali) bor
    cur.execute("INSERT INTO users (name, onboarded, grade) VALUES (%s, TRUE, 7) RETURNING id", (f'Test{i}',))
    ids.append(cur.fetchone()['id'])
for uid in ids:
    a, b = sorted((ali['id'], uid))
    cur.execute('INSERT INTO friendships (user_a, user_b, created_ms) VALUES (%s, %s, 1)', (a, b))
conn.commit(); cur.close(); conn.close()
check('50 ta do\'st', get(ali)['count'] == 50 and get(ali)['max'] == 50)
s, d = post(ali, 'request', {'user_id': sami['id']})
check("51-chi so'rov — limit", s == 400 and d['code'] == 'limit', d)
s, d = post(sami, 'request', {'user_id': ali['id']})
check("To'lgan o'quvchiga so'rov — limit", s == 400 and d['code'] == 'limit', d)
db('DELETE FROM friendships WHERE user_a IN ({0}) OR user_b IN ({0})'.format(','.join(map(str, ids))))
db('DELETE FROM users WHERE id IN ({})'.format(','.join(map(str, ids))))
# Kunlik limit
db("UPDATE friend_requests SET created_ms = %s WHERE from_id = %s", (dostlar.clock.now_ms(), sami['id']))
for i in range(dostlar.REQUESTS_PER_DAY):
    db("INSERT INTO friend_requests (from_id, to_id, status, created_ms) VALUES (%s, %s, 'cancelled', %s)",
       (sami['id'], vali['id'], dostlar.clock.now_ms()))
s, d = post(sami, 'request', {'user_id': vali['id']})
check("Kunlik so'rov limiti", s == 429 and d['code'] == 'limit', d)
db("DELETE FROM friend_requests WHERE from_id = %s", (sami['id'],))

print('— Reyting va lenta')
db("INSERT INTO user_progress (user_id, topic_id, status, completed_at) "
   "SELECT %s, id, %s, CURRENT_TIMESTAMP FROM topics ORDER BY id LIMIT 1", (vali['id'], dostlar.study.STATUS_COMPLETED))
db("INSERT INTO user_achievements (user_id, key, unlocked_ms, seen_ms) VALUES (%s, 'mavzu_1', %s, 1)",
   (vali['id'], dostlar.clock.now_ms()))
rows = get(ali, '/leaderboard')['rows']
check("Reyting: o'zi + do'stlari", sorted(r['id'] for r in rows) == sorted([ali['id'], vali['id']])
      and any(r['me'] for r in rows) and all('rank' in r and 'chaqmoq' in r for r in rows), rows)
check("Reytingda begona yo'q", all(r['id'] != sami['id'] for r in rows))
ev = get(ali, '/feed')['events']
check("Lenta: do'stning mavzusi", any(e['kind'] == 'mavzu' and 'mavzusini tugatdi' in e['text'] for e in ev), ev)
check('Lenta: do\'stning nishoni', any(e['kind'] == 'nishon' and e['user']['id'] == vali['id'] for e in ev), ev)
check("Lentada begona yo'q", all(e['user']['id'] in (vali['id'],) for e in ev), ev)

print('— O\'yinga chaqirish')
r = c.post('/api/games/rooms', headers=ali['h'], json={'game': 'quiz_battle', 'subject': 'math', 'difficulty': 'orta',
                                                       'count': 5, 'max_players': 4, 'public': False}).get_json()
code = r['code']
SENT.clear()
s, d = post(ali, 'invite', {'user_id': vali['id'], 'code': code})
m = last_text(94002)
check("Do'st chaqiriladi + bot xabari", s == 200 and d['sent'] is True and m and code in m['text']
      and m['reply_markup']['inline_keyboard'][0][0]['web_app']['url'].endswith('games.html?kod=' + code), (d, m))
s, d = post(ali, 'invite', {'user_id': vali['id'], 'code': code})
check('Qayta chaqirish — kuting', s == 429 and d['code'] == 'too_soon', d)
s, d = post(ali, 'invite', {'user_id': sami['id'], 'code': code})
check("Do'st bo'lmaganni chaqirib bo'lmaydi", s == 403, d)
s, d = post(sami, 'invite', {'user_id': ali['id'], 'code': code})
check("Roomda bo'lmagan chaqira olmaydi", s == 403, d)
s, d = post(ali, 'invite', {'user_id': vali['id'], 'code': 'ZZZZZZ'})
check("Yo'q room — xato", s == 409, d)
inv = get(vali, '/invites')['invites']
check('Valida chaqiruv ko\'rinadi', len(inv) == 1 and inv[0]['code'] == code and inv[0]['from']['id'] == ali['id'], inv)
check('Overview ichida ham', len(get(vali)['invites']) == 1)
c.post('/api/games/rooms/join', headers=vali['h'], json={'code': code})
check("Roomga kirgach chaqiruv yo'qoladi", not get(vali, '/invites')['invites'])
s, d = post(ali, 'invite', {'user_id': vali['id'], 'code': code})
check("Roomdagi do'stni chaqirib bo'lmaydi", s == 400 and d['code'] in ('already', 'too_soon'), d)

print('— Shikoyat va admin')
SENT.clear()
s, d = post(vali, 'report', {'user_id': sami['id'], 'reason': 'ism', 'note': 'yomon  ism'})
check('Shikoyat yuboriladi', s == 200 and d['ok'], d)
check('Adminga bot xabari', any('Shikoyat' in p.get('text', '') for _, p in SENT), SENT[-1:] )
s, d = post(vali, 'report', {'user_id': sami['id'], 'reason': 'ism'})
check('Takroriy ochiq shikoyat — xato', s == 400, d)
s, d = post(vali, 'report', {'user_id': sami['id'], 'reason': 'nimadir'})
check("Noto'g'ri sabab — xato", s == 400, d)
s, d = post(vali, 'report', {'user_id': vali['id'], 'reason': 'ism'})
check("O'ziga shikoyat — xato", s == 400, d)
check('Admin ro\'yxati: 401 tokensiz', c.get('/api/admin/reports').status_code == 401)
ar = c.get('/api/admin/reports', headers=ADM).get_json()
rep = [x for x in ar['reports'] if x['target_id'] == sami['id']]
check('Admin ko\'radi', ar['ok'] and ar['open'] >= 1 and rep and rep[0]['reason'] == 'Nomaqbul ism'
      and rep[0]['note'] == 'yomon ism' and rep[0]['reporter_id'] == vali['id'], ar)
ar = c.post(f"/api/admin/reports/{rep[0]['id']}/block", headers=ADM).get_json()
check("Bloklash: do'stlik yopiladi", ar['ok'] and any(b['id'] == sami['id'] for b in ar['blocked']), ar)
s, d = post(sami, 'request', {'user_id': vali['id']})
check("Bloklangan so'rov yubora olmaydi", s == 403 and d['code'] == 'blocked', d)
check('Bloklangan qidiruvda chiqmaydi', not get(vali, '/search?q=Sami')['results'])
check('Audit jurnali', db("SELECT COUNT(*) AS n FROM admin_audit_log WHERE action = 'report_block'", (), True)[0]['n'] >= 1)
ar = c.post(f"/api/admin/reports/unblock/{sami['id']}", headers=ADM).get_json()
check('Qayta ochish', ar['ok'] and not any(b['id'] == sami['id'] for b in ar['blocked']))
check('Yana qidiruvda chiqadi', len(get(vali, '/search?q=Sami')['results']) == 1)
post(ali, 'report', {'user_id': sami['id'], 'reason': 'boshqa'})
rid = [x for x in c.get('/api/admin/reports', headers=ADM).get_json()['reports']
       if x['reporter_id'] == ali['id'] and x['status'] == 'open'][0]['id']
ar = c.post(f'/api/admin/reports/{rid}/dismiss', headers=ADM).get_json()
check('Ko\'rib chiqildi (dismiss)', ar['ok'] and [x for x in ar['reports'] if x['id'] == rid][0]['status'] == 'resolved', ar)
check('Qayta hal qilib bo\'lmaydi', c.post(f'/api/admin/reports/{rid}/block', headers=ADM).status_code in (400, 404))

print('— O\'chirish va sahifalar')
post(sami, 'request', {'user_id': vali['id']})
r = c.delete(f"/api/admin/users/{sami['id']}", headers=ADM)
if r.status_code == 405:
    r = c.post(f"/api/admin/users/{sami['id']}/delete", headers=ADM)
check("Foydalanuvchi o'chirildi", r.status_code == 200, r.get_json())
left = db('SELECT (SELECT COUNT(*) FROM friend_requests WHERE from_id = %s OR to_id = %s) + '
          '(SELECT COUNT(*) FROM user_reports WHERE reporter_id = %s OR target_id = %s) AS n',
          (sami['id'],) * 4, True)[0]['n']
check("O'chirilganda do'stlik yozuvlari tozalanadi", left == 0, left)
check('dostlar.html beriladi', c.get('/dostlar.html').status_code == 200)
check('last_seen_ms yoziladi (onlayn)', db('SELECT last_seen_ms FROM users WHERE id = %s', (ali['id'],), True)[0]['last_seen_ms'])
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
