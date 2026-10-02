# -*- coding: utf-8 -*-
"""Dars mazmuni: javob indekslari, izoh va javob mosligi, ruscha tarjima to'liqligi, uy vazifasi tekshiruvi."""
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import study  # noqa: E402
import validate_content  # noqa: E402
from curriculum import ai_curriculum  # noqa: E402

fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:400]}'))
    if not cond:
        fails.append(name)


print('— Mazmun mantiqi (validate_content.py)')
check("Shubhali joy yo'q", validate_content.main() == 0)

print("— Uyga vazifa: o'quvchining to'g'ri javobi o'tadi, savolni ko'chirgan o'tmaydi")
own = copied = total = 0
for s in ai_curriculum.SUBJECTS:
    for t in s['topics']:
        for task in (t.get('homework') or {}).get('tasks', []):
            if task.get('answer') in (None, ''):
                continue
            total += 1
            own += study.answers_match(task['answer'], task['answer'], loose=True, prompt=task['prompt'])
            copied += study.answers_match(task['prompt'], task['answer'], loose=True, prompt=task['prompt'])
check('Har bir javob o\'zi bilan mos', own == total, (own, total))
check("Savolni ko'chirib yozish hech qayerda o'tmaydi", copied == 0, copied)

cases = [
    ("Ksilema suv va minerallarni pastdan yuqoriga, floema organik moddalarni tashiydi",
     "Ksilema suv va minerallarni ildizdan yuqoriga, floema esa organik moddalarni barglardan boshqa qismlarga o'tkazadi.",
     "Ksilema va floemaning vazifalarini ayting.", True),
    ('bilmayman', "Ksilema suv va minerallarni ildizdan yuqoriga, floema esa organik moddalarni o'tkazadi.", '', False),
    ('Клеточная стенка, пластиды, крупная вакуоль',
     '1. Клеточная стенка (клетчатка); 2. Пластиды; 3. Крупная центральная вакуоль (есть у растений).', '', True),
    ('(x-4)(x+4)', '(x - 4)(x + 4)', '', True),
    ('y = x^4 + 4', 'y = x⁴ + 4', '', True),
    ('x=7', 'x = 8', '', False),
    ('was', 'were', '', False),
    ('15.0', '15', '', True),
]
for given, expected, prompt, want in cases:
    check(f'{given[:30]!r} → {want}', study.answers_match(given, expected, loose=True, prompt=prompt) == want)
check("Test (quiz) javobi mazmun bo'yicha emas, aniq tekshiriladi",
      not study.answers_match('Ksilema suv floema organik moddalar', cases[0][1]))
check('Erkin javob: "ha" — yo\'q, ikki so\'zli mazmunli javob — ha',
      not study.open_answer_ok('ha') and study.open_answer_ok('daftarimga chizdim'))

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: ' + ', '.join(fails)))
sys.exit(1 if fails else 0)
