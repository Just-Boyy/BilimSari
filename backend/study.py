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

import hashlib
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone

import curriculum as cur_mod
import lesson_edit
import premium
from db import add_column_if_missing, as_utc, iso_utc, to_tashkent, utc_now
import daily
import jurnal
import til
from games import clock
from games import stats as game_stats

logger = logging.getLogger('bilimsari')

# Sozlamalar
QUIZ_PASS_PERCENT = int(os.environ.get('QUIZ_PASS_PERCENT', '70'))
COOLDOWN_HOURS = int(os.environ.get('COOLDOWN_HOURS', '24'))
# Onboarding'da bitta fan bepul tanlanadi, qolganlari shu narxda sotib olinadi
# (hozircha DEMO — haqiqiy to'lov integratsiyasi yo'q, "to'lash" bosilsa ochiladi).
SUBJECT_PRICE = int(os.environ.get('SUBJECT_PRICE', '12000'))

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
            image TEXT,
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
    cur.execute('CREATE INDEX IF NOT EXISTS idx_topics_subject_key ON topics (subject_key)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_progress_user ON user_progress (user_id)')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS subject_purchases (
            user_id INTEGER NOT NULL,
            subject_key TEXT NOT NULL,
            purchased_at TIMESTAMP NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, subject_key)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS curriculum_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    conn.commit()

    # Eski (jadval allaqachon mavjud) bazalarda yetishmayotgan ustunlarni qo'shadi.
    # CREATE TABLE'dan keyin, alohida commit'lardan keyin turishi shart — aks holda
    # yangi (bo'sh) bazada "ustun allaqachon bor" xatosi rollback qilib, hali
    # commit qilinmagan CREATE TABLE'ni ham bekor qilib yuboradi.
    add_column_if_missing(cur, conn, 'subjects', 'image', 'TEXT')
    # Ruscha kontent (curriculum/ru/*.json): ro'yxatlar uchun alohida ustunlar, dars/test/uy vazifasi — JSON
    add_column_if_missing(cur, conn, 'topics', 'title_ru', 'TEXT')
    add_column_if_missing(cur, conn, 'topics', 'summary_ru', 'TEXT')
    add_column_if_missing(cur, conn, 'topics', 'ru', 'TEXT')

    # users jadvaliga sinf ustuni
    add_column_if_missing(cur, conn, 'users', 'grade', 'INTEGER')
    # Onboarding'da tanlangan bepul fan
    add_column_if_missing(cur, conn, 'users', 'chosen_subject_key', 'TEXT')
    # Testning BIRINCHI urinishidagi to'g'ri javoblar soni — chaqmoq shundan hisoblanadi
    add_column_if_missing(cur, conn, 'user_progress', 'quiz_first_correct', 'INTEGER')
    backfill_first_quiz(cur, conn)


def backfill_first_quiz(cur, conn):
    """Yangi chaqmoq qoidasidan oldingi urinishlar: bitta urinish bo'lsa — natijadan aniq
    hisoblanadi; bir necha urinish bo'lsa birinchisi o'tmagan — 1 ta to'g'ri deb olinadi
    (tugallangan mavzu 5 + 15 = 20 chaqmoq — eski qoidadagi bilan bir xil)."""
    cur.execute('''SELECT p.id, p.quiz_attempts, p.quiz_score, t.quiz FROM user_progress p
                   LEFT JOIN topics t ON t.id = p.topic_id
                   WHERE p.quiz_first_correct IS NULL AND p.quiz_attempts >= 1''')
    rows = cur.fetchall()
    for r in rows:
        n = len(_json(r['quiz'], [])) or 3
        value = round((r['quiz_score'] or 0) * n / 100) if int(r['quiz_attempts']) == 1 else 1
        cur.execute('UPDATE user_progress SET quiz_first_correct = %s WHERE id = %s', (value, r['id']))
    if rows:
        conn.commit()


# ───────────────────────── Curriculum → baza ─────────────────────────

def _curriculum_fingerprint() -> str:
    """Butun curriculum kodining "barmoq izi" — mazmun o'zgarmagan bo'lsa
    bir xil qiymat qaytadi, shunda har bir restart'da bazani qayta
    yozmasdan o'tkazib yuborish mumkin."""
    parts = []
    for grade in cur_mod.GRADES:
        for subject in cur_mod.subjects_for_grade(grade):
            for topic in subject.get('topics', []):
                parts.append(json.dumps({
                    'g': grade, 'k': subject['key'], 'slug': topic['slug'],
                    'title': topic['title'], 'summary': topic.get('summary'),
                    'duration': topic.get('duration'),
                    'lesson': topic.get('lesson'),
                    'quiz': topic.get('quiz'),
                    'homework': topic.get('homework'),
                    'ru': cur_mod.ru_topics(subject['key']).get(topic['slug']),
                }, sort_keys=True, ensure_ascii=False))
    raw = '\n'.join(parts).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def sync_curriculum(cur, conn, force=False):
    """
    curriculum/ paketidagi darslarni bazaga yozadi va endi mavjud bo'lmagan
    (kodda olib tashlangan yoki subject_key'i o'zgargan) qatorlarni o'chiradi.

    Manba — Python modullari (qo'lda yozilgan dastur), baza esa ishchi nusxa.
    Mazmun oldingi restart'dan beri o'zgarmagan bo'lsa (fingerprint bir xil),
    359+ qatorni qayta yozish shart emas — o'tkazib yuboriladi.
    """
    ensure_tables(cur, conn)
    lesson_edit.ensure_tables(cur, conn)

    fingerprint = _curriculum_fingerprint()
    if not force:
        cur.execute("SELECT value FROM curriculum_meta WHERE key = 'fingerprint'")
        row = cur.fetchone()
        if row and row['value'] == fingerprint:
            return 0

    written = 0
    expected_subject_ids = set()
    expected_topic_ids = set()

    for grade in cur_mod.GRADES:
        subjects = cur_mod.subjects_for_grade(grade)
        for order, subject in enumerate(subjects, start=1):
            key = subject['key']
            meta = cur_mod.subject_meta(key)
            sid = cur_mod.subject_id(grade, key)
            expected_subject_ids.add(sid)
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
                    'image': meta.get('image'),
                    'color': meta['color'],
                    'description': subject.get('description') or '',
                    'sort_order': order,
                },
            )
            ru_all = cur_mod.ru_topics(key)
            for seq, topic in enumerate(subject.get('topics', []), start=1):
                tid = cur_mod.topic_id(grade, key, topic['slug'])
                expected_topic_ids.add(tid)
                ru = ru_all.get(topic['slug']) or {}
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
                        'title_ru': ru.get('title') or None,
                        'summary_ru': ru.get('summary') or None,
                        'ru': json.dumps({k: ru[k] for k in ('lesson', 'quiz', 'homework') if ru.get(k)},
                                         ensure_ascii=False) if ru else None,
                    },
                )
                written += 1

    # Kodda endi yo'q fan/mavzularni bazadan ham o'chiramiz (masalan, Algebra
    # Matematikaga birlashtirildi yoki bir fan butunlay olib tashlandi).
    #
    # MUHIM: faqat `topics` qatori o'chadi — `user_progress` esa SAQLANIB
    # QOLADI. Aks holda bir mavzuning slug'ini (yoki fanini) o'zgartirsam,
    # shu mavzuni tugatgan barcha foydalanuvchilarning progressi ham
    # bazadan yo'qolib ketardi (topic_id'da FK yo'q, shuning uchun bu
    # "yetim" qatorlar xatoga sabab bo'lmaydi — ular shunchaki keyingi
    # JOIN'larda hisobga olinmaydi).
    cur.execute('SELECT id FROM topics')
    stale_topic_ids = {r['id'] for r in cur.fetchall()} - expected_topic_ids
    for tid in stale_topic_ids:
        cur.execute('DELETE FROM topics WHERE id = %s', (tid,))

    cur.execute('SELECT id FROM subjects')
    stale_subject_ids = {r['id'] for r in cur.fetchall()} - expected_subject_ids
    for sid in stale_subject_ids:
        cur.execute('DELETE FROM subjects WHERE id = %s', (sid,))

    # Admin paneldagi tahrirlar kod'dagi matn ustidan qayta qo'yiladi
    lesson_edit.apply_overrides(cur)

    cur.execute(
        "INSERT INTO curriculum_meta (key, value) VALUES ('fingerprint', %s) "
        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
        (fingerprint,)
    )
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
        logger.warning('Bazada buzilgan JSON topildi, default qiymat ishlatildi: %r', value)
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


# ───────────────────────── Fan qulfi (bepul + sotib olingan) ─────────────────────────

def get_chosen_subject(cur, user_id):
    cur.execute('SELECT chosen_subject_key FROM users WHERE id = %s', (user_id,))
    row = cur.fetchone()
    return row['chosen_subject_key'] if row else None


def is_subject_unlocked(cur, user_id, subject_key):
    if get_chosen_subject(cur, user_id) == subject_key:
        return True
    cur.execute(
        'SELECT 1 FROM subject_purchases WHERE user_id = %s AND subject_key = %s',
        (user_id, subject_key),
    )
    return cur.fetchone() is not None


def choose_subject(cur, conn, user_id, subject_key):
    """Onboarding'dagi bepul fan tanlovi — faqat bir marta, keyin o'zgartirib
    bo'lmaydi (boshqa fanlar sotib olish orqali ochiladi)."""
    if subject_key not in cur_mod.SUBJECT_CATALOG:
        raise StudyError("Bunday fan mavjud emas", code='bad_subject', http_status=404)
    already = get_chosen_subject(cur, user_id)
    if already:
        if already == subject_key:
            return already
        raise StudyError(
            'Fan allaqachon tanlangan, uni o\'zgartirib bo\'lmaydi', code='already_chosen',
        )
    cur.execute('UPDATE users SET chosen_subject_key = %s WHERE id = %s', (subject_key, user_id))
    conn.commit()
    return subject_key


def unlock_subject(cur, conn, user_id, subject_key):
    """Eskirgan DEMO yo'l (pulsiz ochardi). Endi fan faqat admin tasdiqlagan
    to'lovdan keyin ochiladi — payments.py, "Fan sotib olish" sahifasi."""
    if subject_key not in cur_mod.SUBJECT_CATALOG:
        raise StudyError("Bunday fan mavjud emas", code='bad_subject', http_status=404)
    if is_subject_unlocked(cur, user_id, subject_key):
        return True
    raise StudyError("Fan to'lovdan keyin ochiladi: «Sotib olish» tugmasini bosing.",
                     code='use_shop', http_status=402)


# ───────────────────────── 24 soatlik kutish ─────────────────────────

def last_completion(cur, user_id, subject_key=None):
    """Oxirgi tugallangan mavzu. subject_key berilsa — faqat shu fandagi."""
    if subject_key:
        cur.execute(
            '''SELECT p.topic_id, p.completed_at FROM user_progress p
               JOIN topics t ON t.id = p.topic_id
               WHERE p.user_id = %s AND p.status = %s AND p.completed_at IS NOT NULL AND t.subject_key = %s
               ORDER BY p.completed_at DESC''',
            (user_id, STATUS_COMPLETED, subject_key),
        )
    else:
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


def _build_cooldown(topic_id, completed_at):
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


def cooldown_state(cur, user_id, subject_key=None):
    """
    24 soatlik kutish holati. Kutish HAR BIR FANGA ALOHIDA: bir fanda mavzu
    tugatilsa, faqat o'sha fanning keyingi mavzusi 24 soat yopiladi — boshqa
    fanlarni o'qish mumkin. subject_key berilmasa — eng oxirgi tugallangan
    mavzu bo'yicha (umumiy ma'lumot uchun).

    Vaqt SERVERDA hisoblanadi — brauzer soatini o'zgartirish yoki sahifani
    yangilash bu holatga ta'sir qilmaydi.
    """
    topic_id, completed_at = last_completion(cur, user_id, subject_key)
    return _build_cooldown(topic_id, completed_at)


def _cooldown_from_progress(progress: dict, topic_ids=None):
    """`_progress_map()` natijasidan — qo'shimcha bazaga so'rovsiz —
    cooldown holatini hisoblaydi. topic_ids — bitta fanning mavzulari
    (kutish fanga alohida)."""
    latest_topic_id = None
    latest_completed_at = None
    for topic_id, row in progress.items():
        if row.get('status') != STATUS_COMPLETED:
            continue
        if topic_ids is not None and topic_id not in topic_ids:
            continue
        completed_at = as_utc(row.get('completed_at'))
        if completed_at and (latest_completed_at is None or completed_at > latest_completed_at):
            latest_completed_at = completed_at
            latest_topic_id = topic_id
    return _build_cooldown(latest_topic_id, latest_completed_at)


def compute_streak(cur, user_id):
    """Ketma-ket nechta kun mavzu tugallangani — bugungisi hali bo'lmasa,
    kechadan hisoblanadi (bugun hali tugamagani streak'ni uzmaydi)."""
    cur.execute(
        '''SELECT completed_at FROM user_progress
           WHERE user_id = %s AND status = %s AND completed_at IS NOT NULL''',
        (user_id, STATUS_COMPLETED),
    )
    rows = cur.fetchall()
    if not rows:
        return 0

    days = {to_tashkent(as_utc(r['completed_at'])).date() for r in rows}
    today = to_tashkent(utc_now()).date()
    cursor_day = today if today in days else today - timedelta(days=1)

    streak = 0
    while cursor_day in days:
        streak += 1
        cursor_day -= timedelta(days=1)
    return streak


# ───────────────────────── Chaqmoq va reyting ─────────────────────────

# Har bir dars (oddiy va shaxsiy) uchun ko'pi bilan 30 chaqmoq:
#   test — BIRINCHI urinishda har to'g'ri javobga 5 (ko'pi bilan 15), qayta topshirish chaqmoq bermaydi;
#   uy vazifasi — to'liq bajarilganda 15.
# O'yinlar (Game Hub): 24 soatda 3 ta chaqmoqli o'yin, 1-o'rin +30, qolganlar +20 — games/chances.py
# Kun savoliga to'g'ri javob — +5 chaqmoq (daily.py)
QUIZ_CHAQMOQ_PER_CORRECT = 5
QUIZ_CHAQMOQ_MAX = 15
HOMEWORK_CHAQMOQ = 15
LESSON_CHAQMOQ_SQL = (
    '(CASE WHEN quiz_first_correct IS NULL THEN 0 '
    f'WHEN quiz_first_correct * {QUIZ_CHAQMOQ_PER_CORRECT} >= {QUIZ_CHAQMOQ_MAX} THEN {QUIZ_CHAQMOQ_MAX} '
    f'ELSE quiz_first_correct * {QUIZ_CHAQMOQ_PER_CORRECT} END'
    f" + CASE WHEN homework_status = 'passed' THEN {HOMEWORK_CHAQMOQ} ELSE 0 END)"
)


def quiz_chaqmoq(correct) -> int:
    return min(QUIZ_CHAQMOQ_MAX, max(0, int(correct or 0)) * QUIZ_CHAQMOQ_PER_CORRECT)


def lesson_chaqmoq_by_user(cur) -> dict:
    """{user_id: darslardan (oddiy + shaxsiy) olingan chaqmoq}."""
    out = {}
    for table in ('user_progress', 'personal_topics'):
        cur.execute(f'SELECT user_id, SUM({LESSON_CHAQMOQ_SQL}) AS c FROM {table} GROUP BY user_id')
        for r in cur.fetchall():
            out[r['user_id']] = out.get(r['user_id'], 0) + int(r['c'] or 0)
    return out


def _so_rov_keshi():
    """Bitta so'rov ichidagi chaqmoq keshi — faqat chaqiruvchi (masalan, bosh sahifa) yoqqan bo'lsa.
    Boshqa joylarda hisob o'rtasida chaqmoq o'zgarishi mumkin, shuning uchun standart holatda yo'q."""
    from flask import g, has_request_context
    return getattr(g, 'chaqmoq_kesh', None) if has_request_context() else None


def chaqmoq_parts(cur, user_id) -> dict:
    """Chaqmoq qayerdan kelgani: darslar (oddiy + shaxsiy), o'yinlar, kun savoli."""
    kesh = _so_rov_keshi()
    if kesh is not None and user_id in kesh:
        return dict(kesh[user_id])
    topics = 0
    for table in ('user_progress', 'personal_topics'):
        cur.execute(f'SELECT COALESCE(SUM({LESSON_CHAQMOQ_SQL}), 0) AS c FROM {table} WHERE user_id = %s', (user_id,))
        topics += int(cur.fetchone()['c'] or 0)
    parts = {'topics': topics, 'games': game_stats.chaqmoq_from_games(cur, user_id),
             'daily': daily.chaqmoq_total(cur, user_id)}
    if kesh is not None:
        kesh[user_id] = dict(parts)
    return parts


def compute_chaqmoq(cur, user_id) -> int:
    return sum(chaqmoq_parts(cur, user_id).values())


def today_plan(cur, user_id, daily_answered, now_ms) -> dict:
    """Bugungi reja: kun savoli, 1 ta mavzu va 1 ta o'yin (Toshkent kuni bo'yicha)."""
    start_ms = clock.period_start_ms('day', now_ms)
    day_start = datetime.fromtimestamp(start_ms / 1000, timezone.utc).replace(tzinfo=None)   # naive UTC, bazadagidek
    cur.execute('SELECT MAX(completed_at) AS c FROM user_progress WHERE user_id = %s AND status = %s',
                (user_id, STATUS_COMPLETED))
    last = as_utc((cur.fetchone() or {}).get('c'))
    topic = bool(last and last >= day_start)
    cur.execute('SELECT 1 FROM game_results WHERE user_id = %s AND created_ms >= %s LIMIT 1', (user_id, start_ms))
    game = cur.fetchone() is not None
    tasks = {'daily': bool(daily_answered), 'topic': topic, 'game': game}
    return dict(tasks, done=sum(tasks.values()), total=len(tasks))


def _all_chaqmoq(cur) -> dict:
    """{user_id: jami chaqmoq} — butun jadvallar bo'yicha yig'indi (og'ir so'rov)."""
    chaqmoq_by_user = {uid: c for uid, c in lesson_chaqmoq_by_user(cur).items() if c}
    for uid, bonus in game_stats.chaqmoq_by_user(cur).items():
        if bonus:
            chaqmoq_by_user[uid] = chaqmoq_by_user.get(uid, 0) + bonus
    for uid, bonus in daily.chaqmoq_by_user(cur).items():
        if bonus:
            chaqmoq_by_user[uid] = chaqmoq_by_user.get(uid, 0) + bonus
    return chaqmoq_by_user


# Bosh sahifadagi o'rin (limit=1) uchun umumiy yig'indi keshlanadi: har ochilishda butun jadvallarni
# yig'ish foydalanuvchi ko'paygan sari sekinlashadi. Chaqmoq yozilsa (jurnal.VERSION) yoki 30 s o'tsa —
# qayta hisoblanadi; o'quvchining o'z chaqmog'i esa har doim yangi.
RANK_CACHE_S = 30
_rank_cache = {'t': 0.0, 'v': None, 'data': None}


def _all_chaqmoq_cached(cur) -> dict:
    now = time.monotonic()
    if (_rank_cache['data'] is not None and _rank_cache['v'] == jurnal.VERSION[0]
            and now - _rank_cache['t'] < RANK_CACHE_S):
        return dict(_rank_cache['data'])
    data = _all_chaqmoq(cur)
    _rank_cache.update(t=now, v=jurnal.VERSION[0], data=dict(data))
    return data


def leaderboard(cur, user_id, limit=20):
    """Barcha foydalanuvchilar orasida chaqmoq bo'yicha reyting (mavzular + o'yinlar + kun savoli)."""
    if limit == 1:
        chaqmoq_by_user = _all_chaqmoq_cached(cur)
        mine = compute_chaqmoq(cur, user_id)
        if mine:
            chaqmoq_by_user[user_id] = mine
        else:
            chaqmoq_by_user.pop(user_id, None)
    else:
        chaqmoq_by_user = _all_chaqmoq(cur)

    if not chaqmoq_by_user:
        return {'top': [], 'me': None, 'total_players': 0}

    ranked = sorted(chaqmoq_by_user.items(), key=lambda kv: (-kv[1], kv[0]))
    # Ism va rasm faqat ko'rsatiladiganlarga (top + o'zi) — hamma foydalanuvchini yuklamaymiz
    ids = [uid for uid, _ in ranked[:limit]] + ([user_id] if user_id in chaqmoq_by_user else [])
    ids = list(dict.fromkeys(ids))
    placeholders = ', '.join(['%s'] * len(ids))
    cur.execute(f'SELECT id, name, photo_url FROM users WHERE id IN ({placeholders})', ids)
    info = {row['id']: row for row in cur.fetchall()}

    top = []
    me = None
    for rank, (uid, chaqmoq) in enumerate(ranked, start=1):
        meta = info.get(uid) or {}
        entry = {
            'rank': rank,
            'user_id': uid,
            'name': meta.get('name') or "O'quvchi",
            'photo_url': meta.get('photo_url'),
            'chaqmoq': chaqmoq,
            'me': uid == user_id,
        }
        if uid == user_id:
            me = entry
        if rank <= limit:
            top.append(entry)

    premium.decorate(cur, top + ([me] if me and me not in top else []))
    return {'top': top, 'me': me, 'total_players': len(ranked)}


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


def subject_topics(cur, user_id, subject_key):
    """Fan bo'yicha BARCHA sinflardan yig'ilgan mavzular (bitta umumiy dastur,
    grade ASC/seq ASC tartibida — soddadan murakkabga ketma-ket ochiladi)."""
    cur.execute(
        '''SELECT id, subject_key, grade, seq, slug, title, summary, duration, title_ru, summary_ru
           FROM topics WHERE subject_key = %s ORDER BY grade ASC, seq ASC''',
        (subject_key,),
    )
    topics = til.titles(cur.fetchall())
    if not topics:
        return None, []
    cur.execute(
        'SELECT * FROM subjects WHERE subject_key = %s ORDER BY grade ASC LIMIT 1',
        (subject_key,),
    )
    subject = cur.fetchone()
    progress = _progress_map(cur, user_id)
    cooldown = _cooldown_from_progress(progress, {t['id'] for t in topics})
    return subject, _compute_states(topics, progress, cooldown)


def subjects_overview(cur, user_id):
    """Barcha fanlar (barcha sinflar birlashtirilgan — hammaga bitta standart
    dastur) + har birida progress."""
    cur.execute('SELECT * FROM subjects ORDER BY grade ASC, sort_order ASC')
    all_subjects = cur.fetchall()
    if not all_subjects:
        return []

    cur.execute(
        'SELECT id, subject_key, grade, seq, slug, title, summary, duration, title_ru, summary_ru '
        'FROM topics ORDER BY grade ASC, seq ASC'
    )
    all_topics = til.titles(cur.fetchall())
    progress = _progress_map(cur, user_id)
    chosen = get_chosen_subject(cur, user_id)
    cur.execute('SELECT subject_key FROM subject_purchases WHERE user_id = %s', (user_id,))
    purchased_keys = {r['subject_key'] for r in cur.fetchall()}

    out = []
    seen_keys = set()
    for subject in all_subjects:
        key = subject['subject_key']
        if key in seen_keys:
            continue  # bir fan bir marta — mavzulari barcha sinflardan yig'iladi
        seen_keys.add(key)

        topics = [t for t in all_topics if t['subject_key'] == key]
        cooldown = _cooldown_from_progress(progress, {t['id'] for t in topics})   # har fanga alohida
        states = _compute_states(topics, progress, cooldown)
        done = sum(1 for s in states if s['state'] == STATUS_COMPLETED)
        current = next((s for s in states if s['state'] in (STATUS_CURRENT, STATUS_COOLDOWN)), None)
        locked = key != chosen and key not in purchased_keys
        out.append({
            'id': subject['id'],
            'key': key,
            'name': subject['name'],
            'icon': subject['icon'],
            'image': subject.get('image'),
            'color': subject['color'],
            'total_topics': len(states),
            'completed_topics': done,
            'percent': round(done * 100 / len(states)) if states else 0,
            'current_topic': {
                'title': current['title'], 'slug': current['slug'],
                'state': current['state'], 'grade': current['grade'],
            } if current else None,
            'finished': done == len(states) and len(states) > 0,
            'locked': locked,
            'price': SUBJECT_PRICE if locked else 0,
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
    """Bitta mavzuning holatini (o'sha fandagi — barcha sinflar bo'ylab
    birlashtirilgan — ketma-ketlikni hisobga olib) aniqlaydi."""
    cur.execute(
        '''SELECT id, subject_key, grade, seq, slug, title, summary, duration
           FROM topics WHERE subject_key = %s ORDER BY grade ASC, seq ASC''',
        (topic['subject_key'],),
    )
    siblings = cur.fetchall()
    progress = _progress_map(cur, user_id)
    cooldown = _cooldown_from_progress(progress, {t['id'] for t in siblings})
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

    if not is_subject_unlocked(cur, user_id, topic['subject_key']):
        raise StudyError(
            'Bu fan qulflangan. Ochish uchun sotib oling.',
            code='subject_locked', http_status=403,
            extra={'subject_key': topic['subject_key'], 'price': SUBJECT_PRICE},
        )

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
            f"Bu fanda bugungi mavzuni yakunladingiz. Keyingi mavzu {cooldown.get('text')}dan so'ng ochiladi. "
            f"Bu orada boshqa fanlarni o'qishingiz mumkin.",
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
    topic = til.topic(topic)

    quiz = topic['quiz']
    homework = topic['homework']

    cur.execute(
        'SELECT id, slug, seq, grade, title, title_ru FROM topics WHERE subject_key = %s ORDER BY grade ASC, seq ASC',
        (topic['subject_key'],),
    )
    siblings = til.titles(cur.fetchall())
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
            'icon': subject.get('icon') or 'book',
            'image': subject.get('image'),
            'color': subject.get('color') or '#4F7DF3',
        },
        'lesson': topic['lesson'],
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
        if q.get('visual'):
            # sanash mashqlari uchun shakl: {'shape': 'apple', 'n': 4}
            item['visual'] = q['visual']
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
            'visual': t.get('visual'),
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


_SUPERSCRIPT = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹', '0123456789')
_OPS = str.maketrans({'×': '*', '·': '*', '∙': '*', '÷': '/', '−': '-', '–': '-', '—': '-', '：': ':'})


def _compact(text) -> str:
    """Formula/ifoda uchun: bo'sh joylar va belgilar yozilishidagi farq ahamiyatsiz
    ("(x - 4)(x + 4)" = "(x-4)(x+4)", "x⁴" = "x^4", "3×4" = "3*4")."""
    s = normalize(text).translate(_OPS)
    s = re.sub(r'[⁰¹²³⁴⁵⁶⁷⁸⁹]+', lambda m: '^' + m.group(0).translate(_SUPERSCRIPT), s)
    return re.sub(r'\s+', '', s)


# Mazmunli so'z hisoblanmaydigan bog'lovchi/yordamchi so'zlar (o'zbek, rus, ingliz)
_STOPWORDS = set("""
va bilan uchun bu u ular ham esa emas yoki lekin ammo biroq chunki agar shu shuning sababli kabi orqali
bo'ladi bo'lib bo'lgan bo'lsa qiladi qilib etadi deb degan hamda yana eng juda har hech bir ikki uch
ya'ni masalan qilinadi ishlatiladi hisoblanadi kerak mumkin
и в во на с со к ко по из за от до для о об обо это как что а но или не же ли бы то так его её их он она есть
они мы вы ты я при без под над через также который которая которые является это
the a an of and or to in on at is are was were be been by for with that this it as from not but
""".split())
_TERM_RE = re.compile(r"\d+(?:[.,]\d+)?|[^\W\d_]+(?:'[^\W\d_]+)*")


def _terms(text) -> list:
    """Kutilgan javobdagi mazmunli so'zlar (takrorsiz, tartib saqlanadi): raqamlar va 3+ harfli so'zlar.
    Ro'yxat raqamlari ("1.", "2)") va qavs ichidagi qo'shimcha izoh majburiy hisoblanmaydi."""
    s = re.sub(r'(?:^|(?<=[\s;,]))\d{1,2}[.)](?=\s)', ' ', normalize(text))
    bare = re.sub(r'\([^)]*\)', ' ', s)
    if len(_TERM_RE.findall(bare)) >= 3:
        s = bare
    out = []
    for w in _TERM_RE.findall(s):
        if (w[0].isdigit() or len(w) >= 3) and w not in _STOPWORDS and w not in out:
            out.append(w)
    return out


def _term_found(term, words) -> bool:
    """So'z o'quvchi javobida bormi — qo'shimchalar farqi hisobga olinmaydi
    ("hujayra" ~ "hujayralar", "клеточная" ~ "клеточной"). Raqamlar aniq mos kelishi kerak."""
    if term[0].isdigit():
        return term.replace(',', '.') in {w.replace(',', '.') for w in words}
    req = len(term) if len(term) <= 4 else max(4, len(term) - 3)
    stem = term[:req]
    for w in words:
        if w.startswith(stem) or (len(w) >= 3 and term.startswith(w) and len(w) >= req - 2):
            return True
    return False


KEYWORD_PASS = 0.5   # gap ko'rinishidagi javobda yangi asosiy so'zlarning kamida yarmi bo'lsa — qabul


def keyword_match(given, expected, prompt='') -> bool:
    """Gap ko'rinishidagi javobni mazmuni bo'yicha tekshiradi (so'zma-so'z emas).

    Faqat haqiqiy gap/ro'yxat javobga qo'llanadi: kutilgan javobda kamida 3 ta 4+ harfli so'z
    bo'lishi kerak (formula, son, bitta atama — aniq tekshiriladi). Savolning o'zida bor so'zlar
    hisobga olinmaydi — savolni ko'chirib yozgan o'quvchi o'tib ketmasin. Qolgan ("yangi")
    asosiy so'zlarning kamida yarmi o'quvchi javobida bo'lsa — qabul."""
    terms = _terms(expected)
    if sum(1 for t in terms if not t[0].isdigit() and len(t) >= 4) < 3:
        return False
    prompt_words = _TERM_RE.findall(normalize(prompt))
    new = [t for t in terms if not _term_found(t, prompt_words)]
    if not new:
        return False
    words = _TERM_RE.findall(normalize(given))
    found = sum(1 for t in new if _term_found(t, words))
    return found >= max(1, -(-len(new) * KEYWORD_PASS // 1))


def open_answer_ok(given) -> bool:
    """Erkin javob: kamida 2 so'z va 8 ta harf/raqam (bitta harf yoki "ha" qabul qilinmaydi)."""
    g = normalize(given)
    return len(_TERM_RE.findall(g)) >= 2 and len(re.sub(r'[\W_]', '', g)) >= 8


def answers_match(given, expected, accept=None, loose=False, prompt='') -> bool:
    """Javob to'g'rimi. Har doim: aniq moslik, formula yozilishidagi farqsiz moslik va sonli tenglik.
    loose=True (uyga vazifa) — gap ko'rinishidagi javob so'zma-so'z emas, mazmuni (asosiy so'zlari)
    bo'yicha tekshiriladi; `prompt` — savol matni (undagi so'zlar javob belgisi hisoblanmaydi)."""
    g = normalize(given)
    if not g:
        return False
    candidates = [c for c in [expected] + list(accept or []) if c not in (None, '')]
    for c in candidates:
        if normalize(c) == g or _compact(c) == _compact(g):
            return True
    if loose and any(keyword_match(g, c, prompt) for c in candidates):
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
    quiz = til.topic(topic)['quiz']
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
                given = given.strip().lower() in ('true', '1', 'ha', "to'g'ri", 'togri', 'верно')
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

    earned = 0
    if state['state'] != STATUS_COMPLETED:
        first = not (prog or {}).get('quiz_attempts') and (prog or {}).get('quiz_first_correct') is None
        if first:
            earned = quiz_chaqmoq(correct)
        cur.execute(
            '''UPDATE user_progress
               SET quiz_score = %s,
                   quiz_attempts = quiz_attempts + 1,
                   quiz_passed = %s,
                   quiz_first_correct = COALESCE(quiz_first_correct, %s),
                   lesson_read = 1
               WHERE user_id = %s AND topic_id = %s''',
            (percent, 1 if passed else 0, correct, user_id, topic_id),
        )
        conn.commit()
        if earned:
            jurnal.record(cur, conn, user_id, earned, 'dars', f'dars:{topic_id}:quiz')

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
        'chaqmoq': earned,               # shu urinishda olingan (faqat birinchi urinishda)
    }


def _readable_answer(q):
    qtype = q.get('type', 'mc')
    if qtype == 'mc':
        opts = q.get('options') or []
        idx = q.get('answer', 0)
        return opts[idx] if 0 <= idx < len(opts) else ''
    if qtype == 'tf':
        return til.tf_options()[0 if q.get('answer') else 1]
    return str(q.get('answer', ''))


def submit_homework(cur, conn, user_id, topic_id, answers):
    topic, state, prog, cooldown = open_topic(cur, conn, user_id, topic_id)
    homework = til.topic(topic)['homework']
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
            # Gap ko'rinishidagi javob mazmuni bo'yicha (asosiy so'zlar), qisqa javob — aniq tekshiriladi
            ok = answers_match(given, expected, task.get('accept'), loose=True, prompt=task.get('prompt') or '')
            # Javob noto'g'ri bo'lsa — to'g'ri javob ko'rsatiladi (o'quvchi xatosidan o'rganadi)
            results.append({'id': tid, 'correct': ok, 'checked': True,
                            'correct_answer': expected if not ok else None})
        else:
            # ochiq savol — mazmunli javob yozilgan bo'lsa qabul qilinadi (bitta harf emas)
            ok = open_answer_ok(given)
            results.append({'id': tid, 'correct': ok, 'checked': False, 'correct_answer': None,
                            'hint': None if ok or not normalize(given) else
                            "Javob juda qisqa — fikringizni bir-ikki gap bilan yozing."})
        if ok:
            ok_count += 1

    passed = ok_count == len(tasks)
    status = 'passed' if passed else 'submitted'
    earned = HOMEWORK_CHAQMOQ if passed and (prog or {}).get('homework_status') != 'passed' \
        and state['state'] != STATUS_COMPLETED else 0

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
        if earned:
            jurnal.record(cur, conn, user_id, earned, 'dars', f'dars:{topic_id}:uy')

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
        'chaqmoq': earned,
    }


# ───────────────────────── Mavzuni yakunlash ─────────────────────────

def _try_complete(cur, conn, user_id, topic_id):
    """
    Barcha shartlar bajarilsa mavzuni yakunlaydi:
    dars o'qilgan + quiz o'tilgan + uyga vazifa topshirilgan.

    24 soatlik cheklov shu yerda ham tekshiriladi — BITTA FANDA bir kunda
    ikkita mavzu yakunlab bo'lmaydi (boshqa fanlarning hisobi alohida).
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

    topic = _topic_row(cur, topic_id)
    cooldown = cooldown_state(cur, user_id, topic['subject_key'] if topic else None)
    if cooldown.get('active'):
        return {
            'completed': False,
            'blocked_by_cooldown': True,
            'cooldown': cooldown,
            'message': f"Bu fanda bir kunda faqat bitta mavzu yakunlanadi. "
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
    cooldown = cooldown_state(cur, user_id)
    subjects = subjects_overview(cur, user_id)

    cur.execute(
        'SELECT COUNT(*) AS n FROM user_progress WHERE user_id = %s AND status = %s',
        (user_id, STATUS_COMPLETED),
    )
    completed_total = int(cur.fetchone()['n'] or 0)

    cur.execute('SELECT COUNT(*) AS n FROM topics')
    topics_total = int(cur.fetchone()['n'] or 0)

    # bugungi dars — birinchi ochiq (qulflanmagan) mavzu
    today = None
    for subject in subjects:
        if subject['locked']:
            continue
        if subject['current_topic']:
            today = {
                'subject_key': subject['key'],
                'subject_name': subject['name'],
                'subject_icon': subject['icon'],
                'subject_image': subject.get('image'),
                'subject_color': subject['color'],
                'topic_title': subject['current_topic']['title'],
                'topic_slug': subject['current_topic']['slug'],
                'topic_grade': subject['current_topic']['grade'],
                'state': subject['current_topic']['state'],
            }
            break

    return {
        'subjects': subjects,
        'today': today,
        'cooldown': cooldown,
        'streak': compute_streak(cur, user_id),
        'chaqmoq': compute_chaqmoq(cur, user_id),
        'stats': {
            'completed_topics': completed_total,
            'total_topics': topics_total,
            'percent': round(completed_total * 100 / topics_total) if topics_total else 0,
            'subjects_count': len(subjects),
            'finished_subjects': sum(1 for s in subjects if s['finished']),
        },
    }


# ───────────────────────── O'yin (mavzudan tashqari mashq) ─────────────────────────
#
# Rasmiy dars/progress tizimidan butunlay alohida: bu yerda javob berish
# hech qanday mavzuni yakunlamaydi, cooldown'ga ta'sir qilmaydi va chaqmoq
# bermaydi — faqat o'quvchi allaqachon o'qigan darslarini mashq qilish uchun.

def _practice_items(row):
    """Mavzu testidagi savollar — javobsiz (to'g'ri javob serverda tekshiriladi)."""
    meta = cur_mod.subject_meta(row['subject_key'])
    row = til.topic(row)
    return [{
        'topic_id': row['id'],
        'topic_title': row['title'],
        'subject_name': meta['name'],
        'q_index': i,
        'type': q.get('type', 'mc'),
        'q': q.get('q'),
        'options': q.get('options'),
    } for i, q in enumerate(row['quiz'])]


def review_questions(cur, user_id, count=10):
    """Takrorlash: zaif mavzular (o'yinlarda aniqlik past yoki mavzu testidan
    o'tilmagan) savollari. (savollar, zaif mavzular ro'yxati)."""
    weak = game_stats.weak_topics(cur, user_id)
    if not weak:
        return [], []
    ids = [w['topic_id'] for w in weak]
    marks = ', '.join(['%s'] * len(ids))
    cur.execute(f'SELECT id, title, title_ru, subject_key, quiz, ru FROM topics WHERE id IN ({marks})', ids)
    rows = {r['id']: r for r in cur.fetchall()}
    topics, pool = [], []
    for w in weak:
        row = rows.get(w['topic_id'])
        if not row:
            continue
        topics.append({'topic_id': row['id'], 'title': til.topic(row)['title'], 'accuracy': w['accuracy'],
                       'subject_name': cur_mod.subject_meta(row['subject_key'])['name']})
        pool.extend(_practice_items(row))
    random.shuffle(pool)
    return pool[:count], topics


def game_questions(cur, user_id, count=10):
    """O'quvchi darsini o'qigan (lesson_read) mavzulardan tasodifiy test
    savollari — to'g'ri javob hech qachon frontendga yuborilmaydi."""
    cur.execute(
        '''SELECT t.id, t.title, t.title_ru, t.subject_key, t.quiz, t.ru
           FROM topics t
           JOIN user_progress p ON p.topic_id = t.id AND p.user_id = %s
           WHERE p.lesson_read = 1''',
        (user_id,),
    )
    pool = []
    for row in cur.fetchall():
        pool.extend(_practice_items(row))
    random.shuffle(pool)
    return pool[:count]


def game_check_answer(cur, topic_id, q_index, given):
    """Bitta o'yin savolini tekshiradi. None qaytsa — savol topilmadi."""
    cur.execute('SELECT quiz, ru FROM topics WHERE id = %s', (topic_id,))
    row = cur.fetchone()
    if not row:
        return None
    quiz = til.topic(row)['quiz']
    try:
        q_index = int(q_index)
    except (TypeError, ValueError):
        return None
    if q_index < 0 or q_index >= len(quiz):
        return None

    q = quiz[q_index]
    qtype = q.get('type', 'mc')
    ok = False
    if qtype == 'mc':
        try:
            ok = int(given) == int(q.get('answer', 0))
        except (TypeError, ValueError):
            ok = False
    elif qtype == 'tf':
        if isinstance(given, str):
            given = given.strip().lower() in ('true', '1', 'ha', "to'g'ri", 'togri', 'верно')
        ok = bool(given) == bool(q.get('answer'))
    else:
        ok = answers_match(given, q.get('answer'), q.get('accept'))

    return {
        'correct': ok,
        'explain': q.get('explain', ''),
        'correct_answer': _readable_answer(q),
    }
