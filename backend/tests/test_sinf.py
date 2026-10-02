# -*- coding: utf-8 -*-
"""1-bosqich: sinf tushunchasi saytdan olib tashlangan — API javoblarida, admin panelda, AI promptida."""
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
import ai_tutor  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402

tgbot.tg_api = lambda m, p: {'ok': True, 'result': {'message_id': 1}}
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


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
uid = db("INSERT INTO users (name, onboarded, grade, chosen_subject_key, telegram_id) VALUES ('Sinfsiz', TRUE, 7, 'math', 95001) RETURNING id",
         (), True)[0]['id']
H = {'Authorization': 'Bearer ' + create_token(uid)}

r = c.get('/api/admin/users', headers=ADM).get_json()
check("Admin: ro'yxatda sinf yo'q", r['ok'] and r['users'] and all('grade' not in u for u in r['users']), r['users'][:1])
r = c.get(f'/api/admin/users/{uid}', headers=ADM).get_json()
check("Admin: o'quvchi kartasida sinf yo'q", r['ok'] and 'grade' not in r['user'], r.get('user'))
check("Admin: sinf o'zgartirish yo'li yo'q", c.post(f'/api/admin/users/{uid}/grade', headers=ADM, json={'grade': 5}).status_code in (404, 405))
st = c.get('/api/admin/stats', headers=ADM).get_json()
check("Admin statistika: by_grade yo'q", st['ok'] and 'by_grade' not in st, list(st)[:30])
csv = c.get('/api/admin/users/export.csv', headers=ADM)
check("CSV: 'Sinf' ustuni yo'q", csv.status_code == 200 and 'Sinf' not in csv.get_data(as_text=True).splitlines()[0],
      (csv.status_code, csv.get_data(as_text=True)[:120]))

t = c.get('/api/admin/subjects/math/topics', headers=ADM).get_json()['topics']
check('Admin mavzular: ketma-ket raqam 1..N, sinf yo\'q', [x['seq'] for x in t] == list(range(1, len(t) + 1))
      and all('grade' not in x for x in t), t[:3])
ut = c.get(f'/api/admin/users/{uid}/topics/math', headers=ADM).get_json()
check("O'quvchi mavzulari: butun fan, ketma-ket", ut['ok'] and len(ut['topics']) == len(t)
      and [x['seq'] for x in ut['topics']] == list(range(1, len(t) + 1)), (len(ut.get('topics', [])), len(t)))
third = t[2]
tg = c.get(f"/api/admin/topics/{third['id']}", headers=ADM).get_json()
check("Dars tahriri: raqam 3, sinf yo'q", tg['ok'] and tg['topic']['seq'] == 3 and 'grade' not in tg['topic'], tg.get('topic', {}).get('seq'))

for lang in ('uz', 'ru', 'en'):
    p = ai_tutor._system_prompt(lang, 'Matematika', 'Kasrlar')
    check(f'AI prompt ({lang}): sinf tilga olinmaydi', 'sinf' not in p and 'класс' not in p and 'grade' not in p.lower(), p[:200])

prof = c.get(f'/api/study/profile/{uid}', headers=H).get_json()['profile']
check("Ochiq profilda sinf yo'q", 'grade' not in prof, list(prof))
g = c.get('/api/games/leaderboard?scope=grade', headers=H).get_json()
check("O'yinlar reytingi: sinf bo'yicha yo'q", g['ok'] and g['scope'] == 'global' and 'grade' not in g, g)

conn = get_connection(); cur = conn.cursor()
cur.execute("INSERT INTO ai_explanations (topic_id, mode, lang, reply, created_at) VALUES "
            "('x1', 'full', 'uz', 'Siz 7-sinf o''quvchisi sifatida...', '2026-09-01 10:00:00'), "
            "('x2', 'full', 'uz', 'Oddiy tushuntirish', '2026-09-01 10:00:00'), "
            "('x3', 'full', 'uz', 'Yangi 7-sinf', '2026-10-01 10:00:00')")
conn.commit()
ai_tutor.ensure_cache_table(cur, conn)
cur.execute("SELECT topic_id FROM ai_explanations WHERE topic_id IN ('x1', 'x2', 'x3') ORDER BY topic_id")
left = [r['topic_id'] for r in cur.fetchall()]
cur.close(); conn.close()
check("AI keshi: eski 'sinf'li javob o'chdi, boshqalari qoldi", left == ['x2', 'x3'], left)

for page in ('profile.html', 'foydalanuvchi.html', 'dostlar.html', 'admin.html', 'hamkor.html', 'js/games/hub.js'):
    body = c.get('/' + page).get_data(as_text=True)
    bad = [w for w in ("-sinf'", "-sinf<", 'Sinfim', 'sinfFiltr', 'sinfTanlov', 'Sinfdosh', 'sinfdosh') if w in body]
    check(f"{page}: sinf yozuvi yo'q", not bad, bad)
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
