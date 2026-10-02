# -*- coding: utf-8 -*-
"""24 soatlik kutish har fanga alohida ekanini tekshiradi."""
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
import study  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection, utc_now  # noqa: E402
from games import clock  # noqa: E402

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


def with_cur(fn):
    conn = get_connection(); cur = conn.cursor()
    try:
        return fn(cur, conn)
    finally:
        cur.close(); conn.close()


def topics_of(subject):
    return [r['id'] for r in db('SELECT id FROM topics WHERE subject_key = %s ORDER BY grade, seq', (subject,), True)]


def complete(uid, topic_id, when):
    db('DELETE FROM user_progress WHERE user_id = %s AND topic_id = %s', (uid, topic_id))
    db("INSERT INTO user_progress (user_id, topic_id, status, started_at, completed_at, lesson_read, quiz_passed, homework_status) "
       "VALUES (%s, %s, 'completed', %s, %s, 1, 1, 'passed')", (uid, topic_id, when, when))


def ready_to_complete(uid, topic_id):
    """Dars o'qilgan, test va uy ishi topshirilgan — faqat yakunlash qoldi."""
    db('DELETE FROM user_progress WHERE user_id = %s AND topic_id = %s', (uid, topic_id))
    db("INSERT INTO user_progress (user_id, topic_id, status, started_at, lesson_read, quiz_passed, homework_status) "
       "VALUES (%s, %s, 'in_progress', %s, 1, 1, 'passed')", (uid, topic_id, utc_now()))


uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id) VALUES ('Ali Valiyev', TRUE, 'math', 5501) RETURNING id",
         fetch=True)[0]['id']
db("INSERT INTO subject_purchases (user_id, subject_key) VALUES (%s, 'english')", (uid,))
H = {'Authorization': 'Bearer ' + create_token(uid)}
get = lambda p: (lambda r: (r.status_code, r.get_json() or {}))(c.get(p, headers=H))  # noqa: E731
MATH, ENG = topics_of('math'), topics_of('english')

print('\n=== Matematikada mavzu tugatildi ===')
complete(uid, MATH[0], utc_now())
s, d = get('/api/study/topics/math')
check('Matematika: 2-mavzu kutishda, kutish faol', d['topics'][1]['state'] == 'cooldown' and d['cooldown']['active'], d.get('cooldown'))
s, d = get('/api/study/topics/english')
check('Ingliz tili: kutish YO\'Q, 1-mavzu ochiq', d['topics'][0]['state'] == 'current' and not d['cooldown']['active'], d.get('cooldown'))
s, d = get('/api/study/subjects')
st = {x['key']: (x['current_topic'] or {}).get('state') for x in d['subjects'] if not x['locked']}
check('Fanlar ro\'yxati: math kutishda, english ochiq', st == {'math': 'cooldown', 'english': 'current'}, st)
s, d = get('/api/study/cooldown?subject=english')
check('/cooldown?subject=english — faol emas', s == 200 and not d['cooldown']['active'], d)
s, d = get('/api/study/cooldown?subject=math')
check('/cooldown?subject=math — faol', d['cooldown']['active'], d)

print('\n=== Shu kuni boshqa fanda mavzu tugatish ===')
ready_to_complete(uid, ENG[0])
res = with_cur(lambda cur, conn: study._try_complete(cur, conn, uid, ENG[0]))
check('Ingliz tilida ham mavzu yakunlandi', res and res.get('completed'), res)
s, d = get('/api/study/topics/english')
check('Endi ingliz tilida ham kutish', d['topics'][1]['state'] == 'cooldown' and d['cooldown']['active'])

print('\n=== Bitta fanda ikkinchi mavzu — to\'siladi ===')
ready_to_complete(uid, ENG[1])
res = with_cur(lambda cur, conn: study._try_complete(cur, conn, uid, ENG[1]))
check('Ingliz tilida 2-mavzu shu kuni yakunlanmaydi', res and res.get('blocked_by_cooldown') and 'Bu fanda' in res['message'], res)
db('DELETE FROM user_progress WHERE user_id = %s AND topic_id = %s', (uid, ENG[1]))
t2 = db('SELECT slug, grade FROM topics WHERE id = %s', (MATH[1],), True)[0]
s, d = get(f"/api/study/topic/math/{t2['slug']}?grade={t2['grade']}")
check('Matematika 2-mavzusini ochib bo\'lmaydi (403, fanga oid xabar)', s == 403 and d['code'] == 'cooldown'
      and 'Bu fanda' in d['error'] and 'boshqa fanlarni' in d['error'], (s, d.get('error')))

print('\n=== Eslatmalar ===')
sent = []
notify.send = lambda chat, text, button=None, path='': (sent.append((chat, text, path)) or (True, None))
notify.time = type('TezVaqt', (), {'sleep': staticmethod(lambda s: None)})()
now = utc_now()
complete(uid, MATH[0], now - timedelta(hours=24, minutes=10))
complete(uid, ENG[0], now - timedelta(hours=2))
with_cur(lambda cur, conn: notify.cooldown_ready(cur, conn, int(time.time() * 1000)))
check('Faqat Matematika uchun "keyingi mavzu ochildi"', len(sent) == 1 and 'Matematika' in sent[0][1]
      and sent[0][2] == 'topics.html?fan=math', sent)
sent.clear()
with_cur(lambda cur, conn: notify.cooldown_ready(cur, conn, int(time.time() * 1000)))
check('Takror yuborilmaydi', not sent, sent)

# Kunlik eslatma: soat 20:00 (Toshkent). Ikkala fan kutishda bo'lsa — yuborilmaydi
day_start = clock.period_start_ms('day', int(time.time() * 1000))
evening = day_start + 20 * 3600 * 1000
yest = notify._utc(day_start - 2 * 3600 * 1000)          # kecha 22:00 — 22 soat oldin
complete(uid, MATH[0], yest)
complete(uid, ENG[0], yest)
db("DELETE FROM notify_log WHERE kind = 'daily'")
sent.clear()
with_cur(lambda cur, conn: notify.daily_reminders(cur, conn, evening))
check('Barcha fanlari kutishda — kunlik eslatma yo\'q', not any(x[0] == 5501 for x in sent), sent)
complete(uid, ENG[0], notify._utc(day_start - 10 * 3600 * 1000))   # 30 soat oldin — ingliz tili ochiq
db("DELETE FROM notify_log WHERE kind = 'daily'")
sent.clear()
with_cur(lambda cur, conn: notify.daily_reminders(cur, conn, evening))
check('Bitta fan ochiq — kunlik eslatma yuboriladi', any(x[0] == 5501 for x in sent), sent)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
