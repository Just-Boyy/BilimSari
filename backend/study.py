# -*- coding: utf-8 -*-
"""
BilimSari — o'qish dvigateli.

Bu modul quyidagilarni boshqaradi:
  • jadvallar (subjects, topics, user_progress)
  • curriculum dan bazaga sinxronizatsiya
  • mavzular ketma-ketligi (locked / current / completed)
  • 24 soatlik kutish (Toshkent vaqti bo'yicha, server vaqtida)
  • quiz va uy vazifasini SERVERDA tekshirish

Muhim: to'g'ri javoblar hech qachon frontendga yuborilmaydi.
Progress faqat shu yerdagi funksiyalar orqali o'zgaradi.
"""

import json
import os
import re
from datetime import timedelta

import curriculum as cur_mod
from db import add_column_if_missing, as_utc, iso_utc, to_tashkent, utc_now

# Sozlamalar
QUIZ_PASS_PERCENT = int(os.environ.get('QUIZ_PASS_PERCENT', '70'))
COOLDOWN_HOURS = int(os.environ.get('COOLDOWN_HOURS', '24'))

STATUS_LOCKED = 'locked'        # oldingi mavzu tugallanmagan
STATUS_COOLDOWN = 'cooldown'    # 24 soat kutish davom etmoqda
STATUS_CURRENT = 'current'      # hozir o'qish mumkin
STATUS_IN_PROGRESS = 'in_progress'
STATUS_COMPLETED = 'completed'


class StudyError(Exception):
    """Foydalanuvchiga ko'rsatiladigan xato (o'zbekcha matn)."""

    def __init__(self, message, code='error', http_status=400, extra=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.extra = extra or {}


# ───────────────────────── Jadvallar ─────────────────────────

def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id TEXT PRIMARY KEY,
            grade INTEGER NOT NULL,
            subject_key TEXT NOT NULL,
            name TEXT NOT NULL,
            icon TEXT,
            color TEXT,
            description TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            grade INTEGER NOT NULL,
            subject_key TEXT NOT NULL,
            slug TEXT NOT NULL,
            seq INTEGER NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            duration INTEGER NOT NULL DEFAULT 15,
            lesson JSONB NOT NULL DEFAULT '[]',
            quiz JSONB NOT NULL DEFAULT '[]',
            homework JSONB NOT NULL DEFAULT '{}'
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            topic_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'in_progress',
            lesson_read INTEGER NOT NULL DEFAULT 0,
            quiz_score INTEGER,
            quiz_attempts INTEGER NOT NULL DEFAULT 0,
            quiz_passed INTEGER NOT NULL DEFAULT 0,
            homework_status TEXT NOT NULL DEFAULT 'none',
            homework_answers JSONB,
            homework_attempts INTEGER NOT NULL DEFAULT 0,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            UNIQUE (user_id, topic_id)
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_topics_subject ON topics (subject_id, seq)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_progress_user ON user_progress (user_id)')
    conn.commit()

    # users jadvaliga sinf ustuni
    add_column_if_missing(cur, conn, 'users', 'grade', 'INTEGER')


# ───────────────────────── Curriculum → baza ─────────────────────────

def sync_curriculum(cur, conn, force=False):
    """
    curriculum/ paketidagi darslarni bazaga yozadi.

    Manba — Python modullari (qo'lda yozilgan dastur), baza esa ishchi nusxa.
    Har safar ishga tushganda yangilanadi, shuning uchun darsni kodda tahrirlash
    kifoya.
    """
    ensure_tables(cur, conn)

    if not force:
        cur.execute('SELECT COUNT(*) AS n FROM topics')
        existing = int(cur.fetchone()['n'] or 0)
        expected = sum(
            len(s.get('topics', []))
            for g in cur_mod.GRADES
            for s in cur_mod.subjects_for_grade(g)
        )
        if existing == expected and expected > 0:
            return 0  # o'zgarish yo'q

    written = 0
    for grade in cur_mod.GRADES:
        subjects = cur_mod.subjects_for_grade(grade)
        for order, subject in enumerate(subjects, start=1):
            key = subject['key']
            meta = cur_mod.subject_meta(key)
            sid = cur_mod.subject_id(grade, key)
            _upsert(
                cur,
                'subjects',
                'id',
                {
                    'id': sid,
                    'grade': grade,
                    'subject_key': key,
                    'name': meta['name'],
                    'icon': meta['icon'],
                    'color': meta['color'],
                    'description': subject.get('description') or '',
                    'sort_order': order,
                },
            )
            for seq, topic in enumerate(subject.get('topics', []), start=1):
                tid = cur_mod.topic_id(grade, key, topic['slug'])
                _upsert(
                    cur,
                    'topics',
                    'id',
                    {
                        'id': tid,
                        'subject_id': sid,
                        'grade': grade,
                        'subject_key': key,
                        'slug': topic['slug'],
                        'seq': seq,
                        'title': topic['title'],
                        'summary': topic.get('summary') or '',
                        'duration': int(topic.get('duration') or 15),
                        'lesson': json.dumps(topic.get('lesson') or [], ensure_ascii=False),
                        'quiz': json.dumps(topic.get('quiz') or [], ensure_ascii=False),
                        'homework': json.dumps(topic.get('homework') or {}, ensure_ascii=False),
                    },
                )
                written += 1
    conn.commit()
    return written


def _upsert(cur, table, pk, data):
    cols = list(data.keys())
    placeholders = ', '.join(['%s'] * len(cols))
    updates = ', '.join(f'{c} = EXCLUDED.{c}' for c in cols if c != pk)
    cur.execute(
        f'INSERT INTO {table} ({", ".join(cols)}) VALUES ({placeholders}) '
        f'ON CONFLICT ({pk}) DO UPDATE SET {updates}',
        [data[c] for c in cols],
    )


def _json(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


# ───────────────────────── Sinf ─────────────────────────

def get_user_grade(cur, user_id):
    cur.execute('SELECT grade FROM users WHERE id = %s', (user_id,))
    row = cur.fetchone()
    return int(row['grade']) if row and row.get('grade') else None


def set_user_grade(cur, conn, user_id, grade):
    grade = int(grade)
    if grade not in cur_mod.GRADES:
        raise StudyError("Sinf 1 dan 11 gacha bo'lishi kerak", code='bad_grade')
    cur.execute('UPDATE users SET grade = %s WHERE id = %s', (grade, user_id))
    conn.commit()
    return grade


# ───────────────────────── 24 soatlik kutish ─────────────────────────

def last_completion(cur, user_id):
    cur.execute(
        '''SELECT topic_id, completed_at FROM user_progress
           WHERE user_id = %s AND status = %s AND completed_at IS NOT NULL
           ORDER BY completed_at DESC''',
        (user_id, STATUS_COMPLETED),
    )
    rows = cur.fetchall()
    if not rows:
        return None, None
    row = rows[0]
    return row['topic_id'], as_utc(row['completed_at'])


def cooldown_state(cur, user_id):
    """
    24 soatlik kutish holati. Vaqt SERVERDA hisoblanadi — brauzer soatini
    o'zgartirish yoki sahifani yangilash bu holatga ta'sir qilmaydi.
    """
    topic_id, completed_at = last_completion(cur, user_id)
    if not completed_at:
        return {'active': False, 'seconds_left': 0, 'unlock_at': None,
                'unlock_at_tashkent': None, 'last_topic_id': None}

    unlock_at = completed_at + timedelta(hours=COOLDOWN_HOURS)
    now = utc_now()
    seconds_left = int((unlock_at - now).total_seconds())
    if seconds_left <= 0:
        return {'active': False, 'seconds_left': 0, 'unlock_at': iso_utc(unlock_at),
                'unlock_at_tashkent': None, 'last_topic_id': topic_id}

    tashkent = to_tashkent(unlock_at)
    return {
        'active': True,
        'seconds_left': seconds_left,
        'unlock_at': iso_utc(unlock_at),
        'unlock_at_tashkent': tashkent.strftime('%d.%m.%Y %H:%M'),
        'last_topic_id': topic_id,
        'text': format_remaining(seconds_left),
    }


def format_remaining(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f'{hours} soat {minutes} daqiqa'
    if minutes > 0:
        return f'{minutes} daqiqa'
    return f'{seconds} soniya'


# ───────────────────────── Mavzular va holatlar ─────────────────────────

def _progress_map(cur, user_id, topic_ids=None):
    cur.execute('SELECT * FROM user_progress WHERE user_id = %s', (user_id,))
    rows = cur.fetchall()
    return {r['topic_id']: r for r in rows}


def _topic_row(cur, topic_id):
    cur.execute('SELECT * FROM topics WHERE id = %s', (topic_id,))
    return cur.fetchone()


def _compute_states(topics, progress, cooldown):
    """
    Ketma-ketlik qoidasi:
      • 1-mavzu doim ochiq
      • N-mavzu faqat (N-1) tugallangandan keyin ochiladi
      • kutish davri faol bo'lsa — YANGI mavzu ochilmaydi
      • allaqachon boshlangan mavzuni davom ettirish mumkin
    """
    out = []
    unlocked = True          # oldingi mavzu tugallanganmi
    current_assigned = False
    for topic in topics:
        prog = progress.get(topic['id'])
        status = (prog or {}).get('status')

        if status == STATUS_COMPLETED:
            state = STATUS_COMPLETED
        elif not unlocked:
            state = STATUS_LOCKED
        elif status == STATUS_IN_PROGRESS:
            state = STATUS_CURRENT     # boshlangan — davom ettirish mumkin
            current_assigned = True
        elif cooldown.get('active'):
            state = STATUS_COOLDOWN
        elif not current_assigned:
            state = STATUS_CURRENT
            current_assigned = True
        else:
            state = STATUS_LOCKED

        out.append({
            'id': topic['id'],
            'slug': topic['slug'],
            'seq': topic['seq'],
            'title': topic['title'],
            'summary': topic.get('summary') or '',
            'duration': topic.get('duration') or 15,
            'subject_key': topic['subject_key'],
            'grade': topic['grade'],
            'state': state,
            'lesson_read': bool((prog or {}).get('lesson_read')),
            'quiz_score': (prog or {}).get('quiz_score'),
            'quiz_passed': bool((prog or {}).get('quiz_passed')),
            'homework_status': (prog or {}).get('homework_status') or 'none',
            'completed_at': iso_utc(as_utc((prog or {}).get('completed_at'))),
        })

        if status != STATUS_COMPLETED:
            unlocked = False   # keyingilari yopiq

    return out


def subject_topics(cur, user_id, grade, subject_key):
    cur.execute(
        'SELECT * FROM topics WHERE grade = %s AND subject_key = %s ORDER BY seq ASC',
        (int(grade), subject_key),
    )
    topics = cur.fetchall()
    if not topics:
        return None, []
    cur.execute(
        'SELECT * FROM subjects WHERE grade = %s AND subject_key = %s',
        (int(grade), subject_key),
    )
    subject = cur.fetchone()
    progress = _progress_map(cur, user_id)
    cooldown = cooldown_state(cur, user_id)
    return subject, _compute_states(topics, progress, cooldown)


def subjects_overview(cur, user_id, grade):
    """Sinf bo'yicha barcha fanlar + har birida progress."""
    grade = int(grade)
    cur.execute('SELECT * FROM subjects WHERE grade = %s ORDER BY sort_order ASC', (grade,))
    subjects = cur.fetchall()
    if not subjects:
        return []

    cur.execute('SELECT * FROM topics WHERE grade = %s ORDER BY seq ASC', (grade,))
    all_topics = cur.fetchall()
    progress = _progress_map(cur, user_id)
    cooldown = cooldown_state(cur, user_id)

    out = []
    for subject in subjects:
        topics = [t for t in all_topics if t['subject_key'] == subject['subject_key']]
        states = _compute_states(topics, progress, cooldown)
        done = sum(1 for s in states if s['state'] == STATUS_COMPLETED)
        current = next((s for s in states if s['state'] in (STATUS_CURRENT, STATUS_COOLDOWN)), None)
        out.append({
            'id': subject['id'],
            'key': subject['subject_key'],
            'name': subject['name'],
            'icon': subject['icon'],
            'color': subject['color'],
            'grade': grade,
            'total_topics': len(states),
            'completed_topics': done,
            'percent': round(done * 100 / len(states)) if states else 0,
            'current_topic': {'title': current['title'], 'slug': current['slug'],
                              'state': current['state']} if current else None,
            'finished': done == len(states) and len(states) > 0,
        })
    return out


# ───────────────────────── Mavzuni ochish ─────────────────────────

def _ensure_progress_row(cur, conn, user_id, topic_id):
    cur.execute(
        'SELECT * FROM user_progress WHERE user_id = %s AND topic_id = %s',
        (user_id, topic_id),
    )
    row = cur.fetchone()
    if row:
        return row
    cur.execute(
        '''INSERT INTO user_progress (user_id, topic_id, status, started_at)
           VALUES (%s, %s, %s, %s)''',
        (user_id, topic_id, STATUS_IN_PROGRESS, utc_now()),
    )
    conn.commit()
    cur.execute(
        'SELECT * FROM user_progress WHERE user_id = %s AND topic_id = %s',
        (user_id, topic_id),
    )
    return cur.fetchone()


def topic_state_for(cur, user_id, topic):
    """Bitta mavzuning holatini (o'sha fandagi ketma-ketlikni hisobga olib) aniqlaydi."""
    cur.execute(
        'SELECT * FROM topics WHERE grade = %s AND subject_key = %s ORDER BY seq ASC',
        (topic['grade'], topic['subject_key']),
    )
    siblings = cur.fetchall()
    progress = _progress_map(cur, user_id)
    cooldown = cooldown_state(cur, user_id)
    states = _compute_states(siblings, progress, cooldown)
    for s in states:
        if s['id'] == topic['id']:
            return s, cooldown
    return None, cooldown


def open_topic(cur, conn, user_id, topic_id, register=True):
    """
    Mavzuni ochadi. Qulflangan bo'lsa — StudyError.
    register=True bo'lsa progress qatori yaratiladi (mavzu boshlanadi).
    """
    topic = _topic_row(cur, topic_id)
    if not topic:
        raise StudyError('Mavzu topilmadi', code='not_found', http_status=404)

    state, cooldown = topic_state_for(cur, user_id, topic)
    if state is None:
        raise StudyError('Mavzu topilmadi', code='not_found', http_status=404)

    if state['state'] == STATUS_LOCKED:
        raise StudyError(
            'Bu mavzu hozircha qulflangan. Avval oldingi mavzuni yakunlang.',
            code='locked', http_status=403,
        )
    if state['state'] == STATUS_COOLDOWN:
        raise StudyError(
            f"Bugungi mavzuni yakunladingiz. Keyingi mavzu {cooldown.get('text')}dan so'ng ochiladi.",
            code='cooldown', http_status=403, extra={'cooldown': cooldown},
        )

    prog = None
    if register and state['state'] != STATUS_COMPLETED:
        prog = _ensure_progress_row(cur, conn, user_id, topic_id)
    else:
        cur.execute(
            'SELECT * FROM user_progress WHERE user_id = %s AND topic_id = %s',
            (user_id, topic_id),
        )
        prog = cur.fetchone()

    return topic, state, prog, cooldown


def topic_payload(cur, conn, user_id, topic_id):
    """Mavzu sahifasi uchun to'liq ma'lumot (to'g'ri javoblarsiz)."""
    topic, state, prog, cooldown = open_topic(cur, conn, user_id, topic_id)

    quiz = _json(topic['quiz'], [])
    homework = _json(topic['homework'], {})

    cur.execute(
        'SELECT id, slug, seq, title FROM topics WHERE grade = %s AND subject_key = %s ORDER BY seq ASC',
        (topic['grade'], topic['subject_key']),
    )
    siblings = cur.fetchall()
    index = next((i for i, s in enumerate(siblings) if s['id'] == topic_id), 0)

    cur.execute('SELECT * FROM subjects WHERE id = %s', (topic['subject_id'],))
    subject = cur.fetchone() or {}

    return {
        'id': topic['id'],
        'slug': topic['slug'],
        'seq': topic['seq'],
        'title': topic['title'],
        'summary': topic.get('summary') or '',
        'duration': topic.get('duration') or 15,
        'grade': topic['grade'],
        'subject': {
            'key': topic['subject_key'],
            'name': subject.get('name') or topic['subject_key'],
            'icon': subject.get('icon') or '📘',
            'color': subject.get('color') or '#4F7DF3',
        },
        'lesson': _json(topic['lesson'], []),
        'quiz': public_quiz(quiz),
        'quiz_pass_percent': QUIZ_PASS_PERCENT,
        'homework': public_homework(homework),
        'total_topics': len(siblings),
        'position': index + 1,
        'next_topic': ({'slug': siblings[index + 1]['slug'], 'title': siblings[index + 1]['title']}
                       if index + 1 < len(siblings) else None),
        'progress': {
            'state': state['state'],
            'lesson_read': bool((prog or {}).get('lesson_read')),
            'quiz_score': (prog or {}).get('quiz_score'),
            'quiz_passed': bool((prog or {}).get('quiz_passed')),
            'quiz_attempts': (prog or {}).get('quiz_attempts') or 0,
            'homework_status': (prog or {}).get('homework_status') or 'none',
            'homework_answers': _json((prog or {}).get('homework_answers'), {}),
            'completed_at': iso_utc(as_utc((prog or {}).get('completed_at'))),
        },
        'cooldown': cooldown,
    }


def public_quiz(quiz):
    """To'g'ri javoblarni olib tashlaydi — frontend ularni ko'rmaydi."""
    out = []
    for i, q in enumerate(quiz):
        item = {'index': i, 'type': q.get('type', 'mc'), 'q': q.get('q', '')}
        if item['type'] == 'mc':
            item['options'] = q.get('options', [])
        out.append(item)
    return out


def public_homework(homework):
    tasks = []
    for t in homework.get('tasks', []):
        tasks.append({
            'id': t.get('id'),
            'type': t.get('type', 'text'),
            'prompt': t.get('prompt', ''),
            'hint': t.get('hint') or '',
            'checked': bool(t.get('answer')),
        })
    return {'intro': homework.get('intro', ''), 'tasks': tasks}


# ───────────────────────── Darsni o'qish ─────────────────────────

def mark_lesson_read(cur, conn, user_id, topic_id):
    topic, state, prog, cooldown = open_topic(cur, conn, user_id, topic_id)
    if state['state'] == STATUS_COMPLETED:
        return True
    cur.execute(
        'UPDATE user_progress SET lesson_read = 1 WHERE user_id = %s AND topic_id = %s',
        (user_id, topic_id),
    )
    conn.commit()
    return True


# ───────────────────────── Javoblarni tekshirish ─────────────────────────

_APOSTROPHES = str.maketrans({'ʻ': "'", 'ʼ': "'", '‘': "'", '’': "'", '`': "'", '´': "'"})


def normalize(text) -> str:
    if text is None:
        return ''
    text = str(text).strip().lower().translate(_APOSTROPHES)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip(' .!,;:')
    return text


def answers_match(given, expected, accept=None) -> bool:
    g = normalize(given)
    if not g:
        return False
    candidates = [expected] + list(accept or [])
    for c in candidates:
        if normalize(c) == g:
            return True
    # sonli javoblar: "5" va "5.0" bir xil
    try:
        if abs(float(g.replace(',', '.')) - float(normalize(expected).replace(',', '.'))) < 1e-9:
            return True
    except (ValueError, AttributeError):
        pass
    return False


def grade_quiz(cur, conn, user_id, topic_id, answers):
    topic, state, prog, cooldown = open_topic(cur, conn, user_id, topic_id)
    quiz = _json(topic['quiz'], [])
    if not quiz:
        raise StudyError("Bu mavzuda test yo'q", code='no_quiz')
    if not isinstance(answers, list):
        raise StudyError('Javoblar formati noto\'g\'ri', code='bad_input')

    results = []
    correct = 0
    for i, q in enumerate(quiz):
        given = answers[i] if i < len(answers) else None
        qtype = q.get('type', 'mc')
        ok = False
        if qtype == 'mc':
            try:
                ok = int(given) == int(q.get('answer', 0))
            except (TypeError, ValueError):
                ok = False
        elif qtype == 'tf':
            if isinstance(given, str):
                given = given.strip().lower() in ('true', '1', 'ha', "to'g'ri", 'togri')
            ok = bool(given) == bool(q.get('answer'))
        else:  # fill
            ok = answers_match(given, q.get('answer'), q.get('accept'))
        if ok:
            correct += 1
        results.append({
            'index': i,
            'correct': ok,
            'explain': q.get('explain', ''),
            'correct_answer': _readable_answer(q),
        })

    total = len(quiz)
    percent = round(correct * 100 / total) if total else 0
    passed = percent >= QUIZ_PASS_PERCENT

    if state['state'] != STATUS_COMPLETED:
        cur.execute(
            '''UPDATE user_progress
               SET quiz_score = %s,
                   quiz_attempts = quiz_attempts + 1,
                   quiz_passed = %s,
                   lesson_read = 1
               WHERE user_id = %s AND topic_id = %s''',
            (percent, 1 if passed else 0, user_id, topic_id),
        )
        conn.commit()

    completion = _try_complete(cur, conn, user_id, topic_id) if passed else None

    return {
        'correct': correct,
        'total': total,
        'percent': percent,
        'passed': passed,
        'pass_percent': QUIZ_PASS_PERCENT,
        'results': results,
        'message': ("Ajoyib! Testdan o'tdingiz."
                    if passed else
                    "Yana bir bor mavzuni o'rganib, quizni qayta ishlashingiz mumkin."),
        'completion': completion,
    }


def _readable_answer(q):
    qtype = q.get('type', 'mc')
    if qtype == 'mc':
        opts = q.get('options') or []
        idx = q.get('answer', 0)
        return opts[idx] if 0 <= idx < len(opts) else ''
    if qtype == 'tf':
        return "To'g'ri" if q.get('answer') else "Noto'g'ri"
    return str(q.get('answer', ''))


def submit_homework(cur, conn, user_id, topic_id, answers):
    topic, state, prog, cooldown = open_topic(cur, conn, user_id, topic_id)
    homework = _json(topic['homework'], {})
    tasks = homework.get('tasks', [])
    if not tasks:
        raise StudyError("Bu mavzuda uyga vazifa yo'q", code='no_homework')
    if not isinstance(answers, dict):
        raise StudyError('Javoblar formati noto\'g\'ri', code='bad_input')

    results = []
    ok_count = 0
    for task in tasks:
        tid = task.get('id')
        given = answers.get(tid, '')
        expected = task.get('answer')
        if expected:
            ok = answers_match(given, expected, task.get('accept'))
            results.append({'id': tid, 'correct': ok, 'checked': True,
                            'correct_answer': expected if not ok else None})
        else:
            # ochiq savol — javob yozilgan bo'lsa qabul qilinadi
            ok = len(normalize(given)) >= 2
            results.append({'id': tid, 'correct': ok, 'checked': False,
                            'correct_answer': None})
        if ok:
            ok_count += 1

    passed = ok_count == len(tasks)
    status = 'passed' if passed else 'submitted'

    if state['state'] != STATUS_COMPLETED:
        cur.execute(
            '''UPDATE user_progress
               SET homework_status = %s,
                   homework_answers = %s,
                   homework_attempts = homework_attempts + 1
               WHERE user_id = %s AND topic_id = %s''',
            (status, json.dumps(answers, ensure_ascii=False), user_id, topic_id),
        )
        conn.commit()

    completion = _try_complete(cur, conn, user_id, topic_id) if passed else None

    missing = [r['id'] for r in results if not r['correct']]
    return {
        'passed': passed,
        'correct': ok_count,
        'total': len(tasks),
        'results': results,
        'message': ('Uyga vazifa qabul qilindi!' if passed else
                    f"{len(missing)} ta javob noto'g'ri yoki bo'sh. Tekshirib, qayta yuboring."),
        'completion': completion,
    }


# ───────────────────────── Mavzuni yakunlash ─────────────────────────

def _try_complete(cur, conn, user_id, topic_id):
    """
    Barcha shartlar bajarilsa mavzuni yakunlaydi:
    dars o'qilgan + quiz o'tilgan + uyga vazifa topshirilgan.

    24 soatlik cheklov shu yerda ham tekshiriladi — bir kunda ikkita mavzu
    yakunlab bo'lmaydi.
    """
    cur.execute(
        'SELECT * FROM user_progress WHERE user_id = %s AND topic_id = %s',
        (user_id, topic_id),
    )
    prog = cur.fetchone()
    if not prog or prog['status'] == STATUS_COMPLETED:
        return None

    ready = (
        bool(prog.get('lesson_read'))
        and bool(prog.get('quiz_passed'))
        and prog.get('homework_status') == 'passed'
    )
    if not ready:
        return {
            'completed': False,
            'needs': {
                'lesson': not bool(prog.get('lesson_read')),
                'quiz': not bool(prog.get('quiz_passed')),
                'homework': prog.get('homework_status') != 'passed',
            },
        }

    cooldown = cooldown_state(cur, user_id)
    if cooldown.get('active'):
        return {
            'completed': False,
            'blocked_by_cooldown': True,
            'cooldown': cooldown,
            'message': f"Bir kunda faqat bitta mavzu yakunlanadi. "
                       f"{cooldown.get('text')}dan so'ng qayta urinib ko'ring.",
        }

    now = utc_now()
    cur.execute(
        '''UPDATE user_progress SET status = %s, completed_at = %s
           WHERE user_id = %s AND topic_id = %s''',
        (STATUS_COMPLETED, now, user_id, topic_id),
    )
    conn.commit()

    unlock_at = now + timedelta(hours=COOLDOWN_HOURS)
    return {
        'completed': True,
        'completed_at': iso_utc(now),
        'next_unlock_at': iso_utc(unlock_at),
        'next_unlock_tashkent': to_tashkent(unlock_at).strftime('%d.%m.%Y %H:%M'),
        'cooldown_hours': COOLDOWN_HOURS,
        'message': 'Tabriklaymiz! Mavzuni muvaffaqiyatli yakunladingiz.',
    }


# ───────────────────────── Dashboard ─────────────────────────

def dashboard(cur, user_id):
    grade = get_user_grade(cur, user_id)
    cooldown = cooldown_state(cur, user_id)

    if not grade:
        return {'grade': None, 'needs_onboarding': True, 'cooldown': cooldown,
                'subjects': [], 'stats': {}}

    subjects = subjects_overview(cur, user_id, grade)

    cur.execute(
        'SELECT COUNT(*) AS n FROM user_progress WHERE user_id = %s AND status = %s',
        (user_id, STATUS_COMPLETED),
    )
    completed_total = int(cur.fetchone()['n'] or 0)

    cur.execute('SELECT COUNT(*) AS n FROM topics WHERE grade = %s', (grade,))
    topics_total = int(cur.fetchone()['n'] or 0)

    # bugungi dars — birinchi ochiq mavzu
    today = None
    for subject in subjects:
        if subject['current_topic']:
            today = {
                'subject_key': subject['key'],
                'subject_name': subject['name'],
                'subject_icon': subject['icon'],
                'subject_color': subject['color'],
                'topic_title': subject['current_topic']['title'],
                'topic_slug': subject['current_topic']['slug'],
                'state': subject['current_topic']['state'],
            }
            break

    return {
        'grade': grade,
        'needs_onboarding': False,
        'subjects': subjects,
        'today': today,
        'cooldown': cooldown,
        'stats': {
            'completed_topics': completed_total,
            'total_topics': topics_total,
            'percent': round(completed_total * 100 / topics_total) if topics_total else 0,
            'subjects_count': len(subjects),
            'finished_subjects': sum(1 for s in subjects if s['finished']),
        },
    }
