# -*- coding: utf-8 -*-
"""
Savol generatorlari (provider'lar). Har bir o'yin turi
catalog.GAMES[...]['provider'] orqali PROVIDERS'dagi funksiyaga bog'lanadi.

Ichki savol (faqat serverda, game_sessions.questions ichida saqlanadi):
    choice: {kind, prompt, options, answer, explain, topic, topic_title, link}
    match:  {kind, prompt, left, right, answer, pairs_explain, topic, topic_title, link}
            — left[i] ning juftligi right[answer[i]]

Mijozga faqat public() — javobsiz nusxa ketadi; to'g'ri javob va tushuntirish
savol yopilgandan keyin reveal() orqali ochiladi.

Ikki til: har bir savolda q['ru'] — ruscha matn (prompt, options, explain, topic_title;
match uchun left/right/pairs_explain). Variantlar tartibi va to'g'ri javob bir xil, shuning
uchun bir roomda turli tilli o'yinchilar birga o'ynaydi — har biri o'z tilida ko'radi (loc()).
"""

import json
import math
import random
from fractions import Fraction

import til
from games import catalog, data_code, data_code_ru, data_words
from games.errors import GameError

BAND = {'oson': 0, 'orta': 1, 'qiyin': 2}
MINUS = '−'


def _load_json(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _band_of(index: int, total: int) -> int:
    return min(2, index * 3 // max(1, total))


def _choice(prompt, correct, distractors, rng, explain, topic, topic_title, link=None, ru=None):
    """To'g'ri javob + chalg'ituvchilardan 4 ta noyob variant.
    ru: {'prompt', 'explain', 'topic_title', 'opt': {asl variant: ruscha}} — ruscha nusxa."""
    options = [correct]
    for d in distractors:
        if d and d not in options:
            options.append(d)
        if len(options) == 4:
            break
    rng.shuffle(options)
    q = {
        'kind': 'choice', 'prompt': prompt, 'options': options,
        'answer': options.index(correct), 'explain': explain,
        'topic': topic, 'topic_title': topic_title, 'link': link,
    }
    if ru:
        opt = ru.get('opt') or {}
        q['ru'] = {'prompt': ru.get('prompt', prompt), 'options': [opt.get(o, o) for o in options],
                   'explain': ru.get('explain', explain), 'topic_title': ru.get('topic_title', topic_title)}
    return q


def loc(q: dict, lang=None) -> dict:
    """Savolning o'yinchi tilidagi nusxasi (to'g'ri javob va tuzilma bir xil)."""
    lang = lang or til.req_lang()
    if lang != 'ru' or not isinstance(q.get('ru'), dict):
        return q
    out = dict(q)
    for k, v in q['ru'].items():
        if v not in (None, '', []):
            out[k] = v
    return out


def _round_robin(groups, want, first_cap=1):
    """Guruhlardan navbatma-navbat oladi: avval har biridan first_cap tadan
    (xilma-xillik uchun), keyin qolganlarini tartib bo'yicha."""
    out = []
    taken = [0] * len(groups)
    for cap in (first_cap, None):
        for gi, group in enumerate(groups):
            limit = len(group) if cap is None else min(len(group), cap)
            while taken[gi] < limit:
                if len(out) >= want:
                    return out
                out.append(group[taken[gi]])
                taken[gi] += 1
    return out


# ───────────────────────── Curriculum (Quiz Battle, Quick Answer) ─────────────────────────

def _curriculum_rows(cur, subject):
    cur.execute(
        'SELECT id, grade, slug, title, title_ru, quiz, ru FROM topics WHERE subject_key = %s ORDER BY grade ASC, seq ASC',
        (subject,),
    )
    return cur.fetchall()


def _topic_priority(rows, settings, rng):
    """Mavzular indekslari ustuvorlik tartibida: tanlangan mavzu va unga eng
    yaqinlari, yoki tanlangan qiyinlik oralig'idagi mavzular."""
    n = len(rows)
    chosen = settings.get('topic')
    if chosen:
        idx = next((i for i, r in enumerate(rows) if r['id'] == chosen), None)
        if idx is not None:
            return sorted(range(n), key=lambda i: (abs(i - idx), rng.random()))
    band = BAND[settings['difficulty']]
    primary = [i for i in range(n) if _band_of(i, n) == band]
    rest = [i for i in range(n) if _band_of(i, n) != band]
    rng.shuffle(primary)
    rest.sort(key=lambda i: (abs(_band_of(i, n) - band), rng.random()))
    return primary + rest


def _quiz_options(q, rng):
    """(variantlar, to'g'ri javob indeksi, aralashtirish tartibi — ruscha variantlar ham shu tartibda)."""
    qtype = q.get('type', 'mc')
    if qtype == 'tf':
        return list(til.TF_OPTIONS['uz']), (0 if q.get('answer') else 1), None
    options = [str(o) for o in (q.get('options') or [])]
    try:
        answer = int(q.get('answer', 0))
    except (TypeError, ValueError):
        return None
    if len(options) < 2 or not 0 <= answer < len(options):
        return None
    order = list(range(len(options)))
    rng.shuffle(order)
    return [options[i] for i in order], order.index(answer), order


def _ru_options(r, order):
    if order is None:
        return list(til.TF_OPTIONS['ru'])
    opts = [str(o) for o in (r.get('options') or [])]
    return [opts[i] for i in order]


def _link(settings, row):
    return {'fan': settings['subject'], 'mavzu': row['slug'], 'sinf': row['grade']}


def curriculum_questions(cur, settings, rng):
    rows = _curriculum_rows(cur, settings['subject'])
    groups = []
    for i in _topic_priority(rows, settings, rng):
        row = rows[i]
        quiz, ru_quiz = til.quiz_pair(row)
        items = []
        for qi, q in enumerate(quiz):
            if not isinstance(q, dict) or not q.get('q'):
                continue
            built = _quiz_options(q, rng)
            if not built:
                continue
            options, answer, order = built
            item = {
                'kind': 'choice', 'prompt': str(q['q']), 'options': options, 'answer': answer,
                'explain': str(q.get('explain') or ''), 'topic': row['id'],
                'topic_title': row['title'], 'link': _link(settings, row),
            }
            r = ru_quiz[qi] if ru_quiz and qi < len(ru_quiz) else None
            if r and r.get('q'):
                item['ru'] = {'prompt': str(r['q']), 'options': _ru_options(r, order),
                              'explain': str(r.get('explain') or ''), 'topic_title': row.get('title_ru') or row['title']}
            items.append(item)
        rng.shuffle(items)
        if items:
            groups.append(items)
    out = _round_robin(groups, settings['question_count'], first_cap=3 if settings.get('topic') else 1)
    rng.shuffle(out)
    return out


# ───────────────────────── Memory / Match ─────────────────────────

_GENERIC_ANSWERS = ('barcha', 'hech biri', 'yuqoridagi', "to'g'ri javob yo'q")


def match_questions(cur, settings, rng):
    """Har raund: shu fandagi 4 ta test savoli va ularning to'g'ri javoblari."""
    rows = _curriculum_rows(cur, settings['subject'])
    groups = []
    for i in _topic_priority(rows, settings, rng):
        row = rows[i]
        quiz, ru_quiz = til.quiz_pair(row)
        items = []
        for qi, q in enumerate(quiz):
            if not isinstance(q, dict) or q.get('type', 'mc') != 'mc' or not q.get('q'):
                continue
            options = q.get('options') or []
            try:
                answer = str(options[int(q.get('answer', 0))]).strip()
            except (TypeError, ValueError, IndexError):
                continue
            prompt = str(q['q']).strip()
            if not answer or len(answer) > 70 or len(prompt) > 160:
                continue
            if any(g in answer.lower() for g in _GENERIC_ANSWERS):
                continue
            r = ru_quiz[qi] if ru_quiz and qi < len(ru_quiz) else q
            try:
                r_answer = str((r.get('options') or [])[int(q.get('answer', 0))]).strip() or answer
            except (TypeError, ValueError, IndexError):
                r_answer = answer
            items.append({
                'left': prompt, 'right': answer, 'explain': str(q.get('explain') or ''),
                'topic': row['id'], 'topic_title': row['title'], 'link': _link(settings, row),
                'ru': {'left': str(r.get('q') or prompt).strip(), 'right': r_answer,
                       'explain': str(r.get('explain') or q.get('explain') or ''),
                       'topic_title': row.get('title_ru') or row['title']},
            })
        rng.shuffle(items)
        if items:
            groups.append(items)

    pool = _round_robin(groups, 10 ** 6, first_cap=1)
    rounds = []
    while len(rounds) < settings['question_count'] and len(pool) >= 4:
        group, rest = [], []
        seen_right, seen_left = set(), set()
        for p in pool:
            rk, lk = p['right'].lower(), p['left'].lower()
            if len(group) < 4 and rk not in seen_right and lk not in seen_left:
                group.append(p)
                seen_right.add(rk)
                seen_left.add(lk)
            else:
                rest.append(p)
        pool = rest
        if len(group) < 4:
            break
        order = list(range(4))
        rng.shuffle(order)
        rounds.append({
            'kind': 'match',
            'prompt': "Har bir savolni to'g'ri javobi bilan moslang",
            'left': [g['left'] for g in group],
            'right': [group[j]['right'] for j in order],
            'answer': [order.index(i) for i in range(4)],
            'pairs_explain': [g['explain'] for g in group],
            'explain': '',
            'topic': group[0]['topic'],
            'topic_title': group[0]['topic_title'],
            'link': group[0]['link'],
            'ru': {
                'prompt': 'Сопоставьте каждый вопрос с правильным ответом',
                'left': [g['ru']['left'] for g in group],
                'right': [group[j]['ru']['right'] for j in order],
                'pairs_explain': [g['ru']['explain'] for g in group],
                'topic_title': group[0]['ru']['topic_title'],
            },
        })
    return rounds


# ───────────────────────── Math Battle ─────────────────────────

_SUP = str.maketrans('0123456789-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻')


def _num(n) -> str:
    n = int(n)
    return f'{MINUS}{-n}' if n < 0 else str(n)


def _frac(f: Fraction) -> str:
    return _num(f.numerator) if f.denominator == 1 else f'{_num(f.numerator)}/{f.denominator}'


def _int_distractors(value, extra, rng, positive=True):
    """Yaqin va "tipik xato" qiymatlardan chalg'ituvchilar."""
    cands = [v for v in extra if v != value]
    near = [value + d for d in (1, -1, 2, -2, 10, -10, 3, -3, 5, -5)]
    rng.shuffle(near)
    out = []
    for v in cands + near:
        if v == value or v in out or (positive and v < 0):
            continue
        out.append(v)
    return [_num(v) for v in out]


def _math_add(level, rng):
    if level == 0:
        a, b = rng.randint(12, 89), rng.randint(11, 69)
    elif level == 1:
        a, b = rng.randint(120, 899), rng.randint(105, 699)
    else:
        a, b = rng.randint(1200, 9800), rng.randint(1050, 8900)
    if rng.random() < 0.5:
        if level < 2 and a < b:
            a, b = b, a
        value = a - b
        prompt = f'{_num(a)} {MINUS} {_num(b)} = ?'
        if level == 0 and b % 10 >= 5:
            up = (b // 10 + 1) * 10
            explain = f'{a} {MINUS} {b} = {a} {MINUS} {up} + {up - b} = {_num(value)}.'
        else:
            explain = (f'{_num(a)} {MINUS} {_num(b)} = {_num(value)}. Tekshirish: {_num(value)} + {_num(b)} = {_num(a)}.',
                       f'{_num(a)} {MINUS} {_num(b)} = {_num(value)}. Проверка: {_num(value)} + {_num(b)} = {_num(a)}.')
        extra = [value + 10, value - 10, a + b, value + 100 if level else value + 20]
        return prompt, value, _int_distractors(value, extra, rng, positive=level < 2), explain
    value = a + b
    prompt = f'{_num(a)} + {_num(b)} = ?'
    if level == 0:
        tens, ones = (a // 10 + b // 10) * 10, a % 10 + b % 10
        explain = (f"O'nliklar: {a // 10 * 10} + {b // 10 * 10} = {tens}, birliklar: "
                   f"{a % 10} + {b % 10} = {ones}. Jami: {tens} + {ones} = {value}.",
                   f"Десятки: {a // 10 * 10} + {b // 10 * 10} = {tens}, единицы: "
                   f"{a % 10} + {b % 10} = {ones}. Итого: {tens} + {ones} = {value}.")
    else:
        explain = (f"Xonama-xona qo'shing: {a} + {b} = {value}.", f"Складывайте поразрядно: {a} + {b} = {value}.")
    extra = [value + 10, value - 10, value + 100 if level else value - 1, abs(a - b)]
    return prompt, value, _int_distractors(value, extra, rng), explain


def _math_mul(level, rng):
    if level == 0:
        a, b = rng.randint(2, 10), rng.randint(2, 10)
        value = a * b
        explain = (f"{a} × {b} = {value} — ko'paytirish jadvali.", f'{a} × {b} = {value} — таблица умножения.')
    elif level == 1:
        a, b = rng.randint(11, 19), rng.randint(3, 9)
        value = a * b
        explain = f'{a} × {b} = 10 × {b} + {a - 10} × {b} = {10 * b} + {(a - 10) * b} = {value}.'
    else:
        a, b = rng.randint(12, 49), rng.randint(11, 29)
        value = a * b
        tens, ones = b // 10 * 10, b % 10
        if ones:
            explain = f'{a} × {b} = {a} × {tens} + {a} × {ones} = {a * tens} + {a * ones} = {value}.'
        else:
            explain = f'{a} × {b} = {a} × {b // 10} × 10 = {value}.'
    extra = [value + a, value - a, value + b, value - b, value + 10]
    return f'{a} × {b} = ?', value, _int_distractors(value, extra, rng), explain


def _math_div(level, rng):
    if level == 0:
        b, q = rng.randint(2, 10), rng.randint(2, 10)
    elif level == 1:
        b, q = rng.randint(3, 9), rng.randint(11, 40)
    else:
        b, q = rng.randint(11, 25), rng.randint(12, 60)
    a = b * q
    explain = (f"{b} × {q} = {a}, demak {a} : {b} = {q}.", f'{b} × {q} = {a}, значит {a} : {b} = {q}.')
    extra = [q + 1, q - 1, q + 2, q + 10, q - 2]
    return f'{a} : {b} = ?', q, _int_distractors(q, extra, rng), explain


def _frac_distractors(value: Fraction, cands, rng):
    out = []
    for f in cands:
        if f is None or f <= 0 or f == value:
            continue
        s = _frac(f)
        if s not in out:
            out.append(s)
    k = 1
    while len(out) < 3:
        f = value + Fraction(k, value.denominator * 2 + 1)
        if _frac(f) not in out and f != value:
            out.append(_frac(f))
        k += 1
    return out


def _math_frac(level, rng):
    if level == 0:
        d = rng.choice((5, 7, 11, 13))
        a = rng.randint(1, d - 2)
        b = rng.randint(1, d - 1 - a)
        value = Fraction(a + b, d)
        prompt = f'{a}/{d} + {b}/{d} = ?'
        explain = (f"Maxrajlar bir xil ({d}) — faqat suratlar qo'shiladi: {a} + {b} = {a + b}. Javob: {a + b}/{d}.",
                   f'Знаменатели одинаковые ({d}) — складываются только числители: {a} + {b} = {a + b}. Ответ: {a + b}/{d}.')
        cands = [Fraction(a + b, 2 * d), Fraction(a + b + 1, d), Fraction(abs(a - b) or 1, d), Fraction(a * b, d)]
        return prompt, _frac(value), _frac_distractors(value, cands, rng), explain
    if level == 1:
        d1, d2 = rng.sample((2, 3, 4, 5, 6), 2)
        a, b = rng.randint(1, d1 - 1), rng.randint(1, d2 - 1)
        common = d1 * d2 // math.gcd(d1, d2)
        s = a * common // d1 + b * common // d2
        value = Fraction(a, d1) + Fraction(b, d2)
        reduced = f' = {_frac(value)}' if _frac(value) != f'{s}/{common}' else ''
        explain = (f"Umumiy maxraj {common}: {a}/{d1} = {a * common // d1}/{common}, "
                   f"{b}/{d2} = {b * common // d2}/{common}. Yig'indi: {s}/{common}{reduced}.",
                   f'Общий знаменатель {common}: {a}/{d1} = {a * common // d1}/{common}, '
                   f'{b}/{d2} = {b * common // d2}/{common}. Сумма: {s}/{common}{reduced}.')
        cands = [Fraction(a + b, d1 + d2), Fraction(a * b, d1 * d2),
                 value + Fraction(1, common), value - Fraction(1, common)]
        return f'{a}/{d1} + {b}/{d2} = ?', _frac(value), _frac_distractors(value, cands, rng), explain
    b, d = rng.randint(2, 9), rng.randint(2, 9)
    a, c = rng.randint(1, b - 1), rng.randint(1, d - 1)
    if rng.random() < 0.5:
        value = Fraction(a * c, b * d)
        raw = f'{a * c}/{b * d}'
        tail = f' = {_frac(value)}' if _frac(value) != raw else ''
        explain = (f"Suratlar va maxrajlar ko'paytiriladi: ({a}×{c})/({b}×{d}) = {raw}{tail}.",
                   f'Числители и знаменатели перемножаются: ({a}×{c})/({b}×{d}) = {raw}{tail}.')
        prompt = f'{a}/{b} × {c}/{d} = ?'
        cands = [Fraction(a + c, b + d), Fraction(a * d, b * c), Fraction(a * c, b + d), value * 2]
    else:
        value = Fraction(a * d, b * c)
        raw = f'{a * d}/{b * c}'
        tail = f' = {_frac(value)}' if _frac(value) != raw else ''
        explain = (f"Bo'lish — teskari kasrga ko'paytirish: {a}/{b} × {d}/{c} = {raw}{tail}.",
                   f'Деление — это умножение на обратную дробь: {a}/{b} × {d}/{c} = {raw}{tail}.')
        prompt = f'{a}/{b} : {c}/{d} = ?'
        cands = [Fraction(a * c, b * d), Fraction(b * c, a * d), value * 2, value / 2]
    return prompt, _frac(value), _frac_distractors(value, cands, rng), explain


_PCT_TIPS = {10: "10% — o'ndan bir qism", 20: "20% — beshdan bir qism",
             25: "25% — to'rtdan bir qism", 50: '50% — yarmi'}
_PCT_TIPS_RU = {10: '10% — одна десятая часть', 20: '20% — одна пятая часть',
                25: '25% — одна четвёртая часть', 50: '50% — половина'}


def _math_pct(level, rng):
    if level == 2 and rng.random() < 0.5:
        for _ in range(50):
            n = rng.choice((200, 250, 300, 400, 500, 800, 1000, 1200))
            p = rng.choice((10, 15, 20, 25, 30, 40))
            if n * p % 100 == 0:
                break
        part = n * p // 100
        value = n + part
        prompt = (f"Narx {n} so'm edi va {p}% ga oshdi. Yangi narx necha so'm?",
                  f'Цена была {n} сум и выросла на {p}%. Какой стала новая цена (в сумах)?')
        explain = (f"{n} ning {p}% i = {n} × {p} : 100 = {part}. Yangi narx: {n} + {part} = {value} so'm.",
                   f'{p}% от {n} = {n} × {p} : 100 = {part}. Новая цена: {n} + {part} = {value} сум.')
        extra = [part, n - part, value + 10, n + p]
        return prompt, value, _int_distractors(value, extra, rng), explain
    choices = {
        0: ((10, 20, 25, 50), (20, 40, 60, 80, 100, 120, 200, 400)),
        1: ((5, 15, 30, 40, 75), (40, 60, 80, 120, 200, 240, 300, 400, 600)),
        2: ((12, 35, 45, 120), (100, 200, 300, 400, 500, 600, 800, 1000)),
    }[level]
    for _ in range(50):
        p, n = rng.choice(choices[0]), rng.choice(choices[1])
        if n * p % 100 == 0:
            break
    else:
        p, n = 50, 100
    value = n * p // 100
    tip = _PCT_TIPS.get(p)
    if tip:
        explain = (f'{tip}: {n} ning {p}% i = {value}.', f'{_PCT_TIPS_RU[p]}: {p}% от {n} = {value}.')
    else:
        explain = f'{p}% = {p}/100. {n} × {p} : 100 = {value}.'
    extra = [value + n // 10, value * 2, n - value, value + 5, n * p // 10]
    return ((f'{n} ning {p}% i nechaga teng?', f'Чему равны {p}% от {n}?'), value,
            _int_distractors(value, extra, rng), explain)


def _math_pow(level, rng):
    kind = rng.random()
    if level == 0:
        n = rng.randint(2, 12)
        if kind < 0.5:
            v = n * n
            return (f'{n}² = ?', v, _int_distractors(v, [n * 2, v + n, (n + 1) ** 2, (n - 1) ** 2], rng),
                    f'{n}² = {n} × {n} = {v}.')
        return (f'√{n * n} = ?', n, _int_distractors(n, [n * 2, n + 1, n - 1, n * n // 2], rng),
                (f'√{n * n} = {n}, chunki {n} × {n} = {n * n}.', f'√{n * n} = {n}, потому что {n} × {n} = {n * n}.'))
    if level == 1:
        if kind < 0.5:
            n = rng.randint(11, 25)
            v = n * n
            return (f'{n}² = ?', v, _int_distractors(v, [n * 2, v + 10, (n + 1) ** 2, (n - 1) ** 2], rng),
                    f'{n}² = {n} × {n} = {v}.')
        n = rng.randint(2, 6)
        v = n ** 3
        return (f'{n}³ = ?', v, _int_distractors(v, [n * 3, n * n, (n + 1) ** 3, v + n], rng),
                f'{n}³ = {n} × {n} × {n} = {v}.')
    if kind < 0.35:
        k = rng.randint(5, 10)
        v = 2 ** k
        return (f'2{str(k).translate(_SUP)} = ?', v, _int_distractors(v, [2 * k, v // 2, v * 2, v + 2], rng),
                (f"2{str(k).translate(_SUP)} = {v} — 2 ni {k} marta o'ziga ko'paytiring.",
                 f'2{str(k).translate(_SUP)} = {v} — умножьте 2 само на себя {k} раз.'))
    if kind < 0.7:
        n = rng.randint(13, 30)
        return (f'√{n * n} = ?', n, _int_distractors(n, [n + 1, n - 1, n * 2, n + 10], rng),
                (f'√{n * n} = {n}, chunki {n} × {n} = {n * n}.', f'√{n * n} = {n}, потому что {n} × {n} = {n * n}.'))
    n = rng.randint(2, 5)
    v = -(n ** 3)
    return (f'({MINUS}{n})³ = ?', v, _int_distractors(v, [-v, -(n * 3), n * 3, v + 1], rng, positive=False),
            (f"({MINUS}{n})³ = ({MINUS}{n}) × ({MINUS}{n}) × ({MINUS}{n}) = {_num(v)} — toq darajada manfiy ishora saqlanadi.",
             f'({MINUS}{n})³ = ({MINUS}{n}) × ({MINUS}{n}) × ({MINUS}{n}) = {_num(v)} — в нечётной степени минус сохраняется.'))


MATH_GENERATORS = {
    'qoshish': _math_add,
    'kopaytirish': _math_mul,
    'bolish': _math_div,
    'kasrlar': _math_frac,
    'foizlar': _math_pct,
    'darajalar': _math_pow,
}
MATH_TITLES = dict(catalog.MATH_TOPICS)
MATH_TITLES_RU = {'qoshish': 'Сложение и вычитание', 'kopaytirish': 'Умножение', 'bolish': 'Деление',
                  'kasrlar': 'Дроби', 'foizlar': 'Проценты', 'darajalar': 'Степени и корни'}


def _pair(value):
    """Generator qiymati: oddiy satr (ikkala tilda bir xil) yoki (uz, ru)."""
    return value if isinstance(value, tuple) else (value, value)


def math_questions(cur, settings, rng):
    level = BAND[settings['difficulty']]
    kinds = [settings['topic']] if settings.get('topic') else list(MATH_GENERATORS)
    rng.shuffle(kinds)
    out, seen = [], set()
    attempts = 0
    while len(out) < settings['question_count'] and attempts < 400:
        kind = kinds[attempts % len(kinds)]
        attempts += 1
        prompt, value, distractors, explain = MATH_GENERATORS[kind](level, rng)
        (prompt, prompt_ru), (explain, explain_ru) = _pair(prompt), _pair(explain)
        if prompt in seen or len(distractors) < 3:
            continue
        seen.add(prompt)
        correct = value if isinstance(value, str) else _num(value)
        out.append(_choice(prompt, correct, distractors, rng, explain, kind, MATH_TITLES[kind],
                           ru={'prompt': prompt_ru, 'explain': explain_ru, 'topic_title': MATH_TITLES_RU[kind]}))
    return out


# ───────────────────────── Word Battle ─────────────────────────

def _level_pool(items, level_of, level, rng):
    primary = [x for x in items if level_of(x) == level]
    rest = [x for x in items if level_of(x) != level]
    rng.shuffle(primary)
    rng.shuffle(rest)
    return primary + rest


def _pair_question(pair, pairs, rng, prompt_tpl, explain, topic, title, group_of, ru=None):
    """Sinonim/antonim: juftlikning bir so'zi savol, ikkinchisi javob.
    Chalg'ituvchilar boshqa ma'no guruhlaridan olinadi. ru: (prompt shabloni, tushuntirish, mavzu nomi)."""
    word, answer = (pair[0], pair[1]) if rng.random() < 0.5 else (pair[1], pair[0])
    others = [w for p in pairs if group_of(p) != group_of(pair) for w in (p[0], p[1])]
    rng.shuffle(others)
    ru_spec = {'prompt': ru[0].format(w=word), 'explain': ru[1], 'topic_title': ru[2]} if ru else None
    return _choice(prompt_tpl.format(w=word), answer, others, rng, explain, topic, title, ru=ru_spec)


WORD_TITLES_RU = {
    ('english', 'tarjima'): 'Перевод', ('english', 'sinonim'): 'Синонимы (synonyms)',
    ('english', 'antonim'): 'Антонимы (antonyms)', ('english', 'imlo'): 'Правописание (spelling)',
    ('uzbek', 'sinonim'): 'Синонимы', ('uzbek', 'antonim'): 'Антонимы',
}


def _word_builder(subject, kind, rng):
    """(savollar ro'yxatini beradigan) funksiya: level → iterator."""
    title = dict(catalog.WORD_TOPICS[subject])[kind]
    title_ru = WORD_TITLES_RU.get((subject, kind), title)
    d = data_words

    if subject == 'english' and kind == 'tarjima':
        uz_to_ru = {e[1]: d.EN_RU.get(e[0], e[1]) for e in d.EN_TRANSLATIONS}

        def build(entry):
            en, uz, lvl = entry
            ru = d.EN_RU.get(en, uz)
            same = [e for e in d.EN_TRANSLATIONS if e is not entry]
            same.sort(key=lambda e: (e[2] != lvl, rng.random()))
            if rng.random() < 0.5:
                return _choice(f"“{en}” so'zining o'zbekcha tarjimasi qaysi?", uz,
                               [e[1] for e in same], rng, f'{en} — {uz}.', kind, title,
                               ru={'prompt': f'Как переводится слово «{en}» на русский?', 'explain': f'{en} — {ru}.',
                                   'topic_title': title_ru, 'opt': uz_to_ru})
            return _choice(f"“{uz}” so'zi ingliz tilida qanday bo'ladi?", en,
                           [e[0] for e in same], rng, f'{uz} — {en}.', kind, title,
                           ru={'prompt': f'Как будет «{ru}» по-английски?', 'explain': f'{ru} — {en}.',
                               'topic_title': title_ru})
        return d.EN_TRANSLATIONS, (lambda e: e[2]), build

    if subject == 'english' and kind == 'sinonim':
        def build(p):
            return _pair_question(p, d.EN_SYNONYMS, rng, "“{w}” so'zining sinonimi (ma'nodoshi) qaysi?",
                                  f"{p[0]} = {p[1]} ({p[2]}) — ma'nodosh so'zlar.", kind, title, lambda x: x[3],
                                  ru=('Какой синоним у слова «{w}»?',
                                      f'{p[0]} = {p[1]} ({d.EN_RU.get(p[0], p[2])}) — слова-синонимы.', title_ru))
        return d.EN_SYNONYMS, (lambda p: p[4]), build

    if subject == 'english' and kind == 'antonim':
        def build(p):
            return _pair_question(p, d.EN_ANTONYMS, rng, "“{w}” so'zining antonimi (zid ma'nolisi) qaysi?",
                                  f'{p[0]} ↔ {p[1]}: {p[2]}.', kind, title, lambda x: x[3],
                                  ru=('Какой антоним (слово с противоположным значением) у слова «{w}»?',
                                      f'{p[0]} ↔ {p[1]}: {d.EN_ANT_RU.get(p[0], p[2])}.', title_ru))
        return d.EN_ANTONYMS, (lambda p: p[4]), build

    if subject == 'english' and kind == 'imlo':
        def build(e):
            word, wrong, uz, _ = e
            ru = d.EN_RU.get(word, uz)
            return _choice(f"Qaysi so'z to'g'ri yozilgan? (ma'nosi: {uz})", word, list(wrong), rng,
                           f"To'g'ri yozilishi: {word} — {uz}.", kind, title,
                           ru={'prompt': f'Какое слово написано правильно? (значение: {ru})',
                               'explain': f'Правильное написание: {word} — {ru}.', 'topic_title': title_ru})
        return d.EN_SPELLING, (lambda e: e[3]), build

    if subject == 'uzbek' and kind == 'sinonim':
        def build(p):
            return _pair_question(p, d.UZ_SYNONYMS, rng, "“{w}” so'zining sinonimi qaysi?",
                                  f"{p[0]} — {p[1]}: ma'nosi yaqin so'zlar (sinonimlar).", kind, title, lambda x: x[2],
                                  ru=('Какой синоним у узбекского слова «{w}»?',
                                      f'{p[0]} — {p[1]}: слова, близкие по значению (синонимы).', title_ru))
        return d.UZ_SYNONYMS, (lambda p: p[3]), build

    if subject == 'uzbek' and kind == 'antonim':
        def build(p):
            return _pair_question(p, d.UZ_ANTONYMS, rng, "“{w}” so'ziga zid ma'noli so'z (antonim) qaysi?",
                                  f"{p[0]} — {p[1]}: qarama-qarshi ma'noli so'zlar (antonimlar).", kind, title, lambda x: x[2],
                                  ru=('Какое слово противоположно по значению (антоним) узбекскому слову «{w}»?',
                                      f'{p[0]} — {p[1]}: слова с противоположным значением (антонимы).', title_ru))
        return d.UZ_ANTONYMS, (lambda p: p[3]), build

    return None


def words_questions(cur, settings, rng):
    subject = settings['subject']
    level = BAND[settings['difficulty']]
    kinds = [settings['topic']] if settings.get('topic') else [k for k, _ in catalog.WORD_TOPICS[subject]]
    groups = []
    for kind in kinds:
        spec = _word_builder(subject, kind, rng)
        if not spec:
            continue
        items, level_of, build = spec
        groups.append([build(x) for x in _level_pool(items, level_of, level, rng)])
    out = _round_robin(groups, settings['question_count'], first_cap=2)
    rng.shuffle(out)
    return out


# ───────────────────────── Code Challenge ─────────────────────────

CODE_TITLES = dict(catalog.CODE_TOPICS)
CODE_TITLES_RU = {'algo': 'Алгоритмы'}


def code_questions(cur, settings, rng):
    level = BAND[settings['difficulty']]
    topics = [settings['topic']] if settings.get('topic') else list(CODE_TITLES)
    groups = []
    for topic in topics:
        pool = [(i, q) for i, q in enumerate(data_code.QUESTIONS) if q['topic'] == topic]
        pool.sort(key=lambda x: (abs(x[1]['level'] - level), rng.random()))
        items = []
        for i, q in pool:
            correct = q['options'][q['answer']]
            others = [o for o in q['options'] if o != correct]
            r = data_code_ru.QUESTIONS_RU[i] if i < len(data_code_ru.QUESTIONS_RU) else None
            ru = None
            if r:
                ru = {'prompt': r['q'], 'explain': r['explain'], 'topic_title': CODE_TITLES_RU.get(topic, CODE_TITLES[topic]),
                      'opt': dict(zip(q['options'], r['options'])) if r.get('options') else {}}
            items.append(_choice(q['q'], correct, others, rng, q['explain'], topic, CODE_TITLES[topic], ru=ru))
        groups.append(items)
    out = _round_robin(groups, settings['question_count'], first_cap=2)
    rng.shuffle(out)
    return out


PROVIDERS = {
    'curriculum': curriculum_questions,
    'match': match_questions,
    'math': math_questions,
    'words': words_questions,
    'code': code_questions,
}


def build(cur, settings, rng=None) -> list:
    rng = rng or random.Random()
    provider = PROVIDERS[catalog.GAMES[settings['game_type']]['provider']]
    return provider(cur, settings, rng)[:settings['question_count']]


# ───────────────────────── Mijozga ko'rinish va tekshiruv ─────────────────────────

def public(q: dict) -> dict:
    """Savol matni — to'g'ri javobsiz."""
    if q['kind'] == 'match':
        return {'kind': 'match', 'prompt': q['prompt'], 'left': q['left'], 'right': q['right'],
                'topic_title': q.get('topic_title')}
    return {'kind': 'choice', 'prompt': q['prompt'], 'options': q['options'],
            'topic_title': q.get('topic_title')}


def reveal(q: dict) -> dict:
    """Savol yopilgandan keyin: to'g'ri javob va tushuntirish."""
    if q['kind'] == 'match':
        return {'answer': q['answer'], 'explain': q.get('explain') or '',
                'pairs_explain': q.get('pairs_explain') or []}
    return {'answer': q['answer'], 'explain': q.get('explain') or ''}


def answer_text(q: dict) -> str:
    if q['kind'] == 'match':
        return '; '.join(f"{left} → {q['right'][q['answer'][i]]}" for i, left in enumerate(q['left']))
    return q['options'][q['answer']]


def evaluate(q: dict, raw):
    """(to'g'rimi, qisman to'g'ri juftliklar soni, saqlanadigan javob).
    Noto'g'ri formatdagi javob — GameError."""
    if q['kind'] == 'match':
        size = len(q['left'])
        if not isinstance(raw, list) or len(raw) != size:
            raise GameError('bad_answer', "Barcha juftliklarni moslang.")
        try:
            perm = [int(x) for x in raw]
        except (TypeError, ValueError):
            raise GameError('bad_answer', "Javob noto'g'ri formatda.")
        if any(isinstance(x, bool) for x in raw) or sorted(perm) != list(range(size)):
            raise GameError('bad_answer', "Har bir javobni faqat bir marta ishlating.")
        right = sum(1 for i, j in enumerate(perm) if j == q['answer'][i])
        return right == size, right, perm
    if isinstance(raw, bool):
        raise GameError('bad_answer', "Javob noto'g'ri formatda.")
    try:
        idx = int(raw)
    except (TypeError, ValueError):
        raise GameError('bad_answer', "Javob noto'g'ri formatda.")
    if not 0 <= idx < len(q['options']):
        raise GameError('bad_answer', "Bunday variant yo'q.")
    return idx == q['answer'], 0, idx
