# -*- coding: utf-8 -*-
"""7) zaxira nusxa + tiklash, 8) xato xabarlari (Stars balansi olib tashlangan)."""
import gzip
import json
import logging
import os
import sys
import time
from datetime import datetime

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import admin_api  # noqa: E402
import admin_auth  # noqa: E402
import alerts  # noqa: E402
import backup  # noqa: E402
import notify  # noqa: E402
import payments  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import TASHKENT_TZ, get_connection  # noqa: E402

c = A.app.test_client()
fails = []
OWNER = 5771496552
CALLS, UPLOADS = [], []
STAR = {'balance': 0, 'txs': []}


def fake_tg(method, payload):
    CALLS.append((method, payload))
    if method == 'getMyStarBalance':
        return {'ok': True, 'result': {'amount': STAR['balance'], 'nanostar_amount': 0}}
    if method == 'getStarTransactions':
        off, lim = payload['offset'], payload['limit']
        return {'ok': True, 'result': {'transactions': STAR['txs'][off:off + lim]}}
    return {'ok': True, 'result': {'message_id': 1}}


def fake_upload(method, data, files, timeout=120):
    name, fh, mime = files['document']
    UPLOADS.append({'method': method, 'data': data, 'name': name, 'blob': fh.read()})
    return {'ok': True, 'result': {'message_id': 2}}


tgbot.tg_api = fake_tg
tgbot.tg_upload = fake_upload
admin_api.BOT_TOKEN = 'test'


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


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
db('DELETE FROM error_log')

# ─────────────────────────────────────────────
print('=== 8) Xato xabarlari ===')
def xato(tag):
    try:
        1 / 0
    except ZeroDivisionError:
        logging.getLogger('bilimsari.sinov').exception('Sinov xatosi %s', tag)


CALLS.clear()
xato('A')
alerts.flush()
owner_msgs = [p for m, p in CALLS if m == 'sendMessage' and p['chat_id'] == OWNER]
check('Egaga "Serverda xato" xabari', len(owner_msgs) == 1 and 'Serverda xato' in owner_msgs[0]['text']
      and 'ZeroDivisionError' in owner_msgs[0]['text'], CALLS)
rows = db('SELECT * FROM error_log', fetch=True)
check('error_log ga yozildi (trace bilan)', len(rows) == 1 and 'ZeroDivisionError' in rows[0]['trace']
      and rows[0]['notified'] == 1, rows)

CALLS.clear()
xato('B')
alerts.flush()
check('Bir xil xato 30 daqiqada qayta xabar qilinmaydi (lekin jurnalda bor)',
      not [1 for m, p in CALLS if m == 'sendMessage'] and len(db('SELECT id FROM error_log', fetch=True)) == 2)

# Flask so'rovidagi kutilmagan xato
orig = A.app.view_functions['health']
A.app.view_functions['health'] = lambda: {}['yoq']
CALLS.clear()
r = c.get('/api/health')
A.app.view_functions['health'] = orig
alerts.flush()
msgs = [p['text'] for m, p in CALLS if m == 'sendMessage']
check("So'rovdagi kutilmagan xato: 500 va xabarda so'rov yo'li", r.status_code == 500 and msgs
      and 'GET /api/health' in msgs[0] and 'KeyError' in msgs[0], msgs)

# Ogohlantirish (WARNING) — xabar yo'q
CALLS.clear()
logging.getLogger('bilimsari.sinov').warning('shunchaki ogohlantirish')
alerts.flush()
check('WARNING xabar qilinmaydi', not CALLS)

# O'z oqimidagi xato qayta navbatga tushmaydi (aylanib qolmaydi)
def bad_tg(method, payload):
    raise RuntimeError('telegram ishlamayapti')
tgbot.tg_api = bad_tg
try:
    raise ValueError('boshqa xato')
except ValueError:
    logging.getLogger('bilimsari.sinov2').exception('Boshqa')
alerts.flush()
tgbot.tg_api = fake_tg
n_before = len(db('SELECT id FROM error_log', fetch=True))
alerts.flush()
check("Telegram ishlamasa ham aylanib qolmaydi", n_before == 4, n_before)

r = c.get('/api/admin/system', headers=ADM).get_json()
check('Admin: /system — xatolar va sonlar', r['ok'] and len(r['errors']) == 4 and r['error_counts']['day'] == 4
      and r['errors'][0]['source'].startswith('bilimsari.sinov2'), r)
CALLS.clear()
r = c.post('/api/admin/errors/test', headers=ADM).get_json()
check('Admin: sinov xabari', r['ok'] and r['sent'] == 1 and 'Sinov xabari' in CALLS[-1][1]['text'], r)
check('Admin: /system himoyalangan', c.get('/api/admin/system').status_code == 401)
r = c.post('/api/admin/errors/clear', headers=ADM).get_json()
check('Admin: jurnalni tozalash', r['ok'] and not db('SELECT id FROM error_log', fetch=True))

# ─────────────────────────────────────────────
print('\n=== 7) Zaxira nusxa ===')
uid = db("INSERT INTO users (name, onboarded, telegram_id) VALUES ('Zaxira Test', TRUE, 99001) RETURNING id",
         fetch=True)[0]['id']
create_token(uid)
db("INSERT INTO user_photos (user_id, mime, data, updated_ms) VALUES (%s, 'image/jpeg', 'QUJD', 1) "
   "ON CONFLICT (user_id) DO NOTHING", (uid,))
counts = {t: db(f'SELECT COUNT(*) AS n FROM {t}', fetch=True)[0]['n']
          for t in ('users', 'user_progress', 'pay_orders', 'user_achievements', 'daily_answers', 'user_photos')}

UPLOADS.clear()
r = c.post('/api/admin/backup', headers=ADM).get_json()
check('Admin: "Hozir zaxira olish" — fayl egaga yuborildi', r['ok'] and r['sent'] == 1 and len(UPLOADS) == 1
      and UPLOADS[0]['data']['chat_id'] == OWNER and UPLOADS[0]['name'].endswith('.json.gz'), r)
data = backup.unpack(UPLOADS[0]['blob'])
check('Nusxada kerakli jadvallar bor, tokenlar/darslar yo\'q',
      {'users', 'user_progress', 'pay_orders', 'user_photos', 'pay_settings'} <= set(data['tables'])
      and not {'tokens', 'topics', 'subjects', 'rate_hits'} & set(data['tables']), sorted(data['tables']))
check("Qatorlar soni to'g'ri", all(len(data['tables'][t]['rows']) == n for t, n in counts.items()),
      {t: len(data['tables'][t]['rows']) for t in counts})
check('Izohda o\'quvchilar soni', f"{counts['users']} o'quvchi" in UPLOADS[0]['data']['caption'])
h = c.get('/api/admin/system', headers=ADM).get_json()['backups']
check('backup_log: qo\'lda, yuborilgan', h and h[0]['origin'] == 'manual' and h[0]['sent'] == 1
      and h[0]['row_count'] == r['rows'], h)

# Tiklash: yangi bo'sh bazaga
old_path = os.environ.get('SQLITE_PATH')
import tempfile  # noqa: E402
new_path = os.path.join(tempfile.mkdtemp(prefix='bilimsari-restore-test-'), 'restore_test.db')
for suffix in ('', '-wal', '-shm'):
    if os.path.exists(new_path + suffix):
        os.remove(new_path + suffix)
os.environ['SQLITE_PATH'] = new_path
A._init_db()
conn = get_connection(); cur = conn.cursor()
written = backup.restore(cur, conn, data)
cur.close(); conn.close()
restored = {t: db(f'SELECT COUNT(*) AS n FROM {t}', fetch=True)[0]['n'] for t in counts}
check('Tiklangan bazada qatorlar soni bir xil', restored == counts, (restored, counts))
u = db('SELECT name, telegram_id FROM users WHERE id = %s', (uid,), True)
check("O'quvchi ma'lumoti tiklandi", u and u[0]['name'] == 'Zaxira Test' and int(u[0]['telegram_id']) == 99001, u)
check("Darslar kod'dan qayta yaratildi", db('SELECT COUNT(*) AS n FROM topics', fetch=True)[0]['n'] > 100)
conn = get_connection(); cur = conn.cursor()
again = backup.restore(cur, conn, data)
cur.close(); conn.close()
check('Qayta tiklash takrorlamaydi (ON CONFLICT)', sum(again.values()) == 0 and
      {t: db(f'SELECT COUNT(*) AS n FROM {t}', fetch=True)[0]['n'] for t in counts} == counts, again)
# Skript: --apply yo'q — hech narsa yozmaydi
bpath = os.path.join(os.path.dirname(new_path), 'backup_test.json.gz')
open(bpath, 'wb').write(UPLOADS[0]['blob'])
import subprocess  # noqa: E402
out = subprocess.run([sys.executable, 'scripts/restore_backup.py', bpath], capture_output=True, text=True,
                     env=dict(os.environ, DATABASE_URL='', PYTHONIOENCODING='utf-8'), encoding='utf-8')
check("restore_backup.py (ko'rish rejimi) ishlaydi", out.returncode == 0 and 'Hech narsa yozilmadi' in out.stdout,
      out.stdout + out.stderr)
out = subprocess.run([sys.executable, 'scripts/restore_backup.py', bpath, '--apply'], capture_output=True,
                     text=True, env=dict(os.environ, DATABASE_URL='', PYTHONIOENCODING='utf-8'), encoding='utf-8')
check("restore_backup.py --apply: o'quvchilar bor bazaga yozmaydi", out.returncode == 1
      and '--replace' in out.stdout, out.stdout + out.stderr)
os.environ['SQLITE_PATH'] = old_path

# Rejalashtiruvchi: 03:00 dan keyin kuniga bir marta
db("DELETE FROM job_runs WHERE job = 'backup'")
t = datetime(2026, 9, 29, 2, 50, tzinfo=TASHKENT_TZ)
UPLOADS.clear()
notify.tick(int(t.timestamp() * 1000))
check('02:50 da nusxa olinmaydi', not UPLOADS)
t = datetime(2026, 9, 29, 3, 1, tzinfo=TASHKENT_TZ)
notify.tick(int(t.timestamp() * 1000))
notify.tick(int(t.timestamp() * 1000) + 60_000)
check('03:01 da bitta avtomatik nusxa', len(UPLOADS) == 1 and '29.09.2026 03:01' in UPLOADS[0]['data']['caption'],
      [u['data']['caption'] for u in UPLOADS])

# Juda katta fayl — rasmlarsiz
old_limit = backup.TG_LIMIT
backup.TG_LIMIT = 10
conn = get_connection(); cur = conn.cursor()
blob, d2, note = backup.make(cur)
cur.close(); conn.close()
backup.TG_LIMIT = old_limit
check("Fayl juda katta bo'lsa — rasmlar tashlab yuboriladi", 'user_photos' not in d2['tables'] and note, note)

# ─────────────────────────────────────────────
print('\n=== 4) Stars balansi olib tashlangan ===')
check('/api/admin/pay/stars — 404', c.get('/api/admin/pay/stars', headers=ADM).status_code == 404)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
