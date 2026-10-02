# -*- coding: utf-8 -*-
"""5) Batafsil statistika: faol o'quvchilar, qaytganlar, fanlar, do'kon konversiyasi, soatlar."""
import os
import sys
from datetime import datetime, timedelta, timezone

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import admin_auth  # noqa: E402
import analytics  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import TASHKENT_TZ, get_connection  # noqa: E402
from games import clock  # noqa: E402

c = A.app.test_client()
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:600]}'))
    if not cond:
        fails.append(name)


def db(sql, params=(), fetch=False):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall() if fetch else None
    conn.commit(); cur.close(); conn.close()
    return rows


# Toza jadvallar
for t in ('activity_days', 'user_progress', 'game_results', 'daily_answers', 'pay_orders', 'tokens', 'users'):
    db(f'DELETE FROM {t}')

NOW = datetime(2026, 9, 28, 15, 0, tzinfo=TASHKENT_TZ)
NOW_MS = int(NOW.timestamp() * 1000)
clock.now_ms = lambda: NOW_MS


def at(days_ago, hour=10):
    """Toshkent vaqti → (naive UTC datetime, ms)."""
    loc = (NOW - timedelta(days=days_ago)).replace(hour=hour, minute=0)
    return loc.astimezone(timezone.utc).replace(tzinfo=None), int(loc.timestamp() * 1000)


def user(name, days_ago, hour=10):
    utc, _ = at(days_ago, hour)
    return db('INSERT INTO users (name, onboarded, created_at) VALUES (%s, TRUE, %s) RETURNING id', (name, utc), True)[0]['id']


MATH = db("SELECT id FROM topics WHERE subject_key = 'math' ORDER BY grade, seq LIMIT 2", fetch=True)
BIO = db("SELECT id FROM topics WHERE subject_key = 'biology' ORDER BY grade, seq LIMIT 1", fetch=True)[0]['id']


def progress(uid, tid, days_ago, done=False, hour=10):
    utc, _ = at(days_ago, hour)
    db('INSERT INTO user_progress (user_id, topic_id, status, started_at, completed_at) VALUES (%s, %s, %s, %s, %s)',
       (uid, tid, 'completed' if done else 'in_progress', utc, utc if done else None))


# 10 kun oldin 4 kishi ro'yxatdan o'tdi: a ertasi kuni qaytdi, b 5-kuni, c va d qaytmadi
a, b, cc, d = (user(n, 10) for n in 'abcd')
progress(a, MATH[0]['id'], 9, done=True, hour=19)      # ertasi kuni, 19:00
progress(b, MATH[1]['id'], 5, hour=19)                 # 5 kundan keyin
# 3 kun oldin 2 kishi: e ertasi kuni o'yin o'ynadi, f kun savolini bugun ochdi
e, f = user('e', 3), user('f', 3)
_, ms = at(2, 20)
db("INSERT INTO game_results (session_id, room_id, user_id, game_type, subject, difficulty, score, earned, correct, wrong, "
   "total, accuracy, rank, players, created_ms) VALUES (1, 1, %s, 'quiz', 'biology', 'easy', 5, 5, 5, 0, 5, 100, 1, 1, %s)",
   (e, ms))
_, ms = at(0, 9)
db("INSERT INTO daily_answers (day, user_id, opened_ms) VALUES ('2026-09-28', %s, %s)", (f, ms))
progress(e, BIO, 1, done=True, hour=19)
# Bugun g ro'yxatdan o'tdi (ertasi kun hali kelmagan)
g = user('g', 0)
# Ilova ochilishi (activity_days): a bugun ilovani ochdi — dars qilmagan
c.get('/api/me', headers={'Authorization': 'Bearer ' + create_token(a)})
check("auth_required activity_days'ga yozadi (bir marta)",
      db('SELECT COUNT(*) AS n FROM activity_days WHERE user_id = %s', (a,), True)[0]['n'] == 1)
c.get('/api/me', headers={'Authorization': 'Bearer ' + create_token(a)})
check('Qayta so\'rov — qator qo\'shilmaydi', db('SELECT COUNT(*) AS n FROM activity_days', fetch=True)[0]['n'] == 1)
# Do'kon: a va b ochdi, b buyurtma berdi (rad), cc do'konni ochmay buyurtma berib to'ladi
c.get('/api/pay/shop', headers={'Authorization': 'Bearer ' + create_token(a)})
analytics.touch(b, analytics.SHOP)
_, ms = at(4)
db("INSERT INTO pay_orders (code, user_id, chat_id, items, base_amount, amount, status, created_ms, method) "
   "VALUES ('BS-1', %s, 0, '[]', 1, 1, 'rejected', %s, 'card')", (b, ms))
db("INSERT INTO pay_orders (code, user_id, chat_id, items, base_amount, amount, status, created_ms, method) "
   "VALUES ('BS-2', %s, 0, '[]', 1, 1, 'approved', %s, 'card')", (cc, ms))

ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
r = c.get('/api/admin/stats/detail?days=30', headers=ADM).get_json()
check('Endpoint ishlaydi', r['ok'] and r['days'] == 30 and len(r['dau']) == 30, r)
dau = {p['date']: p['n'] for p in r['dau']}
check('10 kun oldin 4 ta faol (ro\'yxatdan o\'tish)', dau['2026-09-18'] == 4, dau)
check('9 kun oldin 1 ta (a qaytdi)', dau['2026-09-19'] == 1, dau)
# bugun: a (ilova), f (kun savoli), g (ro'yxat) = 3
check('Bugun faol = 3 (ilova ochish + kun savoli + yangi)', r['dau_today'] == 3, r['dau_today'])
check("7 kunda faol: a,b?,e,f,g,cc(buyurtma)", r['wau'] == 6, r['wau'])
ret = r['retention']
# D1: 18-sentabr kogortasi (4) → 1 qaytdi; 25-sentabr (2) → e qaytdi (26-da o'yin); bugungi g — hisoblanmaydi
check('Ertasi kuni qaytgan: 2/6 = 33%', ret['d1_base'] == 6 and ret['d1'] == 33, ret)
# D7: faqat 18-sentabr kogortasi (7 kun o'tgan): a (19), b (23), cc (24 - buyurtma) → 3/4
check('7 kun ichida qaytgan: 3/4 = 75%', ret['d7_base'] == 4 and ret['d7'] == 75, ret)
coh = {x['date']: x for x in r['cohorts']}
check('Bugungi kogorta — "hali erta" (None)', coh['2026-09-28']['d1'] is None and coh['2026-09-28']['signups'] == 1, coh)
subj = {s['key']: s for s in r['subjects']}
check('Fanlar: matematika 2 o\'quvchi, 1 mavzu; biologiya 1 o\'quvchi, 1 mavzu, 1 o\'yin',
      subj['math']['learners'] == 2 and subj['math']['completed'] == 1 and subj['biology']['learners'] == 1
      and subj['biology']['completed'] == 1 and subj['biology']['games'] == 1, r['subjects'])
check('Fanlar saralangan (ko\'p o\'quvchi birinchi)', r['subjects'][0]['key'] == 'math')
fn = r['funnel']
check("Do'kon: 3 ochgan (a, b + buyurtma bergan cc), 2 buyurtma, 1 to'lagan → 33%",
      fn['visitors'] == 3 and fn['ordered'] == 2 and fn['paid'] == 1 and 'paid_stars' not in fn
      and fn['conversion'] == 33 and fn['shop_tracked_since'] == '2026-09-28', fn)
check('Faol soatlar: 19:00 eng ko\'p', r['hours'].index(max(r['hours'])) == 19 and sum(r['hours']) > 0, r['hours'])
r7 = c.get('/api/admin/stats/detail?days=7', headers=ADM).get_json()
check('7 kunlik davr', r7['days'] == 7 and len(r7['dau']) == 7 and r7['mau'] is None)
check("Noto'g'ri davr → 30", c.get('/api/admin/stats/detail?days=abc', headers=ADM).get_json()['days'] == 30)
check('Himoyalangan', c.get('/api/admin/stats/detail').status_code == 401)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
