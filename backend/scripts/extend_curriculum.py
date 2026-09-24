# -*- coding: utf-8 -*-
"""
Mavjud curriculum/ai_curriculum.py'dagi har bir fanni TARGET_TOPICS
darajasigacha kengaytiradi — mavjud mavzularga TEGMAYDI, faqat davomini
(oldingisidan murakkabroq) qo'shadi.

Ishga tushirish: GOOGLE_AI_API_KEY (yoki GEMINI_API_KEY) muhit
o'zgaruvchisi o'rnatilgan holda, backend/ papkasidan:
    python scripts/extend_curriculum.py
"""
import ast
import json
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from curriculum import SUBJECT_CATALOG  # noqa: E402

API_KEY = (
    os.environ.get('GOOGLE_AI_API_KEY')
    or os.environ.get('GEMINI_API_KEY')
    or os.environ.get('GOOGLE_API_KEY')
    or ''
)
MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.6-flash')
OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'curriculum', 'ai_curriculum.py')

TARGET_TOPICS = 40

SCHEMA_HINT = """
Har bir mavzu quyidagi JSON tuzilishida bo'lishi shart:
{
  "slug": "lotin-harflarda-tire-bilan-nom",
  "title": "Mavzu nomi",
  "summary": "1-2 gapli qisqa tavsif",
  "duration": 15,
  "lesson": [
    {"type": "text", "title": "Kirish", "body": "..."},
    {"type": "example", "title": "Misol", "body": "..."},
    {"type": "steps", "title": "Qadamlar", "items": ["...", "..."]},
    {"type": "note", "body": "Esda tuting: ..."}
  ],
  "quiz": [
    {"type": "mc", "q": "...", "options": ["...", "...", "...", "..."], "answer": 0, "explain": "..."},
    {"type": "tf", "q": "...", "answer": true, "explain": "..."},
    {"type": "mc", "q": "...", "options": ["...", "...", "...", "..."], "answer": 2, "explain": "..."}
  ],
  "homework": {
    "intro": "Uyga vazifa haqida qisqa matn",
    "tasks": [
      {"id": "t1", "type": "text", "prompt": "...", "answer": "...", "hint": "..."},
      {"id": "t2", "type": "open", "prompt": "..."}
    ]
  }
}
"""


def build_prompt(subject_name: str, existing_titles: list, need: int) -> str:
    titles_list = '\n'.join(f'{i + 1}. {t}' for i, t in enumerate(existing_titles))
    return f"""Sen O'zbekiston maktab dasturi bo'yicha tajribali metodist-o'qituvchisan.

"{subject_name}" fanida quyidagi {len(existing_titles)} ta mavzu allaqachon tayyor (oson→murakkab tartibda):

{titles_list}

Vazifa: shu ro'yxatning DAVOMI sifatida yana {need} ta YANGI mavzu tuzib chiq, o'zbek tilida.

QOIDALAR:
- Bu {need} ta mavzu yuqoridagi {len(existing_titles)}-mavzudan HAM MURAKKABROQ bo'lsin va
  o'zi ham ichida osondan murakkabga ketma-ket joylashsin. Yuqori chegara yo'q — oxirgi
  mavzular oliy ta'lim bilan tutashadigan darajada chuqur bo'lishi mumkin.
- Yuqoridagi mavzularni TAKRORLAMA — butunlay yangi, bog'liq mavzular bo'lsin.
- Har bir mavzuning "lesson" qismi haqiqiy, foydali, aniq o'quv matni bo'lsin (umumiy gaplar emas).
- "slug" — lotin harflar, raqam, tire bilan, takrorlanmas (masalan: "kvadrat-tenglama-ildizlari").
- Test savollari (quiz) va uyga vazifa (homework) mavzuga mos, aniq javobli bo'lsin.

{SCHEMA_HINT}

Javobni FAQAT quyidagi JSON formatida qaytar (boshqa hech qanday matn, izoh yoki markdown belgisiz):
{{"topics": [ <{need} ta mavzu obyekti> ]}}
"""


def call_gemini(prompt: str) -> list:
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent'
    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 65536,
            'responseMimeType': 'application/json',
        },
    }
    r = requests.post(url, json=payload, headers={'x-goog-api-key': API_KEY}, timeout=300)
    data = r.json() if r.content else {}
    if r.status_code != 200:
        raise RuntimeError(f'Gemini xatosi ({r.status_code}): {json.dumps(data)[:500]}')
    cands = data.get('candidates') or []
    if not cands:
        raise RuntimeError(f'Gemini bo\'sh javob qaytardi: {json.dumps(data)[:500]}')
    finish_reason = cands[0].get('finishReason')
    parts = (cands[0].get('content') or {}).get('parts') or []
    text = ''.join(p.get('text', '') for p in parts if isinstance(p, dict)).strip()
    if not text:
        raise RuntimeError(f'Gemini matn qaytarmadi (finishReason={finish_reason}): {json.dumps(data)[:500]}')
    text = re.sub(r'^```(json)?|```$', '', text.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'JSON parse xatosi ({exc}), finishReason={finish_reason}, uzunlik={len(text)}')
    topics = parsed.get('topics') if isinstance(parsed, dict) else None
    if not isinstance(topics, list) or not topics:
        raise RuntimeError(f'"topics" ro\'yxati topilmadi: {json.dumps(parsed)[:300]}')
    return topics


def generate_more(subject_name: str, existing_titles: list, need: int, attempts: int = 8):
    last_err = None
    for i in range(1, attempts + 1):
        try:
            print(f'    urinish {i}/{attempts}...', flush=True)
            topics = call_gemini(build_prompt(subject_name, existing_titles, need))
            print(f'    {len(topics)} ta yangi mavzu olindi', flush=True)
            return topics
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f'    xato: {exc}', flush=True)
            time.sleep(min(5 * (2 ** (i - 1)), 90))
    raise RuntimeError(f'{attempts} urinishdan keyin ham muvaffaqiyatsiz: {last_err}')


def load_subjects() -> list:
    with open(OUT_PATH, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=OUT_PATH)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == 'SUBJECTS' for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError('SUBJECTS topilmadi')


def write_output(subjects: list):
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""AI (Gemini) tomonidan generatsiya qilingan curriculum. scripts/generate_curriculum.py + scripts/extend_curriculum.py orqali yaratilgan."""\n\n')
        f.write('SUBJECTS = ')
        f.write(_py_repr(subjects))
        f.write('\n')


def _py_repr(obj, indent=0):
    sp = '    ' * indent
    sp2 = '    ' * (indent + 1)
    if isinstance(obj, dict):
        if not obj:
            return '{}'
        items = ',\n'.join(f'{sp2}{_py_repr(k)}: {_py_repr(v, indent + 1)}' for k, v in obj.items())
        return '{\n' + items + '\n' + sp + '}'
    if isinstance(obj, list):
        if not obj:
            return '[]'
        items = ',\n'.join(f'{sp2}{_py_repr(v, indent + 1)}' for v in obj)
        return '[\n' + items + '\n' + sp + ']'
    return repr(obj)


def main():
    if not API_KEY:
        print('XATO: GOOGLE_AI_API_KEY muhit o\'zgaruvchisi topilmadi.')
        sys.exit(1)

    subjects = load_subjects()
    by_key = {s['key']: s for s in subjects}

    for key, meta in SUBJECT_CATALOG.items():
        subject = by_key.get(key)
        if not subject:
            print(f'DIQQAT: {key} SUBJECTS ichida yo\'q, o\'tkazib yuborildi')
            continue
        existing = subject['topics']
        need = TARGET_TOPICS - len(existing)
        if need <= 0:
            print(f'{key}: allaqachon {len(existing)} ta mavzu bor, o\'tkazib yuborildi')
            continue

        print(f'\n=== {key} ({meta["name"]}) — {len(existing)} bor, {need} ta kerak ===', flush=True)
        existing_slugs = {t['slug'] for t in existing}
        titles = [t['title'] for t in existing]
        try:
            new_topics = generate_more(meta['name'], titles, need)
        except Exception as exc:  # noqa: BLE001
            print(f'  [{key}] TASHLAB KETILDI: {exc}', flush=True)
            continue

        # Slug to'qnashuvlarini oldini olamiz
        added = 0
        for t in new_topics:
            slug = t.get('slug') or ''
            base = slug or f'{key}-qoshimcha'
            i = 1
            while slug in existing_slugs or not slug:
                slug = f'{base}-{i}'
                i += 1
            t['slug'] = slug
            existing_slugs.add(slug)
            existing.append(t)
            added += 1
            if len(existing) >= TARGET_TOPICS:
                break

        write_output(subjects)
        print(f'  Saqlandi: {key} endi {len(existing)} ta mavzu ({added} ta qo\'shildi)', flush=True)

    print(f'\nTayyor! {OUT_PATH}')


if __name__ == '__main__':
    main()
