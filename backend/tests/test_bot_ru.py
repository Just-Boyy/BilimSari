# -*- coding: utf-8 -*-
"""Bot xabarlari o'quvchi tilida (uz/ru) va marafondagi shubhali akkaunt belgilari."""
import os
import re
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import botchat  # noqa: E402
import dostlar  # noqa: E402
import marafon  # noqa: E402
import payments  # noqa: E402
import tgbot  # noqa: E402
from db import get_connection  # noqa: E402
from games import clock  # noqa: E402

c = A.app.test_client()
fails = []
CALLS = []
MID = [7000]
OWNER = 5771496552


def fake_tg(method, payload):
    MID[0] += 1
    CALLS.append((method, payload))
    return {'ok': True, 'result': {'message_id': MID[0]}}


tgbot.tg_api = fake_tg
A.tg_api = fake_tg


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:600]}'))
    if not cond:
        fails.append(name)


def db(sql, params=(), fetch=False):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall() if fetch else None
    conn.commit(); cur.close(); conn.close()
    return rows


def mk(name, tg=None, lang=None, created='2026-01-01 00:00:00'):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id) VALUES (%s, TRUE, 'math', %s) RETURNING id",
             (name, tg), True)[0]['id']
    db('UPDATE users SET lang = %s, created_at = %s WHERE id = %s', (lang, created, uid))
    return uid


HOOK = {'X-Telegram-Bot-Api-Secret-Token': A.WEBHOOK_SECRET}
UPD = [500]


def hook(frm, text, lang_code=None):
    CALLS.clear()
    UPD[0] += 1
    sender = {'id': frm, 'first_name': 'Ivan'}
    if lang_code:
        sender['language_code'] = lang_code
    body = {'update_id': UPD[0], 'message': {'message_id': UPD[0], 'chat': {'id': frm, 'type': 'private'},
                                              'from': sender, 'text': text}}
    return c.post('/telegram/webhook', headers=HOOK, json=body).status_code


def texts(chat):
    return [p.get('text') or '' for m, p in CALLS if m == 'sendMessage' and p.get('chat_id') == chat]


def keyboard_labels(chat):
    out = []
    for m, p in CALLS:
        if p.get('chat_id') == chat:
            for row in ((p.get('reply_markup') or {}).get('keyboard') or []) + \
                       ((p.get('reply_markup') or {}).get('inline_keyboard') or []):
                out += [b.get('text') for b in row]
    return out


CYR = re.compile('[А-Яа-яЁё]')

RU_TG, UZ_TG, NEW_RU_TG, PICKED_UZ_TG = 9100001, 9100002, 9100003, 9100004
mk('Иван', RU_TG, 'ru')
mk('Ali', UZ_TG, 'uz')
mk('Olim', PICKED_UZ_TG, 'uz')

print('\n=== Til aniqlash ===')
check('users.lang=ru -> ru', tgbot.lang_of(RU_TG) == 'ru')
check('users.lang=uz -> uz (Telegram ruscha bo\'lsa ham)', tgbot.lang_of(PICKED_UZ_TG, 'ru') == 'uz')
check('bazada yo\'q, Telegram ru-RU -> ru', tgbot.lang_of(NEW_RU_TG, 'ru-RU') == 'ru')
check('bazada yo\'q, Telegram en -> uz', tgbot.lang_of(NEW_RU_TG, 'en') == 'uz')
check('pick: L -> ru', tgbot.pick(tgbot.L('a', 'б'), 'ru') == 'б' and tgbot.pick('x', 'ru') == 'x')
check('kun_ru', [tgbot.kun_ru(n) for n in (1, 2, 5, 11, 21, 22)] == ['день', 'дня', 'дней', 'дней', 'день', 'дня'])
check("som ru/uz", payments.som(12000, 'ru') == '12 000 сум' and payments.som(12000) == "12 000 so'm")

print('\n=== /start, /help, menyu ===')
hook(NEW_RU_TG, '/start', 'ru')
t = texts(NEW_RU_TG)
check('/start (Telegram ruscha, yangi) -> ruscha salom', t and t[0].startswith('Привет'), t)
check('/start -> ruscha menyu', '🛒 Магазин' in keyboard_labels(NEW_RU_TG), keyboard_labels(NEW_RU_TG))
hook(UZ_TG, '/start', 'ru')
t = texts(UZ_TG)
check("/start (ilovada o'zbekcha tanlagan) -> o'zbekcha", t and t[0].startswith('Salom'), t)
check("/start -> o'zbekcha menyu", botchat.BTN_SHOP in keyboard_labels(UZ_TG))
hook(RU_TG, '/help')
t = texts(RU_TG)
check('/help ruscha', t and t[0].startswith('Команды'), t)
hook(RU_TG, '/kun')
t = texts(RU_TG)
check('/kun ruscha', t and 'Вопрос дня' in t[0], t)

hook(RU_TG, '🛒 Магазин')
t = texts(RU_TG)
check('ruscha menyu tugmasi (Магазин) -> ruscha do\'kon', t and 'Покупка предмета' in t[0], t)
check("do'kon tugmasi ruscha", 'Открыть магазин' in keyboard_labels(RU_TG), keyboard_labels(RU_TG))
hook(UZ_TG, '🛒 Магазин')
t = texts(UZ_TG)
check("ruscha tugma o'zbek o'quvchida ham ishlaydi (o'zbekcha javob)", t and "Fan sotib olish" in t[0], t)
hook(RU_TG, botchat.BTN_SHOP)
t = texts(RU_TG)
check("o'zbekcha tugma ruscha o'quvchida -> ruscha javob", t and 'Покупка предмета' in t[0], t)
hook(RU_TG, '📚 Открыть приложение')
check('Открыть приложение', any('Нажмите кнопку' in x for x in texts(RU_TG)), texts(RU_TG))
hook(RU_TG, '🧾 Мои платежи')
check("To'lovlarim (bo'sh) ruscha", any('нет платежей' in x for x in texts(RU_TG)), texts(RU_TG))
hook(RU_TG, '💬 Связаться с админом')
check('Admin bilan bog\'lanish ruscha', any('Напишите свой вопрос' in x for x in texts(RU_TG)), texts(RU_TG))

print('\n=== Jonli chat ===')
hook(RU_TG, 'Здравствуйте, вопрос по оплате')
admin_msgs = texts(OWNER)
check("adminga xabar o'zbekcha sarlavha bilan", admin_msgs and admin_msgs[0].startswith('💬 '), CALLS)
check('o\'quvchiga ruscha tasdiq', any('отправлено админу' in x for x in texts(RU_TG)), texts(RU_TG))
link = db('SELECT admin_message_id FROM bot_chat_links WHERE user_chat_id = %s ORDER BY created_ms DESC LIMIT 1', (RU_TG,), True)
if link:
    CALLS.clear()
    UPD[0] += 1
    c.post('/telegram/webhook', headers=HOOK, json={'update_id': UPD[0], 'message': {
        'message_id': UPD[0], 'chat': {'id': OWNER, 'type': 'private'}, 'from': {'id': OWNER, 'first_name': 'Admin'},
        'text': 'Добрый день!', 'reply_to_message': {'message_id': link[0]['admin_message_id']}}})
    check('admin javobi ruscha o\'quvchiga "Админ:" bilan', any(x.startswith('👨‍💼 <b>Админ:</b>') for x in texts(RU_TG)),
          texts(RU_TG))
else:
    check('bot_chat_links yozildi', False)

print('\n=== Tayyor javoblar tarjimasi ===')
src = ''.join(open(f, encoding='utf-8').read() for f in ('payments.py', 'botchat.py', 'partners.py'))
missing = [k for k in botchat.RU_TEXT if k not in src.replace('\\n', '\n')]
check("RU_TEXT kalitlari kodda bor (matn o'zgarsa tarjima eskirmasin)", not missing, missing)
r = botchat.ru_text("✅ Chek qabul qilindi! Buyurtma <b>AB12</b> adminga yuborildi.\n"
                    "Odatda 5–30 daqiqada tekshiriladi — natija shu yerga keladi.")
check('andoza: chek qabul qilindi', r.startswith('✅ Чек принят! Заказ <b>AB12</b>'), r)
r = botchat.ru_text("Chekingiz (AB12) allaqachon tekshirilmoqda. Natija shu yerga keladi. Savolingiz bo'lsa, matn bilan yozing.")
check('andoza: allaqachon tekshirilmoqda', r.startswith('Ваш чек (AB12)'), r)
check("noma'lum matn o'zgarmaydi", botchat.ru_text('Salom') == 'Salom')

print('\n=== Do\'stlar xabari ===')
a = mk('Ali Valiyev', 9100010, 'uz')
b = mk('Пётр', 9100011, 'ru')
conn = get_connection(); cur = conn.cursor()
CALLS.clear()
dostlar.send_request(cur, conn, a, b)
cur.close(); conn.close()
t = texts(9100011)
check("do'stlik so'rovi ruscha o'quvchiga ruscha", t and 'заявку в друзья' in t[0], t)

print('\n=== Bot sozlamasi: ruscha buyruqlar ===')
CALLS.clear()
old = A.BOT_TOKEN
A.BOT_TOKEN = '000000:SINOV'
try:
    A.setup_telegram_bot()
finally:
    A.BOT_TOKEN = old
ru_cmds = [p for m, p in CALLS if m == 'setMyCommands' and p.get('language_code') == 'ru']
check('setMyCommands language_code=ru', ru_cmds and all(CYR.search(x['description']) for x in ru_cmds[0]['commands']),
      CALLS)
check('ruscha tavsif', any(m == 'setMyDescription' and p.get('language_code') == 'ru' for m, p in CALLS))

print('\n=== Marafon: ikkinchi akkaunt belgilari ===')
now = clock.now_ms()
DAY = 24 * 3600 * 1000
m = {'id': 999, 'start_ms': now - 2 * DAY, 'end_ms': now + DAY}
cheat = mk('Hiyla', 9100020)
farm = mk('Soxta', 9100021, created='2099-01-01 00:00:00')   # marafon boshlangandan keyin ochilgan
honest = mk('Halol', 9100022)
others = [mk(f'Raqib {i}', 9100030 + i) for i in range(5)]
crowd = [mk(f'Olomon {i}', 9100040 + i) for i in range(5)]
SID = [1000]


def game(players, chaqmoq_for, at):
    SID[0] += 1
    for rank, uid in enumerate(players, 1):
        db('''INSERT INTO game_results (session_id, room_id, user_id, game_type, subject, difficulty, score, earned,
              correct, wrong, total, accuracy, rank, players, created_ms, chaqmoq)
              VALUES (%s, 1, %s, 'chaqmoq', 'math', 'easy', 10, 10, 5, 0, 5, 100, %s, %s, %s, %s)''',
           (SID[0], uid, rank, len(players), at, 30 if uid in chaqmoq_for else 0))


for i in range(6):
    game([cheat, farm], {cheat}, now - DAY + i * 1000)
for i, o in enumerate(others):
    game([honest, o], {honest}, now - DAY + i * 1000)
    for j in range(4):
        game([o, crowd[j]], set(), now - DAY + 50000 + i * 100 + j)
game([cheat, -1], {cheat}, now - DAY + 99000)          # kompyuter bilan o'yin raqib hisoblanmaydi
conn = get_connection(); cur = conn.cursor()
fl = marafon._flags(cur, m, cheat, marafon._user(cur, cheat))
fl_honest = marafon._flags(cur, m, honest, marafon._user(cur, honest))
cur.close(); conn.close()
check('bitta raqib bilan 6/7', any("6/7 tasi bitta raqib bilan (ID %d)" % farm in f for f in fl), fl)
check('raqib yangi akkaunt deb belgilandi', any('raqib yangi akkaunt' in f for f in fl), fl)
check('ikkinchi akkaunt belgisi', any('ikkinchi akkaunt' in f for f in fl), fl)
check("yangi akkauntlar bilan o'yinlar belgisi", any('marafon paytida ochilgan akkauntlar' in f for f in fl), fl)
check("halol o'yinchida belgi yo'q", fl_honest == [], fl_honest)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
sys.exit(1 if fails else 0)
