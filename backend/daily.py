# -*- coding: utf-8 -*-
"""
Kun savoli — har kuni hamma uchun bitta bir xil savol (Toshkent sanasi).

* Savol kunning birinchi so'rovida curriculum testlaridan tanlanadi va
  daily_questions'da saqlanadi — kun davomida hamma uchun bir xil qoladi.
  Fanlar kunma-kun navbatma-navbat almashadi.
* Har o'quvchiga bitta urinish. Tezlik server vaqti bilan o'lchanadi: savol
  birinchi ochilgan paytdan (opened_ms) javobgacha (answered_ms).
* To'g'ri javob — +5 chaqmoq. Kunlik reyting: to'g'ri javob berganlar,
  tezroq javob bergan yuqorida. Streak — ketma-ket javob berilgan kunlar.
"""

import hashlib
import json
from datetime import date, timedelta

import curriculum as cur_mod
import jurnal
import premium
import til
from games import clock
from games.errors import GameError

CHAQMOQ_CORRECT = 5
DAY_MS = 24 * 3600 * 1000
TF_OPTIONS = ["To'g'ri", "Noto'g'ri"]


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS daily_questions (
            day TEXT PRIMARY KEY,
            topic_id TEXT NOT NULL,
            q_index INTEGER NOT NULL,
            created_ms BIGINT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS daily_answers (
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            opened_ms BIGINT NOT NULL,
            answered_ms BIGINT,
            answer INTEGER,
            correct INTEGER,
            chaqmoq INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (day, user_id)
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_daily_answers_user ON daily_answers (user_id)')
    conn.commit()


def today(now_ms) -> str:
    return clock.tashkent_date(now_ms).isoformat()


def _quiz(value):
    if isinstance(value, list):
        return value
    try:
        return json.loads(value or '[]')
    except (TypeError, ValueError):
        return []


def _pick(cur, day):
    """Sanaga qarab deterministik tanlov: fan navbat bilan, fan ichida —
    osonroq 2/3 qismdagi mavzulardan (hamma sinf o'quvchisi javob bera olsin)."""
    subjects = list(cur_mod.SUBJECT_CATALOG)
    subject = subjects[date.fromisoformat(day).toordinal() % len(subjects)]
    cur.execute('SELECT id, quiz FROM topics WHERE subject_key = %s ORDER BY grade, seq', (subject,))
    rows = cur.fetchall()
    rows = rows[:max(1, len(rows) * 2 // 3)]
    candidates = [(r['id'], i) for r in rows for i, q in enumerate(_quiz(r['quiz']))
                  if isinstance(q, dict) and q.get('q') and q.get('type', 'mc') in ('mc', 'tf')]
    if not candidates:
        raise GameError('no_question', "Bugungi savol hali tayyor emas.", 503)
    h = int(hashlib.sha256(day.encode()).hexdigest(), 16)
    return candidates[h % len(candidates)]


def _question(cur, conn, day, now_ms):
    cur.execute('SELECT topic_id, q_index FROM daily_questions WHERE day = %s', (day,))
    row = cur.fetchone()
    if not row:
        topic_id, q_index = _pick(cur, day)
        cur.execute('INSERT INTO daily_questions (day, topic_id, q_index, created_ms) VALUES (%s, %s, %s, %s) '
                    'ON CONFLICT (day) DO NOTHING', (day, topic_id, q_index, now_ms))
        conn.commit()
        cur.execute('SELECT topic_id, q_index FROM daily_questions WHERE day = %s', (day,))
        row = cur.fetchone()
    cur.execute('SELECT id, title, title_ru, subject_key, quiz, ru FROM topics WHERE id = %s', (row['topic_id'],))
    topic = cur.fetchone()
    lang = til.req_lang()
    topic = til.topic(topic, lang) if topic else None          # ruscha interfeysda — ruscha savol (javob bir xil)
    quiz = topic['quiz'] if topic else []
    # Admin mavzuni tahrirlab, savolni o'chirgan yoki turini o'zgartirgan bo'lishi mumkin
    q = quiz[row['q_index']] if 0 <= int(row['q_index']) < len(quiz) else None
    if not isinstance(q, dict) or q.get('type', 'mc') not in ('mc', 'tf') or not q.get('q'):
        raise GameError('no_question', "Bugungi savol topilmadi.", 503)
    kind = q.get('type', 'mc')
    if kind == 'tf':
        options, answer = til.tf_options(lang), (0 if q.get('answer') else 1)
    else:
        options, answer = [str(o) for o in q.get('options') or []], int(q.get('answer', 0))
    return {
        'kind': kind, 'prompt': q['q'], 'options': options, 'answer': answer, 'explain': q.get('explain') or '',
        'topic_title': topic['title'], 'subject_name': cur_mod.subject_meta(topic['subject_key'])['name'],
    }


def subject_of_day(cur, conn, now_ms) -> str:
    """Bugungi savol qaysi fandan (eslatma matni uchun; vaqt hisobi boshlanmaydi)."""
    return _question(cur, conn, today(now_ms), now_ms)['subject_name']


def _first(name):
    parts = str(name or '').split()
    return (parts[0] if parts else "O'quvchi")[:20]


def ranking(cur, day, user_id, limit=10) -> dict:
    cur.execute(
        '''SELECT a.user_id, a.answered_ms - a.opened_ms AS ms, u.name, u.photo_url FROM daily_answers a
           LEFT JOIN users u ON u.id = a.user_id
           WHERE a.day = %s AND a.correct = 1 ORDER BY ms, a.answered_ms''',
        (day,),
    )
    rows = cur.fetchall()
    top = [{'rank': i + 1, 'user_id': r['user_id'], 'name': _first(r['name']), 'photo_url': r['photo_url'],
            'seconds': round(int(r['ms']) / 1000, 1), 'me': r['user_id'] == user_id}
           for i, r in enumerate(rows[:limit])]
    premium.decorate(cur, top)
    mine = next(({'rank': i + 1, 'seconds': round(int(r['ms']) / 1000, 1)}
                 for i, r in enumerate(rows) if r['user_id'] == user_id), None)
    cur.execute('SELECT COUNT(*) AS n FROM daily_answers WHERE day = %s AND answered_ms IS NOT NULL', (day,))
    return {'top': top, 'me': mine, 'correct_count': len(rows), 'answered_count': int(cur.fetchone()['n'])}


def streak(cur, user_id, now_ms) -> int:
    cur.execute('SELECT day FROM daily_answers WHERE user_id = %s AND answered_ms IS NOT NULL', (user_id,))
    days = {date.fromisoformat(r['day']) for r in cur.fetchall()}
    cursor = clock.tashkent_date(now_ms)
    if cursor not in days:
        cursor -= timedelta(days=1)
    n = 0
    while cursor in days:
        n += 1
        cursor -= timedelta(days=1)
    return n


def _result(q, mine):
    return {
        'correct': bool(mine['correct']), 'your_answer': mine['answer'], 'right_answer': q['answer'],
        'explain': q['explain'], 'seconds': round((int(mine['answered_ms']) - int(mine['opened_ms'])) / 1000, 1),
        'chaqmoq': int(mine['chaqmoq']),
    }


def state(cur, conn, user_id, now_ms, peek=False) -> dict:
    """Bugungi savol. Birinchi ochilishda vaqt hisobi boshlanadi. Javob
    berilgunga qadar to'g'ri javob yuborilmaydi. peek=True — hali ochilmagan
    bo'lsa savol matnisiz holat (vaqt boshlanmaydi)."""
    day = today(now_ms)
    q = _question(cur, conn, day, now_ms)
    if not peek:
        cur.execute('INSERT INTO daily_answers (day, user_id, opened_ms) VALUES (%s, %s, %s) '
                    'ON CONFLICT (day, user_id) DO NOTHING', (day, user_id, now_ms))
        conn.commit()
    cur.execute('SELECT * FROM daily_answers WHERE day = %s AND user_id = %s', (day, user_id))
    mine = cur.fetchone()
    data = {
        'day': day, 'topic_title': q['topic_title'], 'subject_name': q['subject_name'],
        'opened': mine is not None, 'answered': bool(mine and mine['answered_ms'] is not None),
        'streak': streak(cur, user_id, now_ms),
        'next_in_s': (clock.period_start_ms('day', now_ms) + DAY_MS - now_ms) // 1000,
    }
    if not mine:
        return data
    data.update({'kind': q['kind'], 'prompt': q['prompt'], 'options': q['options'],
                 'elapsed_ms': now_ms - int(mine['opened_ms'])})
    if data['answered']:
        data['result'] = _result(q, mine)
        data['ranking'] = ranking(cur, day, user_id)
    return data


def answer(cur, conn, user_id, raw, now_ms) -> dict:
    day = today(now_ms)
    q = _question(cur, conn, day, now_ms)
    if isinstance(raw, bool):
        raise GameError('bad_answer', "Javob noto'g'ri formatda.")
    try:
        choice = int(raw)
    except (TypeError, ValueError):
        raise GameError('bad_answer', "Javob noto'g'ri formatda.")
    if not 0 <= choice < len(q['options']):
        raise GameError('bad_answer', "Bunday variant yo'q.")
    correct = choice == q['answer']
    cur.execute(
        '''UPDATE daily_answers SET answered_ms = %s, answer = %s, correct = %s, chaqmoq = %s
           WHERE day = %s AND user_id = %s AND answered_ms IS NULL''',
        (now_ms, choice, int(correct), CHAQMOQ_CORRECT if correct else 0, day, user_id),
    )
    if cur.rowcount != 1:
        conn.rollback()
        cur.execute('SELECT 1 FROM daily_answers WHERE day = %s AND user_id = %s', (day, user_id))
        if cur.fetchone():
            raise GameError('already_answered', "Bugungi savolga javob bergansiz. Ertaga yangi savol!", 409)
        raise GameError('not_opened', "Avval savolni oching.", 409)
    conn.commit()
    if correct:
        jurnal.record(cur, conn, user_id, CHAQMOQ_CORRECT, 'kun', f'kun:{day}', now_ms)
    return state(cur, conn, user_id, now_ms)


WEEK_LABELS = ('Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh', 'Ya')


def week(cur, user_id, now_ms) -> list:
    """Joriy hafta (dushanbadan): har kuni javob berilganmi — streak taqvimi uchun."""
    t = clock.tashkent_date(now_ms)
    monday = t - timedelta(days=t.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]
    cur.execute('SELECT day, correct FROM daily_answers WHERE user_id = %s AND answered_ms IS NOT NULL '
                'AND day >= %s AND day <= %s', (user_id, days[0].isoformat(), days[-1].isoformat()))
    got = {r['day']: bool(r['correct']) for r in cur.fetchall()}
    return [{'day': d.isoformat(), 'label': WEEK_LABELS[i], 'answered': d.isoformat() in got,
             'correct': got.get(d.isoformat(), False), 'today': d == t, 'future': d > t}
            for i, d in enumerate(days)]


def status(cur, user_id, now_ms) -> dict:
    """Bosh sahifa kartasi uchun holat (savolni ochmaydi — vaqt boshlanmaydi):
    javob, streak, keyingi savolgacha vaqt, bugungi mini reyting va hafta taqvimi."""
    day = today(now_ms)
    cur.execute('SELECT answered_ms, correct FROM daily_answers WHERE day = %s AND user_id = %s', (day, user_id))
    mine = cur.fetchone()
    answered = bool(mine and mine['answered_ms'] is not None)
    rk = ranking(cur, day, user_id, limit=3)
    return {
        'day': day,
        'answered': answered, 'correct': bool(answered and mine['correct']),
        'streak': streak(cur, user_id, now_ms),
        'next_in_s': (clock.period_start_ms('day', now_ms) + DAY_MS - now_ms) // 1000,
        'answered_count': rk['answered_count'], 'correct_count': rk['correct_count'],
        'my_rank': rk['me']['rank'] if rk['me'] else None,
        'top': [{'name': t['name'], 'photo_url': t['photo_url'], 'premium': t['premium'], 'emoji': t['emoji']}
                for t in rk['top']],
        'week': week(cur, user_id, now_ms),
    }


def chaqmoq_by_user(cur) -> dict:
    cur.execute('SELECT user_id, SUM(chaqmoq) AS c FROM daily_answers GROUP BY user_id')
    return {r['user_id']: int(r['c'] or 0) for r in cur.fetchall()}


def chaqmoq_total(cur, user_id) -> int:
    cur.execute('SELECT COALESCE(SUM(chaqmoq), 0) AS c FROM daily_answers WHERE user_id = %s', (user_id,))
    return int(cur.fetchone()['c'] or 0)
