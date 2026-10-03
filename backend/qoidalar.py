# -*- coding: utf-8 -*-
"""
Ilova qoidalari (admin panel → «Qoidalar»): dasturchi kodda yozadigan raqamlar — chaqmoq mukofotlari,
o'yin imkoniyatlari, kutish vaqtlari, eslatma soatlari — panelda o'zgartiriladi.

Qiymatlar pay_settings jadvalida (kalit 'rules', JSON) saqlanadi va ishlayotgan modullarning o'zgaruvchilariga
qo'llanadi (chances.WIN, study.COOLDOWN_HOURS, ...): ular funksiyalar ichida har safar o'qiladi, shuning uchun
yangi qiymat darhol ishlaydi. Har gunicorn worker REFRESH_S da bir marta bazadan yangilaydi.

Qoidaga bog'liq tushuntirish matnlari ("+5 chaqmoq", "24 soatda 3 ta o'yin") TEMPLATES orqali avtomatik
yangilanadi — sayt.py ularni o'quvchi sahifalaridagi matn almashtirishlariga qo'shadi.
"""

import json
import logging
import time

import daily
import jurnal
import notify
import personal
import study
from games import chances
from games import engine as game_engine

logger = logging.getLogger('bilimsari.qoidalar')

KEY = 'rules'
REFRESH_S = 10
H = 3600 * 1000

# kalit: (bo'lim, nomi, modul, o'zgaruvchi, ko'paytiruvchi, min, max, birlik, izoh, avvalgilarga ta'sir qiladimi)
RULES = {
    'games.max_chances': ("O'yinlar", "Chaqmoq beradigan o'yinlar soni (bir aylanada)", chances, 'MAX', 1, 1, 50, 'ta', '', False),
    'games.reset_hours': ("O'yinlar", 'Imkoniyatlar yangilanish vaqti', chances, 'RESET_MS', H, 1, 168, 'soat',
                          "Oxirgi chaqmoqli o'yin tugagandan keyin sanaladi", False),
    'games.win': ("O'yinlar", "1-o'rin uchun chaqmoq", chances, 'WIN', 1, 0, 1000, 'chaqmoq', '', False),
    'games.play': ("O'yinlar", "Qolgan o'rinlar uchun chaqmoq", chances, 'PLAY', 1, 0, 1000, 'chaqmoq', '', False),
    'games.points_correct': ("O'yinlar", "To'g'ri javob uchun ball", game_engine, 'POINTS_CORRECT', 1, 0, 1000, 'ball', '', False),
    'games.points_fast': ("O'yinlar", 'Tez javob uchun qo\'shimcha ball', game_engine, 'POINTS_FAST', 1, 0, 1000, 'ball', '', False),
    'games.bonus_win': ("O'yinlar", "G'olib bonusi", game_engine, 'BONUS_WIN', 1, 0, 1000, 'ball', '', False),
    'games.bonus_complete': ("O'yinlar", "O'yinni oxirigacha o'ynagan bonusi", game_engine, 'BONUS_COMPLETE', 1, 0, 1000, 'ball',
                             "Savollarning kamida yarmiga javob bergan", False),
    'games.xp_cap': ("O'yinlar", "Kunlik o'yin balli chegarasi", game_engine, 'DAILY_XP_CAP', 1, 0, 100000, 'ball',
                     "Kuniga shundan ortiq ball darajaga hisoblanmaydi", False),
    'lesson.cooldown_hours': ('Darslar', 'Bir fanda mavzular orasidagi kutish', study, 'COOLDOWN_HOURS', 1, 0, 168, 'soat',
                              "0 — kutishsiz, mavzular ketma-ket ochiladi", False),
    'lesson.quiz_pass': ('Darslar', "Testdan o'tish chegarasi", study, 'QUIZ_PASS_PERCENT', 1, 1, 100, '%', '', False),
    'lesson.quiz_per_correct': ('Darslar', "Testda har to'g'ri javob uchun chaqmoq (1-urinish)", study, 'QUIZ_CHAQMOQ_PER_CORRECT',
                                1, 0, 100, 'chaqmoq', '', True),
    'lesson.quiz_max': ('Darslar', 'Bitta test uchun eng ko\'p chaqmoq', study, 'QUIZ_CHAQMOQ_MAX', 1, 0, 1000, 'chaqmoq', '', True),
    'lesson.homework': ('Darslar', 'Uy vazifasi uchun chaqmoq', study, 'HOMEWORK_CHAQMOQ', 1, 0, 1000, 'chaqmoq', '', True),
    'daily.reward': ('Kun savoli', "To'g'ri javob uchun chaqmoq", daily, 'CHAQMOQ_CORRECT', 1, 0, 1000, 'chaqmoq',
                     'Yangi javoblarga ta\'sir qiladi', False),
    'personal.every_hours': ('Shaxsiy darslar', 'Yangi shaxsiy dars yaratish oralig\'i', personal, 'GENERATE_EVERY_MS', H, 1, 168,
                             'soat', '', False),
    'notify.question_hour': ('Eslatmalar', '«Kun savoli tayyor» xabari vaqti', notify, 'QUESTION_HOUR', 1, 0, 21, 'soat (Toshkent)',
                             'Shu soatdan 3 soat ichida yuboriladi', False),
    'notify.daily_hour': ('Eslatmalar', "Kunlik eslatmaning standart vaqti", notify, 'DAILY_HOUR', 1, 7, 22, 'soat (Toshkent)',
                          "Vaqtni o'zi tanlamagan o'quvchilar uchun", False),
    'notify.active_days': ('Eslatmalar', 'Shuncha kun kirmaganlarga eslatma yuborilmaydi', notify, 'ACTIVE_DAYS', 1, 1, 365, 'kun',
                           '', False),
    'notify.pay_summary_hour': ('Eslatmalar', "Adminga kunlik to'lov hisoboti vaqti", notify, 'PAY_SUMMARY_HOUR', 1, 0, 23,
                                'soat (Toshkent)', '', False),
    'notify.premium_soon_days': ('Eslatmalar', 'Premium tugashidan necha kun oldin eslatiladi', notify, 'PREMIUM_SOON_DAYS', 1, 1, 30,
                                 'kun', '', False),
}
# Kod yuklanganda — standart qiymatlar (admin o'zgartirmagan bo'lsa shular)
DEFAULTS = {k: int(getattr(r[2], r[3]) // r[4]) for k, r in RULES.items()}


class RuleError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


_state = {'t': 0.0, 'values': {}}


def _load(cur) -> dict:
    cur.execute('SELECT value FROM pay_settings WHERE key = %s', (KEY,))
    row = cur.fetchone()
    try:
        data = json.loads(row['value']) if row and row['value'] else {}
    except (TypeError, ValueError):
        data = {}
    return {k: int(v) for k, v in data.items() if k in RULES and isinstance(v, (int, float))}


def values() -> dict:
    """Joriy qiymatlar (standart + admin o'zgartirganlari)."""
    return dict(DEFAULTS, **_state['values'])


def _apply(overrides):
    old = values()
    _state['values'] = dict(overrides)
    cur_values = values()
    for key, r in RULES.items():
        setattr(r[2], r[3], cur_values[key] * r[4])
    notify.QUESTION_LAST_HOUR = min(24, cur_values['notify.question_hour'] + 3)
    study.LESSON_CHAQMOQ_SQL = study.build_lesson_chaqmoq_sql()
    if any(old[k] != cur_values[k] for k in RULES if RULES[k][9] or k.startswith('daily.')):
        jurnal.VERSION[0] += 1       # chaqmoq hisobi o'zgardi — reyting keshi yangilansin


def refresh(cur=None, force=False):
    """Bazadagi qiymatlarni modullarga qo'llaydi (REFRESH_S da bir marta). Baza ishlamasa — eskisi qoladi."""
    now = time.monotonic()
    if not force and now - _state['t'] < REFRESH_S:
        return
    _state['t'] = now
    try:
        if cur is not None:
            overrides = _load(cur)
        else:
            from db import get_connection   # noqa: PLC0415
            conn = get_connection()
            c = conn.cursor()
            try:
                overrides = _load(c)
            finally:
                c.close()
                conn.close()
    except Exception:  # noqa: BLE001
        logger.warning("Qoidalar o'qilmadi", exc_info=True)
        return
    if overrides != _state['values']:
        _apply(overrides)


def save(cur, conn, changes) -> dict:
    """changes: {kalit: son yoki None (standartga qaytarish)}."""
    if not isinstance(changes, dict) or not changes:
        raise RuleError("O'zgarish yo'q.")
    data = _load(cur)
    for key, value in changes.items():
        if key not in RULES:
            raise RuleError(f"Noma'lum qoida: {key}")
        if value is None or value == '':
            data.pop(key, None)
            continue
        try:
            n = int(value)
        except (TypeError, ValueError):
            raise RuleError(f"«{RULES[key][1]}» — butun son kiriting.")
        lo, hi = RULES[key][5], RULES[key][6]
        if not lo <= n <= hi:
            raise RuleError(f"«{RULES[key][1]}» {lo} dan {hi} gacha bo'lishi kerak.")
        if n == DEFAULTS[key]:
            data.pop(key, None)
        else:
            data[key] = n
    v = dict(DEFAULTS, **data)
    if v['lesson.quiz_max'] < v['lesson.quiz_per_correct']:
        raise RuleError("Bitta test uchun eng ko'p chaqmoq har to'g'ri javob chaqmog'idan kam bo'lmasin.")
    cur.execute('DELETE FROM pay_settings WHERE key = %s', (KEY,))
    if data:
        cur.execute('INSERT INTO pay_settings (key, value) VALUES (%s, %s)', (KEY, json.dumps(data)))
    conn.commit()
    _state['t'] = time.monotonic()
    _apply(data)
    return values()


def listing() -> list:
    v = values()
    return [{'key': k, 'group': r[0], 'label': r[1], 'value': v[k], 'default': DEFAULTS[k], 'min': r[5], 'max': r[6],
             'unit': r[7], 'hint': r[8], 'retro': r[9]} for k, r in RULES.items()]


# ───────────────────────── Qoidaga bog'liq matnlar ─────────────────────────

def _ru_soat(n):
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return 'час'
    return 'часа' if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else 'часов'


def _ru_igra(n):
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return 'игра'
    return 'игры' if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else 'игр'


def _ru_molniya(n):
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return 'молния'
    return 'молнии' if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else 'молний'


# (o'zbekcha shablon, ruscha shablon) — {nom} qoidalar qiymatlari bilan to'ldiriladi.
# Standart qiymatlar bilan to'ldirilgan o'zbekcha matn kodda yozilgani bilan AYNAN bir xil bo'lishi kerak.
TEMPLATES = [
    ("Testda har to'g'ri javob +{quiz} (1-urinish), uy vazifasi +{hw}",
     'В тесте +{quiz} за верный ответ (1-я попытка), домашка +{hw}'),
    ("To'g'ri javob +{daily}", 'Правильный ответ +{daily}'),
    ("To'g'ri va tez javob bering — +{daily} chaqmoq va kunlik reyting.",
     'Отвечайте правильно и быстро — +{daily} {daily_m} и место в рейтинге дня.'),
    ("O'yinlarda {reset} soatda {max} ta chaqmoqli o'yin: 1-o'rin +{win}, qolganlar +{play}. "
     "Kompyuter bilan o'yin chaqmoq bermaydi.",
     'В играх за {reset} {reset_s} {max} {max_i} с молниями: 1-е место +{win}, остальные +{play}. '
     'Игра с компьютером молний не даёт.'),
    ("Oxirgi chaqmoqli o'yin tugagach {reset} soatlik taymer boshlanadi.",
     'После последней игры с молниями запустится {reset}-часовой таймер.'),
    ("Har {ph} soatda bitta shaxsiy dars yaratiladi. Keyingisi:",
     'Новый личный урок можно создавать раз в {ph} {ph_s}. Следующий через:'),
    ("O'zingizda ochiq fanlardan istalgan mavzuni yozing — AI siz uchun dars, 3 savolli test va uy vazifasini tayyorlaydi. "
     "Har {ph} soatda bitta yangi dars yaratiladi, o'qish esa cheksiz. Darslar faqat sizga ko'rinadi va Premium tugasa ham "
     "o'zingizda qoladi.",
     'Напишите любую тему по вашим открытым предметам — ИИ подготовит для вас урок, тест из 3 вопросов и домашнее задание. '
     'Новый урок можно создавать раз в {ph} {ph_s}, а заниматься — без ограничений. Уроки видите только вы, и они '
     'останутся у вас даже после окончания Premium.'),
    ("Hamma bir xil savolga javob beradi. To'g'ri javob +{pc} ball, tez javob yana +{pf}.",
     'Все отвечают на один и тот же вопрос. Правильный ответ +{pc} очков, быстрый — ещё +{pf}.'),
]


def _fields(v) -> dict:
    return {'quiz': v['lesson.quiz_per_correct'], 'hw': v['lesson.homework'], 'daily': v['daily.reward'],
            'daily_m': _ru_molniya(v['daily.reward']), 'reset': v['games.reset_hours'], 'reset_s': _ru_soat(v['games.reset_hours']),
            'max': v['games.max_chances'], 'max_i': _ru_igra(v['games.max_chances']), 'win': v['games.win'],
            'play': v['games.play'], 'ph': v['personal.every_hours'], 'ph_s': _ru_soat(v['personal.every_hours']),
            'pc': v['games.points_correct'], 'pf': v['games.points_fast']}


def auto_texts() -> dict:
    """{'uz': {asl matn: yangi}, 'ru': {asl matn: yangi ruscha}} — faqat qiymati o'zgargan qoidalar uchun."""
    base, cur_f = _fields(DEFAULTS), _fields(values())
    out = {'uz': {}, 'ru': {}}
    if base == cur_f:
        return out
    for uz, ru in TEMPLATES:
        orig, new = uz.format(**base), uz.format(**cur_f)
        if orig != new:
            out['uz'][orig] = new
            out['ru'][orig] = ru.format(**cur_f)
    return out
