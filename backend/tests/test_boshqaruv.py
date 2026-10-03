# -*- coding: utf-8 -*-
"""Admin boshqaruvi: bot/ilova tanaffusi, funksiya kalitlari, e'lon, bloklash, bonus chaqmoq va o'quvchi amallari."""
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import timedelta
from urllib.parse import urlencode

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import admin_auth  # noqa: E402
import boshqaruv  # noqa: E402
import notify  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection, utc_now  # noqa: E402
from games import clock  # noqa: E402

c = A.app.test_client()
fails = []
CALLS = []
MID = [9000]
OWNER = 5771496552
FAKE_TOKEN = '000000:SINOV-BOSHQARUV'


def fake_tg(method, payload):
    MID[0] += 1
    CALLS.append((method, payload))
    return {'ok': True, 'result': {'message_id': MID[0]}}


tgbot.tg_api = fake_tg
A.tg_api = fake_tg
A.BOT_TOKEN = FAKE_TOKEN          # Telegram orqali kirish (initData imzosi) va webhookni qayta o'rnatish uchun


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


def mk(name, tg):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id) VALUES (%s, TRUE, 'math', %s) RETURNING id",
             (name, tg), True)[0]['id']
    return uid, {'Authorization': 'Bearer ' + create_token(uid)}


def init_data(tg_id, first_name='Yangi'):
    fields = {'auth_date': str(int(time.time())), 'query_id': 'AAHtest',
              'user': json.dumps({'id': tg_id, 'first_name': first_name, 'username': f'u{tg_id}'}, separators=(',', ':'))}
    dcs = '\n'.join(f'{k}={v}' for k, v in sorted(fields.items()))
    secret = hmac.new(b'WebAppData', FAKE_TOKEN.encode(), hashlib.sha256).digest()
    fields['hash'] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
HOOK = {'X-Telegram-Bot-Api-Secret-Token': A.WEBHOOK_SECRET}
UPD = [800]


def hook(frm, text=None, callback=None):
    CALLS.clear()
    UPD[0] += 1
    sender = {'id': frm, 'first_name': 'Ali'}
    if callback:
        body = {'update_id': UPD[0], 'callback_query': {'id': 'cb1', 'from': sender, 'data': callback}}
    else:
        body = {'update_id': UPD[0], 'message': {'message_id': UPD[0], 'chat': {'id': frm, 'type': 'private'},
                                                  'from': sender, 'text': text}}
    return c.post('/telegram/webhook', headers=HOOK, json=body).status_code


def sent_to(chat):
    return [p.get('text') or '' for m, p in CALLS if m == 'sendMessage' and p.get('chat_id') == chat]


def control(action, body=None):
    return c.post(f'/api/admin/control/{action}', headers=ADM, json=body or {}).get_json()


def user_act(uid, action, body=None):
    r = c.post(f'/api/admin/users/{uid}/{action}', headers=ADM, json=body or {})
    return r.status_code, r.get_json()


ALI_TG, VALI_TG = 9300001, 9300002
ali, ali_h = mk('Ali Valiyev', ALI_TG)
vali, vali_h = mk('Vali', VALI_TG)
adm_user, adm_h = mk('Ega', OWNER)

print('\n=== Boshqaruv holati ===')
r = c.get('/api/admin/control', headers=ADM).get_json()
check('Admin: holat ochiladi, hamma bo\'lim yoqiq, tanaffus yo\'q',
      r['ok'] and all(f['on'] for f in r['features']) and r['pause'] == {'bot': None, 'app': None}, r)
check('Admin tokensiz — 401', c.get('/api/admin/control').status_code == 401)
check("Ro'yxatdagi kalitlar", {f['key'] for f in r['features']} == set(boshqaruv.FEATURES), r['features'])

print('\n=== Ilovani to\'xtatish ===')
r = control('pause', {'targets': ['app'], 'minutes': 30, 'message': 'Yangi fanlar qo\'shilmoqda'})
check('Ilova to\'xtatildi (30 daq)', r['ok'] and r['pause']['app']['active'] and r['pause']['bot'] is None, r)
d = c.get('/api/study/dashboard', headers=ali_h)
j = d.get_json()
check("O'quvchiga 423 maintenance + izoh + vaqt", d.status_code == 423 and j['code'] == 'maintenance'
      and j['message'] == "Yangi fanlar qo'shilmoqda" and 29 * 60000 < j['until_ms'] - clock.now_ms() <= 30 * 60000, (d.status_code, j))
check('Admin (Telegram egasi) ilovadan foydalanadi', c.get('/api/study/dashboard', headers=adm_h).status_code == 200)
check('Admin panel ishlaydi', c.get('/api/admin/stats', headers=ADM).status_code == 200)
hook(ALI_TG, '/help')
check('Faqat ilova to\'xtatilgan — bot odatdagidek javob beradi', any('Buyruqlar' in t for t in sent_to(ALI_TG)), CALLS)
r = control('resume', {'targets': ['app']})
check('Ilova qayta yoqildi', r['ok'] and r['pause']['app'] is None
      and c.get('/api/study/dashboard', headers=ali_h).status_code == 200, r)

control('pause', {'targets': ['app'], 'minutes': 1})
real_now = clock.now_ms
clock.now_ms = lambda: real_now() + 2 * 60000
check('Muddat tugasa ilova o\'zi yoqiladi', c.get('/api/study/dashboard', headers=ali_h).status_code == 200)
clock.now_ms = real_now
control('resume', {'targets': ['app']})
r = c.post('/api/admin/control/pause', headers=ADM, json={'targets': [], 'minutes': 10})
check("Hech narsa tanlanmasa — 400", r.status_code == 400, r.get_json())
r = c.post('/api/admin/control/pause', headers=ADM, json={'targets': ['bot'], 'minutes': 99999999})
check("Juda uzun muddat — 400", r.status_code == 400, r.get_json())

print('\n=== Botni to\'xtatish ===')
control('pause', {'targets': ['bot'], 'minutes': 60, 'message': 'Server yangilanmoqda'})
hook(ALI_TG, '/start')
t = sent_to(ALI_TG)
check("O'quvchiga bir marta «texnik ishlar» javobi (izoh va vaqt bilan)",
      len(t) == 1 and 'texnik ishlar' in t[0] and 'Server yangilanmoqda' in t[0] and 'qayta ishga tushadi' in t[0], CALLS)
hook(ALI_TG, 'yana yozdim')
check('Ikkinchi xabarga javob yo\'q (chat to\'lmaydi)', not sent_to(ALI_TG), CALLS)
hook(ALI_TG, callback='ord:cancel:1')
cb = [p for m, p in CALLS if m == 'answerCallbackQuery']
check('Tugma bosilsa — qisqa izoh', cb and 'texnik' in cb[0]['text'].lower(), CALLS)
hook(OWNER, '/start')
check('Admin botdan odatdagidek foydalanadi', any(t.startswith('Salom') for t in sent_to(OWNER)), CALLS)
check('Eslatmalar to\'xtatilgan', boshqaruv.notifications_off())
CALLS.clear()
ok = notify._deliver(get_connection().cursor(), get_connection(), {'id': ali, 'telegram_id': ALI_TG, 'lang': 'uz'},
                     'sinov', 'r1', 'Eslatma', None, '')
check('notify._deliver hech narsa yubormaydi', ok is False and not CALLS, CALLS)
control('resume', {'targets': ['bot']})
check('Bot qayta yoqildi — eslatmalar ochiq', not boshqaruv.notifications_off())

print('\n=== Bo\'limlar ===')
r = control('features', {'features': {'games': False, 'daily': False}})
check("O'yinlar va kun savoli o'chdi", r['ok'] and not next(f for f in r['features'] if f['key'] == 'games')['on'], r)
s = c.post('/api/games/rooms', headers=ali_h, json={'game': 'quiz_battle', 'subject': 'math'})
check("Yangi o'yin — 423 feature_off", s.status_code == 423 and s.get_json()['code'] == 'feature_off'
      and s.get_json()['feature'] == 'games', (s.status_code, s.get_json()))
check("O'yin reytingi ko'rinadi", c.get('/api/games/leaderboard', headers=ali_h).status_code == 200)
check('Kun savoli — 423', c.get('/api/study/daily', headers=ali_h).status_code == 423)
check('Admin uchun ochiq', c.post('/api/games/rooms', headers=adm_h,
                                  json={'game': 'quiz_battle', 'subject': 'math'}).status_code != 423)
check("Boshqa bo'limlar ochiq", c.get('/api/study/dashboard', headers=ali_h).status_code == 200)
control('features', {'features': {'games': True, 'daily': True}})
check("Qayta yoqildi", c.get('/api/study/daily', headers=ali_h).status_code == 200)
r = c.post('/api/admin/control/features', headers=ADM, json={'features': {'yoq': False}})
check("Noma'lum kalit — 400", r.status_code == 400)

control('features', {'features': {'registration': False}})
r = c.post('/api/telegram/auth', json={'initData': init_data(9300099)})
check("Ro'yxat yopiq: yangi o'quvchi — 423 registration_closed", r.status_code == 423
      and r.get_json()['code'] == 'registration_closed', (r.status_code, r.get_json()))
check("Yangi o'quvchi yaratilmadi", not db('SELECT id FROM users WHERE telegram_id = %s', (9300099,), True))
r = c.post('/api/telegram/auth', json={'initData': init_data(ALI_TG, 'Ali')})
check("Eski o'quvchi kira oladi", r.status_code == 200 and r.get_json()['ok'], r.get_json())
control('features', {'features': {'registration': True}})
r = c.post('/api/telegram/auth', json={'initData': init_data(9300099)})
check("Ro'yxat ochilgach yangi o'quvchi kiradi", r.status_code == 200 and r.get_json()['ok'], r.get_json())
ali_h = {'Authorization': 'Bearer ' + create_token(ali)}

control('features', {'features': {'notifications': False}})
check("Eslatmalar kaliti o'chiq — yuborilmaydi", boshqaruv.notifications_off())
control('features', {'features': {'notifications': True}})

print("\n=== E'lon ===")
r = control('announcement', {'text': 'Ertaga yangi fan!', 'text_ru': 'Завтра новый предмет!', 'kind': 'warn', 'minutes': 60})
check("E'lon qo'yildi", r['ok'] and r['announcement']['text'] == 'Ertaga yangi fan!', r)
d = c.get('/api/study/dashboard', headers=ali_h).get_json()
check("Bosh sahifada (o'zbekcha)", d['announcement'] and d['announcement']['text'] == 'Ertaga yangi fan!'
      and d['announcement']['kind'] == 'warn', d.get('announcement'))
d = c.get('/api/study/dashboard', headers=dict(ali_h, **{'X-Lang': 'ru'})).get_json()
check('Bosh sahifada (ruscha)', d['announcement'] and d['announcement']['text'] == 'Завтра новый предмет!', d.get('announcement'))
r = c.post('/api/admin/control/announcement', headers=ADM, json={'text': '   '})
check("Bo'sh e'lon — 400", r.status_code == 400)
control('announcement-clear')
check("E'lon olib tashlandi", c.get('/api/study/dashboard', headers=ali_h).get_json()['announcement'] is None)

print('\n=== Bonus chaqmoq ===')
before = c.get(f'/api/admin/users/{ali}/control', headers=ADM).get_json()['chaqmoq']
s, r = user_act(ali, 'bonus', {'amount': 50, 'note': 'Tanlov g\'olibi'})
check('+50 chaqmoq', s == 200 and r['chaqmoq'] == before + 50 and r['parts']['bonus'] == 50 and r['bonus'][0]['note'], r)
check("O'quvchiga bot xabari", any('+50' in t for t in sent_to(ALI_TG) + [p.get('text', '') for _, p in CALLS]), CALLS)
d = c.get('/api/study/dashboard', headers=ali_h).get_json()
check("Bosh sahifada bonus qismi", d['chaqmoq_parts']['bonus'] == 50 and d['chaqmoq'] == before + 50, d['chaqmoq_parts'])
lb = c.get('/api/study/leaderboard', headers=vali_h).get_json()
check('Umumiy reytingda hisobga olingan', any(x['user_id'] == ali and x['chaqmoq'] == before + 50 for x in lb['top']), lb)
s, r = user_act(ali, 'bonus', {'amount': -20})
check('-20 chaqmoq (ayirish)', s == 200 and r['parts']['bonus'] == 30, r)
s, r = user_act(ali, 'bonus', {'amount': 0})
check("0 chaqmoq — 400", s == 400, r)

print('\n=== Bloklash ===')
db("""INSERT INTO game_results (session_id, room_id, user_id, game_type, subject, difficulty, score, earned, xp,
      correct, wrong, total, accuracy, rank, players, created_ms, chaqmoq)
      VALUES (770001, 1, %s, 'quiz_battle', 'math', 'orta', 40, 40, 40, 4, 0, 4, 100, 1, 2, %s, 30)""", (ali, clock.now_ms()))
CALLS.clear()
s, r = user_act(ali, 'ban', {'minutes': 0, 'reason': 'Aldash'})
check('Muddatsiz bloklandi', s == 200 and r['ban'] == {'until_ms': None, 'reason': 'Aldash'}, r)
check("O'quvchiga bot xabari (sabab bilan)", any('bloklangan' in t and 'Aldash' in t for t in sent_to(ALI_TG)), CALLS)
check('Eski seanslar yopildi (401)', c.get('/api/study/dashboard', headers=ali_h).status_code == 401)
ali_h = {'Authorization': 'Bearer ' + create_token(ali)}
d = c.get('/api/study/dashboard', headers=ali_h)
check('Qayta kirsa ham — 403 banned + sabab', d.status_code == 403 and d.get_json()['code'] == 'banned'
      and d.get_json()['reason'] == 'Aldash' and d.get_json()['until_ms'] is None, (d.status_code, d.get_json()))
hook(ALI_TG, '/start')
check('Botda — «bloklangan» javobi', any('bloklangan' in t for t in sent_to(ALI_TG)), CALLS)
time.sleep(boshqaruv.CACHE_S + 0.2)          # bloklanganlar keshi yangilansin
lb = c.get('/api/study/leaderboard', headers=vali_h).get_json()
check('Umumiy reytingda yo\'q', all(x['user_id'] != ali for x in lb['top']), lb['top'])
g = c.get('/api/games/leaderboard?period=all', headers=vali_h).get_json()
check("O'yin reytingida yo'q (boshqalar bor)", all(x['user_id'] != ali for x in g['top']), g['top'])
ov = c.get('/api/admin/control', headers=ADM).get_json()
check("Admin: bloklanganlar ro'yxatida", any(b['id'] == ali and b['reason'] == 'Aldash' for b in ov['banned']), ov['banned'])
s, r = user_act(ali, 'unban')
check('Blokdan chiqarildi', s == 200 and r['ban'] is None, r)
check('Endi ilova ishlaydi', c.get('/api/study/dashboard', headers=ali_h).status_code == 200)
lb = c.get('/api/study/leaderboard', headers=vali_h).get_json()
check('Reytingga qaytdi', any(x['user_id'] == ali for x in lb['top']), lb['top'])
s, r = user_act(ali, 'ban', {'minutes': 1440, 'reason': ''})
check('1 kunlik blok', s == 200 and r['ban'] and 1439 * 60000 < r['ban']['until_ms'] - clock.now_ms() <= 1440 * 60000, r)
user_act(ali, 'unban')
ali_h = {'Authorization': 'Bearer ' + create_token(ali)}

print("\n=== O'quvchi amallari ===")
s, r = user_act(ali, 'rename', {'name': '  Ali   Yangi  '})
row = db('SELECT name, custom_name FROM users WHERE id = %s', (ali,), True)[0]
check('Ism o\'zgardi (Telegram qayta yozmaydi)', s == 200 and row['name'] == 'Ali Yangi' and int(row['custom_name']) == 1, row)
s, r = user_act(ali, 'rename', {'name': 'A'})
check('Juda qisqa ism — 400', s == 400, r)

db('INSERT INTO game_chance_state (user_id, used, reset_at_ms) VALUES (%s, 3, %s)', (ali, clock.now_ms() + 3600000))
before = c.get(f'/api/admin/users/{ali}/control', headers=ADM).get_json()['chances']['left']
s, r = user_act(ali, 'reset-chances')
check("O'yin imkoniyatlari tiklandi (0 → 3)", before == 0 and s == 200 and r['chances']['left'] == 3, (before, r.get('chances')))

topic = db("SELECT id FROM topics WHERE subject_key = 'math' ORDER BY seq LIMIT 1", fetch=True)[0]['id']
db("INSERT INTO user_progress (user_id, topic_id, status, completed_at) VALUES (%s, %s, 'completed', %s)",
   (ali, topic, utc_now() - timedelta(hours=1)))
r = c.get(f'/api/admin/users/{ali}/control', headers=ADM).get_json()
check('Dars kutishi bor', r['cooldown']['active'], r['cooldown'])
s, r = user_act(ali, 'reset-cooldown')
check('Dars kutishi bekor qilindi', s == 200 and not r['cooldown']['active'], r.get('cooldown'))

s, r = user_act(ali, 'logout')
check('Hamma qurilmadan chiqarildi', s == 200 and r['sessions'] == 0
      and c.get('/api/study/dashboard', headers=ali_h).status_code == 401, r)
s, r = user_act(999999, 'ban', {'minutes': 0})
check("Yo'q o'quvchi — 404", s == 404, r)
s, r = user_act(ali, 'nimadir')
check("Noma'lum amal — 404", s == 404, r)

print('\n=== Bot holati va webhook ===')
CALLS.clear()
r = control('webhook')
check('Webhook qayta o\'rnatildi (kunlik egallashsiz)', r['ok'] and any(m == 'setWebhook' for m, _ in CALLS)
      and any(m == 'setMyCommands' for m, _ in CALLS), CALLS)
r = c.get('/api/admin/control?bot=1', headers=ADM).get_json()
check('Bot holati qaytadi', r['ok'] and 'bot' in r, r)

print('\n=== Audit va o\'chirish ===')
audit = [i['action'] for i in c.get('/api/admin/audit?limit=200', headers=ADM).get_json()['items']]
check('Audit jurnalida amallar', {'control_pause', 'control_resume', 'control_features', 'announcement_set', 'user_ban',
                                  'user_unban', 'user_bonus', 'user_rename', 'user_reset_chances', 'user_reset_cooldown',
                                  'user_logout', 'bot_webhook'} <= set(audit), set(audit))
c.delete(f'/api/admin/users/{ali}', headers=ADM)
check("O'quvchi o'chirilsa bonuslari ham o'chadi", not db('SELECT id FROM chaqmoq_bonus WHERE user_id = %s', (ali,), True))

html = open(os.path.join(BACKEND, 'admin.html'), encoding='utf-8').read()
check("admin.html: Boshqaruv bo'limi va o'quvchi amallari", 'id="bolim-boshqaruv"' in html and 'userBoshqaruvYukla(id)' in html
      and 'data-bolim="boshqaruv"' in html)
api_js = open(os.path.join(BACKEND, 'js', 'api.js'), encoding='utf-8').read()
i18n = open(os.path.join(BACKEND, 'js', 'i18n.js'), encoding='utf-8').read()
check("api.js: texnik ishlar / blok oynasi", 'holatOyna(data)' in api_js)
check("O'quvchiga ko'rinadigan xabarlarning ruschasi bor", all(m in i18n for m in (
    boshqaruv.MSG_MAINTENANCE, boshqaruv.MSG_BANNED, boshqaruv.MSG_FEATURE_OFF, boshqaruv.MSG_REGISTRATION)))

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
sys.exit(1 if fails else 0)
