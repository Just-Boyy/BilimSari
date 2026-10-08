# -*- coding: utf-8 -*-
"""Ommaviy xabarga rasm: admin rasm yuklaydi → birinchi o'quvchiga rasm Telegram'ga yuklanadi, qolganlarga
Telegram bergan file_id bilan (qayta yuklanmaydi); ruscha interfeysdagilarga ruscha izoh; cheklovlar."""
import base64
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
import broadcast  # noqa: E402
import tgbot  # noqa: E402
from db import get_connection  # noqa: E402

CALLS = []


def fake_api(method, payload):
    CALLS.append(('api', method, payload))
    return {'ok': True, 'result': {'message_id': len(CALLS)}}


def fake_upload(method, data, files, timeout=120):
    CALLS.append(('upload', method, data, files))
    return {'ok': True, 'result': {'message_id': len(CALLS), 'photo': [{'file_id': 'kichik'}, {'file_id': 'FILE_ID_1'}]}}


tgbot.tg_api = fake_api
tgbot.tg_upload = fake_upload
tgbot.BOT_TOKEN = tgbot.BOT_TOKEN or '123:TEST'
broadcast._spawn = broadcast.run          # testda fon oqimi o'rniga darhol
broadcast.PAUSE_S = 0
c = A.app.test_client()
ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:500]}'))
    if not cond:
        fails.append(name)


conn = get_connection()
cur = conn.cursor()
for i, lang in enumerate(['uz', 'uz', 'ru'], 1):
    cur.execute("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id, notify, lang) VALUES (%s, TRUE, 'math', %s, 1, %s)",
                (f'Odam{i}', 9800000 + i, lang))
conn.commit()
cur.close()
conn.close()

RASM = b'\x89PNG\r\n\x1a\n' + b'rasm-baytlari' * 50
DATA_URL = 'data:image/jpeg;base64,' + base64.b64encode(RASM).decode()

print('\n=== Rasmli xabar ===')
CALLS.clear()
r = c.post('/api/admin/broadcasts', headers=ADM, json={'text': 'Biz endi Instagramdamiz! 🎉', 'text_ru': 'Мы в Instagram! 🎉',
                                                     'photo': DATA_URL, 'segment': 'all'})
d = r.get_json()
check('Yaratildi va yuborildi', r.status_code == 200 and d['items'][0]['state'] == 'done' and d['items'][0]['sent'] == 3, d)
check('Tarixda rasm belgisi', d['items'][0].get('photo') is True)
up = [x for x in CALLS if x[0] == 'upload']
check('Rasm faqat bir marta yuklandi (birinchi o\'quvchiga)', len(up) == 1 and up[0][1] == 'sendPhoto'
      and up[0][3]['photo'][1] == RASM and up[0][2]['caption'] == 'Biz endi Instagramdamiz! 🎉', up)
qolgan = [x for x in CALLS if x[0] == 'api' and x[1] == 'sendPhoto']
check("Qolganlarga file_id bilan (qayta yuklanmaydi)", len(qolgan) == 2 and all(x[2]['photo'] == 'FILE_ID_1' for x in qolgan), qolgan)
check('Ruscha interfeysdagiga ruscha izoh', any(x[2]['caption'] == 'Мы в Instagram! 🎉' for x in qolgan), qolgan)
check("sendMessage ishlatilmadi", not [x for x in CALLS if x[1] == 'sendMessage'])
conn = get_connection()
cur = conn.cursor()
cur.execute('SELECT photo_id FROM broadcasts ORDER BY id DESC LIMIT 1')
check('file_id bazada saqlandi (worker qayta ishga tushsa ham qayta yuklanmaydi)', cur.fetchone()['photo_id'] == 'FILE_ID_1')
cur.close()
conn.close()

print('\n=== Tugma va formatlash rasm bilan ===')
CALLS.clear()
r = c.post('/api/admin/broadcasts', headers=ADM, json={'text': '<b>Yangi</b> video', 'html': True, 'photo': DATA_URL,
                                                     'button_text': 'Ochish', 'button_path': 'dashboard.html', 'segment': 'uz'})
up = [x for x in CALLS if x[0] == 'upload']
check('HTML va tugma rasmli xabarda ham bor', r.status_code == 200 and up and up[0][2].get('parse_mode') == 'HTML'
      and '"web_app"' in up[0][2].get('reply_markup', ''), up)

print('\n=== Faqat rasm (matnsiz) ===')
CALLS.clear()
r = c.post('/api/admin/broadcasts', headers=ADM, json={'text': '', 'photo': DATA_URL, 'segment': 'ru'})
check('Matnsiz rasm ham yuboriladi', r.status_code == 200 and r.get_json()['items'][0]['sent'] == 1, r.get_json())

print('\n=== Cheklovlar ===')
r = c.post('/api/admin/broadcasts', headers=ADM, json={'text': 'x' * 1100, 'photo': DATA_URL})
check('Rasm bilan 1024 dan uzun matn — 400', r.status_code == 400 and '1024' in r.get_json()['error'], r.get_json())
r = c.post('/api/admin/broadcasts', headers=ADM, json={'text': 'salom', 'photo': 'data:text/html;base64,PGh0bWw+'})
check("Rasm emas — 400", r.status_code == 400, r.get_json())
r = c.post('/api/admin/broadcasts', headers=ADM, json={'text': '', 'photo': ''})
check("Na matn, na rasm — 400", r.status_code == 400)

print('\n=== Oddiy (rasmsiz) xabar avvalgidek ===')
CALLS.clear()
r = c.post('/api/admin/broadcasts', headers=ADM, json={'text': 'Oddiy xabar', 'segment': 'all'})
check('sendMessage bilan ketdi', r.status_code == 200 and len([x for x in CALLS if x[1] == 'sendMessage']) == 3
      and not [x for x in CALLS if x[0] == 'upload'], CALLS[:2])

print('\n=== Admin panel ===')
html = open(os.path.join(BACKEND, 'admin.html'), encoding='utf-8').read()
check('Formada rasm tanlash, ko\'rinish va kichraytirish', 'id="xabarRasm"' in html and 'id="xabarRasmKorinish"' in html
      and "toDataURL('image/jpeg', 0.85)" in html and "photo: xabarRasm || ''" in html)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
sys.exit(1 if fails else 0)
