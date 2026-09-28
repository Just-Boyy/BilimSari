# -*- coding: utf-8 -*-
"""
Admin paneldan mavzuni tahrirlash: sarlavha, qisqa tavsif, davomiylik,
dars matni (bloklar) va test savollari.

Darslarning asl manbasi — curriculum/ paketidagi kod; baza (topics) uning
ishchi nusxasi va kod o'zgarganda qayta yoziladi. Shuning uchun admin
tahriri alohida topic_overrides jadvalida saqlanadi va har sinxronlashdan
keyin topics ustiga qayta qo'yiladi — kod yangilansa ham tahrir yo'qolmaydi.
"Asl holiga qaytarish" tahrirni o'chiradi va kod'dagi matnni tiklaydi.
Uy vazifasi tahrirlanmaydi (koddagisi qoladi).
"""

import json

import curriculum as cur_mod
from games import clock

BLOCK_TYPES = ('text', 'example', 'steps', 'formula', 'note', 'life', 'table')
QUIZ_TYPES = ('mc', 'tf', 'fill')
EDITABLE = ('title', 'summary', 'duration', 'lesson', 'quiz')
MAX_BLOCKS, MAX_QUESTIONS = 40, 30
MAX_TEXT = 4000


class EditError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS topic_overrides (
            topic_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            updated_ms BIGINT NOT NULL
        )
    ''')
    conn.commit()


# ───────────────────────── Tekshiruv ─────────────────────────

def _text(value, where, required=True, limit=MAX_TEXT) -> str:
    text = str(value if value is not None else '').strip()
    if required and not text:
        raise EditError(f"{where}: matn bo'sh bo'lmasin.")
    if len(text) > limit:
        raise EditError(f"{where}: matn juda uzun ({len(text)} belgi, ko'pi bilan {limit}).")
    return text


def _block(b, n) -> dict:
    where = f'{n}-blok'
    if not isinstance(b, dict) or b.get('type') not in BLOCK_TYPES:
        raise EditError(f"{where}: turi noto'g'ri.")
    kind = b['type']
    out = {'type': kind}
    if kind in ('text', 'example', 'steps', 'note', 'life') and str(b.get('title') or '').strip():
        out['title'] = _text(b['title'], f'{where} sarlavhasi', limit=160)
    if kind == 'steps':
        items = [str(i).strip() for i in (b.get('items') or []) if str(i).strip()]
        if not items:
            raise EditError(f"{where}: kamida bitta qadam yozing.")
        if len(items) > 20:
            raise EditError(f"{where}: qadamlar ko'pi bilan 20 ta.")
        out['items'] = [_text(i, f'{where} qadami', limit=1000) for i in items]
    elif kind == 'table':
        head = [str(h).strip() for h in (b.get('head') or [])]
        rows = [[str(c).strip() for c in r] for r in (b.get('rows') or []) if isinstance(r, list) and any(
            str(c).strip() for c in r)]
        if not 1 <= len(head) <= 6 or not all(head):
            raise EditError(f"{where}: jadval sarlavhasida 1–6 ta ustun nomi bo'lsin.")
        if not 1 <= len(rows) <= 30:
            raise EditError(f"{where}: jadvalda 1–30 ta qator bo'lsin.")
        if any(len(r) != len(head) for r in rows):
            raise EditError(f"{where}: har bir qatorda {len(head)} ta katak bo'lsin.")
        out['head'] = [_text(h, f'{where} ustuni', limit=80) for h in head]
        out['rows'] = [[_text(c, f'{where} katagi', required=False, limit=200) for c in r] for r in rows]
    else:
        out['body'] = _text(b.get('body'), where, limit=300 if kind == 'formula' else MAX_TEXT)
    return out


def _question(q, n) -> dict:
    where = f'{n}-savol'
    if not isinstance(q, dict) or q.get('type') not in QUIZ_TYPES:
        raise EditError(f"{where}: turi noto'g'ri.")
    kind = q['type']
    out = {'type': kind, 'q': _text(q.get('q'), where, limit=1000)}
    if kind == 'mc':
        options = [str(o).strip() for o in (q.get('options') or [])]
        if not 2 <= len(options) <= 6 or not all(options):
            raise EditError(f"{where}: 2–6 ta javob varianti bo'lsin, hammasi to'ldirilgan.")
        if len(set(o.lower() for o in options)) != len(options):
            raise EditError(f"{where}: javob variantlari takrorlanmasin.")
        try:
            answer = int(q.get('answer'))
        except (TypeError, ValueError):
            answer = -1
        if not 0 <= answer < len(options):
            raise EditError(f"{where}: to'g'ri javobni belgilang.")
        out['options'] = [_text(o, f'{where} varianti', limit=300) for o in options]
        out['answer'] = answer
    elif kind == 'tf':
        if not isinstance(q.get('answer'), bool):
            raise EditError(f"{where}: «To'g'ri» yoki «Noto'g'ri»ni tanlang.")
        out['answer'] = q['answer']
    else:
        out['answer'] = _text(q.get('answer'), f'{where} javobi', limit=200)
        accept = [str(a).strip() for a in (q.get('accept') or []) if str(a).strip()]
        if len(accept) > 10:
            raise EditError(f"{where}: qo'shimcha javoblar ko'pi bilan 10 ta.")
        if accept:
            out['accept'] = [_text(a, f'{where} javobi', limit=200) for a in accept]
    explain = str(q.get('explain') or '').strip()
    if explain:
        out['explain'] = _text(explain, f'{where} izohi', limit=1000)
    return out


def validate(body) -> dict:
    """Admin yuborgan ma'lumotni tekshiradi va toza nusxasini qaytaradi."""
    if not isinstance(body, dict):
        raise EditError("Ma'lumot noto'g'ri.")
    title = _text(body.get('title'), 'Sarlavha', limit=120)
    if len(title) < 3:
        raise EditError('Sarlavha kamida 3 ta belgidan iborat bo\'lsin.')
    summary = _text(body.get('summary'), 'Qisqa tavsif', required=False, limit=300)
    try:
        duration = int(body.get('duration'))
    except (TypeError, ValueError):
        duration = 0
    if not 1 <= duration <= 120:
        raise EditError("Davomiylik 1 dan 120 daqiqagacha bo'lsin.")
    lesson, quiz = body.get('lesson'), body.get('quiz')
    if not isinstance(lesson, list) or not 1 <= len(lesson) <= MAX_BLOCKS:
        raise EditError(f"Dars matnida 1–{MAX_BLOCKS} ta blok bo'lsin.")
    if not isinstance(quiz, list) or not 1 <= len(quiz) <= MAX_QUESTIONS:
        raise EditError(f"Testda 1–{MAX_QUESTIONS} ta savol bo'lsin.")
    return {
        'title': title, 'summary': summary, 'duration': duration,
        'lesson': [_block(b, i) for i, b in enumerate(lesson, start=1)],
        'quiz': [_question(q, i) for i, q in enumerate(quiz, start=1)],
    }


# ───────────────────────── Saqlash ─────────────────────────

def _load(value, default):
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _write_topic(cur, topic_id, data):
    cur.execute('UPDATE topics SET title = %s, summary = %s, duration = %s, lesson = %s, quiz = %s WHERE id = %s',
                (data['title'], data['summary'], int(data['duration']),
                 json.dumps(data['lesson'], ensure_ascii=False), json.dumps(data['quiz'], ensure_ascii=False),
                 topic_id))


def overrides(cur) -> dict:
    cur.execute('SELECT topic_id, data, updated_ms FROM topic_overrides')
    return {r['topic_id']: {'data': _load(r['data'], {}), 'updated_ms': int(r['updated_ms'])} for r in cur.fetchall()}


def apply_overrides(cur) -> int:
    """Sinxronlashdan keyin: barcha admin tahrirlarini topics ustiga qo'yadi."""
    n = 0
    for topic_id, o in overrides(cur).items():
        data = o['data']
        if all(k in data for k in EDITABLE):
            _write_topic(cur, topic_id, data)
            n += max(cur.rowcount, 0)
    return n


def _clear_ai_cache(cur, topic_id):
    try:
        cur.execute('DELETE FROM ai_explanations WHERE topic_id = %s', (topic_id,))
    except Exception:  # noqa: BLE001  (jadval yo'q bo'lsa — muhim emas)
        pass


def get(cur, topic_id):
    cur.execute('SELECT * FROM topics WHERE id = %s', (topic_id,))
    row = cur.fetchone()
    if not row:
        return None
    cur.execute('SELECT updated_ms FROM topic_overrides WHERE topic_id = %s', (topic_id,))
    o = cur.fetchone()
    return {
        'id': row['id'], 'subject_key': row['subject_key'],
        'subject_name': cur_mod.subject_meta(row['subject_key'])['name'],
        'grade': row['grade'], 'seq': row['seq'], 'title': row['title'], 'summary': row['summary'] or '',
        'duration': int(row['duration'] or 15),
        'lesson': _load(row['lesson'], []), 'quiz': _load(row['quiz'], []),
        'edited': bool(o), 'edited_ms': int(o['updated_ms']) if o else None,
    }


def save(cur, conn, topic_id, body, now=None):
    now = now or clock.now_ms()
    cur.execute('SELECT id FROM topics WHERE id = %s', (topic_id,))
    if not cur.fetchone():
        raise EditError('Mavzu topilmadi.')
    data = validate(body)
    raw = json.dumps(data, ensure_ascii=False)
    cur.execute('INSERT INTO topic_overrides (topic_id, data, updated_ms) VALUES (%s, %s, %s) '
                'ON CONFLICT (topic_id) DO UPDATE SET data = EXCLUDED.data, updated_ms = EXCLUDED.updated_ms',
                (topic_id, raw, now))
    _write_topic(cur, topic_id, data)
    _clear_ai_cache(cur, topic_id)
    conn.commit()
    return get(cur, topic_id)


def _code_topic(row):
    for subject in cur_mod.subjects_for_grade(row['grade']):
        if subject['key'] == row['subject_key']:
            for topic in subject.get('topics', []):
                if topic['slug'] == row['slug']:
                    return topic
    return None


def reset(cur, conn, topic_id):
    """Tahrirni o'chiradi va kod'dagi asl matnni tiklaydi."""
    cur.execute('SELECT id, grade, subject_key, slug FROM topics WHERE id = %s', (topic_id,))
    row = cur.fetchone()
    if not row:
        raise EditError('Mavzu topilmadi.')
    original = _code_topic(row)
    if not original:
        raise EditError("Mavzuning asl matni kodda topilmadi.")
    cur.execute('DELETE FROM topic_overrides WHERE topic_id = %s', (topic_id,))
    _write_topic(cur, topic_id, {
        'title': original['title'], 'summary': original.get('summary') or '',
        'duration': int(original.get('duration') or 15),
        'lesson': original.get('lesson') or [], 'quiz': original.get('quiz') or [],
    })
    _clear_ai_cache(cur, topic_id)
    conn.commit()
    return get(cur, topic_id)
