# -*- coding: utf-8 -*-
"""6) Admin paneldan mavzu matni va test savollarini tahrirlash."""
import copy
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
import backup  # noqa: E402
import study  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402

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


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
db('DELETE FROM topic_overrides')
T = db("SELECT id, slug, grade FROM topics WHERE subject_key = 'math' ORDER BY grade, seq LIMIT 1", fetch=True)[0]
TID, SLUG, GRADE = T['id'], T['slug'], T['grade']
uid = db("INSERT INTO users (name, onboarded, grade, chosen_subject_key) VALUES ('Tahrir', TRUE, %s, 'math') RETURNING id",
         (GRADE,), True)[0]['id']
U = {'Authorization': 'Bearer ' + create_token(uid)}

r = c.get(f'/api/admin/topics/{TID}', headers=ADM).get_json()
check('Admin: mavzuni olish', r['ok'] and r['topic']['id'] == TID and not r['topic']['edited']
      and r['topic']['lesson'] and r['topic']['quiz'], r)
orig = r['topic']
check('Himoyalangan', c.get(f'/api/admin/topics/{TID}').status_code == 401
      and c.put(f'/api/admin/topics/{TID}', json={}).status_code == 401)

new = {k: copy.deepcopy(orig[k]) for k in ('title', 'summary', 'duration', 'lesson', 'quiz')}
new['title'] = 'Yangi sarlavha (tahrir)'
new['lesson'][0]['body'] = 'ADMIN YOZGAN MATN'
new['lesson'].append({'type': 'table', 'head': ['A', 'B'], 'rows': [['1', '2'], ['3', '4']]})
new['lesson'].append({'type': 'formula', 'body': 'a^2 + b^2 = c^2'})
new['quiz'] = [
    {'type': 'mc', 'q': 'Ikki karra ikki?', 'options': ['3', '4', '5'], 'answer': 1, 'explain': 'Chunki 4.'},
    {'type': 'tf', 'q': 'Yer yumaloq.', 'answer': True},
    {'type': 'fill', 'q': 'Besh qo\'shuv besh?', 'answer': '10', 'accept': ["o'n"]},
]
db("INSERT INTO ai_explanations (topic_id, mode, lang, reply) VALUES (%s, 'explain', 'uz', 'eski') ON CONFLICT DO NOTHING",
   (TID,))
r = c.put(f'/api/admin/topics/{TID}', headers=ADM, json=new).get_json()
check('Saqlash', r['ok'] and r['topic']['edited'] and r['topic']['title'] == 'Yangi sarlavha (tahrir)'
      and len(r['topic']['quiz']) == 3, r)
check('AI tushuntirish keshi tozalandi', not db('SELECT 1 FROM ai_explanations WHERE topic_id = %s', (TID,), True))

s = c.get(f'/api/study/topic/math/{SLUG}?grade={GRADE}', headers=U).get_json()
text = str(s)
check("O'quvchi yangi matnni ko'radi", s.get('ok') and 'ADMIN YOZGAN MATN' in text and 'Yangi sarlavha' in text
      and 'a^2 + b^2' in text, text[:500])
check("O'quvchiga to'g'ri javoblar ko'rinmaydi", "'answer'" not in str(s.get('quiz')) and len(s['quiz']) == 3, s.get('quiz'))
q = c.post('/api/study/quiz', headers=U, json={'grade': GRADE, 'subject_key': 'math', 'slug': SLUG,
                                               'answers': [1, True, "O'n"]}).get_json()
check('Test yangi javoblar bo\'yicha tekshiriladi (3/3)', q.get('ok') and q.get('correct') == 3
      or (q.get('ok') and all(x['correct'] for x in q.get('results', []))), q)

lst = c.get('/api/admin/subjects/math/topics', headers=ADM).get_json()['topics']
check("Ro'yxatda «Tahrirlangan» belgisi", next(t for t in lst if t['id'] == TID)['edited']
      and not any(t['edited'] for t in lst if t['id'] != TID))

# Kod qayta sinxronlansa ham tahrir saqlanadi
conn = get_connection(); cur = conn.cursor()
study.sync_curriculum(cur, conn, force=True)
cur.close(); conn.close()
row = db('SELECT title, lesson FROM topics WHERE id = %s', (TID,), True)[0]
check('Kod qayta yozilgandan keyin ham tahrir joyida', row['title'] == 'Yangi sarlavha (tahrir)'
      and 'ADMIN YOZGAN MATN' in str(row['lesson']), row['title'])

# Tekshiruv: noto'g'ri ma'lumot saqlanmaydi
bad_cases = [
    ('Bo\'sh sarlavha', dict(new, title='  '), 'Sarlavha'),
    ('Variantli savolda javob yo\'q', dict(new, quiz=[{'type': 'mc', 'q': 'x?', 'options': ['a', 'b'], 'answer': 5}]),
     "to'g'ri javobni"),
    ('Bitta variant', dict(new, quiz=[{'type': 'mc', 'q': 'x?', 'options': ['a'], 'answer': 0}]), '2–6'),
    ('Takror variant', dict(new, quiz=[{'type': 'mc', 'q': 'x?', 'options': ['a', 'A'], 'answer': 0}]), 'takrorlanmasin'),
    ("To'g'ri/Noto'g'ri tanlanmagan", dict(new, quiz=[{'type': 'tf', 'q': 'x?'}]), "To'g'ri"),
    ('Jadval qatori mos emas', dict(new, lesson=[{'type': 'table', 'head': ['A', 'B'], 'rows': [['1']]}]), '2 ta katak'),
    ("Bo'sh matn bloki", dict(new, lesson=[{'type': 'text', 'body': ''}]), "bo'sh"),
    ("Blok yo'q", dict(new, lesson=[]), 'blok'),
    ('Savol yo\'q', dict(new, quiz=[]), 'savol'),
    ("Noto'g'ri blok turi", dict(new, lesson=[{'type': 'video', 'body': 'x'}]), 'turi'),
    ('Davomiylik 0', dict(new, duration=0), 'Davomiylik'),
    ('Juda uzun matn', dict(new, lesson=[{'type': 'text', 'body': 'x' * 5000}]), 'uzun'),
]
for name, body, needle in bad_cases:
    rr = c.put(f'/api/admin/topics/{TID}', headers=ADM, json=body)
    check(f'Rad etiladi: {name}', rr.status_code == 400 and needle in rr.get_json()['error'], rr.get_json())
check('Xato saqlashdan keyin ham avvalgi tahrir joyida',
      db('SELECT title FROM topics WHERE id = %s', (TID,), True)[0]['title'] == 'Yangi sarlavha (tahrir)')
check("Yo'q mavzu — 400/404", c.put('/api/admin/topics/yoq-7-yoq', headers=ADM, json=new).status_code == 400
      and c.get('/api/admin/topics/yoq-7-yoq', headers=ADM).status_code == 404)

# Kun savoli: tahrirdan keyin indeks yo'q bo'lsa — 500 emas
from games import clock  # noqa: E402
import daily  # noqa: E402
day = daily.today(clock.now_ms())
db('DELETE FROM daily_questions WHERE day = %s', (day,))
db('INSERT INTO daily_questions (day, topic_id, q_index, created_ms) VALUES (%s, %s, 7, 0)', (day, TID))
rd = c.get('/api/study/daily', headers=U)
check("Kun savoli: savol o'chirilgan bo'lsa ham 500 emas", rd.status_code != 500, rd.status_code)
db('DELETE FROM daily_questions WHERE day = %s', (day,))

# Zaxira nusxaga tahrir kiradi
conn = get_connection(); cur = conn.cursor()
data = backup.dump(cur)
cur.close(); conn.close()
check('Zaxira nusxada topic_overrides bor', len(data['tables'].get('topic_overrides', {}).get('rows', [])) == 1)

# Asl holiga qaytarish
r = c.post(f'/api/admin/topics/{TID}/reset', headers=ADM).get_json()
check('Asl holiga qaytarish', r['ok'] and not r['topic']['edited'] and r['topic']['title'] == orig['title']
      and r['topic']['quiz'] == orig['quiz'] and r['topic']['lesson'] == orig['lesson'], r)
check("Tahrir yozuvi o'chdi", not db('SELECT 1 FROM topic_overrides', fetch=True))
conn = get_connection(); cur = conn.cursor()
study.sync_curriculum(cur, conn, force=True)
cur.close(); conn.close()
check('Qayta sinxronlashdan keyin ham asl matn', db('SELECT title FROM topics WHERE id = %s', (TID,), True)[0]['title']
      == orig['title'])
audit = [r['action'] for r in db('SELECT action FROM admin_audit_log ORDER BY id DESC LIMIT 5', fetch=True)]
check('Audit jurnalida tahrir va qaytarish', 'topic_edit' in audit and 'topic_reset' in audit, audit)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
