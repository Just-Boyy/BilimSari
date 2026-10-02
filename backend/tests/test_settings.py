# -*- coding: utf-8 -*-
"""Sozlamalar testi: ism, rasm, Telegram qayta yozmasligi, avatar nishonlari."""
import base64
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
import telegram_auth  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402

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


def hdr(tok):
    return {'Authorization': 'Bearer ' + tok}


def post(path, tok, body):
    r = c.post(path, headers=hdr(tok), json=body)
    return r.status_code, (r.get_json() or {})


def user_row(uid):
    return db('SELECT name, photo_url, tg_photo_url, custom_name, custom_photo FROM users WHERE id = %s', (uid,), True)[0]


# Telegram orqali kirish: imzo tekshiruvini soxtalashtiramiz
A.BOT_TOKEN = 'test'
TG = {}
telegram_auth.validate_init_data = lambda init, token: dict(TG)


def tg_login(first, photo):
    TG.update({'telegram_id': 777001, 'first_name': first, 'last_name': 'Karimov', 'username': 'ali_k', 'photo_url': photo})
    r = c.post('/api/telegram/auth', json={'initData': 'x'})
    return r.get_json()


print('\n=== Telegram orqali kirish ===')
d = tg_login('Ali', 'https://t.me/p1.jpg')
uid, tok = d['user']['id'], d['token']
row = user_row(uid)
check('Yangi o\'quvchi: Telegram ismi va rasmi', row['name'] == 'Ali Karimov' and row['photo_url'] == row['tg_photo_url'] == 'https://t.me/p1.jpg', row)
d = tg_login('Alisher', 'https://t.me/p2.jpg')
row = user_row(uid)
check('O\'zgartirmagan bo\'lsa — Telegram bilan yangilanadi', row['name'] == 'Alisher Karimov' and row['photo_url'] == 'https://t.me/p2.jpg', row)

print('\n=== Ism ===')
for bad, why in (('A', 'qisqa'), ('x' * 41, 'uzun'), ('   ', 'bo\'sh')):
    s, r = post('/api/profile/name', tok, {'name': bad})
    check(f'Noto\'g\'ri ism ({why}) -> 400', s == 400, (s, r))
s, r = post('/api/profile/name', tok, {'name': '  Ali   Valiyev  '})
check('Ism saqlandi, bo\'shliqlar tozalandi', s == 200 and r['user']['name'] == 'Ali Valiyev' and user_row(uid)['custom_name'] == 1, (s, r))
d = tg_login('Alisher', 'https://t.me/p2.jpg')
check('Telegram orqali kirish o\'zgartirilgan ismni qayta yozmaydi', user_row(uid)['name'] == 'Ali Valiyev' and d['user']['name'] == 'Ali Valiyev', (user_row(uid), d['user']))

print('\n=== Rasm ===')
png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 64
jpg = b'\xff\xd8\xff\xe0' + b'\x11' * 64
url = lambda kind, raw: f'data:image/{kind};base64,' + base64.b64encode(raw).decode()  # noqa: E731
cases = [
    ('GIF formati', url('gif', b'GIF89a' + b'\x00' * 10)),
    ('base64 buzilgan', 'data:image/png;base64,@@@@'),
    ('Sarlavha mos emas (png deb jpg)', url('png', jpg)),
    ('Juda katta (>300 KB)', url('jpeg', b'\xff\xd8\xff' + b'\x00' * (310 * 1024))),
    ('Rasm yo\'q', None),
    ('Oddiy matn', 'salom'),
]
for name, img in cases:
    s, r = post('/api/profile/photo', tok, {'image': img})
    check(f'Rad etildi: {name}', s == 400 and r.get('code') == 'bad_photo', (s, r))
r = c.post('/api/profile/photo', headers=hdr(tok), json={'image': 'data:image/jpeg;base64,' + 'A' * (3 * 1024 * 1024)})
check('So\'rov hajmi > 2 MB -> 413', r.status_code == 413, r.status_code)

s, r = post('/api/profile/photo', tok, {'image': url('png', png)})
photo = r.get('photo_url') or ''
check('Rasm saqlandi', s == 200 and photo.startswith(f'/api/photo/{uid}?v='), (s, r))
row = user_row(uid)
check('users: custom_photo=1, Telegram rasmi alohida', row['custom_photo'] == 1 and row['photo_url'] == photo and row['tg_photo_url'] == 'https://t.me/p2.jpg', row)
g = c.get(photo)
check('Rasm beriladi: to\'g\'ri tur, baytlar, uzoq kesh', g.status_code == 200 and g.mimetype == 'image/png' and g.data == png
      and 'immutable' in g.headers.get('Cache-Control', ''), (g.status_code, g.mimetype, g.headers.get('Cache-Control')))
me = c.get('/api/me', headers=hdr(tok)).get_json()
check('/api/me: custom_photo', me['user']['custom_photo'] is True and me['user']['photo_url'] == photo, me['user'])
d = tg_login('Alisher', 'https://t.me/p3.jpg')
row = user_row(uid)
check('Telegram orqali kirish yuklangan rasmni qayta yozmaydi', row['photo_url'] == photo and d['user']['photo_url'] == photo and row['tg_photo_url'] == 'https://t.me/p3.jpg', (row, d['user']))
s, r = post('/api/profile/photo', tok, {'image': url('jpeg', jpg)})
check('Rasm almashtirildi (yangi URL)', s == 200 and r['photo_url'] != photo and c.get(r['photo_url']).data == jpg, r)
check('Bazada bitta rasm', db('SELECT COUNT(*) AS n FROM user_photos WHERE user_id = %s', (uid,), True)[0]['n'] == 1)
s, r = post('/api/profile/photo/remove', tok, {})
row = user_row(uid)
check('O\'chirildi -> Telegram rasmi qaytdi', s == 200 and r['photo_url'] == 'https://t.me/p3.jpg' and row['custom_photo'] == 0, (r, row))
check('Eski rasm manzili 404', c.get(photo).status_code == 404)
tg_login('Alisher', 'https://t.me/p4.jpg')
check('Keyin yana Telegram bilan yangilanadi', user_row(uid)['photo_url'] == 'https://t.me/p4.jpg', user_row(uid))
check('Kirishsiz yuklab bo\'lmaydi', c.post('/api/profile/photo', json={'image': url('png', png)}).status_code == 401)

print('\n=== Avatar nishonlari ===')
now = int(time.time() * 1000)
for i, k in enumerate(['mavzu_1', 'oyin_1', 'galaba_1', 'kun_1', 'streak_3', 'turnir_3', 'bot_qiyin']):
    db('INSERT INTO user_achievements (user_id, key, unlocked_ms, seen_ms) VALUES (%s, %s, %s, %s)', (uid, k, now - i, now))
r = c.get('/api/study/achievements', headers=hdr(tok)).get_json()
check('Boshida tanlanmagan (avtomatik)', r['pinned'] == [] and r['max_pinned'] == 6, r.get('pinned'))
s, r = post('/api/study/achievements/pin', tok, {'keys': ['kun_1', 'galaba_1', 'kun_1']})
check('Tanlandi (takror olib tashlandi)', s == 200 and r['pinned'] == ['kun_1', 'galaba_1'], (s, r))
r = c.get('/api/study/achievements', headers=hdr(tok)).get_json()
check('Ro\'yxatda tanlanganlar tartibi bilan', r['pinned'] == ['kun_1', 'galaba_1'], r['pinned'])
s, r = post('/api/study/achievements/pin', tok, {'keys': ['mavzu_100']})
check('Olinmagan nishon -> 400', s == 400 and r['code'] == 'not_unlocked', (s, r))
s, r = post('/api/study/achievements/pin', tok, {'keys': ['mavzu_1', 'oyin_1', 'galaba_1', 'kun_1', 'streak_3', 'turnir_3', 'bot_qiyin']})
check('7 ta -> 400', s == 400 and r['code'] == 'too_many', (s, r))
for bad in ('kun_1', [1, 2], None):
    s, r = post('/api/study/achievements/pin', tok, {'keys': bad})
    check(f'Noto\'g\'ri format ({bad!r}) -> 400', s == 400, (s, r))
s, r = post('/api/study/achievements/pin', tok, {'keys': []})
check('Bo\'sh ro\'yxat -> avtomatik rejim', s == 200 and c.get('/api/study/achievements', headers=hdr(tok)).get_json()['pinned'] == [], r)

print('\n=== Sahifa ===')
check('settings.html ochiladi', c.get('/settings.html').status_code == 200)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
