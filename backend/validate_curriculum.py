# -*- coding: utf-8 -*-
"""
O'quv dasturini tekshirish.

Yangi dars qo'shgandan keyin shuni ishga tushiring:
    python validate_curriculum.py

Tekshiradi: majburiy maydonlar, javob indekslari, slug takrorlanishi,
quiz/uy vazifasi yetarliligi.
"""

import sys

sys.stdout.reconfigure(encoding='utf-8')

import curriculum as cur_mod

BLOK_TURLARI = {'text', 'example', 'steps', 'formula', 'note', 'life', 'table'}
SAVOL_TURLARI = {'mc', 'tf', 'fill'}
VAZIFA_TURLARI = {'number', 'text', 'open'}

xatolar = []
ogohlantirishlar = []
jami_mavzu = 0
jami_savol = 0
jami_vazifa = 0


def xato(joy, matn):
    xatolar.append(f'{joy}: {matn}')


def ogoh(joy, matn):
    ogohlantirishlar.append(f'{joy}: {matn}')


for grade in cur_mod.GRADES:
    subjects = cur_mod.subjects_for_grade(grade)
    if not subjects:
        continue

    ko_rilgan_fan = set()
    for subject in subjects:
        key = subject.get('key')
        if not key:
            xato(f'{grade}-sinf', "fanda 'key' yo'q")
            continue
        if key in ko_rilgan_fan:
            xato(f'{grade}-sinf', f"'{key}' fani ikki marta yozilgan")
        ko_rilgan_fan.add(key)
        if key not in cur_mod.SUBJECT_CATALOG:
            xato(f'{grade}-sinf/{key}', 'SUBJECT_CATALOG da bunday fan yo\'q')

        topics = subject.get('topics') or []
        if not topics:
            xato(f'{grade}-sinf/{key}', "mavzular yo'q")

        ko_rilgan_slug = set()
        for i, topic in enumerate(topics, start=1):
            joy = f'{grade}-sinf/{key}/#{i}'
            slug = topic.get('slug')

            if not slug:
                xato(joy, "slug yo'q")
            elif slug in ko_rilgan_slug:
                xato(joy, f"slug '{slug}' takrorlangan")
            else:
                ko_rilgan_slug.add(slug)
                joy = f'{grade}-sinf/{key}/{slug}'

            if not topic.get('title'):
                xato(joy, "sarlavha (title) yo'q")
            if not topic.get('summary'):
                ogoh(joy, "qisqa tavsif (summary) yo'q")

            jami_mavzu += 1

            # ── Dars ──
            lesson = topic.get('lesson') or []
            if len(lesson) < 3:
                xato(joy, f'dars bloklari juda kam ({len(lesson)} ta, kamida 3 kerak)')
            for j, blok in enumerate(lesson, start=1):
                tur = blok.get('type')
                if tur not in BLOK_TURLARI:
                    xato(joy, f"{j}-blok turi noma'lum: '{tur}'")
                if tur == 'steps':
                    if not blok.get('items'):
                        xato(joy, f'{j}-blok (steps) bo\'sh')
                elif tur == 'table':
                    head = blok.get('head') or []
                    for r, row in enumerate(blok.get('rows') or [], start=1):
                        if len(row) != len(head):
                            xato(joy, f'{j}-blok jadval {r}-qatori ustunlar soniga mos emas')
                elif not blok.get('body'):
                    xato(joy, f'{j}-blok matni (body) bo\'sh')

            # ── Quiz ──
            quiz = topic.get('quiz') or []
            if len(quiz) < 4:
                xato(joy, f'quiz savollari kam ({len(quiz)} ta, kamida 4 kerak)')
            jami_savol += len(quiz)

            for j, q in enumerate(quiz, start=1):
                qjoy = f'{joy} quiz#{j}'
                tur = q.get('type')
                if tur not in SAVOL_TURLARI:
                    xato(qjoy, f"savol turi noto'g'ri: '{tur}'")
                    continue
                if not q.get('q'):
                    xato(qjoy, "savol matni yo'q")
                if not q.get('explain'):
                    ogoh(qjoy, "tushuntirish (explain) yo'q")

                if tur == 'mc':
                    opts = q.get('options') or []
                    if len(opts) < 2:
                        xato(qjoy, f'variantlar kam ({len(opts)} ta)')
                    ans = q.get('answer')
                    if not isinstance(ans, int) or isinstance(ans, bool):
                        xato(qjoy, f"mc javobi butun son bo'lishi kerak, hozir: {ans!r}")
                    elif not (0 <= ans < len(opts)):
                        xato(qjoy, f'javob indeksi chegaradan tashqarida: {ans} '
                                   f'({len(opts)} ta variant)')
                    if len(set(map(str, opts))) != len(opts):
                        ogoh(qjoy, 'bir xil variantlar bor')
                elif tur == 'tf':
                    if not isinstance(q.get('answer'), bool):
                        xato(qjoy, "tf javobi True/False bo'lishi kerak")
                else:  # fill
                    if not str(q.get('answer') or '').strip():
                        xato(qjoy, "fill javobi bo'sh")

            # ── Uyga vazifa ──
            hw = topic.get('homework') or {}
            tasks = hw.get('tasks') or []
            if len(tasks) < 3:
                xato(joy, f'uy vazifasi kam ({len(tasks)} ta, kamida 3 kerak)')
            jami_vazifa += len(tasks)

            ko_rilgan_id = set()
            tekshiriladigan = 0
            for t in tasks:
                tid = t.get('id')
                tjoy = f'{joy} uy/{tid}'
                if not tid:
                    xato(tjoy, "vazifada id yo'q")
                elif tid in ko_rilgan_id:
                    xato(tjoy, f"id '{tid}' takrorlangan")
                else:
                    ko_rilgan_id.add(tid)
                if t.get('type') not in VAZIFA_TURLARI:
                    xato(tjoy, f"vazifa turi noto'g'ri: '{t.get('type')}'")
                if not t.get('prompt'):
                    xato(tjoy, "savol matni yo'q")
                if t.get('type') == 'open':
                    if t.get('answer'):
                        xato(tjoy, "'open' turdagi vazifada javob bo'lmasligi kerak")
                else:
                    if not str(t.get('answer') or '').strip():
                        xato(tjoy, "javob (answer) yo'q")
                    else:
                        tekshiriladigan += 1

            if tekshiriladigan == 0 and tasks:
                ogoh(joy, "uy vazifasida avtomatik tekshiriladigan savol yo'q")


# ── Natija ──
print()
print('═' * 58)
print(f'  Mavzular: {jami_mavzu}   Quiz savollari: {jami_savol}   '
      f'Uy vazifalari: {jami_vazifa}')
print('═' * 58)

if ogohlantirishlar:
    print(f'\nOgohlantirish ({len(ogohlantirishlar)}):')
    for w in ogohlantirishlar[:25]:
        print(f'  ! {w}')
    if len(ogohlantirishlar) > 25:
        print(f'  ... yana {len(ogohlantirishlar) - 25} ta')

if xatolar:
    print(f'\nXATO ({len(xatolar)}):')
    for e in xatolar:
        print(f'  ✗ {e}')
    sys.exit(1)

print('\n✓ Dastur to\'liq va xatosiz.')
