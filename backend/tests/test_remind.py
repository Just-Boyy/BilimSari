# -*- coding: utf-8 -*-
"""Eslatma vaqtini tanlash: API va har soatlik rejalashtiruvchi."""
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
import notify  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402
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


def mk(name, tg):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id) VALUES (%s, TRUE, 'math', %s) RETURNING id",
             (name, tg), True)[0]['id']
    return {'id': uid, 'tg': tg, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


def post(u, body):
    r = c.post('/api/profile/notify', headers=u['h'], json=body)
    return r.status_code, r.get_json() or {}


u17, u19, u7 = mk('Oydin', 7017), mk('Bobur', 7019), mk('Tong', 7007)

print('\n=== API ===')
me = c.get('/api/me', headers=u19['h']).get_json()
check('Standart vaqt 19:00', me['user']['remind_hour'] == 19, me['user'].get('remind_hour'))
s, d = post(u17, {'remind_hour': 17})
check('17:00 saqlandi', s == 200 and d['remind_hour'] == 17 and d['notify'] is True, d)
for bad in (5, 23, 'abc', None):
    s, d = post(u17, {'remind_hour': bad})
    check(f'Noto\'g\'ri soat ({bad!r}) -> 400', s == 400 and d.get('code') == 'bad_hour', (s, d))
s, d = post(u7, {'remind_hour': 7})
check('07:00 saqlandi', d['remind_hour'] == 7)
s, d = post(u17, {'on': False})
check('Faqat "on" yuborilsa soat o\'zgarmaydi', d['notify'] is False and d['remind_hour'] == 17, d)
s, d = post(u17, {'on': True})
check('Qayta yoqildi', d['notify'] is True and d['remind_hour'] == 17, d)
check('/api/me: tanlangan soat', c.get('/api/me', headers=u17['h']).get_json()['user']['remind_hour'] == 17)

print('\n=== Rejalashtiruvchi (har soat) ===')
sent = []
notify.send = lambda chat, text, button=None, path='': (sent.append((chat, text, path)) or (True, None))
notify.time = type('TezVaqt', (), {'sleep': staticmethod(lambda s: None)})()
day = clock.period_start_ms('day', int(time.time() * 1000))
at = lambda h, m=5: day + h * 3600 * 1000 + m * 60 * 1000   # noqa: E731
mine = lambda: sorted(x[0] for x in sent if x[0] in (7017, 7019, 7007))  # noqa: E731

notify.tick(at(6))
check('06:05 — hech kimga', mine() == [], sent)
notify.tick(at(17))
check('17:05 — faqat 17:00 ni tanlaganga', mine() == [7017], sent)
text17 = next(t for ch, t, p in sent if ch == 7017)
check('Kechki matn', 'bugun hali dars qilmadingiz' in text17, text17)
sent.clear()
notify.tick(at(17, 40))
check('Shu soatda ikkinchi marta yuborilmaydi', mine() == [], sent)
notify.tick(at(19))
check('19:05 — standart (19:00) dagilarga', mine() == [7019], sent)
sent.clear()
notify.tick(at(20))
check('Hech kimga ikki marta kelmaydi', mine() == [], sent)

# Ertasi kun: server 07:00 da ishlamagan — 08:30 da kechikib yuboriladi
day += 24 * 3600 * 1000
sent.clear()
notify.tick(at(8, 30))
check('Kechikkan eslatma (07:00 → 08:30)', 7007 in mine() and 7017 not in mine() and 7019 not in mine(), sent)
text7 = next(t for ch, t, p in sent if ch == 7007)
check('Ertalabki matn: "Xayrli tong"', text7.startswith('Xayrli tong'), text7)
sent.clear()
notify.tick(at(12))
check('07:00 ni tanlaganga 12:00 da yuborilmaydi (2 soatdan ko\'p kechikdi)', 7007 not in mine())

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
