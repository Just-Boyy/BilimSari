# -*- coding: utf-8 -*-
"""Admin paneli: brauzerga o'tish (bir martalik kod), qoidalar, matnlar, bot matnlari, dizayn, ma'lumotlar bazasi,
ommaviy xabar (guruh/vaqt), rejalashtirilgan ishlar, kun savoli rejasi va uy vazifasini tahrirlash."""
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
import admin_api  # noqa: E402
import admin_auth  # noqa: E402
import broadcast  # noqa: E402
import qoidalar  # noqa: E402
import sayt  # noqa: E402
import study  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402
from games import chances, clock  # noqa: E402

c = A.app.test_client()
fails = []
CALLS = []
MID = [20000]
OWNER = 5771496552
FAKE = '000000:SINOV-ADMIN-KUCH'


def fake_tg(method, payload):
    MID[0] += 1
    CALLS.append((method, payload))
    if method == 'getWebhookInfo':
        return {'ok': True, 'result': {'url': 'https://x/telegram/webhook', 'pending_update_count': 0}}
    return {'ok': True, 'result': {'message_id': MID[0]}}


tgbot.tg_api = fake_tg
A.tg_api = fake_tg
A.BOT_TOKEN = FAKE
admin_api.BOT_TOKEN = FAKE
tgbot.BOT_TOKEN = FAKE


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


def mk(name, tg=None, lang=None):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id) VALUES (%s, TRUE, 'math', %s) RETURNING id",
             (name, tg), True)[0]['id']
    if lang:
        db('UPDATE users SET lang = %s WHERE id = %s', (lang, uid))
    return uid, {'Authorization': 'Bearer ' + create_token(uid)}


def init_data(tg_id):
    fields = {'auth_date': str(int(time.time())), 'query_id': 'AAHtest',
              'user': json.dumps({'id': tg_id, 'first_name': 'Ega', 'username': f'u{tg_id}'}, separators=(',', ':'))}
    dcs = '\n'.join(f'{k}={v}' for k, v in sorted(fields.items()))
    secret = hmac.new(b'WebAppData', FAKE.encode(), hashlib.sha256).digest()
    fields['hash'] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}


def get(path):
    r = c.get(path, headers=ADM)
    return r.status_code, r.get_json(silent=True)


def post(path, body=None):
    r = c.post(path, headers=ADM, json=body or {})
    return r.status_code, r.get_json(silent=True)


ali, ali_h = mk('Ali Valiyev', 9400001)
vali, vali_h = mk('Вали', 9400002, 'ru')
olim, olim_h = mk('Olim', 9400003)

print("\n=== Admin panel brauzerda: bir martalik kod ===")
r = c.post('/api/admin/handoff', json={'initData': init_data(OWNER)})
code = (r.get_json() or {}).get('code')
check('Ilova ichida admin uchun kod beriladi', r.status_code == 200 and code, r.get_json())
r = c.post('/api/admin/handoff', json={'initData': init_data(9400001)})
check("Admin bo'lmaganga — 403", r.status_code == 403 and r.get_json()['code'] == 'not_admin')
r = c.post('/api/admin/handoff', json={'initData': 'buzilgan'})
check('Soxta initData — 403', r.status_code == 403)
r = c.post('/api/admin/handoff/redeem', json={'code': code})
tok = (r.get_json() or {}).get('token')
check('Brauzerda kod → admin token', r.status_code == 200 and tok
      and c.get('/api/admin/stats', headers={'Authorization': 'Bearer ' + tok}).status_code == 200, r.get_json())
r = c.post('/api/admin/handoff/redeem', json={'code': code})
check('Kod ikkinchi marta ishlamaydi', r.status_code == 403, r.get_json())
r = c.post('/api/admin/handoff/redeem', json={'code': code[:-3] + 'abc'})
check("Buzilgan kod — 403", r.status_code == 403)
r = c.post('/api/admin/handoff', json={'initData': init_data(OWNER)})
code2 = r.get_json()['code']
old_age = admin_auth.HANDOFF_MAX_AGE
admin_auth.HANDOFF_MAX_AGE = -1
check("Muddati o'tgan kod — 403", c.post('/api/admin/handoff/redeem', json={'code': code2}).status_code == 403)
admin_auth.HANDOFF_MAX_AGE = old_age
ui_js = open(os.path.join(BACKEND, 'js', 'ui.js'), encoding='utf-8').read()
check("ui.js: admin havolasi tashqi brauzerda (openLink)", "a[href^=\"admin.html\"]" in ui_js and 'tg.openLink(url' in ui_js)

print('\n=== Qoidalar ===')
s, r = get('/api/admin/rules')
check("Qoidalar ro'yxati", s == 200 and len(r['rules']) == len(qoidalar.RULES) and all(x['value'] == x['default'] for x in r['rules']), r)
s, r = post('/api/admin/rules', {'values': {'games.win': 40, 'games.max_chances': 5, 'games.reset_hours': 12,
                                            'lesson.quiz_per_correct': 10, 'lesson.quiz_max': 30, 'daily.reward': 7}})
check('Saqlandi', s == 200 and r['ok'], r)
check("O'yin qoidalari darhol ishlaydi", chances.WIN == 40 and chances.MAX == 5 and chances.RESET_MS == 12 * 3600 * 1000)
conn = get_connection(); cur = conn.cursor()
st = chances.status(cur, ali, clock.now_ms())
cur.close(); conn.close()
check("O'yin holatida yangi qiymatlar", st['max'] == 5 and st['win'] == 40 and st['left'] == 5, st)
check('Dars chaqmoqi formulasi qayta qurildi', '* 10 >= 30' in study.LESSON_CHAQMOQ_SQL, study.LESSON_CHAQMOQ_SQL)
import daily  # noqa: E402
check('Kun savoli mukofoti', daily.CHAQMOQ_CORRECT == 7)
cfg = c.get('/api/site/config').get_json()
k = "O'yinlarda 24 soatda 3 ta chaqmoqli o'yin: 1-o'rin +30, qolganlar +20. Kompyuter bilan o'yin chaqmoq bermaydi."
check("Tushuntirish matni avtomatik yangilandi (o'zbekcha)",
      cfg['texts']['uz'].get(k) == "O'yinlarda 12 soatda 5 ta chaqmoqli o'yin: 1-o'rin +40, qolganlar +20. "
                                    "Kompyuter bilan o'yin chaqmoq bermaydi.", cfg['texts']['uz'].get(k))
check('... va ruschasi (to\'g\'ri kelishik bilan)', cfg['texts']['ru'].get(k) ==
      'В играх за 12 часов 5 игр с молниями: 1-е место +40, остальные +20. Игра с компьютером молний не даёт.', cfg['texts']['ru'].get(k))
check("Dars matni ham", cfg['texts']['uz'].get("Testda har to'g'ri javob +5 (1-urinish), uy vazifasi +15") ==
      "Testda har to'g'ri javob +10 (1-urinish), uy vazifasi +15")
s, r = post('/api/admin/rules', {'values': {'games.win': 5000}})
check("Chegaradan tashqari — 400", s == 400, r)
s, r = post('/api/admin/rules', {'values': {'lesson.quiz_max': 5}})
check("Test maksimumi bitta javobdan kam — 400", s == 400, r)
s, r = post('/api/admin/rules', {'values': {'nomalum': 1}})
check("Noma'lum qoida — 400", s == 400)
# Boshqa worker: bazaga to'g'ridan-to'g'ri yozilgan qiymat refresh() bilan qo'llanadi
db("UPDATE pay_settings SET value = %s WHERE key = 'rules'", (json.dumps({'games.win': 55}),))
qoidalar.refresh(force=True)
check("Boshqa worker yozgan qiymat ham qo'llanadi", chances.WIN == 55 and chances.MAX == 3, (chances.WIN, chances.MAX))
s, r = post('/api/admin/rules', {'values': {'games.win': None}})
check('Standartga qaytarish', s == 200 and chances.WIN == 30 and study.LESSON_CHAQMOQ_SQL == study.build_lesson_chaqmoq_sql()
      and '* 5 >= 15' in study.LESSON_CHAQMOQ_SQL, (chances.WIN, study.LESSON_CHAQMOQ_SQL))
check("Qoidalar standart bo'lsa — avtomatik matn yo'q", not c.get('/api/site/config').get_json()['texts']['uz'])

print('\n=== Matnlar ===')
s, r = get('/api/admin/texts/search?q=kun savoli')
check('Katalogdan qidirish', s == 200 and any(x['uz'] == 'Kun savoli' and x['ru'] == 'Вопрос дня' for x in r['items']), r)
s, r = post('/api/admin/texts', {'orig': '  Kun  savoli ', 'uz': 'Bugungi savol', 'ru': 'Вопрос сегодня'})
check("Yozuv o'zgartirildi", s == 200 and any(x['orig'] == 'Kun savoli' for x in r['texts']), r)
cfg = c.get('/api/site/config').get_json()
check("Ochiq config'da (uz va ru)", cfg['texts']['uz'].get('Kun savoli') == 'Bugungi savol'
      and cfg['texts']['ru'].get('Kun savoli') == 'Вопрос сегодня', cfg['texts'])
s, r = post('/api/admin/texts', {'orig': 'Profil', 'ru': 'Мой профиль'})
cfg = c.get('/api/site/config').get_json()
check("Faqat ruscha o'zgartirish", 'Profil' not in cfg['texts']['uz'] and cfg['texts']['ru'].get('Profil') == 'Мой профиль')
s, r = post('/api/admin/texts', {'orig': 'Kun savoli', 'delete': True})
check('Asliga qaytarish', s == 200 and all(x['orig'] != 'Kun savoli' for x in r['texts']))
check("Bo'sh asl matn — 400", post('/api/admin/texts', {'orig': '', 'uz': 'x'})[0] == 400)
i18n = open(os.path.join(BACKEND, 'js', 'i18n.js'), encoding='utf-8').read()
check("i18n.js: almashtirishlar, ranglar, yashirish qo'llanadi", "fetch('/api/site/config'" in i18n and 'saytQoy' in i18n
      and "til === 'ru' && el.hasAttribute('data-ru')" in i18n)

print('\n=== Bot matnlari ===')
s, r = post('/api/admin/bot-texts', {'key': 'start', 'uz': 'Assalomu alaykum, <b>{ism}</b>! Xush kelibsiz & marhamat.',
                                     'ru': 'Здравствуйте, {ism}!'})
check('/start matni saqlandi', s == 200 and any(b['key'] == 'start' and b['custom'] for b in r['bot']), r)
CALLS.clear()
c.post('/telegram/webhook', headers={'X-Telegram-Bot-Api-Secret-Token': A.WEBHOOK_SECRET}, json={
    'update_id': 70001, 'message': {'message_id': 1, 'chat': {'id': 9400001, 'type': 'private'},
                                    'from': {'id': 9400001, 'first_name': 'Ali<x>'}, 'text': '/start'}})
t = [p['text'] for m, p in CALLS if m == 'sendMessage']
check("Bot yangi matn bilan javob beradi (ism xavfsiz, & to'g'ri)",
      t and t[0] == 'Assalomu alaykum, <b>Ali&lt;x&gt;</b>! Xush kelibsiz &amp; marhamat.', t)
CALLS.clear()
c.post('/telegram/webhook', headers={'X-Telegram-Bot-Api-Secret-Token': A.WEBHOOK_SECRET}, json={
    'update_id': 70002, 'message': {'message_id': 2, 'chat': {'id': 9400002, 'type': 'private'},
                                    'from': {'id': 9400002, 'first_name': 'Вали'}, 'text': '/start'}})
t = [p['text'] for m, p in CALLS if m == 'sendMessage']
check('Ruscha o\'quvchiga ruscha matn', t and t[0] == 'Здравствуйте, Вали!', t)
check("Teg juftligi buzilsa — 400", post('/api/admin/bot-texts', {'key': 'help', 'uz': '<b>Yordam'})[0] == 400)
CALLS.clear()
s, r = post('/api/admin/bot-texts', {'key': 'description', 'uz': 'Yangi tavsif', 'ru': 'Новое описание'})
check("Tavsif o'zgarsa Telegram'ga darhol yuboriladi", s == 200 and any(
    m == 'setMyDescription' and p.get('description') == 'Yangi tavsif' for m, p in CALLS)
      and any(m == 'setMyDescription' and p.get('description') == 'Новое описание' for m, p in CALLS), CALLS)
s, r = post('/api/admin/bot-texts', {'key': 'start', 'uz': '', 'ru': ''})
check('Standartga qaytarish', s == 200 and not any(b['key'] == 'start' and b['custom'] for b in r['bot']))

print('\n=== Dizayn ===')
s, r = post('/api/admin/design', {'colors': {'primary': '#123456', 'bg': '#f3f4f6'}, 'hide': ['nav.games', 'dash.reja', 'xyz']})
cfg = c.get('/api/site/config').get_json()
check("Rang va yashirilgan bloklar config'da", s == 200 and cfg['theme'] == {'--yashil': '#123456'}
      and '.pastki-nav > a[href="games.html"]' in cfg['hide'] and '#rejaBo-lim' in cfg['hide'] and len(cfg['hide']) == 2, cfg)
check("Noto'g'ri rang — 400", post('/api/admin/design', {'colors': {'primary': 'red;}body{'}})[0] == 400)
s, r = post('/api/admin/design', {'colors': {}, 'hide': []})
check('Standartga qaytdi', c.get('/api/site/config').get_json()['theme'] == {} and not c.get('/api/site/config').get_json()['hide'])

print("\n=== Ma'lumotlar bazasi ===")
s, r = get('/api/admin/db/tables')
names = [t['name'] for t in r['tables']]
check("Jadvallar ro'yxati (maxfiylarsiz)", s == 200 and 'users' in names and 'tokens' not in names and 'admin_settings' not in names, names)
s, r = get('/api/admin/db/rows?table=users&q=Ali&col=name')
check('Qidirish', s == 200 and r['total'] >= 1 and all('Ali' in x['name'] for x in r['rows']), r)
check('Parol xeshi ko\'rinmaydi', all(c2['name'] != 'password_hash' for c2 in r['columns']))
s, r = get('/api/admin/db/rows?table=tokens')
check("Maxfiy jadval — 404", s == 404)
s, r = get('/api/admin/db/rows?table=' + 'users%22%3B%20DROP%20TABLE%20users%3B--')
check("SQL injection urinish — 404", s == 404 and db('SELECT COUNT(*) AS n FROM users', fetch=True)[0]['n'] >= 3)
s, r = get('/api/admin/db/row?table=users&key=' + json.dumps({'id': ali}))
check("Bitta qator", s == 200 and r['row']['name'] == 'Ali Valiyev', r)
s, r = post('/api/admin/db/update', {'table': 'users', 'key': {'id': ali}, 'changes': {'name': 'Ali Bazadan', 'notify': '0'}})
row = db('SELECT name, notify FROM users WHERE id = %s', (ali,), True)[0]
check('Tahrirlash (tur bo\'yicha aylantirish)', s == 200 and row['name'] == 'Ali Bazadan' and int(row['notify']) == 0, (s, r, row))
check("Birlamchi kalitni o'zgartirib bo'lmaydi", post('/api/admin/db/update', {'table': 'users', 'key': {'id': ali},
                                                                                  'changes': {'id': 999}})[0] == 400)
check("Son ustuniga matn — 400", post('/api/admin/db/update', {'table': 'users', 'key': {'id': ali},
                                                                'changes': {'notify': 'abc'}})[0] == 400)
db("INSERT INTO promo_codes (code, percent, active, created_ms) VALUES ('BAZATEST', 10, 1, 1)")
pk = db("SELECT * FROM promo_codes WHERE code = 'BAZATEST'", fetch=True)[0]
key = {k: pk[k] for k in ('id',) if k in pk} or {'code': 'BAZATEST'}
s, r = post('/api/admin/db/delete', {'table': 'promo_codes', 'key': key})
check("Qatorni o'chirish", s == 200 and not db("SELECT 1 FROM promo_codes WHERE code = 'BAZATEST'", fetch=True), (s, r, key))
rr = c.get('/api/admin/db/export?table=users', headers=ADM)
check('CSV yuklab olish', rr.status_code == 200 and 'name' in rr.get_data(as_text=True).splitlines()[0], rr.status_code)
audit = [i for i in c.get('/api/admin/audit?limit=100', headers=ADM).get_json()['items'] if i['action'] == 'db_update']
check('Audit: eski → yangi qiymat', audit and 'Ali Valiyev' in audit[0]['detail'] and 'Ali Bazadan' in audit[0]['detail'], audit[:1])

print('\n=== Ommaviy xabar: guruh va vaqt ===')
db('UPDATE users SET notify = 1')
s, r = get('/api/admin/broadcasts')
seg = {x['key']: x['count'] for x in r['segments']}
check('Guruhlar va soni', s == 200 and seg['all'] >= 3 and seg['ru'] == 1 and seg['uz'] >= 2, seg)
future = (clock.tashkent_date(clock.now_ms()) + timedelta(days=2)).isoformat() + 'T10:00'
s, r = post('/api/admin/broadcasts', {'text': 'Ertaga yangilik', 'segment': 'all', 'start_at': future})
sched = r['items'][0]
check('Rejalashtirildi', s == 200 and sched['state'] == 'scheduled' and sched['start_ms'] > clock.now_ms(), r['items'][:1])
s, r = post(f"/api/admin/broadcasts/{sched['id']}/cancel")
check('Bekor qilindi', s == 200 and r['items'][0]['state'] == 'cancelled', r['items'][:1])
CALLS.clear()
s, r = post('/api/admin/broadcasts', {'text': 'Привет русским', 'segment': 'ru', 'button_text': 'Открыть', 'button_path': 'daily.html'})
bid = r['items'][0]['id']
for _ in range(60):
    if broadcast.get(get_connection().cursor(), bid)['state'] == 'done':
        break
    time.sleep(0.1)
to = [p['chat_id'] for m, p in CALLS if m == 'sendMessage' and p.get('text') == 'Привет русским']
check('Faqat ruscha guruhga yuborildi (tugma bilan)', to == [9400002] and any(
    p.get('reply_markup') for m, p in CALLS if m == 'sendMessage' and p.get('text') == 'Привет русским'), CALLS)
check("Tugma uchun sahifa noto'g'ri — 400", post('/api/admin/broadcasts', {'text': 'x', 'button_text': 'a',
                                                                             'button_path': 'https://evil'})[0] == 400)
conn = get_connection(); cur = conn.cursor()
info = broadcast.start(cur, conn, 'Kechikkan', segment='uz', start_ms=clock.now_ms() + 5 * 60000)
cur.execute('UPDATE broadcasts SET start_ms = %s WHERE id = %s', (clock.now_ms() - 1000, info['id']))
conn.commit()
CALLS.clear()
broadcast.start_due(cur, conn)
cur.close(); conn.close()
for _ in range(60):
    if broadcast.get(get_connection().cursor(), info['id'])['state'] == 'done':
        break
    time.sleep(0.1)
check('Vaqti kelgan xabar o\'zi boshlanadi', broadcast.get(get_connection().cursor(), info['id'])['state'] == 'done'
      and 9400002 not in [p['chat_id'] for m, p in CALLS if m == 'sendMessage'], CALLS)

print('\n=== Rejalashtirilgan ishlar ===')
s, r = get('/api/admin/jobs')
check("Ishlar ro'yxati", s == 200 and any(j['key'] == 'cleanup' and j['runnable'] for j in r['jobs']), r)
s, r = post('/api/admin/jobs/cleanup/run')
check('Tozalash hozir bajarildi', s == 200 and r['ok'], r)
check("Noma'lum ish — 404", post('/api/admin/jobs/yoq/run')[0] == 404)

print('\n=== Kun savoli rejasi ===')
s, r = get('/api/admin/daily-plan')
check('7 kunlik reja', s == 200 and len(r['days']) == 7 and all(d.get('question') for d in r['days']), r)
tomorrow = r['days'][1]['day']
topic = db("SELECT id FROM topics WHERE subject_key = 'history' ORDER BY seq LIMIT 1", fetch=True)[0]['id']
s, q = get('/api/admin/daily-plan/questions?topic_id=' + topic)
check("Mavzu savollari (variantli)", s == 200 and q['items'], q)
s, r = post('/api/admin/daily-plan', {'day': tomorrow, 'topic_id': topic, 'q_index': q['items'][0]['q_index']})
check('Ertangi savol tanlandi', s == 200 and r['days'][1]['admin'] and r['days'][1]['topic_id'] == topic, r['days'][1])
today = r['days'][0]['day']
s, r = post('/api/admin/daily-plan', {'day': today, 'topic_id': topic, 'q_index': q['items'][0]['q_index']})
d = c.get('/api/study/daily', headers=olim_h).get_json()
check("Bugungi savol o'quvchiga shu savol bo'lib chiqadi", s == 200 and d.get('ok') and topic, (s, d.get('question', d)))
c.post('/api/study/daily/answer', headers=olim_h, json={'answer': 0})
s, r = post('/api/admin/daily-plan', {'day': today, 'reset': True})
check("Javob berilgan kunni almashtirib bo'lmaydi", s == 400, r)
s, r = post('/api/admin/daily-plan', {'day': tomorrow, 'reset': True})
check('Avtomatikka qaytarish', s == 200 and not r['days'][1]['admin'], r['days'][1])
check("O'tgan kun — 400", post('/api/admin/daily-plan', {'day': '2020-01-01', 'reset': True})[0] == 400)

print('\n=== Uy vazifasini tahrirlash ===')
tid = db("SELECT id FROM topics WHERE subject_key = 'math' ORDER BY seq LIMIT 1", fetch=True)[0]['id']
t = c.get(f'/api/admin/topics/{tid}', headers=ADM).get_json()['topic']
check('Muharrirda uy vazifasi bor', t['homework']['tasks'] and t['homework']['tasks'][0]['type'] == 'text', t.get('homework'))
body = {k: t[k] for k in ('title', 'summary', 'duration', 'lesson', 'quiz')}
body['homework'] = {'intro': 'Yangi kirish', 'tasks': [
    {'type': 'text', 'prompt': '2+2 nechchi?', 'answer': '4', 'hint': 'Qo\'shing'},
    {'type': 'open', 'prompt': 'Qo\'shishni tushuntiring', 'answer': 'keraksiz'}]}
r = c.put(f'/api/admin/topics/{tid}', headers=ADM, json=body)
hw = json.loads(db('SELECT homework, ru FROM topics WHERE id = %s', (tid,), True)[0]['homework'])
ru = json.loads(db('SELECT ru FROM topics WHERE id = %s', (tid,), True)[0]['ru'] or '{}')
check("Uy vazifasi saqlandi", r.status_code == 200 and hw['intro'] == 'Yangi kirish' and hw['tasks'][0]['answer'] == '4'
      and hw['tasks'][1] == {'id': 't2', 'type': 'open', 'prompt': "Qo'shishni tushuntiring"}, (r.get_json(), hw))
check("Eskirgan ruscha uy vazifasi olib tashlandi", 'homework' not in ru, list(ru))
tr = db('SELECT slug, grade FROM topics WHERE id = %s', (tid,), True)[0]
lesson = c.get(f"/api/study/topic/math/{tr['slug']}?grade={tr['grade']}", headers=ali_h).get_json()
check("O'quvchi yangi uy vazifasini ko'radi", 'Yangi kirish' in json.dumps(lesson, ensure_ascii=False), str(lesson)[:300])
body['homework'] = {'intro': '', 'tasks': [{'type': 'text', 'prompt': 'x'}]}
check("Javobsiz topshiriq — 400", c.put(f'/api/admin/topics/{tid}', headers=ADM, json=body).status_code == 400)
r = c.post(f'/api/admin/topics/{tid}/reset', headers=ADM)
hw = json.loads(db('SELECT homework FROM topics WHERE id = %s', (tid,), True)[0]['homework'])
check('Asl holiga qaytarilganda uy vazifasi ham tiklanadi', r.status_code == 200 and hw['intro'] != 'Yangi kirish', hw)

print('\n=== Admin panel sahifasi ===')
html = open(os.path.join(BACKEND, 'admin.html'), encoding='utf-8').read()
check("Yangi bo'limlar", all(f'id="bolim-{b}"' in html for b in ('qoidalar', 'matnlar', 'dizayn', 'baza', 'xabar'))
      and 'id="ishlarQuti"' in html and 'id="kunRejaQuti"' in html and 'data-hwturi' in html)
check("Brauzerda kod bilan kirish", 'AdminAPI.kodBilanKirish(kod)' in html)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
sys.exit(1 if fails else 0)
