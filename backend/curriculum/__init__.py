"""
BilimSari o'quv dasturi (curriculum).

Bu yerda platformaning RASMIY darslari saqlanadi. AI emas — qo'lda yozilgan,
maktab dasturi tartibida. Yangi sinf/fan qo'shish uchun: gradeNN.py fayl
yarating va pastdagi _GRADE_MODULES ga qo'shing.

Ma'lumot shakli
───────────────
SUBJECTS = [
  {
    "key": "math",                  # SUBJECT_CATALOG dagi kalit
    "topics": [
      {
        "slug": "sonlar",
        "title": "Sonlar",
        "summary": "Qisqa tavsif",
        "duration": 15,             # taxminiy daqiqa
        "lesson": [ <bloklar> ],    # dars matni
        "quiz": [ <savollar> ],     # test
        "homework": {"intro": "...", "tasks": [ ... ]},
      },
    ],
  },
]

Dars bloklari (lesson):
  {"type": "text",    "title": "...", "body": "..."}
  {"type": "example", "title": "...", "body": "..."}
  {"type": "steps",   "title": "...", "items": ["...", "..."]}
  {"type": "formula", "body": "a + b = c"}
  {"type": "note",    "body": "Esda tuting: ..."}
  {"type": "life",    "body": "Hayotdan misol: ..."}
  {"type": "table",   "head": ["A", "B"], "rows": [["1", "2"]]}

Quiz savollari:
  {"type": "mc",   "q": "...", "options": [...], "answer": 0, "explain": "..."}
  {"type": "tf",   "q": "...", "answer": True,   "explain": "..."}
  {"type": "fill", "q": "...", "answer": "5",    "accept": ["besh"], "explain": "..."}

Uyga vazifa tasklari:
  {"id": "t1", "type": "number|text|open", "prompt": "...", "answer": "7", "hint": "..."}
  type "open" — javob tekshirilmaydi, faqat topshirilgani qayd etiladi.
"""

from importlib import import_module

# ───────────────────────── Fanlar katalogi ─────────────────────────

SUBJECT_CATALOG = {
    # 'icon' — js/icons.js dagi ikonka nomi (emoji emas), 'image' berilgan bo'lsa
    # frontend shu rasmni icon o'rniga ko'rsatadi (assets/ ostidagi fayl nomi).
    'math':        {'name': 'Matematika',     'icon': 'calc',     'color': '#4F7DF3', 'image': 'assets/subject-math.png'},
    'geometry':    {'name': 'Geometriya',     'icon': 'ruler',    'color': '#3B82C4'},
    'uzbek':       {'name': 'Ona tili',       'icon': 'bookOpen', 'color': '#22A06B', 'image': 'assets/subject-uzbek.png'},
    'literature':  {'name': 'Adabiyot',       'icon': 'scroll',   'color': '#8E44AD'},
    'english':     {'name': 'Ingliz tili',    'icon': 'lang',     'color': '#E74C3C', 'image': 'assets/subject-english.png'},
    'russian':     {'name': 'Rus tili',       'icon': 'chat',     'color': '#2980B9', 'image': 'assets/subject-russian.png'},
    'history':     {'name': 'Tarix',          'icon': 'landmark', 'color': '#B7791F', 'image': 'assets/subject-history.png'},
    'geography':   {'name': 'Geografiya',     'icon': 'map',      'color': '#0E9F6E', 'image': 'assets/subject-geography.png'},
    'chemistry':   {'name': 'Kimyo',          'icon': 'flask',    'color': '#E17055', 'image': 'assets/subject-chemistry.png'},
    'biology':     {'name': 'Biologiya',      'icon': 'dna',      'color': '#00B894', 'image': 'assets/subject-biology.png'},
    'law':         {'name': 'Huquq',          'icon': 'scale',    'color': '#B45309', 'image': 'assets/subject-law.png'},
    'informatics': {'name': 'Informatika',    'icon': 'code',     'color': '#475569'},
}

GRADES = list(range(1, 12))  # 1-sinfdan 11-sinfgacha

# Qaysi sinf uchun dars yozilgan bo'lsa — shu yerda
_GRADE_MODULES = {
    1: 'curriculum.grade01',
    5: 'curriculum.grade05',
    9: 'curriculum.grade09',
}

_cache: dict[int, list] = {}


def subjects_for_grade(grade: int) -> list:
    """Sinf uchun fanlar + mavzular. Dars yozilmagan sinfda — bo'sh ro'yxat."""
    grade = int(grade)
    if grade in _cache:
        return _cache[grade]
    module_path = _GRADE_MODULES.get(grade)
    if not module_path:
        _cache[grade] = []
        return []
    try:
        module = import_module(module_path)
        subjects = getattr(module, 'SUBJECTS', [])
    except ModuleNotFoundError:
        subjects = []  # bu sinf uchun dars hali yozilmagan — normal holat
    except Exception as exc:  # noqa: BLE001 — dastur to'xtamasin
        print(f'Curriculum yuklash xatosi ({module_path}): {exc}')
        subjects = []
    _cache[grade] = subjects
    return subjects


def grade_has_content(grade: int) -> bool:
    return bool(subjects_for_grade(grade))


def grades_overview() -> list:
    """Onboarding uchun: har bir sinf va unda nechta fan/mavzu borligi."""
    out = []
    for g in GRADES:
        subjects = subjects_for_grade(g)
        out.append({
            'grade': g,
            'label': f'{g}-sinf',
            'subject_count': len(subjects),
            'topic_count': sum(len(s.get('topics', [])) for s in subjects),
            'available': bool(subjects),
        })
    return out


def subject_meta(key: str) -> dict:
    return SUBJECT_CATALOG.get(key, {'name': key, 'icon': 'book', 'color': '#64748B'})


def subject_id(grade: int, key: str) -> str:
    return f'{key}-{grade}'


def topic_id(grade: int, key: str, slug: str) -> str:
    return f'{key}-{grade}-{slug}'


def find_topic(grade: int, subject_key: str, slug: str):
    for subject in subjects_for_grade(grade):
        if subject['key'] == subject_key:
            for index, topic in enumerate(subject.get('topics', []), start=1):
                if topic['slug'] == slug:
                    return subject, topic, index
    return None, None, None
