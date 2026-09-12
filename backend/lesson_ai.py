"""AI orqali dars generatsiya + DB cache"""
import json
import os
import re
import requests

GOOGLE_AI_API_KEY = (
    os.environ.get('GOOGLE_AI_API_KEY')
    or os.environ.get('GEMINI_API_KEY')
    or os.environ.get('GOOGLE_API_KEY')
    or ''
)
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash-lite')

COURSE_META = {
    'english': {'name': 'Ingliz tili', 'lang': 'uz', 'focus': 'English vocabulary, phrases, grammar for beginners'},
    'uzbek': {'name': "Ona tili", 'lang': 'uz', 'focus': "O'zbek tili imlo, so'z va gap"},
    'russian': {'name': 'Rus tili', 'lang': 'uz', 'focus': 'Russian basics for Uzbek speakers'},
    'geography': {'name': 'Geografiya', 'lang': 'uz', 'focus': "Geografiya: dunyo, O'zbekiston, tabiat"},
    'math': {'name': 'Matematika', 'lang': 'uz', 'focus': 'School math: arithmetic, basics'},
    'geometry': {'name': 'Geometriya', 'lang': 'uz', 'focus': 'Geometry basics'},
    'biology': {'name': 'Biologiya', 'lang': 'uz', 'focus': 'Biology basics for school'},
    'law': {'name': 'Huquq', 'lang': 'uz', 'focus': "Huquq asoslari"},
    'literature': {'name': 'Adabiyot', 'lang': 'uz', 'focus': "O'zbek adabiyoti"},
    'history': {'name': 'Tarix', 'lang': 'uz', 'focus': "Tarix asoslari"},
    'physics': {'name': 'Fizika', 'lang': 'uz', 'focus': 'Physics basics'},
    'chemistry': {'name': 'Kimyo', 'lang': 'uz', 'focus': 'Chemistry basics'},
}


def ensure_ai_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ai_lessons (
            id SERIAL PRIMARY KEY,
            course_id TEXT NOT NULL,
            seq INTEGER NOT NULL,
            title TEXT NOT NULL,
            unit_title TEXT,
            questions JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE (course_id, seq)
        )
    ''')
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_ai_lessons_course
        ON ai_lessons (course_id, seq)
    ''')
    conn.commit()


def list_lessons(cur, course_id):
    cur.execute(
        '''
        SELECT id, course_id, seq, title, unit_title
        FROM ai_lessons
        WHERE course_id = %s
        ORDER BY seq ASC
        ''',
        (course_id,),
    )
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_lesson(cur, course_id, seq):
    cur.execute(
        '''
        SELECT id, course_id, seq, title, unit_title, questions
        FROM ai_lessons
        WHERE course_id = %s AND seq = %s
        ''',
        (course_id, seq),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def max_seq(cur, course_id):
    cur.execute('SELECT COALESCE(MAX(seq), 0) AS m FROM ai_lessons WHERE course_id = %s', (course_id,))
    return int(cur.fetchone()['m'] or 0)


def _extract_json(text: str):
    text = (text or '').strip()
    if not text:
        return None
    # strip markdown fences
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def _normalize_questions(raw):
    out = []
    if not isinstance(raw, list):
        return out
    for item in raw[:8]:
        if not isinstance(item, dict):
            continue
        t = (item.get('type') or 'mc').lower()
        if t not in ('mc', 'tf', 'fill'):
            t = 'mc'
        q = {
            'type': t,
            'q': str(item.get('q') or item.get('question') or '').strip(),
        }
        if not q['q']:
            continue
        if t == 'mc':
            opts = item.get('options') or []
            if not isinstance(opts, list):
                opts = []
            opts = [str(o) for o in opts][:4]
            while len(opts) < 2:
                opts.append('—')
            ans = item.get('answer', 0)
            try:
                ans = int(ans)
            except Exception:
                ans = 0
            if ans < 0 or ans >= len(opts):
                ans = 0
            q['options'] = opts
            q['answer'] = ans
        elif t == 'tf':
            ans = item.get('answer', True)
            if isinstance(ans, str):
                ans = ans.lower() in ('true', '1', 'ha', 'to‘g‘ri', 'togri')
            q['answer'] = bool(ans)
        else:
            q['answer'] = str(item.get('answer') or '').strip()
            if not q['answer']:
                continue
        out.append(q)
    return out


def generate_lesson_via_ai(course_id: str, seq: int, previous_title: str = ''):
    meta = COURSE_META.get(course_id, {
        'name': course_id,
        'lang': 'uz',
        'focus': course_id,
    })
    if not GOOGLE_AI_API_KEY:
        return None, 'GOOGLE_AI_API_KEY yo‘q'

    prev = previous_title or 'boshlanish'
    prompt = f"""Sen BilimSari ta'lim platformasi uchun dars muallifisan.
Fan: {meta['name']} ({course_id})
Mavzu yo'nalishi: {meta['focus']}
Bu dars tartib raqami: {seq}
Oldingi dars: {prev}

Vazifa: KEYINGI yangi darsni yarat (takrorlama).
Javobni FAQAT JSON qaytar, hech qanday izohsiz.

Format:
{{
  "title": "Qisqa dars nomi (o'zbekcha)",
  "unit_title": "Bo'lim nomi",
  "questions": [
    {{"type": "mc", "q": "Savol matni?", "options": ["A", "B", "C", "D"], "answer": 0}},
    {{"type": "tf", "q": "Tasdiq gap.", "answer": true}},
    {{"type": "mc", "q": "Yana savol?", "options": ["A", "B", "C", "D"], "answer": 1}},
    {{"type": "fill", "q": "Bo'sh joyni to'ldiring: ...", "answer": "javob"}},
    {{"type": "mc", "q": "Yana bir savol", "options": ["A", "B", "C", "D"], "answer": 2}}
  ]
}}

Qoidalar:
- Kamida 5 ta savol
- type: faqat mc, tf yoki fill
- mc da answer — to'g'ri variant indeksi (0 dan)
- O'quvchi darajasi: maktab, boshlang'ich-o'rta
- Savollar aniq va tekshirish mumkin bo'lsin
- Matnlar o'zbek tilida (fan ingliz/rus bo'lsa atamalar aralashishi mumkin)
"""

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{GEMINI_MODEL}:generateContent?key={GOOGLE_AI_API_KEY}'
    )
    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 2048,
            'responseMimeType': 'application/json',
        },
    }
    try:
        r = requests.post(url, json=payload, timeout=60)
        data = r.json() if r.content else {}
        if r.status_code != 200:
            err = (data.get('error') or {}).get('message') or r.text[:200]
            return None, f'AI xato: {err}'
        parts = (((data.get('candidates') or [{}])[0]).get('content') or {}).get('parts') or []
        text = ''.join((p.get('text') or '') for p in parts if isinstance(p, dict))
        parsed = _extract_json(text)
        if not parsed:
            return None, 'AI JSON qaytarmadi'
        title = str(parsed.get('title') or f'Dars {seq}').strip()[:120]
        unit_title = str(parsed.get('unit_title') or f'Bo‘lim {(seq - 1) // 5 + 1}').strip()[:120]
        questions = _normalize_questions(parsed.get('questions'))
        if len(questions) < 3:
            return None, 'AI savollari yetarli emas'
        return {
            'title': title,
            'unit_title': unit_title,
            'questions': questions,
        }, None
    except Exception as e:
        return None, str(e)


def get_or_create_next_lesson(cur, conn, course_id: str):
    ensure_ai_tables(cur, conn)
    cur_max = max_seq(cur, course_id)
    next_seq = cur_max + 1

    # agar allaqachon bo'lsa (race)
    existing = get_lesson(cur, course_id, next_seq)
    if existing:
        return existing, None

    prev_title = ''
    if cur_max > 0:
        prev = get_lesson(cur, course_id, cur_max)
        if prev:
            prev_title = prev.get('title') or ''

    generated, err = generate_lesson_via_ai(course_id, next_seq, prev_title)
    if err:
        return None, err

    cur.execute(
        '''
        INSERT INTO ai_lessons (course_id, seq, title, unit_title, questions)
        VALUES (%s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (course_id, seq) DO UPDATE
          SET title = EXCLUDED.title
        RETURNING id, course_id, seq, title, unit_title, questions
        ''',
        (
            course_id,
            next_seq,
            generated['title'],
            generated['unit_title'],
            json.dumps(generated['questions'], ensure_ascii=False),
        ),
    )
    row = cur.fetchone()
    conn.commit()
    return dict(row), None


def ensure_min_lessons(cur, conn, course_id: str, minimum: int = 1):
    """Kursda kamida N ta dars bo'lsin — yo'q bo'lsa AI yaratadi."""
    ensure_ai_tables(cur, conn)
    n = max_seq(cur, course_id)
    while n < minimum:
        lesson, err = get_or_create_next_lesson(cur, conn, course_id)
        if err:
            return err
        n = max_seq(cur, course_id)
    return None
