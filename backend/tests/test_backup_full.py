# -*- coding: utf-8 -*-
"""To'liq zaxira: yuklab olish (faqat parol bilan), barcha jadvallar, yangi bazaga tiklash."""
import os
import subprocess
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import admin_auth  # noqa: E402
import backup  # noqa: E402
from db import get_connection  # noqa: E402

c = A.app.test_client()
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:400]}'))
    if not cond:
        fails.append(name)


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
PW = admin_auth.ADMIN_PASSWORD
check('Test muhitida admin paroli bor', bool(PW), 'ADMIN_PASSWORD kerak')

r = c.post('/api/admin/backup/download', json={'password': PW})
check('Tokensiz — 401', r.status_code == 401, r.status_code)
r = c.post('/api/admin/backup/download', headers=ADM, json={'password': 'xato'})
check("Noto'g'ri parol — 403", r.status_code == 403, r.status_code)
r = c.post('/api/admin/backup/download', headers=ADM, json={'password': PW})
check('Parol bilan — fayl (gzip)', r.status_code == 200 and r.mimetype == 'application/gzip'
      and 'bilimsari-toliq-' in r.headers.get('Content-Disposition', ''), (r.status_code, r.headers))
data = backup.unpack(r.data)
conn = get_connection(); cur = conn.cursor()
src = {}
for t in backup.table_names(cur):
    cur.execute(f'SELECT COUNT(*) AS n FROM {t}')
    src[t] = int(cur.fetchone()['n'])
cur.close(); conn.close()
# Yuklab olish zaxira tayyor bo'lgandan keyin admin jurnaliga "backup_download" yozadi — o'sha qator zaxirada yo'q
src['admin_audit_log'] -= 1
check("Hech bir jadval tashlab ketilmagan (topics, tokens ham bor)", set(data['tables']) == set(src) and data['skipped'] == []
      and 'topics' in data['tables'] and 'tokens' in data['tables'], (set(src) - set(data['tables']), data['skipped']))
check("Har bir jadvaldagi qatorlar soni mos", all(len(data['tables'][t]['rows']) == n for t, n in src.items()),
      {t: (n, len(data['tables'][t]['rows'])) for t, n in src.items() if len(data['tables'][t]['rows']) != n})
print('     jadvallar:', len(src), '| qatorlar:', sum(src.values()), '| hajm:', len(r.data), 'bayt')

# Yangi bo'sh bazaga tiklash (alohida jarayonda — yangi SQLite fayl)
import tempfile  # noqa: E402
_TMP = tempfile.mkdtemp(prefix='bilimsari-backup-test-')
out = os.path.join(_TMP, 'r_restore_full.db')
blob = os.path.join(_TMP, 'r_full_backup.json.gz')
open(blob, 'wb').write(r.data)
if os.path.exists(out):
    os.remove(out)
code = f'''
import os, sys, json
sys.path.insert(0, {BACKEND!r}); os.chdir({BACKEND!r})
import app, backup
from db import get_connection
data = backup.unpack(open({blob!r}, 'rb').read())
conn = get_connection(); cur = conn.cursor()
backup.restore(cur, conn, data, replace=True)
res = {{}}
for t in data['tables']:
    try:
        cur.execute('SELECT COUNT(*) AS n FROM ' + t); res[t] = int(cur.fetchone()['n'])
    except Exception as e:
        conn.rollback(); res[t] = -1
print('JSON' + json.dumps(res))
'''
env = dict(os.environ, SQLITE_PATH=out, DATABASE_URL='', FLASK_SKIP_DOTENV='1', SCHEDULER_ENABLED='0', PYTHONIOENCODING='utf-8')
p = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, env=env, encoding='utf-8')
line = [x for x in p.stdout.splitlines() if x.startswith('JSON')]
import json  # noqa: E402
got = json.loads(line[0][4:]) if line else {}
check("Yangi bazaga tiklandi", bool(got), p.stderr[-600:])
diff = {t: (src.get(t), got.get(t)) for t in src if t in got and got[t] != src[t]}
# Tiklashda init_db o'zi yaratgan qatorlar (masalan, sozlamalar) bo'lishi mumkin — faqat kamayishni xato hisoblaymiz
kam = {t: v for t, v in diff.items() if v[1] < v[0]}
check("Tiklangan bazada hech bir jadvalda qator kam emas", not kam, kam)
check("Asosiy jadvallar aynan mos (users, pay_orders, user_progress, premium_log, partner_earnings)",
      all(got.get(t) == src.get(t) for t in ('users', 'pay_orders', 'user_progress', 'premium_log', 'partner_earnings')),
      {t: (src.get(t), got.get(t)) for t in ('users', 'pay_orders', 'user_progress', 'premium_log', 'partner_earnings')})
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
