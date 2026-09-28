# -*- coding: utf-8 -*-
"""
Shaxsiy darslar — Bilim Premium imkoniyati.

O'quvchi o'zida ochiq fanni tanlab, mavzu nomini yozadi. AI avval mavzu shu
fanga tegishliligini tekshiradi va 3 ta aniq nom taklif qiladi (xato yozilgan
bo'lsa ham). O'quvchi birini tanlasa, dars (matn, 3 ta savolli test va 3 ta
topshiriqli uy vazifasi) fonda yaratiladi; tayyor bo'lgach ilovada va botda
xabar beriladi. Dars faqat o'quvchining o'zigagina ko'rinadi.

Qoidalar:
  * 24 soatda bitta dars yaratiladi (fanlar soniga qaramay). Yaratilmay qolgan
    (xato) urinish hisobga olinmaydi.
  * Shaxsiy darslarda 24 soatlik kutish yo'q — xohlagancha o'qiladi.
  * Chaqmoq oddiy darslardagidek: testning birinchi urinishida har to'g'ri
    javobga 5 (ko'pi bilan 15), uy vazifasi bajarilganda 15.
  * Uy vazifasida to'g'ri javob ko'rsatilmaydi.
  * Premium tugasa ham yaratilgan darslar qoladi; yangisini yaratib bo'lmaydi.
"""

import html
import json
import logging
import threading

import ai_tutor
import curriculum as cur_mod
import lesson_edit
import premium
import study
import tgbot
from db import get_connection
from games import clock

logger = logging.getLogger('bilimsari.personal')

GENERATE_EVERY_MS = 24 * 3600 * 1000
STALE_MS = 10 * 60 * 1000            # shuncha vaqtdan beri "yaratilmoqda" — server qayta ishga tushgan
QUIZ_SIZE = 3
HOMEWORK_SIZE = 3
GENERATING, READY, FAILED = 'generating', 'ready', 'failed'


class PersonalError(Exception):
    def __init__(self, message, code='bad_request', http_status=400):
        super().__init__(message)
        self.message, self.code, self.http_status = message, code, http_status


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS personal_topics (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            subject_key TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            summary TEXT,
            duration INTEGER,
            lesson TEXT,
            quiz TEXT,
            homework TEXT,
            error TEXT,
            created_ms BIGINT NOT NULL,
            ready_ms BIGINT,
            seen INTEGER NOT NULL DEFAULT 0,
            lesson_read INTEGER NOT NULL DEFAULT 0,
            quiz_attempts INTEGER NOT NULL DEFAULT 0,
            quiz_first_correct INTEGER,
            quiz_score INTEGER,
            quiz_passed INTEGER NOT NULL DEFAULT 0,
            homework_status TEXT NOT NULL DEFAULT 'none',
            homework_answers TEXT,
            homework_attempts INTEGER NOT NULL DEFAULT 0,
            completed_ms BIGINT
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_personal_user ON personal_topics (user_id, created_ms)')
    conn.commit()


# ───────────────────────── Yordamchilar ─────────────────────────

def _load(value, default):
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def owned_subjects(cur, user_id) -> list:
    """O'quvchida ochiq fanlar (bepul tanlangan + sotib olingan), katalog tartibida."""
    cur.execute('SELECT chosen_subject_key FROM users WHERE id = %s', (user_id,))
    keys = {(cur.fetchone() or {}).get('chosen_subject_key')}
    cur.execute('SELECT subject_key FROM subject_purchases WHERE user_id = %s', (user_id,))
    keys |= {r['subject_key'] for r in cur.fetchall()}
    return [dict(cur_mod.subject_meta(k), key=k) for k in cur_mod.SUBJECT_CATALOG if k in keys]


def limit_state(cur, user_id, now=None) -> dict:
    now = now or clock.now_ms()
    cur.execute("SELECT MAX(created_ms) AS m FROM personal_topics WHERE user_id = %s AND status != %s",
                (user_id, FAILED))
    last = int((cur.fetchone() or {}).get('m') or 0)
    next_ms = last + GENERATE_EVERY_MS if last else 0
    return {'can': now >= next_ms, 'next_ms': next_ms if now < next_ms else None,
            'seconds_left': max(0, (next_ms - now) // 1000) if now < next_ms else 0}


def _require(cur, user_id, subject_key, now):
    if not premium.is_active(premium.until(cur, user_id), now):
        raise PersonalError("Shaxsiy darslar faqat Bilim Premium bilan yaratiladi.", 'premium_required', 403)
    if subject_key not in {s['key'] for s in owned_subjects(cur, user_id)}:
        raise PersonalError("Faqat o'zingizda ochiq fanlar uchun dars yaratish mumkin.", 'not_owned', 403)
    lim = limit_state(cur, user_id, now)
    if not lim['can']:
        raise PersonalError("Har 24 soatda bitta shaxsiy dars yaratiladi. Keyingisi — "
                            f"{study.format_remaining(lim['seconds_left'])}dan so'ng.", 'limit', 429)


def _progress(r) -> dict:
    return {
        'state': 'completed' if r['completed_ms'] else ('in_progress' if r['lesson_read'] or r['quiz_attempts'] else 'current'),
        'lesson_read': bool(r['lesson_read']),
        'quiz_passed': bool(r['quiz_passed']),
        'quiz_attempts': int(r['quiz_attempts'] or 0),
        'quiz_score': r['quiz_score'],
        'homework_status': r['homework_status'] or 'none',
        'homework_answers': _load(r['homework_answers'], {}),
        'chaqmoq': (study.quiz_chaqmoq(r['quiz_first_correct']) if r['quiz_first_correct'] is not None else 0) +
                   (study.HOMEWORK_CHAQMOQ if r['homework_status'] == 'passed' else 0),
    }


def _row(cur, user_id, pid):
    cur.execute('SELECT * FROM personal_topics WHERE id = %s AND user_id = %s', (pid, user_id))
    return cur.fetchone()


# ───────────────────────── Ro'yxat ─────────────────────────

def overview(cur, user_id, now=None) -> dict:
    now = now or clock.now_ms()
    subjects = owned_subjects(cur, user_id)
    cur.execute('SELECT * FROM personal_topics WHERE user_id = %s AND status != %s ORDER BY created_ms DESC',
                (user_id, FAILED))
    rows = cur.fetchall()
    groups = {}
    for r in rows:
        meta = cur_mod.subject_meta(r['subject_key'])
        g = groups.setdefault(r['subject_key'], {'key': r['subject_key'], 'name': meta['name'],
                                                  'color': meta.get('color'), 'image': meta.get('image'),
                                                  'icon': meta.get('icon'), 'topics': []})
        item = {'id': r['id'], 'title': r['title'], 'status': r['status'], 'created_ms': int(r['created_ms'])}
        if r['status'] == READY:
            item['progress'] = _progress(r)
        g['topics'].append(item)
    order = {k: i for i, k in enumerate(cur_mod.SUBJECT_CATALOG)}
    cur.execute('SELECT id, title FROM personal_topics WHERE user_id = %s AND status = %s AND seen = 0',
                (user_id, READY))
    fresh = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT id, title, error FROM personal_topics WHERE user_id = %s AND status = %s AND seen = 0',
                (user_id, FAILED))
    failed = [dict(r) for r in cur.fetchall()]
    return {
        'premium': premium.status(cur, user_id, now),
        'limit': limit_state(cur, user_id, now),
        'subjects': subjects,
        'groups': sorted(groups.values(), key=lambda g: order.get(g['key'], 99)),
        'generating': [{'id': r['id'], 'title': r['title'], 'subject_key': r['subject_key']}
                       for r in rows if r['status'] == GENERATING],
        'fresh': fresh,
        'failed': failed,
        'total': sum(1 for r in rows if r['status'] == READY),
    }


def mark_seen(cur, conn, user_id, ids):
    ids = [int(i) for i in ids or [] if str(i).isdigit()][:50]
    if not ids:
        return
    marks = ', '.join(['%s'] * len(ids))
    cur.execute(f'UPDATE personal_topics SET seen = 1 WHERE user_id = %s AND id IN ({marks})', [user_id] + ids)
    conn.commit()


# ───────────────────────── Mavzu nomi: tekshirish va variantlar ─────────────────────────

SUGGEST_PROMPT = """Sen O'zbekiston maktab dasturi bo'yicha tajribali metodistsan.
O'quvchi "{subject}" fanidan o'zi o'rganmoqchi bo'lgan mavzuni yozdi: "{text}"

Vazifa:
1. Bu matn "{subject}" faniga tegishli o'quv mavzusimi? Imlo xatolari, qisqartma yoki noaniq yozuv
   bo'lsa ham, mazmunan shu fanga oid bo'lsa — tegishli deb hisobla. Boshqa fanga oid, o'quv
   mavzusi bo'lmagan, haqoratli yoki ma'nosiz bo'lsa — tegishli emas.
2. Tegishli bo'lsa, o'quvchi nimani nazarda tutganini eng yaxshi ifodalaydigan 3 ta ANIQ va TO'G'RI
   yozilgan mavzu nomini o'zbek tilida taklif qil (har biri 80 belgidan qisqa, bir-biridan farqli,
   birinchisi eng mosi).

Javobni FAQAT JSON ko'rinishida qaytar:
{{"relevant": true, "options": ["...", "...", "..."]}}
yoki
{{"relevant": false, "options": []}}"""


def suggest(cur, user_id, subject_key, text, now=None) -> dict:
    now = now or clock.now_ms()
    _require(cur, user_id, subject_key, now)
    text = ' '.join(str(text or '').split())
    subject = cur_mod.subject_meta(subject_key)['name']
    if len(text) < 2 or len(text) > 120:
        raise PersonalError(f"Iltimos, {subject} fanidan mavzu nomini kiriting.", 'off_topic')
    data, error = ai_tutor.call_gemini_json(SUGGEST_PROMPT.format(subject=subject, text=text.replace('"', "'")),
                                            max_tokens=1024, timeout=15, attempts=3, waits=(1, 2))
    if error:
        raise PersonalError("AI hozir javob bermadi. Birozdan keyin qayta urinib ko'ring.", 'ai_error', 502)
    options = []
    for o in (data or {}).get('options') or []:
        o = ' '.join(str(o or '').split())[:100]
        if len(o) >= 3 and o.lower() not in {x.lower() for x in options}:
            options.append(o)
    if not (data or {}).get('relevant') or not options:
        raise PersonalError(f"Iltimos, {subject} fanidan mavzu nomini kiriting.", 'off_topic')
    return {'subject': subject, 'options': options[:3]}


# ───────────────────────── Dars yaratish ─────────────────────────

LESSON_PROMPT = """Sen O'zbekiston maktab dasturi bo'yicha tajribali o'qituvchi-metodistsan.
"{subject}" fanidan "{title}" mavzusida bitta to'liq dars tuz, o'zbek tilida (lotin yozuvida).

Talablar:
- "lesson": 4–7 ta blok. Haqiqiy, aniq, foydali o'quv matni; tushunarli, misollar bilan.
  Blok turlari: {{"type": "text", "title": "...", "body": "..."}}, {{"type": "example", "title": "...", "body": "..."}},
  {{"type": "steps", "title": "...", "items": ["...", "..."]}}, {{"type": "note", "body": "Esda tuting: ..."}},
  {{"type": "formula", "body": "..."}} (faqat kerak bo'lsa).
- "quiz": AYNAN 3 ta savol, aynan shu ko'rinishda:
  {{"type": "mc", "q": "savol matni", "options": ["...", "...", "...", "..."], "answer": 1, "explain": "..."}}
  ("answer" — to'g'ri variant indeksi 0–3) yoki {{"type": "tf", "q": "tasdiq", "answer": true, "explain": "..."}}.
- "homework": {{"intro": "...", "tasks": [AYNAN 3 ta topshiriq]}}. Har bir topshiriq:
  {{"id": "t1", "type": "number" yoki "text", "prompt": "...", "answer": "aniq qisqa javob", "hint": "..."}}.
  Javob bitta son yoki 1–3 so'zdan iborat bo'lsin (tekshirib bo'ladigan).
- "summary": 1–2 gapli qisqa tavsif. "duration": daqiqada (10–25).

Javobni FAQAT JSON ko'rinishida qaytar:
{{"title": "{title}", "summary": "...", "duration": 15, "lesson": [...], "quiz": [...], "homework": {{"intro": "...", "tasks": [...]}}}}"""


def _clean_homework(hw) -> dict:
    if not isinstance(hw, dict):
        raise lesson_edit.EditError("Uy vazifasi yo'q.")
    tasks = []
    for t in hw.get('tasks') or []:
        if not isinstance(t, dict) or len(tasks) == HOMEWORK_SIZE:
            continue
        prompt = ' '.join(str(t.get('prompt') or t.get('question') or t.get('task') or '').split())[:1000]
        answer = ' '.join(str(t.get('answer') or '').split())
        if not prompt or not answer or len(answer) > 200:
            continue
        tasks.append({'id': f't{len(tasks) + 1}', 'type': 'number' if t.get('type') == 'number' else 'text',
                      'prompt': prompt, 'answer': answer, 'hint': ' '.join(str(t.get('hint') or '').split())[:300]})
    if len(tasks) != HOMEWORK_SIZE:
        raise lesson_edit.EditError(f"Uy vazifasida {HOMEWORK_SIZE} ta topshiriq bo'lishi kerak.")
    return {'intro': ' '.join(str(hw.get('intro') or '').split())[:600], 'tasks': tasks}


def _txt(value, limit):
    return str(value if value is not None else '').strip()[:limit]


def _fix_blocks(blocks) -> list:
    """AI yozgan bloklardagi mayda kamchiliklarni tuzatadi (noma'lum tur, juda uzun matn,
    bo'sh qadamlar) — lesson_edit.validate rad etmasligi uchun."""
    out = []
    for b in blocks if isinstance(blocks, list) else []:
        if not isinstance(b, dict):
            continue
        kind = b.get('type') if b.get('type') in lesson_edit.BLOCK_TYPES else ('text' if b.get('body') else None)
        if kind in (None, 'table'):
            continue                        # jadval AI'da ko'pincha buziladi — tashlab ketiladi
        item = {'type': kind}
        if kind in ('text', 'example', 'steps', 'note', 'life') and _txt(b.get('title'), 150):
            item['title'] = _txt(b.get('title'), 150)
        if kind == 'steps':
            steps = [_txt(i, 900) for i in (b.get('items') or []) if _txt(i, 900)][:20]
            if not steps:
                continue
            item['items'] = steps
        else:
            body = _txt(b.get('body'), 290 if kind == 'formula' else lesson_edit.MAX_TEXT - 100)
            if not body:
                continue
            item['body'] = body
        out.append(item)
    return out[:lesson_edit.MAX_BLOCKS]


def _fix_question(q):
    if not isinstance(q, dict):
        return None
    savol = _txt(q.get('q') or q.get('question') or q.get('text'), 900)   # AI ba'zan boshqa nom bilan yozadi
    if not savol:
        return None
    out = {'type': q.get('type'), 'q': savol}
    if _txt(q.get('explain'), 900):
        out['explain'] = _txt(q.get('explain'), 900)
    if q.get('type') == 'tf':
        a = q.get('answer')
        if isinstance(a, str):
            a = a.strip().lower() in ('true', 'ha', "to'g'ri", '1')
        out['answer'] = bool(a)
        return out
    if q.get('type') != 'mc':
        return None
    raw = [_txt(o, 290) for o in (q.get('options') or [])]
    answer = q.get('answer')
    if isinstance(answer, str) and not answer.strip().isdigit():
        answer = next((i for i, o in enumerate(raw) if o.lower() == answer.strip().lower()), -1)
    try:
        answer = int(answer)
    except (TypeError, ValueError):
        return None
    if not 0 <= answer < len(raw) or not raw[answer]:
        return None
    right = raw[answer]
    options, seen = [], set()
    for o in raw:
        if o and o.lower() not in seen:
            seen.add(o.lower())
            options.append(o)
    options = options[:6]
    if right not in options:
        options[-1] = right
    if len(options) < 2:
        return None
    out['options'] = options
    out['answer'] = options.index(right)
    return out


def _clean_lesson(data, title) -> dict:
    if not isinstance(data, dict):
        raise lesson_edit.EditError("Dars topilmadi.")
    quiz = [q for q in (_fix_question(x) for x in (data.get('quiz') or [])) if q][:QUIZ_SIZE]
    if len(quiz) != QUIZ_SIZE:
        raise lesson_edit.EditError(f"Testda {QUIZ_SIZE} ta savol bo'lishi kerak.")
    data = dict(data, lesson=_fix_blocks(data.get('lesson')), summary=_txt(data.get('summary'), 290))
    try:
        duration = min(60, max(5, int(data.get('duration') or 15)))
    except (TypeError, ValueError):
        duration = 15
    clean = lesson_edit.validate({'title': title, 'summary': data.get('summary') or '', 'duration': duration,
                                  'lesson': data.get('lesson'), 'quiz': quiz})
    clean['homework'] = _clean_homework(data.get('homework'))
    return clean


def generate(cur, conn, user, subject_key, title, now=None) -> dict:
    """Darsni yaratishni boshlaydi (fonda). Yangi qator ma'lumotini qaytaradi."""
    now = now or clock.now_ms()
    _require(cur, user['id'], subject_key, now)
    title = ' '.join(str(title or '').split())[:120]
    if len(title) < 3:
        raise PersonalError("Mavzu nomini tanlang.", 'bad_title')
    cur.execute('SELECT 1 FROM personal_topics WHERE user_id = %s AND status = %s', (user['id'], GENERATING))
    if cur.fetchone():
        raise PersonalError("Bitta dars allaqachon tayyorlanmoqda. Tayyor bo'lishini kuting.", 'busy', 409)
    cur.execute('INSERT INTO personal_topics (user_id, subject_key, title, status, created_ms) '
                'VALUES (%s, %s, %s, %s, %s) RETURNING id', (user['id'], subject_key, title, GENERATING, now))
    pid = cur.fetchone()['id']
    conn.commit()
    threading.Thread(target=build, args=(pid,), name='bilimsari-personal', daemon=True).start()
    return {'id': pid, 'title': title, 'subject_key': subject_key, 'status': GENERATING}


def build(pid, attempts=2):
    """Fon oqimi: AI darsni yozadi, tekshiriladi va saqlanadi; o'quvchiga botda xabar."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT p.*, u.telegram_id FROM personal_topics p JOIN users u ON u.id = p.user_id WHERE p.id = %s',
                    (pid,))
        row = cur.fetchone()
        if not row or row['status'] != GENERATING:
            return
        subject = cur_mod.subject_meta(row['subject_key'])['name']
        prompt = LESSON_PROMPT.format(subject=subject, title=row['title'].replace('"', "'"))
        clean, last_error = None, None
        for _ in range(attempts):
            data, error = ai_tutor.call_gemini_json(prompt, max_tokens=16384, timeout=180, attempts=5,
                                                    waits=(3, 8, 15, 30))
            if error:
                last_error = error
                continue
            try:
                clean = _clean_lesson(data, row['title'])
                break
            except lesson_edit.EditError as exc:
                last_error = exc.message
        now = clock.now_ms()
        if clean:
            cur.execute('''UPDATE personal_topics SET status = %s, summary = %s, duration = %s, lesson = %s, quiz = %s,
                                                      homework = %s, ready_ms = %s WHERE id = %s AND status = %s''',
                        (READY, clean['summary'], clean['duration'], json.dumps(clean['lesson'], ensure_ascii=False),
                         json.dumps(clean['quiz'], ensure_ascii=False), json.dumps(clean['homework'], ensure_ascii=False),
                         now, pid, GENERATING))
            conn.commit()
            if row['telegram_id']:
                tgbot.send(row['telegram_id'],
                           f"✅ <b>Shaxsiy darsingiz tayyor!</b>\n«{html.escape(row['title'])}» ({html.escape(subject)}) "
                           f"shaxsiy darslaringizga qo'shildi.", 'Darsni ochish', f'topic.html?shaxsiy={pid}')
        else:
            logger.warning('Shaxsiy dars yaratilmadi (%s): %s', pid, last_error)
            cur.execute('UPDATE personal_topics SET status = %s, error = %s WHERE id = %s AND status = %s',
                        (FAILED, str(last_error or '')[:300], pid, GENERATING))
            conn.commit()
            if row['telegram_id']:
                tgbot.send(row['telegram_id'],
                           f"❌ «{html.escape(row['title'])}» darsini tayyorlab bo'lmadi. Qayta urinib ko'ring — "
                           f"bu urinish 24 soatlik limitga hisoblanmadi.", 'Qayta urinish', 'shaxsiy.html')
    except Exception:  # noqa: BLE001
        conn.rollback()
        logger.exception('Shaxsiy dars yaratishda xato (%s)', pid)
        cur.execute('UPDATE personal_topics SET status = %s, error = %s WHERE id = %s AND status = %s',
                    (FAILED, 'server', pid, GENERATING))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def housekeeping(cur, conn, now=None):
    """Server qayta ishga tushib, yarim qolgan yaratishlar — xato deb belgilanadi (limit qaytadi)."""
    now = now or clock.now_ms()
    cur.execute('UPDATE personal_topics SET status = %s, error = %s WHERE status = %s AND created_ms < %s',
                (FAILED, 'timeout', GENERATING, now - STALE_MS))
    conn.commit()


# ───────────────────────── Darsni o'qish ─────────────────────────

def payload(cur, conn, user_id, pid, now=None) -> dict:
    r = _row(cur, user_id, pid)
    if not r:
        raise PersonalError('Dars topilmadi.', 'not_found', 404)
    if r['status'] == GENERATING:
        raise PersonalError("Dars hali tayyorlanmoqda. Tayyor bo'lgach xabar beramiz.", 'generating', 409)
    if r['status'] != READY:
        raise PersonalError('Dars topilmadi.', 'not_found', 404)
    if not r['seen']:
        cur.execute('UPDATE personal_topics SET seen = 1 WHERE id = %s', (pid,))
        conn.commit()
    meta = cur_mod.subject_meta(r['subject_key'])
    quiz = _load(r['quiz'], [])
    return {
        'personal': True, 'id': r['id'], 'title': r['title'], 'summary': r['summary'] or '',
        'duration': int(r['duration'] or 15),
        'subject': {'key': r['subject_key'], 'name': meta['name'], 'icon': meta.get('icon') or 'book',
                    'image': meta.get('image'), 'color': meta.get('color') or '#4F7DF3'},
        'lesson': _load(r['lesson'], []),
        'quiz': study.public_quiz(quiz),
        'quiz_pass_percent': study.QUIZ_PASS_PERCENT,
        'homework': study.public_homework(_load(r['homework'], {})),
        'progress': _progress(r),
        'premium': premium.is_active(premium.until(cur, user_id), now),
    }


def mark_read(cur, conn, user_id, pid):
    if not _row(cur, user_id, pid):
        raise PersonalError('Dars topilmadi.', 'not_found', 404)
    cur.execute('UPDATE personal_topics SET lesson_read = 1 WHERE id = %s', (pid,))
    conn.commit()


def _complete_if_ready(cur, conn, pid, now):
    cur.execute('SELECT * FROM personal_topics WHERE id = %s', (pid,))
    r = cur.fetchone()
    if r['completed_ms'] or not (r['lesson_read'] and r['quiz_passed'] and r['homework_status'] == 'passed'):
        return None
    cur.execute('UPDATE personal_topics SET completed_ms = %s WHERE id = %s', (now, pid))
    conn.commit()
    return {'completed': True, 'personal': True, 'message': 'Tabriklaymiz! Mavzuni muvaffaqiyatli yakunladingiz.'}


def grade_quiz(cur, conn, user_id, pid, answers, now=None) -> dict:
    now = now or clock.now_ms()
    r = _row(cur, user_id, pid)
    if not r or r['status'] != READY:
        raise PersonalError('Dars topilmadi.', 'not_found', 404)
    if not isinstance(answers, list):
        raise PersonalError("Javoblar formati noto'g'ri", 'bad_input')
    quiz = _load(r['quiz'], [])
    results, correct = [], 0
    for i, q in enumerate(quiz):
        given = answers[i] if i < len(answers) else None
        if q.get('type') == 'tf':
            if isinstance(given, str):
                given = given.strip().lower() in ('true', '1', 'ha', "to'g'ri", 'togri')
            ok = bool(given) == bool(q.get('answer'))
        else:
            try:
                ok = int(given) == int(q.get('answer', 0))
            except (TypeError, ValueError):
                ok = False
        correct += ok
        results.append({'index': i, 'correct': ok, 'explain': q.get('explain', ''),
                        'correct_answer': study._readable_answer(q)})
    total = len(quiz)
    percent = round(correct * 100 / total) if total else 0
    passed = percent >= study.QUIZ_PASS_PERCENT
    first = not r['quiz_attempts'] and r['quiz_first_correct'] is None
    cur.execute('''UPDATE personal_topics SET quiz_score = %s, quiz_attempts = quiz_attempts + 1,
                                              quiz_passed = CASE WHEN quiz_passed = 1 THEN 1 ELSE %s END,
                                              quiz_first_correct = COALESCE(quiz_first_correct, %s), lesson_read = 1
                   WHERE id = %s''', (percent, int(passed), correct, pid))
    conn.commit()
    return {
        'correct': correct, 'total': total, 'percent': percent, 'passed': passed,
        'pass_percent': study.QUIZ_PASS_PERCENT, 'results': results,
        'message': ("Ajoyib! Testdan o'tdingiz." if passed
                    else "Yana bir bor mavzuni o'rganib, quizni qayta ishlashingiz mumkin."),
        'completion': _complete_if_ready(cur, conn, pid, now) if passed else None,
        'chaqmoq': study.quiz_chaqmoq(correct) if first else 0,
    }


def submit_homework(cur, conn, user_id, pid, answers, now=None) -> dict:
    now = now or clock.now_ms()
    r = _row(cur, user_id, pid)
    if not r or r['status'] != READY:
        raise PersonalError('Dars topilmadi.', 'not_found', 404)
    if not isinstance(answers, dict):
        raise PersonalError("Javoblar formati noto'g'ri", 'bad_input')
    tasks = _load(r['homework'], {}).get('tasks', [])
    results, ok_count = [], 0
    for t in tasks:
        ok = study.answers_match(answers.get(t['id'], ''), t.get('answer'), t.get('accept'))
        ok_count += ok
        results.append({'id': t['id'], 'correct': ok, 'checked': True, 'correct_answer': None})
    passed = bool(tasks) and ok_count == len(tasks)
    earned = study.HOMEWORK_CHAQMOQ if passed and r['homework_status'] != 'passed' else 0
    cur.execute('''UPDATE personal_topics SET homework_status = CASE WHEN homework_status = 'passed' THEN 'passed' ELSE %s END,
                                              homework_answers = %s, homework_attempts = homework_attempts + 1
                   WHERE id = %s''', ('passed' if passed else 'submitted', json.dumps(answers, ensure_ascii=False), pid))
    conn.commit()
    missing = len(tasks) - ok_count
    return {
        'passed': passed, 'correct': ok_count, 'total': len(tasks), 'results': results,
        'message': ('Uyga vazifa qabul qilindi!' if passed
                    else f"{missing} ta javob noto'g'ri yoki bo'sh. Tekshirib, qayta yuboring."),
        'completion': _complete_if_ready(cur, conn, pid, now) if passed else None,
        'chaqmoq': earned,
    }


def ai_context(cur, user_id, pid):
    """AI tushuntirish uchun: (fan nomi, sarlavha, matn) — faqat egasiga."""
    r = _row(cur, user_id, pid)
    if not r or r['status'] != READY:
        return None, None, None
    parts = []
    for b in _load(r['lesson'], []):
        parts += [b.get('title') or '', b.get('body') or ''] + list(b.get('items') or [])
    return cur_mod.subject_meta(r['subject_key'])['name'], r['title'], '\n'.join(p for p in parts if p)[:4000]
