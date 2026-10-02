# -*- coding: utf-8 -*-
"""Dars mazmunini avtomatik tekshirish (validate_curriculum.py tuzilmani, bu — mantiqni tekshiradi).

Topadi:
  * mc: to'g'ri javob indeksi variantlardan tashqarida, bo'sh yoki takroriy variantlar;
  * mc: izohdagi yakuniy son boshqa variantga teng, to'g'ri variantga emas (javob indeksi xato bo'lishi mumkin);
  * tf: izoh "Xato/Noto'g'ri/Неверно" bilan boshlanadi, javob esa true (yoki aksincha);
  * ruscha tarjima: savollar soni, turi, variantlar soni o'zbekchasiga mos emas; tarjimasiz mavzu.

    python validate_content.py          # topilganlarini chiqaradi, bor bo'lsa — chiqish kodi 1
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from curriculum import ai_curriculum  # noqa: E402

NEG_START = re.compile(r"^\s*(xato|noto'g'ri|noto‘g‘ri|yo'q|yo‘q|aksincha|неверно|нет[,.]|наоборот|ложь|false\b)", re.I)
# "To'g'ri shakli: ...", "Правильно: ..." — to'g'ri variantni ko'rsatadi, javobni tasdiqlamaydi
POS_START = re.compile(r"^\s*(to'g'ri|to‘g‘ri|ha[,.]|верно|да[,.]|true\b)(?!\s*(shakli|javob|varianti|yozilishi|форма|вариант))", re.I)
NUM = re.compile(r'-?\d+(?:[.,]\d+)?')


def _num(text):
    """Variant matni sof son bo'lsa — o'sha son (birliklar bilan: "15 sm", "4 ta" ham)."""
    m = re.fullmatch(r"\s*(-?\d+(?:[.,]\d+)?)\s*(?:[a-zA-Zа-яА-Я%°'π²³ ]{0,6})\s*", str(text))
    return float(m.group(1).replace(',', '.')) if m else None


def check_quiz(where, quiz, issues):
    for i, q in enumerate(quiz or []):
        t = q.get('type', 'mc')
        tag = f'{where} Q{i}'
        if t == 'mc':
            opts = q.get('options') or []
            a = q.get('answer')
            if not isinstance(a, int) or not 0 <= a < len(opts):
                issues.append(f"{tag}: javob indeksi {a!r} variantlar ({len(opts)}) ichida emas")
                continue
            norm = [str(o).strip().lower() for o in opts]
            if any(not o for o in norm):
                issues.append(f'{tag}: bo\'sh variant')
            if len(set(norm)) != len(norm):
                issues.append(f'{tag}: takroriy variantlar {opts}')
            # Izohdagi yakuniy son boshqa sonli variantga teng bo'lsa — shubhali
            nums = [_num(o) for o in opts]
            if all(n is not None for n in nums) and len(set(nums)) == len(nums):
                found = [float(x.replace(',', '.')) for x in NUM.findall(str(q.get('explain') or ''))]
                if found:
                    last = found[-1]
                    if last != nums[a] and last in nums:
                        issues.append(f"{tag}: izoh oxirgi soni {last:g} — {nums.index(last)}-variant, javob esa "
                                      f"{a}-variant ({opts[a]}). Savol: {q.get('q')!r}")
        elif t == 'tf':
            a = q.get('answer')
            if not isinstance(a, bool):
                issues.append(f'{tag}: tf javobi bool emas ({a!r})')
                continue
            e = str(q.get('explain') or '')
            if a and NEG_START.search(e):
                issues.append(f'{tag}: javob TRUE, izoh inkor bilan boshlanadi: {e[:90]!r}')
            if not a and POS_START.search(e) and not NEG_START.search(e):
                issues.append(f'{tag}: javob FALSE, izoh tasdiq bilan boshlanadi: {e[:90]!r}')
        elif t == 'fill':
            if q.get('answer') in (None, ''):
                issues.append(f'{tag}: fill javobi bo\'sh')


def check_ru(where, uz_quiz, ru, issues):
    if not ru:
        issues.append(f'{where}: ruscha tarjima yo\'q')
        return
    rq = ru.get('quiz') or []
    if len(rq) != len(uz_quiz or []):
        issues.append(f'{where}: ruscha savollar soni {len(rq)} ≠ {len(uz_quiz or [])}')
        return
    for i, (q, r) in enumerate(zip(uz_quiz, rq)):
        if r.get('type', 'mc') != q.get('type', 'mc'):
            issues.append(f'{where} Q{i}: ruscha savol turi boshqa')
        elif q.get('type', 'mc') == 'mc' and len(r.get('options') or []) != len(q.get('options') or []):
            issues.append(f'{where} Q{i}: ruscha variantlar soni boshqa')


def main():
    issues = []
    for s in ai_curriculum.SUBJECTS:
        path = os.path.join(HERE, 'curriculum', 'ru', s['key'] + '.json')
        ru_all = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
        for t in s['topics']:
            where = f"{s['key']}/{t['slug']}"
            check_quiz(where, t.get('quiz'), issues)
            ru = ru_all.get(t['slug'])
            check_ru(where, t.get('quiz'), ru, issues)
            if ru:
                check_quiz(where + ' [ru]', [dict(r, answer=q.get('answer')) for q, r in zip(t.get('quiz') or [], ru.get('quiz') or [])], issues)
    for x in issues:
        print(x)
    print(f'\n{len(issues)} ta shubhali joy' if issues else 'Hammasi joyida.')
    return 1 if issues else 0


if __name__ == '__main__':
    sys.exit(main())
