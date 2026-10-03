# -*- coding: utf-8 -*-
"""
Admin qo'shgan mavzular (admin panel → «Fanlar» → fan → «Yangi mavzu»): AI yozadi (o'zbekcha + ruscha) yoki
admin qo'lda yozadi. Mavzu fan OXIRIGA qo'shiladi — o'quvchilarning progressi va mavzular tartibi buzilmaydi.

Kod'dagi mavzular (curriculum/) sinxronlanganda bazadan kodda yo'q mavzular o'chiriladi — shuning uchun admin
mavzulari alohida admin_topics jadvalida saqlanadi va har sinxronlashdan keyin topics'ga qayta qo'yiladi
(study.sync_curriculum → apply). Keyingi tahrirlar odatdagidek topic_overrides orqali (lesson_edit).
"""

import json
import logging
import threading

import ai_tutor
import curriculum as cur_mod
import lesson_edit
from db import get_connection
from games import clock

logger = logging.getLogger('bilimsari.mavzu_qosh')

GENERATING, READY, FAILED = 'generating', 'ready', 'failed'

LESSON_PROMPT = """Sen O'zbekiston maktab dasturi bo'yicha tajribali o'qituvchi-metodistsan.
"{subject}" fanidan "{title}" mavzusida maktab darsligi uchun bitta to'liq dars tuz, o'zbek tilida (lotin yozuvida).
{izoh}
Talablar:
- "lesson": 4–6 ta blok. Haqiqiy, aniq, foydali o'quv matni; tushunarli, misollar bilan.
  Blok turlari: {{"type": "text", "title": "...", "body": "..."}}, {{"type": "example", "title": "...", "body": "..."}},
  {{"type": "steps", "title": "...", "items": ["...", "..."]}}, {{"type": "note", "body": "Esda tuting: ..."}},
  {{"type": "formula", "body": "..."}} (faqat kerak bo'lsa).
- "quiz": AYNAN 3 ta savol: {{"type": "mc", "q": "...", "options": ["...", "...", "...", "..."], "answer": 1, "explain": "..."}}
  ("answer" — to'g'ri variant indeksi 0–3) yoki {{"type": "tf", "q": "tasdiq", "answer": true, "explain": "..."}}.
- "homework": {{"intro": "...", "tasks": [2 ta topshiriq]}}:
  1) {{"id": "t1", "type": "text", "prompt": "...", "answer": "aniq qisqa javob (son yoki 1–3 so'z)", "hint": "..."}}
  2) {{"id": "t2", "type": "open", "prompt": "fikr yuritishni talab qiladigan savol"}}.
- "summary": 1–2 gapli qisqa tavsif. "duration": daqiqada (10–25).

Javobni FAQAT JSON ko'rinishida qaytar:
{{"title": "{title}", "summary": "...", "duration": 15, "lesson": [...], "quiz": [...], "homework": {{"intro": "...", "tasks": [...]}}}}"""

RU_PROMPT = """Quyidagi o'zbekcha maktab darsini rus tiliga tarjima qil. Tuzilma, bloklar soni va tartibi, savollar va
variantlar soni va tartibi, "answer" indekslari va true/false qiymatlari O'ZGARMASIN — faqat matnlar tarjima qilinsin.
Uy vazifasidagi "id" lar o'zgarmasin; "text" topshiriqning "answer"ini ham tarjima qil (son bo'lsa — o'zi).
Javobni FAQAT JSON ko'rinishida qaytar: {{"title", "summary", "lesson", "quiz", "homework"}}.

{data}"""


class TopicError(Exception):
    def __init__(self, message, http_status=400):
        super().__init__(message)
        self.message = message
        self.http_status = http_status


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admin_topics (
            id TEXT PRIMARY KEY,
            subject_key TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            grade INTEGER NOT NULL,
            seq INTEGER NOT NULL,
            slug TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            data TEXT,
            ru TEXT,
            note TEXT,
            error TEXT,
            created_ms BIGINT NOT NULL
        )
    ''')
    conn.commit()


def _load(v, default):
    try:
        return json.loads(v) if v else default
    except (TypeError, ValueError):
        return default


def _place(cur, key):
    """Fan oxiri: (subject_id, grade, seq) — hali tayyorlanayotgan admin mavzulari ham hisobga olinadi."""
    cur.execute('SELECT subject_id, grade, seq FROM topics WHERE subject_key = %s ORDER BY grade DESC, seq DESC LIMIT 1', (key,))
    last = cur.fetchone()
    if not last:
        raise TopicError("Bu fanda mavzular yo'q.")
    grade = int(last['grade'])
    cur.execute('SELECT MAX(seq) AS s FROM admin_topics WHERE subject_key = %s AND grade = %s', (key, grade))
    reserved = int((cur.fetchone() or {}).get('s') or 0)
    return last['subject_id'], grade, max(int(last['seq']), reserved) + 1


def _publish(cur, row, data, ru=None):
    """topics jadvaliga yozadi (yangi yoki mavjud qatorni yangilaydi)."""
    ru = ru or {}
    cur.execute('DELETE FROM topics WHERE id = %s', (row['id'],))
    cur.execute('''INSERT INTO topics (id, subject_id, grade, subject_key, slug, seq, title, summary, duration, lesson, quiz,
                                       homework, title_ru, summary_ru, ru)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (row['id'], row['subject_id'], int(row['grade']), row['subject_key'], row['slug'], int(row['seq']),
                 data['title'], data.get('summary') or '', int(data.get('duration') or 15),
                 json.dumps(data['lesson'], ensure_ascii=False), json.dumps(data['quiz'], ensure_ascii=False),
                 json.dumps(data.get('homework') or {}, ensure_ascii=False),
                 ru.get('title') or None, ru.get('summary') or None,
                 json.dumps({k: ru[k] for k in ('lesson', 'quiz', 'homework') if ru.get(k)}, ensure_ascii=False) if ru else None))


def _template(title) -> dict:
    return lesson_edit.validate({
        'title': title, 'summary': '', 'duration': 15,
        'lesson': [{'type': 'text', 'title': title, 'body': "Dars matnini shu yerga yozing."}],
        'quiz': [{'type': 'tf', 'q': "Savol matnini yozing.", 'answer': True}],
        'homework': {'intro': '', 'tasks': [{'type': 'open', 'prompt': "Topshiriqni yozing."}]},
    })


def create(cur, conn, key, title, mode='ai', note='', now=None) -> dict:
    now = now or clock.now_ms()
    if key not in cur_mod.SUBJECT_CATALOG:
        raise TopicError("Fan noto'g'ri.")
    title = ' '.join(str(title or '').split())[:120]
    if len(title) < 3:
        raise TopicError("Mavzu nomini yozing (kamida 3 belgi).")
    sid, grade, seq = _place(cur, key)
    slug = 'admin-' + format(now, 'x')
    row = {'id': cur_mod.topic_id(grade, key, slug), 'subject_key': key, 'subject_id': sid, 'grade': grade, 'seq': seq,
           'slug': slug, 'title': title}
    note = ' '.join(str(note or '').split())[:500]
    if mode == 'manual':
        data = _template(title)
        cur.execute('''INSERT INTO admin_topics (id, subject_key, subject_id, grade, seq, slug, title, status, data, note, created_ms)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (row['id'], key, sid, grade, seq, slug, title, READY, json.dumps(data, ensure_ascii=False), note, now))
        _publish(cur, row, data)
        conn.commit()
    else:
        cur.execute('''INSERT INTO admin_topics (id, subject_key, subject_id, grade, seq, slug, title, status, note, created_ms)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (row['id'], key, sid, grade, seq, slug, title, GENERATING, note, now))
        conn.commit()
        _spawn(row['id'])
    return get(cur, row['id'])


def _spawn(tid):
    threading.Thread(target=build, args=(tid,), name='bilimsari-mavzu-qosh', daemon=True).start()


def _clean(data, title) -> dict:
    import personal   # noqa: PLC0415 — AI javobini tozalovchi yordamchilar shaxsiy darslar bilan umumiy
    if not isinstance(data, dict):
        raise lesson_edit.EditError("AI javobi noto'g'ri.")
    quiz = [q for q in (personal._fix_question(x) for x in (data.get('quiz') or [])) if q][:3]
    if len(quiz) < 2:
        raise lesson_edit.EditError("Testda savollar yetarli emas.")
    hw = data.get('homework') or {}
    tasks = []
    for t in hw.get('tasks') or []:
        if not isinstance(t, dict):
            continue
        prompt = ' '.join(str(t.get('prompt') or '').split())[:1000]
        if not prompt:
            continue
        if t.get('type') == 'open' or not str(t.get('answer') or '').strip():
            tasks.append({'type': 'open', 'prompt': prompt})
        else:
            tasks.append({'type': 'text', 'prompt': prompt, 'answer': ' '.join(str(t['answer']).split())[:300],
                          'hint': ' '.join(str(t.get('hint') or '').split())[:500]})
    try:
        duration = min(60, max(5, int(data.get('duration') or 15)))
    except (TypeError, ValueError):
        duration = 15
    return lesson_edit.validate({'title': title, 'summary': str(data.get('summary') or '')[:290], 'duration': duration,
                                 'lesson': personal._fix_blocks(data.get('lesson')), 'quiz': quiz,
                                 'homework': {'intro': hw.get('intro') or '', 'tasks': tasks[:4]}})


def _ru(clean) -> dict:
    """Ruscha tarjima (AI). Bo'lmasa — {} (ruscha interfeysda o'zbekcha ko'rinadi)."""
    src = {k: clean[k] for k in ('title', 'summary', 'lesson', 'quiz', 'homework')}
    src['homework'] = {'intro': clean['homework'].get('intro'),
                       'tasks': [{k: v for k, v in t.items() if k != 'type'} for t in clean['homework'].get('tasks') or []]}
    data, error = ai_tutor.call_gemini_json(RU_PROMPT.format(data=json.dumps(src, ensure_ascii=False)), max_tokens=16384,
                                            timeout=180, attempts=5, waits=(3, 8, 15, 30), budget=600)
    if error or not isinstance(data, dict):
        return {}
    ru = {'title': ' '.join(str(data.get('title') or '').split())[:120],
          'summary': str(data.get('summary') or '')[:300]}
    if isinstance(data.get('lesson'), list) and len(data['lesson']) == len(clean['lesson']):
        ru['lesson'] = data['lesson']
    if isinstance(data.get('quiz'), list):
        ru['quiz'] = data['quiz']
    if isinstance(data.get('homework'), dict):
        ru['homework'] = data['homework']
    return ru


def build(tid, attempts=2):
    """Fon oqimi: AI darsni (va ruscha tarjimasini) yozadi, tekshiradi va fan oxiriga qo'shadi."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM admin_topics WHERE id = %s', (tid,))
        row = cur.fetchone()
        if not row or row['status'] != GENERATING:
            return
        subject = cur_mod.subject_meta(row['subject_key'])['name']
        izoh = f"Admin izohi: {row['note']}\n" if row.get('note') else ''
        prompt = LESSON_PROMPT.format(subject=subject, title=row['title'].replace('"', "'"), izoh=izoh)
        clean, last_error = None, None
        for _ in range(attempts):
            data, error = ai_tutor.call_gemini_json(prompt, max_tokens=16384, timeout=180, attempts=7,
                                                    waits=(3, 8, 15, 30), budget=900)
            if error:
                last_error = error
                continue
            try:
                clean = _clean(data, row['title'])
                break
            except lesson_edit.EditError as exc:
                last_error = exc.message
        if not clean:
            cur.execute('UPDATE admin_topics SET status = %s, error = %s WHERE id = %s', (FAILED, str(last_error or '')[:300], tid))
            conn.commit()
            return
        ru = _ru(clean)
        cur.execute('UPDATE admin_topics SET status = %s, data = %s, ru = %s, error = NULL WHERE id = %s AND status = %s',
                    (READY, json.dumps(clean, ensure_ascii=False), json.dumps(ru, ensure_ascii=False) if ru else None,
                     tid, GENERATING))
        if cur.rowcount == 1:
            _publish(cur, row, clean, ru)
        conn.commit()
    except Exception:  # noqa: BLE001
        conn.rollback()
        logger.exception('Admin mavzusini yaratishda xato (%s)', tid)
        cur.execute('UPDATE admin_topics SET status = %s, error = %s WHERE id = %s', (FAILED, 'server', tid))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def retry(cur, conn, tid) -> dict:
    cur.execute("UPDATE admin_topics SET status = %s, error = NULL WHERE id = %s AND status = %s", (GENERATING, tid, FAILED))
    if cur.rowcount != 1:
        raise TopicError("Faqat yaratilmay qolgan mavzuni qayta urinish mumkin.")
    conn.commit()
    _spawn(tid)
    return get(cur, tid)


def delete(cur, conn, tid):
    cur.execute('SELECT id FROM admin_topics WHERE id = %s', (tid,))
    if not cur.fetchone():
        raise TopicError("Faqat admin qo'shgan mavzuni o'chirish mumkin.", 404)
    for table in ('admin_topics', 'topics', 'topic_overrides'):
        cur.execute(f'DELETE FROM {table} WHERE {"id" if table != "topic_overrides" else "topic_id"} = %s', (tid,))
    conn.commit()


def get(cur, tid):
    cur.execute('SELECT id, subject_key, title, status, error, note, created_ms, ru FROM admin_topics WHERE id = %s', (tid,))
    r = cur.fetchone()
    if not r:
        return None
    return {'id': r['id'], 'subject_key': r['subject_key'], 'title': r['title'], 'status': r['status'], 'error': r['error'],
            'note': r['note'] or '', 'created_ms': int(r['created_ms']), 'ru': bool(r.get('ru'))}


def listing(cur, key) -> list:
    cur.execute('SELECT id FROM admin_topics WHERE subject_key = %s ORDER BY created_ms DESC', (key,))
    return [get(cur, r['id']) for r in cur.fetchall()]


def ids(cur) -> set:
    try:
        cur.execute('SELECT id FROM admin_topics')
        return {r['id'] for r in cur.fetchall()}
    except Exception:  # noqa: BLE001 — jadval hali yo'q (birinchi ishga tushish)
        return set()


def original(cur, tid):
    """Admin mavzusining dastlabki matni («Asl holiga qaytarish» uchun) yoki None."""
    cur.execute('SELECT data FROM admin_topics WHERE id = %s AND status = %s', (tid, READY))
    r = cur.fetchone()
    return _load(r['data'], None) if r else None


def apply(cur) -> int:
    """Sinxronlashdan keyin: tayyor admin mavzularini topics'ga qayta qo'yadi."""
    try:
        cur.execute('SELECT * FROM admin_topics WHERE status = %s', (READY,))
        rows = cur.fetchall()
    except Exception:  # noqa: BLE001
        return 0
    for r in rows:
        data = _load(r['data'], None)
        if data:
            _publish(cur, r, data, _load(r.get('ru'), {}))
    return len(rows)
