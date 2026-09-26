# -*- coding: utf-8 -*-
"""
O'yinlar katalogi — yagona manba.

Yangi o'yin qo'shish uchun GAMES ga bitta yozuv va (kerak bo'lsa)
questions.PROVIDERS ga savol generatori qo'shiladi. Frontend ro'yxatni
/api/games/catalog orqali oladi, shuning uchun mavjud kodni buzish shart emas.
"""

import curriculum as cur_mod
from games.errors import GameError

DIFFICULTIES = {'oson': 'Oson', 'orta': "O'rta", 'qiyin': 'Qiyin'}
PLAYER_LIMITS = (2, 4, 8, 16)
QUESTION_COUNTS = (5, 10, 15, 20)
REVEAL_SECONDS = 4

CURRICULUM_SUBJECTS = tuple(cur_mod.SUBJECT_CATALOG.keys())

MATH_TOPICS = (
    ('qoshish', "Qo'shish va ayirish"),
    ('kopaytirish', "Ko'paytirish"),
    ('bolish', "Bo'lish"),
    ('kasrlar', 'Kasrlar'),
    ('foizlar', 'Foizlar'),
    ('darajalar', 'Darajalar va ildizlar'),
)

WORD_TOPICS = {
    'uzbek': (
        ('sinonim', 'Sinonimlar'),
        ('antonim', 'Antonimlar'),
    ),
    'english': (
        ('tarjima', 'Tarjima'),
        ('sinonim', 'Sinonimlar (synonyms)'),
        ('antonim', 'Antonimlar (antonyms)'),
        ('imlo', "To'g'ri yozilish (spelling)"),
    ),
}

CODE_TOPICS = (
    ('html', 'HTML'),
    ('css', 'CSS'),
    ('js', 'JavaScript'),
    ('python', 'Python'),
    ('algo', 'Algoritmlar'),
)

GAMES = {
    'quiz_battle': {
        'name': 'Quiz Battle',
        'icon': 'brain',
        'tagline': "Bilimingni boshqa o'quvchilar bilan sinab ko'r.",
        'rules': "Hamma bir xil savolga javob beradi. To'g'ri javob +10 ball, tez javob yana +5.",
        'renderer': 'choice',
        'provider': 'curriculum',
        'mode': 'all',
        'subjects': CURRICULUM_SUBJECTS,
        'time_limit': 20,
        'counts': QUESTION_COUNTS,
        'default_count': 10,
    },
    'quick_answer': {
        'name': 'Quick Answer',
        'icon': 'zap',
        'tagline': "Kim birinchi to'g'ri javob bersa — ball o'shaniki.",
        'rules': "Savolga birinchi bo'lib to'g'ri javob bergan o'yinchi ballni oladi. Har savolga bitta urinish.",
        'renderer': 'choice',
        'provider': 'curriculum',
        'mode': 'first',
        'subjects': CURRICULUM_SUBJECTS,
        'time_limit': 15,
        'counts': QUESTION_COUNTS,
        'default_count': 10,
    },
    'word_battle': {
        'name': 'Word Battle',
        'icon': 'lang',
        'tagline': "Sinonim, antonim, tarjima va imlo bellashuvi.",
        'rules': "So'z boyligingizni sinang: ma'nodosh va zid so'zlar, tarjima va to'g'ri yozilish.",
        'renderer': 'choice',
        'provider': 'words',
        'mode': 'all',
        'subjects': ('english', 'uzbek'),
        'time_limit': 15,
        'counts': QUESTION_COUNTS,
        'default_count': 10,
    },
    'math_battle': {
        'name': 'Math Battle',
        'icon': 'calc',
        'tagline': "Misollarni imkon qadar tez va to'g'ri yeching.",
        'rules': "Har o'yinda yangi misollar. Og'zaki hisoblash tezligingizni oshiring.",
        'renderer': 'choice',
        'provider': 'math',
        'mode': 'all',
        'subjects': ('math',),
        'time_limit': 15,
        'counts': QUESTION_COUNTS,
        'default_count': 10,
    },
    'code_challenge': {
        'name': 'Code Challenge',
        'icon': 'code',
        'tagline': "HTML, CSS, JavaScript, Python va algoritmlar.",
        'rules': "Boshlang'ich dasturlash savollari: kod natijasini toping, to'g'ri tegni tanlang.",
        'renderer': 'choice',
        'provider': 'code',
        'mode': 'all',
        'subjects': ('informatics',),
        'time_limit': 25,
        'counts': QUESTION_COUNTS,
        'default_count': 10,
    },
    'memory_match': {
        'name': 'Memory / Match',
        'icon': 'puzzle',
        'tagline': "Savol va javoblarni juftlab moslang.",
        'rules': "Har raundda 4 ta savolni to'g'ri javobi bilan moslang. Hammasi to'g'ri bo'lsa +10 ball.",
        'renderer': 'match',
        'provider': 'match',
        'mode': 'all',
        'subjects': CURRICULUM_SUBJECTS,
        'time_limit': 45,
        'counts': (5, 10),
        'default_count': 5,
    },
}


def subject_info(key: str) -> dict:
    meta = cur_mod.subject_meta(key)
    return {
        'key': key,
        'name': meta['name'],
        'icon': meta['icon'],
        'color': meta['color'],
        'image': meta.get('image'),
    }


def generated_topics(game_type: str, subject: str):
    """Kod ichida yaratiladigan o'yinlar mavzulari. None — curriculum
    mavzulari (bazadagi topics jadvali) ishlatiladi."""
    provider = GAMES[game_type]['provider']
    if provider == 'math':
        return [{'key': k, 'title': t} for k, t in MATH_TOPICS]
    if provider == 'words':
        return [{'key': k, 'title': t} for k, t in WORD_TOPICS.get(subject, ())]
    if provider == 'code':
        return [{'key': k, 'title': t} for k, t in CODE_TOPICS]
    return None


def estimated_minutes(game_type: str, count: int) -> int:
    """Taxminiy davomiylik: odatda javoblar vaqt tugashidan oldin beriladi."""
    game = GAMES[game_type]
    seconds = count * (game['time_limit'] * 0.6 + REVEAL_SECONDS) + 5
    return max(1, round(seconds / 60))


def public_catalog() -> list:
    items = []
    for key, g in GAMES.items():
        items.append({
            'key': key,
            'name': g['name'],
            'icon': g['icon'],
            'tagline': g['tagline'],
            'rules': g['rules'],
            'renderer': g['renderer'],
            'mode': g['mode'],
            'subjects': [subject_info(s) for s in g['subjects']],
            'counts': list(g['counts']),
            'default_count': g['default_count'],
            'time_limit': g['time_limit'],
            'minutes': estimated_minutes(key, g['default_count']),
            'generated_topics': {s: generated_topics(key, s) for s in g['subjects']}
            if g['provider'] in ('math', 'words', 'code') else None,
        })
    return items


def curriculum_topics(cur, subject: str) -> list:
    """Fan mavzulari soddadan murakkabga (grade, seq) + har birining qiyinlik
    darajasi — ro'yxatdagi o'rniga qarab uchga bo'linadi."""
    cur.execute(
        'SELECT id, title FROM topics WHERE subject_key = %s ORDER BY grade ASC, seq ASC',
        (subject,),
    )
    rows = cur.fetchall()
    total = len(rows)
    keys = list(DIFFICULTIES)
    return [
        {'key': r['id'], 'title': r['title'], 'difficulty': keys[min(2, i * 3 // max(1, total))]}
        for i, r in enumerate(rows)
    ]


def _int_choice(raw, allowed, default):
    try:
        value = int(raw) if raw not in (None, '') else default
    except (TypeError, ValueError):
        return None
    return value if value in allowed else None


def validate_settings(cur, raw: dict) -> dict:
    """Mijozdan kelgan sozlamalarni tekshiradi va normallashtiradi."""
    raw = raw or {}
    game_type = raw.get('game')
    game = GAMES.get(game_type)
    if not game:
        raise GameError('bad_settings', "Bunday o'yin topilmadi.")

    subject = raw.get('subject') or game['subjects'][0]
    if subject not in game['subjects']:
        raise GameError('bad_settings', "Bu o'yin uchun fan noto'g'ri tanlangan.")

    difficulty = raw.get('difficulty') or 'orta'
    if difficulty not in DIFFICULTIES:
        raise GameError('bad_settings', "Qiyinlik darajasi noto'g'ri.")

    count = _int_choice(raw.get('count'), game['counts'], game['default_count'])
    if count is None:
        raise GameError('bad_settings', "Savollar soni noto'g'ri.")

    max_players = _int_choice(raw.get('max_players'), PLAYER_LIMITS, 4)
    if max_players is None:
        raise GameError('bad_settings', "O'yinchilar soni 2, 4, 8 yoki 16 bo'lishi mumkin.")

    topic = raw.get('topic') or None
    if topic is not None:
        topic = str(topic)[:120]
        generated = generated_topics(game_type, subject)
        if generated is not None:
            if topic not in {t['key'] for t in generated}:
                raise GameError('bad_settings', "Mavzu topilmadi.")
        else:
            cur.execute('SELECT 1 FROM topics WHERE id = %s AND subject_key = %s', (topic, subject))
            if not cur.fetchone():
                raise GameError('bad_settings', "Mavzu topilmadi.")

    return {
        'game_type': game_type,
        'subject': subject,
        'topic': topic,
        'difficulty': difficulty,
        'question_count': count,
        'max_players': max_players,
    }


_TOPIC_TITLES = {}


def topic_title(cur, game_type: str, subject: str, topic):
    if not topic:
        return None
    key = (game_type, subject, topic)
    if key not in _TOPIC_TITLES:
        generated = generated_topics(game_type, subject)
        if generated is not None:
            title = next((t['title'] for t in generated if t['key'] == topic), None)
        else:
            cur.execute('SELECT title FROM topics WHERE id = %s', (topic,))
            row = cur.fetchone()
            title = row['title'] if row else None
        if len(_TOPIC_TITLES) > 2000:
            _TOPIC_TITLES.clear()
        _TOPIC_TITLES[key] = title
    return _TOPIC_TITLES[key]


def describe_settings(cur, room: dict) -> dict:
    subject = subject_info(room['subject'])
    return {
        'subject': room['subject'],
        'subject_name': subject['name'],
        'subject_icon': subject['icon'],
        'topic': room['topic'],
        'topic_title': topic_title(cur, room['game_type'], room['subject'], room['topic']),
        'difficulty': room['difficulty'],
        'difficulty_name': DIFFICULTIES.get(room['difficulty'], room['difficulty']),
        'question_count': int(room['question_count']),
        'max_players': int(room['max_players']),
        'is_public': bool(room['is_public']),
        'minutes': estimated_minutes(room['game_type'], int(room['question_count'])),
    }
