# -*- coding: utf-8 -*-
"""
AI (Gemini) yordamida to'liq curriculum generatsiya qiladi.

Har bir fan uchun 30 ta mavzu, daraja 7-sinfdan boshlab yuqoriga qarab
murakkablashadi (yuqori chegara yo'q). Natija curriculum/ai_curriculum.py
fayliga Python SUBJECTS ro'yxati sifatida yoziladi — mavjud
curriculum/__init__.py formatiga mos.

Ishga tushirish: GOOGLE_AI_API_KEY (yoki GEMINI_API_KEY) muhit
o'zgaruvchisi o'rnatilgan holda, backend/ papkasidan:
    python scripts/generate_curriculum.py
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

TOPICS_PER_SUBJECT = 30

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


def build_prompt(subject_key: str, subject_name: str) -> str:
    return f"""Sen O'zbekiston maktab dasturi bo'yicha tajribali metodist-o'qituvchisan.

Vazifa: "{subject_name}" fani uchun {TOPICS_PER_SUBJECT} ta mavzu tuzib chiq, o'zbek tilida.

QOIDALAR:
- Daraja: eng OSON mavzu 7-sinf darajasidan PASTROQ bo'lmasin (masalan, "qo'shish-ayirish" kabi
  boshlang'ich sinf darajasidagi mavzular MUTLAQO kerak emas). Yuqori chegara yo'q — oxirgi
  mavzular oliy ta'lim bilan tutashadigan darajada chuqur/murakkab bo'lishi mumkin.
- Mavzular 1-sondan {TOPICS_PER_SUBJECT}-songacha OSONDAN MURAKKABGA qat'iy ketma-ketlikda
  joylashsin (har biri oldingisidan biroz chuqurroq).
- Har bir mavzuning "lesson" qismi haqiqiy, foydali, aniq o'quv matni bo'lsin (umumiy gaplar emas).
- "slug" — lotin harflar, raqam, tire bilan, takrorlanmas (masalan: "kvadrat-tenglama-ildizlari").
- Test savollari (quiz) va uyga vazifa (homework) mavzuga mos, aniq javobli bo'lsin.

{SCHEMA_HINT}

Javobni FAQAT quyidagi JSON formatida qaytar (boshqa hech qanday matn, izoh yoki markdown belgisiz):
{{"topics": [ <{TOPICS_PER_SUBJECT} ta mavzu obyekti> ]}}
"""


def call_gemini(prompt: str) -> dict:
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


def generate_subject(subject_key: str, subject_name: str, attempts: int = 8):
    last_err = None
    for i in range(1, attempts + 1):
        try:
            print(f'  [{subject_key}] urinish {i}/{attempts}...', flush=True)
            topics = call_gemini(build_prompt(subject_key, subject_name))
            print(f'  [{subject_key}] {len(topics)} ta mavzu olindi', flush=True)
            return topics
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f'  [{subject_key}] xato: {exc}', flush=True)
            time.sleep(min(5 * (2 ** (i - 1)), 90))
    raise RuntimeError(f'{subject_key}: {attempts} urinishdan keyin ham muvaffaqiyatsiz: {last_err}')


def load_existing() -> list:
    """Oldingi (uzilib qolgan) ishga tushirishdan qisman natijani o'qiydi —
    qayta ishga tushirilganda tugallangan fanlar qayta generatsiya qilinmaydi.

    exec() o'rniga ast.literal_eval() ishlatiladi — fayl faqat sof
    literal (SUBJECTS = [...]) bo'lishi kerak, kod ijro etilmaydi."""
    if not os.path.exists(OUT_PATH):
        return []
    try:
        with open(OUT_PATH, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=OUT_PATH)
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == 'SUBJECTS' for t in node.targets
            ):
                return ast.literal_eval(node.value)
        return []
    except Exception as exc:  # noqa: BLE001
        print(f'Eski faylni o\'qib bo\'lmadi ({exc}) — noldan boshlanadi.')
        return []


def main():
    if not API_KEY:
        print('XATO: GOOGLE_AI_API_KEY muhit o\'zgaruvchisi topilmadi.')
        sys.exit(1)

    all_subjects = load_existing()
    done_keys = {s['key'] for s in all_subjects}
    if done_keys:
        print(f'Davom ettirilmoqda — tayyor: {sorted(done_keys)}', flush=True)

    failed = []
    for key, meta in SUBJECT_CATALOG.items():
        if key in done_keys:
            continue
        print(f'\n=== {key} ({meta["name"]}) ===', flush=True)
        try:
            topics = generate_subject(key, meta['name'])
        except Exception as exc:  # noqa: BLE001
            print(f'  [{key}] TASHLAB KETILDI: {exc}', flush=True)
            failed.append(key)
            continue
        all_subjects.append({'key': key, 'topics': topics})
        # Har bir fandan keyin qisman saqlaymiz — uzilib qolsa ham progress yo'qolmaydi.
        write_output(all_subjects)
        print(f'  Saqlandi: {len(all_subjects)}/{len(SUBJECT_CATALOG)} fan', flush=True)

    if failed:
        print(f'\nMUVAFFAQIYATSIZ fanlar (qayta ishga tushirsangiz, faqat shular sinaladi): {failed}')
    print(f'\nTayyor! {OUT_PATH}')


def write_output(subjects: list):
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""AI (Gemini) tomonidan generatsiya qilingan curriculum. scripts/generate_curriculum.py orqali yaratilgan."""\n\n')
        f.write('SUBJECTS = ')
        f.write(_py_repr(subjects))
        f.write('\n')


def _py_repr(obj, indent=0):
    """json.dumps'ga o'xshash, lekin Python literal (True/False/None) qaytaradi."""
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


if __name__ == '__main__':
    main()
