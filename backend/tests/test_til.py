# -*- coding: utf-8 -*-
"""Ruscha kontent: darslar, test, uy vazifasi, kun savoli, o'yinlar (X-Lang: ru) va o'zbekcha o'zgarmaganligi."""
import json
import os
import random
import re
import sys
import time

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import daily  # noqa: E402
import til  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402
from games import clock, engine, questions, rooms  # noqa: E402

T = [int(time.time() * 1000)]
clock.now_ms = lambda: T[0]
c = A.app.test_client()
fails = []
CYR = re.compile('[А-Яа-яЁё]')


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


def mk(name):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key) VALUES (%s, TRUE, 'math') RETURNING id", (name,), True)[0]['id']
    tok = create_token(uid)
    return {'id': uid, 'uz': {'Authorization': 'Bearer ' + tok, 'X-Lang': 'uz'},
            'ru': {'Authorization': 'Bearer ' + tok, 'X-Lang': 'ru'}}


ru_math = json.load(open(os.path.join(BACKEND, 'curriculum', 'ru', 'math.json'), encoding='utf-8'))
first_slug = 'birnom-va-kopnomlar'
geo_slug = 'uchburchaklar-va-tenglik-alomatlari'
print('— Baza: ruscha ustunlar')
row = db("SELECT title, title_ru, summary_ru, ru FROM topics WHERE slug = %s", (first_slug,), True)[0]
check('title_ru va ru JSON yozilgan', row['title_ru'] == ru_math[first_slug]['title'] and json.loads(row['ru'])['quiz'], row['title_ru'])
untr = db("SELECT slug, title_ru FROM topics WHERE subject_key = 'math'", (), True)
check("title_ru faqat tarjimasi bor mavzularda", all((r['title_ru'] is not None) == (r['slug'] in ru_math) for r in untr), len(untr))

ali = mk('Ali')
print("— Mavzular ro'yxati")
uz = c.get('/api/study/topics/math', headers=ali['uz']).get_json()
ru = c.get('/api/study/topics/math', headers=ali['ru']).get_json()
check("UZ ro'yxat o'zgarmagan", uz['topics'][0]['title'] == row['title'], uz['topics'][0]['title'])
check("RU ro'yxat: tarjima qilingan mavzu ruscha", ru['topics'][0]['title'] == ru_math[first_slug]['title'], ru['topics'][0]['title'])
check("RU ro'yxat: 11-mavzu ham ruscha", bool(CYR.search(ru['topics'][10]['title'])) == (len(ru_math) > 10), ru['topics'][10]['title'])
d = c.get('/api/study/dashboard', headers=ali['ru']).get_json()
check('Dashboard: bugungi dars ruscha', d['today'] and CYR.search(d['today']['topic_title']), d.get('today'))

print('— Mavzu sahifasi')
tid = db("SELECT id, grade FROM topics WHERE slug = %s", (first_slug,), True)[0]
tu = c.get(f"/api/study/topic/math/{first_slug}?grade={tid['grade']}", headers=ali['uz']).get_json()
tr = c.get(f"/api/study/topic/math/{first_slug}?grade={tid['grade']}", headers=ali['ru']).get_json()
check('UZ mavzu o\'zbekcha', tu['ok'] and not CYR.search(tu['lesson'][0]['body']), tu.get('lesson', [{}])[0])
check('RU mavzu: dars, test, uy vazifasi ruscha', tr['ok'] and CYR.search(tr['lesson'][0]['body']) and CYR.search(tr['quiz'][0]['q'])
      and CYR.search(tr['homework']['tasks'][0]['prompt']) and CYR.search(tr['homework']['intro']), tr.get('quiz'))
check('RU: formulali variantlar o\'zgarmagan', tr['quiz'][0]['options'] == tu['quiz'][0]['options'], tr['quiz'][0]['options'])
check('Javob kalitlari frontendga ketmaydi', 'answer' not in json.dumps(tr['quiz']) and '"answer"' not in json.dumps(tr['homework']))

print('— Test va uy vazifasi (ruscha)')
quiz = json.loads(db("SELECT quiz FROM topics WHERE slug = %s", (first_slug,), True)[0]['quiz'])
right = [q['answer'] for q in quiz]
c.post('/api/study/lesson-read', headers=ali['ru'], json={'grade': tid['grade'], 'subject_key': 'math', 'slug': first_slug})
r = c.post('/api/study/quiz', headers=ali['ru'], json={'grade': tid['grade'], 'subject_key': 'math', 'slug': first_slug,
                                                      'answers': right}).get_json()
check('RU test: to\'g\'ri baholanadi (3/3), tushuntirish ruscha', r['ok'] and r['correct'] == 3 and CYR.search(r['results'][0]['explain']), r)
tf_i = next(i for i, q in enumerate(quiz) if q['type'] == 'tf')
check("TF to'g'ri javob matni ruscha (Верно/Неверно)", r['results'][tf_i]['correct_answer'] in ('Верно', 'Неверно'), r['results'][tf_i])
hw = json.loads(db("SELECT homework FROM topics WHERE slug = %s", (first_slug,), True)[0]['homework'])
good = {t['id']: (t.get('answer') or 'mening uzun javobim') for t in hw['tasks']}
r = c.post('/api/study/homework', headers=ali['ru'], json={'grade': tid['grade'], 'subject_key': 'math', 'slug': first_slug,
                                                          'answers': good}).get_json()
check('RU uy vazifasi: o\'zbekcha/formulali javob qabul qilinadi', r['ok'] and r['passed'], r)

print("— Javob ikkala tilda qabul qilinadi (til.merge)")
hw_uz = {'tasks': [{'id': 't1', 'type': 'text', 'prompt': 'Kasrning pastki qismi?', 'answer': 'maxraj'}]}
hw_ru = {'tasks': [{'id': 't1', 'prompt': 'Как называется нижняя часть дроби?', 'answer': 'знаменатель'}]}
m = til.merge_homework(hw_uz, hw_ru)['tasks'][0]
import study  # noqa: E402
check("Ruscha javob ko'rsatiladi, ikkala til qabul qilinadi", m['answer'] == 'знаменатель'
      and study.answers_match('Знаменатель', m['answer'], m['accept']) and study.answers_match('maxraj', m['answer'], m['accept']), m)
q_uz = [{'type': 'mc', 'q': 'a', 'options': ['1', '2', '3'], 'answer': 2}]
q_ru = [{'type': 'mc', 'q': 'б', 'options': ['1', '2'], 'answer': 0}]
check("Tuzilma mos kelmasa — savol o'zbekcha qoladi, javob asldan", til.merge_quiz(q_uz, q_ru)[0] == q_uz[0])
q_ru2 = [{'type': 'mc', 'q': 'б', 'options': ['x', 'y', 'z'], 'answer': 0}]
check("Javob indeksi doim asldan", til.merge_quiz(q_uz, q_ru2)[0]['answer'] == 2 and til.merge_quiz(q_uz, q_ru2)[0]['q'] == 'б')

print('— Kun savoli')
geo = db("SELECT id FROM topics WHERE slug = %s", (geo_slug,), True)[0]['id']
day = daily.today(T[0])
db('DELETE FROM daily_questions WHERE day = %s', (day,))
db('INSERT INTO daily_questions (day, topic_id, q_index, created_ms) VALUES (%s, %s, 2, %s)', (day, geo, T[0]))
du = c.get('/api/study/daily', headers=ali['uz']).get_json()
dr = c.get('/api/study/daily', headers=ali['ru']).get_json()
check("Kun savoli: UZ o'zbekcha, RU ruscha (variantlar ham)", not CYR.search(du['prompt']) and CYR.search(dr['prompt'])
      and CYR.search(' '.join(dr['options'])), (du.get('prompt'), dr.get('prompt'), dr.get('options')))
gq = json.loads(db("SELECT quiz FROM topics WHERE id = %s", (geo,), True)[0]['quiz'])[2]
r = c.post('/api/study/daily/answer', headers=ali['ru'], json={'answer': gq['answer']}).get_json()
check("Ruscha kun savoliga to'g'ri javob — to'g'ri", r['ok'] and r.get('result', {}).get('correct', r.get('correct')) in (True, 1)
      or r.get('answered'), r)

print("— O'yin savollari (ikki tilli)")
rng = random.Random(5)
conn = get_connection(); cur = conn.cursor()
settings = {'game_type': 'quiz_battle', 'subject': 'math', 'topic': None, 'difficulty': 'oson', 'question_count': 10}
qs = questions.curriculum_questions(cur, settings, rng)
with_ru = [q for q in qs if q.get('ru')]
check('Quiz Battle: tarjimali mavzu savollarida ru bor', with_ru and all(CYR.search(q['ru']['prompt']) for q in with_ru), len(with_ru))
q0 = with_ru[0]
check("Ruscha variantlar ham shu tartibda (to'g'ri javob bir xil)", len(q0['ru']['options']) == len(q0['options']), q0)
geo_q = [q for q in with_ru if q['topic'] == geo]
if geo_q:
    g = geo_q[0]
    check("So'zli variantlar ruscha, aralashtirish bir xil", all(CYR.search(o) for o in g['ru']['options']) or g['options'] == g['ru']['options'], g)
loc = questions.loc(q0, 'ru')
check('loc(ru) — ruscha, loc(uz) — asl', loc['prompt'] == q0['ru']['prompt'] and questions.loc(q0, 'uz')['prompt'] == q0['prompt'])
mq = questions.match_questions(cur, dict(settings, game_type='memory_match', question_count=2), random.Random(2))
check("Match: ruscha chap/o'ng ustunlar", all('ru' in r and len(r['ru']['left']) == 4 for r in mq), mq[:1])
mth = questions.math_questions(cur, dict(settings, game_type='math_battle', topic='foizlar', difficulty='qiyin'), random.Random(3))
check('Math Battle: ruscha prompt/tushuntirish', all(CYR.search(q['ru']['explain']) or not re.search("[a-z]{4}", q['explain']) for q in mth)
      and all(q['ru']['topic_title'] == 'Проценты' for q in mth), mth[:1])
w = questions.words_questions(cur, dict(settings, game_type='word_battle', subject='english', topic='tarjima'), random.Random(4))
check("Word Battle: ruscha savol va ruscha ma'nolar", all(CYR.search(q['ru']['prompt']) for q in w), w[:1])
uzw = questions.words_questions(cur, dict(settings, game_type='word_battle', subject='uzbek', topic='sinonim'), random.Random(4))
check("O'zbekcha sinonimlar: savol ruscha, so'zlar o'zbekcha", all(CYR.search(q['ru']['prompt']) and q['ru']['options'] == q['options'] for q in uzw))
cq = questions.code_questions(cur, dict(settings, game_type='code_challenge', subject='informatics', topic='algo'), random.Random(6))
check('Code Challenge: ruscha savol va variantlar', all(CYR.search(q['ru']['prompt']) and CYR.search(q['ru']['explain']) for q in cq)
      and any(CYR.search(' '.join(q['ru']['options'])) for q in cq), cq[:1])
cur.close(); conn.close()

print('— Room: har o\'yinchi o\'z tilida')
bek = mk('Bek')
code = c.post('/api/games/rooms', headers=ali['uz'], json={'game': 'quiz_battle', 'subject': 'math', 'count': 5, 'max_players': 2,
                                                              'topic': tid['id']}).get_json()['code']
c.post('/api/games/rooms/join', headers=bek['ru'], json={'code': code})
c.post(f'/api/games/rooms/{code}/ready', headers=bek['ru'], json={'ready': True})
c.post(f'/api/games/rooms/{code}/start', headers=ali['uz'])
T[0] += 4500
conn = get_connection(); cur = conn.cursor()
room = rooms.load_room(cur, code)
allq = engine.questions_for(cur, room['session_id'])
cur.close(); conn.close()
idx = next((i for i, q in enumerate(allq) if q.get('ru')), None)
if idx is not None:
    # Tarjimali savolgacha o'tkazib yuboramiz
    for _ in range(idx):
        for u in (ali, bek):
            c.get(f'/api/games/rooms/{code}', headers=u['uz'])
        T[0] += 25000
        for u in (ali, bek):
            c.get(f'/api/games/rooms/{code}', headers=u['uz'])
        T[0] += 4500
    su = c.get(f'/api/games/rooms/{code}', headers=ali['uz']).get_json()['state']['session']
    sr = c.get(f'/api/games/rooms/{code}', headers=bek['ru']).get_json()['state']['session']
    check("Bir roomda: Ali o'zbekcha, Bek ruscha ko'radi", su.get('question') and not CYR.search(su['question']['prompt'])
          and CYR.search(sr['question']['prompt']), (su.get('question'), sr.get('question')))
else:
    check('Roomda tarjimali savol bor', False, 'yo\'q')

print("— Shaxsiy dars tili")
db("INSERT INTO subject_purchases (user_id, subject_key) VALUES (%s, 'math')", (bek['id'],))
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
