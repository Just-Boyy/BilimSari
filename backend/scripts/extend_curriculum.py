# -*- coding: utf-8 -*-
"""
curriculum/ai_curriculum.py'dagi fanlarni kerakli mavzu sonigacha kengaytiradi —
mavjud mavzularga TEGMAYDI, faqat davomini (oldingisidan murakkabroq) qo'shadi.
SUBJECT_CATALOG'da bor, lekin SUBJECTS'da yo'q fan noldan (7-sinf darajasidan) yaratiladi.

Ikki tilli: har bir AI so'rovi mavzuni o'zbekcha VA ruscha birga qaytaradi
(bitta so'rovda). O'zbekchasi ai_curriculum.py'ga, ruschasi
curriculum/ru/<fan>.json'ga yoziladi — deploydan keyin sinxronlash ikkalasini
ham bazaga oladi.

Ishga tushirish: GOOGLE_AI_API_KEY (yoki GEMINI_API_KEY) muhit
o'zgaruvchisi o'rnatilgan holda, backend/ papkasidan:
    python scripts/extend_curriculum.py              # har bir fan 40 tagacha
    python scripts/extend_curriculum.py 50           # har bir fan 50 tagacha
    python scripts/extend_curriculum.py 50 math law  # faqat shu fanlar
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
CURRICULUM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'curriculum')
OUT_PATH = os.path.join(CURRICULUM_DIR, 'ai_curriculum.py')
RU_DIR = os.path.join(CURRICULUM_DIR, 'ru')

TARGET_TOPICS = int(os.environ.get('CURRICULUM_TARGET', '40'))
# Bitta so'rovda nechta mavzu (o'zbekcha + ruscha) — javob token chegarasiga sig'ishi uchun
BATCH = int(os.environ.get('CURRICULUM_BATCH', '5'))


class QuotaExhausted(RuntimeError):
    """429 — kunlik kvota tugagan; skript darhol to'xtaydi (qayta ishga
    tushirilsa, tayyor mavzularni o'tkazib yuborib davom etadi)."""

SCHEMA_HINT = """
Har bir mavzu quyidagi JSON tuzilishida bo'lishi shart ("ru" — shu mavzuning ruscha tarjimasi):
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
  },
  "ru": {
    "title": "Название темы",
    "summary": "...",
    "lesson": [
      {"type": "text", "title": "Введение", "body": "..."},
      {"type": "example", "title": "Пример", "body": "..."},
      {"type": "steps", "title": "Шаги", "items": ["...", "..."]},
      {"type": "note", "body": "Помните: ..."}
    ],
    "quiz": [
      {"type": "mc", "q": "...", "options": ["...", "...", "...", "..."], "answer": 0, "explain": "..."},
      {"type": "tf", "q": "...", "answer": true, "explain": "..."},
      {"type": "mc", "q": "...", "options": ["...", "...", "...", "..."], "answer": 2, "explain": "..."}
    ],
    "homework": {
      "intro": "...",
      "tasks": [
        {"id": "t1", "type": "text", "prompt": "...", "answer": "...", "hint": "..."},
        {"id": "t2", "type": "open", "prompt": "..."}
      ]
    }
  }
}
"""

# Fanga xos tarjima qoidalari (qolgan fanlarda hamma matn ruschaga o'giriladi)
RU_RULES = {
    'english': "Ingliz tili fani: inglizcha misollar, gaplar, test savollaridagi inglizcha jumlalar va "
               "variantlar ruschada ham INGLIZCHA qoladi; faqat o'zbekcha tushuntirishlar ruschaga o'giriladi.",
    'uzbek': "Ona tili fani: o'zbekcha misollar, so'zlar, gaplar va test variantlari ruschada ham O'ZBEKCHA "
             "qoladi; faqat tushuntirishlar ruschaga o'giriladi.",
    'russian': "Rus tili fani: ruscha misollar o'z holicha qoladi; o'zbekcha tushuntirishlar ruschaga o'giriladi.",
    'literature': "Adabiyot fani: asar nomlari rus tilidagi qabul qilingan nomi bilan (masalan, "
                  "«O'tkan kunlar» — «Минувшие дни»), she'riy iqtiboslar asl tilida qoladi.",
}


def build_prompt(subject_key: str, subject_name: str, existing_titles: list, need: int) -> str:
    if existing_titles:
        titles_list = '\n'.join(f'{i + 1}. {t}' for i, t in enumerate(existing_titles))
        task = f""""{subject_name}" fanida quyidagi {len(existing_titles)} ta mavzu allaqachon tayyor (oson→murakkab tartibda):

{titles_list}

Vazifa: shu ro'yxatning DAVOMI sifatida yana {need} ta YANGI mavzu tuzib chiq.

QOIDALAR:
- Bu {need} ta mavzu yuqoridagi {len(existing_titles)}-mavzudan HAM MURAKKABROQ bo'lsin va
  o'zi ham ichida osondan murakkabga ketma-ket joylashsin. Yuqori chegara yo'q — oxirgi
  mavzular oliy ta'lim bilan tutashadigan darajada chuqur bo'lishi mumkin.
- Yuqoridagi mavzularni TAKRORLAMA — butunlay yangi, bog'liq mavzular bo'lsin."""
    else:
        task = f"""Vazifa: "{subject_name}" fani uchun dastlabki {need} ta mavzuni tuzib chiq.

QOIDALAR:
- Daraja: eng OSON mavzu 7-sinf darajasidan PASTROQ bo'lmasin (boshlang'ich sinf
  darajasidagi mavzular MUTLAQO kerak emas). Mavzular OSONDAN MURAKKABGA qat'iy
  ketma-ketlikda joylashsin."""
    return f"""Sen O'zbekiston maktab dasturi bo'yicha tajribali metodist-o'qituvchisan.

{task}
- Har bir mavzuning "lesson" qismi haqiqiy, foydali, aniq o'quv matni bo'lsin (umumiy gaplar emas).
- "slug" — lotin harflar, raqam, tire bilan, takrorlanmas (masalan: "kvadrat-tenglama-ildizlari").
- Test savollari (quiz) va uyga vazifa (homework) mavzuga mos, aniq javobli bo'lsin.

IKKI TIL (o'zbekcha + ruscha, shu javobning o'zida):
- Asosiy maydonlar O'ZBEK tilida (lotin yozuvi). Har bir mavzuda "ru" maydoni ham bo'lsin —
  shu mavzuning TO'LIQ ruscha tarjimasi (title, summary, lesson, quiz, homework).
- "ru" tuzilmasi o'zbekchasi bilan AYNAN bir xil: lesson bloklari soni va turi, quiz savollari
  soni, turi va tartibi, har bir "mc" savoldagi variantlar soni va TARTIBI, homework "tasks"
  "id"lari. "answer" indekslari va true/false qiymatlari o'zgarmaydi.
- Ruscha matn tabiiy, savodli adabiy rus tilida bo'lsin (so'zma-so'z emas); formulalar,
  raqamlar, kod va belgilar o'zgarmaydi.
{('- ' + RU_RULES[subject_key]) if subject_key in RU_RULES else ''}

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
    if r.status_code == 429:
        # Kunlik kvota tugagan — qayta urinish foydasiz, kvota ertaga yangilanadi
        raise QuotaExhausted(f'Gemini kvotasi tugadi (429): {json.dumps(data)[:300]}')
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


def generate_more(subject_key: str, subject_name: str, existing_titles: list, need: int, attempts: int = 8):
    last_err = None
    for i in range(1, attempts + 1):
        try:
            print(f'    urinish {i}/{attempts}...', flush=True)
            topics = call_gemini(build_prompt(subject_key, subject_name, existing_titles, need))
            print(f'    {len(topics)} ta yangi mavzu olindi', flush=True)
            return topics
        except QuotaExhausted:
            raise
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f'    xato: {exc}', flush=True)
            time.sleep(min(5 * (2 ** (i - 1)), 90))
    raise RuntimeError(f'{attempts} urinishdan keyin ham muvaffaqiyatsiz: {last_err}')


def split_ru(topic: dict):
    """Mavzudan "ru" qismini ajratib oladi. Yaroqsiz bo'lsa — None (mavzu ruschada
    o'zbekcha ko'rinadi). Tuzilma qisman mos kelmasa, ilova o'sha savol/vazifani
    o'zbekcha ko'rsatadi (til.merge_quiz / til.merge_homework)."""
    ru = topic.pop('ru', None)
    if not isinstance(ru, dict) or not isinstance(ru.get('title'), str) or not ru['title'].strip():
        return None
    out = {'title': ru['title'].strip(), 'summary': ru.get('summary') or ''}
    if isinstance(ru.get('lesson'), list) and all(isinstance(b, dict) for b in ru['lesson']):
        out['lesson'] = ru['lesson']
    if isinstance(ru.get('quiz'), list):
        out['quiz'] = ru['quiz']
        uz_quiz = topic.get('quiz') or []
        bad = [i for i, q in enumerate(uz_quiz)
               if i >= len(ru['quiz']) or not isinstance(ru['quiz'][i], dict)
               or ru['quiz'][i].get('type', 'mc') != q.get('type', 'mc')
               or len(ru['quiz'][i].get('options') or []) != len(q.get('options') or [])]
        if bad:
            print(f'    diqqat: {topic.get("slug")} — {len(bad)} ta savol tuzilmasi mos emas (o\'zbekcha qoladi)', flush=True)
    if isinstance(ru.get('homework'), dict):
        out['homework'] = ru['homework']
    return out


def load_subjects() -> list:
    if not os.path.exists(OUT_PATH):
        return []
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


def save_ru(subject_key: str, new_ru: dict):
    """Yangi mavzular tarjimasini curriculum/ru/<fan>.json'ga qo'shadi (mavjudlariga tegmaydi)."""
    if not new_ru:
        return
    path = os.path.join(RU_DIR, f'{subject_key}.json')
    data = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    data.update(new_ru)
    os.makedirs(RU_DIR, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


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


def extend(target: int, only=None):
    """Har bir fanni `target` tagacha to'ldiradi; `only` — faqat shu fan kalitlari."""
    subjects = load_subjects()
    by_key = {s['key']: s for s in subjects}

    for key, meta in SUBJECT_CATALOG.items():
        if only and key not in only:
            continue
        subject = by_key.get(key) or {'key': key, 'topics': []}
        existing = subject['topics']
        if len(existing) >= target:
            print(f'{key}: allaqachon {len(existing)} ta mavzu bor, o\'tkazib yuborildi')
            continue

        print(f'\n=== {key} ({meta["name"]}) — {len(existing)} bor, {target - len(existing)} ta kerak ===', flush=True)
        existing_slugs = {t['slug'] for t in existing}
        while len(existing) < target:
            need = min(BATCH, target - len(existing))
            try:
                new_topics = generate_more(key, meta['name'], [t['title'] for t in existing], need)
            except QuotaExhausted as exc:
                print(f'  TO\'XTATILDI: {exc}', flush=True)
                return
            except Exception as exc:  # noqa: BLE001
                print(f'  [{key}] TASHLAB KETILDI: {exc}', flush=True)
                break

            new_ru = {}
            added = 0
            for t in new_topics[:need]:
                if not isinstance(t, dict):
                    continue
                ru = split_ru(t)
                # Slug to'qnashuvlarini oldini olamiz
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
                if ru:
                    new_ru[slug] = ru
                else:
                    print(f'    diqqat: {slug} — ruscha tarjima kelmadi (ruschada o\'zbekcha ko\'rinadi)', flush=True)
            if not added:
                print(f'  [{key}] AI yaroqli mavzu qaytarmadi — to\'xtatildi', flush=True)
                break

            if key not in by_key:
                subjects.append(subject)
                by_key[key] = subject
            write_output(subjects)
            save_ru(key, new_ru)
            print(f'  Saqlandi: {key} endi {len(existing)} ta mavzu (+{added}, ruschasi bilan: {len(new_ru)})', flush=True)

    print(f'\nTayyor! {OUT_PATH}')


def main(argv):
    if not API_KEY:
        print('XATO: GOOGLE_AI_API_KEY muhit o\'zgaruvchisi topilmadi.')
        sys.exit(1)
    args = list(argv)
    target = int(args.pop(0)) if args and args[0].isdigit() else TARGET_TOPICS
    unknown = [a for a in args if a not in SUBJECT_CATALOG]
    if unknown:
        print(f'XATO: noma\'lum fan(lar): {unknown}. Mavjud: {list(SUBJECT_CATALOG)}')
        sys.exit(1)
    extend(target, set(args) or None)


if __name__ == '__main__':
    main(sys.argv[1:])
