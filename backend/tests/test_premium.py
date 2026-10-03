# -*- coding: utf-8 -*-
"""Bilim Premium: to'lov, AI qulfi, shaxsiy darslar, yangi chaqmoq qoidasi, eslatmalar, admin."""
import json
import os
import sys
import time

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402
import admin_auth  # noqa: E402
import ai_tutor  # noqa: E402
import notify  # noqa: E402
import payments  # noqa: E402
import personal  # noqa: E402
import premium  # noqa: E402
import study  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402
from games import clock  # noqa: E402

c = A.app.test_client()
fails = []
CALLS = []
DAY = 24 * 3600 * 1000


def fake_tg(method, payload):
    CALLS.append((method, payload))
    if method == 'createInvoiceLink':
        return {'ok': True, 'result': 'https://t.me/$inv'}
    return {'ok': True, 'result': {'message_id': 1}}


tgbot.tg_api = fake_tg


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


def withcur(fn):
    conn = get_connection(); cur = conn.cursor()
    try:
        return fn(cur, conn)
    finally:
        cur.close(); conn.close()


def mk(name, tg, username=None, chosen='math'):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id, username, grade) "
             "VALUES (%s, TRUE, %s, %s, %s, 7) RETURNING id", (name, chosen, tg, username), True)[0]['id']
    return {'id': uid, 'tg': tg, 'h': {'Authorization': 'Bearer ' + create_token(uid)}}


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
withcur(lambda cur, conn: payments.save_settings(cur, conn, {'card_number': '8600123412341234', 'card_holder': 'Test'}))
u = mk('Premium Test', 70001, 'premtest')
v = mk('Oddiy Test', 70002)

print('=== 1) Premium sotib olish (karta) ===')
r = c.get('/api/premium', headers=u['h']).get_json()
check('Holat: faol emas, narx 34 900, Stars yo\'q, 23 emoji', r['ok'] and not r['premium']['active'] and r['price'] == 34900
      and 'stars' not in r and len(r['emoji']) == 23, r)
CALLS.clear()
r = c.post('/api/premium/order', headers=u['h'], json={}).get_json()
check("Buyurtma: Bilim Premium (1 oy), 34 900 so'm", r['ok'] and r['order']['amount'] == 34900
      and r['order']['items'][0]['name'] == 'Bilim Premium (1 oy)', r)
msg = [p['text'] for m, p in CALLS if m == 'sendMessage']
check("Botga yo'riqnoma: Premium faollashtiriladi", msg and 'Bilim Premium' in msg[0] and "Premium'ni faollashtiradi" in msg[0], msg)
oid = r['order']['id']
withcur(lambda cur, conn: payments.attach_receipt(cur, conn, 70001, 'file1', 'uniq1', 'photo'))
CALLS.clear()
ok, _ = withcur(lambda cur, conn: payments.decide(cur, conn, oid, True, 'Admin'))
st = c.get('/api/premium', headers=u['h']).get_json()['premium']
check('Admin tasdiqladi → Premium 30 kun', ok and st['active'] and st['days_left'] == 30, st)
check("Fan ochilmadi (premium fan emas)", not db('SELECT 1 FROM subject_purchases WHERE user_id = %s', (u['id'],), True))
msg = [p['text'] for m, p in CALLS if m == 'sendMessage']
check("O'quvchiga: Premium faollashdi", any('Bilim Premium</b> faollashdi' in t for t in msg), msg)
r = c.post('/api/premium/order', headers=u['h'], json={})
check('Faol premium — qayta sotib olinmaydi (409)', r.status_code == 409 and r.get_json()['code'] == 'premium_active')
check('/api/premium/stars endi yo\'q', c.post('/api/premium/stars', headers=u['h'], json={}).status_code in (404, 405))

print('\n=== 2) Ikkinchi o\'quvchi karta bilan ===')
r = c.post('/api/premium/order', headers=v['h'], json={}).get_json()
oid2 = r['order']['id']
withcur(lambda cur, conn: payments.attach_receipt(cur, conn, 70002, 'file2', 'uniq2', 'photo'))
withcur(lambda cur, conn: payments.decide(cur, conn, oid2, True, 'Admin'))
st = c.get('/api/premium', headers=v['h']).get_json()['premium']
check('Karta → Premium faol', st['active'], st)

print('\n=== 3) Sozlamalar ===')
r = c.post('/api/admin/pay/settings', headers=ADM, json={'premium_price': 39900}).get_json()
check('Admin narxni o\'zgartira oladi', r['ok'] and r['settings']['premium_price'] == 39900 and 'premium_stars' not in r['settings'], r)
r = c.post('/api/admin/pay/settings', headers=ADM, json={'premium_price': 500})
check('Premium narxi < 1000 — rad', r.status_code == 400)
c.post('/api/admin/pay/settings', headers=ADM, json={'premium_price': 34900})

print('\n=== 4) AI faqat Premium ===')
w = mk('Premiumsiz', 70003)
T = db("SELECT id, slug, grade FROM topics WHERE subject_key = 'math' ORDER BY grade, seq LIMIT 1", fetch=True)[0]
r = c.post('/api/ai/explain', headers=w['h'], json={'subject_key': 'math', 'slug': T['slug'], 'grade': T['grade'], 'mode': 'full'})
check('Premiumsiz — 403 premium_required', r.status_code == 403 and r.get_json()['code'] == 'premium_required')
r = c.post('/api/ai/tutor', headers=w['h'], json={'message': 'salom'})
check('AI savol ham yopiq', r.status_code == 403)
db('DELETE FROM ai_explanations')
db("INSERT INTO ai_explanations (topic_id, mode, lang, reply) VALUES (%s, 'full', 'uz', 'KESH')", (T['id'],))
r = c.post('/api/ai/explain', headers=u['h'], json={'subject_key': 'math', 'slug': T['slug'], 'grade': T['grade'], 'mode': 'full'}).get_json()
check('Premium — AI ishlaydi', r['ok'] and r['reply'] == 'KESH', r)
tp = c.get(f"/api/study/topic/math/{T['slug']}?grade={T['grade']}", headers=u['h']).get_json()
tw = c.get(f"/api/study/topic/math/{T['slug']}?grade={T['grade']}", headers=w['h']).get_json()
check('Mavzu sahifasida premium belgisi', tp['premium'] is True and tw['premium'] is False)

print('\n=== 5) Yangi chaqmoq qoidasi (oddiy darslar) ===')
quiz = json.loads(db('SELECT quiz FROM topics WHERE id = %s', (T['id'],), True)[0]['quiz']) \
    if isinstance(db('SELECT quiz FROM topics WHERE id = %s', (T['id'],), True)[0]['quiz'], str) \
    else db('SELECT quiz FROM topics WHERE id = %s', (T['id'],), True)[0]['quiz']
right = [q['answer'] for q in quiz]
wrong = [((a + 1) % 4) if isinstance(a, int) and not isinstance(a, bool) else (not a) for a in right]
answers = [right[0], wrong[1], right[2]]
c.post('/api/study/lesson-read', headers=w['h'], json={'grade': T['grade'], 'subject_key': 'math', 'slug': T['slug']})
r = c.post('/api/study/quiz', headers=w['h'], json={'grade': T['grade'], 'subject_key': 'math', 'slug': T['slug'], 'answers': answers}).get_json()
check('1-urinish: 2 to\'g\'ri → +10 chaqmoq', r['ok'] and r['correct'] == 2 and r['chaqmoq'] == 10, r)
r = c.post('/api/study/quiz', headers=w['h'], json={'grade': T['grade'], 'subject_key': 'math', 'slug': T['slug'], 'answers': right}).get_json()
check('2-urinish: hammasi to\'g\'ri, lekin chaqmoq yo\'q', r['ok'] and r['correct'] == 3 and r['chaqmoq'] == 0, r)
hw = json.loads(db('SELECT homework FROM topics WHERE id = %s', (T['id'],), True)[0]['homework']) \
    if isinstance(db('SELECT homework FROM topics WHERE id = %s', (T['id'],), True)[0]['homework'], str) \
    else db('SELECT homework FROM topics WHERE id = %s', (T['id'],), True)[0]['homework']
bad = {t['id']: 'xxxxx' for t in hw['tasks']}
r = c.post('/api/study/homework', headers=w['h'], json={'grade': T['grade'], 'subject_key': 'math', 'slug': T['slug'], 'answers': bad}).get_json()
check('Uy vazifasi: xato javobda to\'g\'ri javob ko\'rsatiladi', r['ok'] and not r['passed']
      and all(x['correct_answer'] for x in r['results'] if x['checked']) and r['chaqmoq'] == 0, r)
good = {t['id']: (t.get('answer') or 'mening javobim uzun') for t in hw['tasks']}
r = c.post('/api/study/homework', headers=w['h'], json={'grade': T['grade'], 'subject_key': 'math', 'slug': T['slug'], 'answers': good}).get_json()
check('Uy vazifasi bajarildi → +15', r['ok'] and r['passed'] and r['chaqmoq'] == 15, r)
parts = withcur(lambda cur, conn: study.chaqmoq_parts(cur, w['id']))
check('Darslardan jami 25 (10 + 15)', parts['topics'] == 25, parts)
# Eski yozuvlar (yangi qoidadan oldin)
T2 = db("SELECT id FROM topics WHERE subject_key = 'math' ORDER BY grade, seq LIMIT 1 OFFSET 1", fetch=True)[0]['id']
T3 = db("SELECT id FROM topics WHERE subject_key = 'math' ORDER BY grade, seq LIMIT 1 OFFSET 2", fetch=True)[0]['id']
z = mk('Eski', 70004)
db("INSERT INTO user_progress (user_id, topic_id, status, quiz_attempts, quiz_score, quiz_passed, homework_status) "
   "VALUES (%s, %s, 'completed', 1, 67, 1, 'passed')", (z['id'], T2))
db("INSERT INTO user_progress (user_id, topic_id, status, quiz_attempts, quiz_score, quiz_passed, homework_status) "
   "VALUES (%s, %s, 'completed', 3, 100, 1, 'passed')", (z['id'], T3))
withcur(lambda cur, conn: study.backfill_first_quiz(cur, conn))
rows = {r['topic_id']: r['quiz_first_correct'] for r in db('SELECT topic_id, quiz_first_correct FROM user_progress WHERE user_id = %s', (z['id'],), True)}
check('Eski: 1 urinish 67% → 2 to\'g\'ri; 3 urinish → 1', rows[T2] == 2 and rows[T3] == 1, rows)
check('Eski tugallangan mavzular: 25 + 20 = 45', withcur(lambda cur, conn: study.chaqmoq_parts(cur, z['id']))['topics'] == 45)

print('\n=== 6) Shaxsiy darslar ===')
GOOD = {
    'title': 'x', 'summary': 'Kasrlarni qo\'shish haqida', 'duration': 15,
    'lesson': [{'type': 'text', 'title': 'Kirish', 'body': 'Kasr — butunning bo\'lagi.'},
               {'type': 'example', 'title': 'Misol', 'body': '1/4 + 2/4 = 3/4'},
               {'type': 'steps', 'title': 'Qadamlar', 'items': ['Maxrajni tekshiring', 'Suratlarni qo\'shing']},
               {'type': 'note', 'body': 'Esda tuting: maxrajlar bir xil bo\'lishi kerak.'}],
    'quiz': [{'type': 'mc', 'q': '1/4+1/4=?', 'options': ['1/2', '2/8', '1/8', '1'], 'answer': 0, 'explain': 'Qisqaradi'},
             {'type': 'tf', 'q': '1/2 = 2/4', 'answer': True, 'explain': 'Teng'},
             {'type': 'mc', 'q': '2/5+1/5=?', 'options': ['3/10', '3/5', '1/5', '2/5'], 'answer': 1, 'explain': 'Surat qo\'shiladi'},
             {'type': 'mc', 'q': 'ortiqcha', 'options': ['a', 'b'], 'answer': 0}],
    'homework': {'intro': 'Hisoblang', 'tasks': [
        {'id': 'a', 'type': 'text', 'prompt': '1/3 + 1/3 = ?', 'answer': '2/3', 'hint': 'Suratlar'},
        {'id': 'b', 'type': 'number', 'prompt': '2 + 3 = ?', 'answer': '5'},
        {'id': 'c', 'type': 'text', 'prompt': 'Kasrning pastki qismi?', 'answer': 'maxraj'}]},
}
AI = {'mode': 'ok'}


def fake_ai(prompt, system=None, max_tokens=0, timeout=0, **kw):
    if 'relevant' in prompt:
        if 'futbol' in prompt:
            return {'relevant': False, 'options': []}, None
        return {'relevant': True, 'options': ['Kasrlarni qo\'shish', 'Oddiy kasrlarni qo\'shish va ayirish',
                                             'Maxrajlari bir xil kasrlar']}, None
    if AI['mode'] == 'bad':
        return {'lesson': []}, None
    time.sleep(0.2)
    return dict(GOOD), None


ai_tutor.call_gemini_json = fake_ai
r = c.get('/api/personal', headers=w['h']).get_json()
check('Premiumsiz: ro\'yxat ochiladi, premium faol emas', r['ok'] and not r['premium']['active'])
r = c.post('/api/personal/suggest', headers=w['h'], json={'subject_key': 'math', 'text': 'kasrlar'})
check('Premiumsiz — yaratib bo\'lmaydi (403)', r.status_code == 403 and r.get_json()['code'] == 'premium_required')
r = c.post('/api/personal/suggest', headers=u['h'], json={'subject_key': 'history', 'text': 'Temuriylar'})
check("O'zida yo'q fan — 403", r.status_code == 403 and r.get_json()['code'] == 'not_owned')
r = c.post('/api/personal/suggest', headers=u['h'], json={'subject_key': 'math', 'text': 'futbol'})
check('Fanga aloqasiz — "Iltimos, Matematika fanidan..."', r.status_code == 400
      and r.get_json()['error'] == 'Iltimos, Matematika fanidan mavzu nomini kiriting.', r.get_json())
r = c.post('/api/personal/suggest', headers=u['h'], json={'subject_key': 'math', 'text': 'kasrlrni qushish'}).get_json()
check('3 ta variant', r['ok'] and len(r['options']) == 3 and r['subject'] == 'Matematika', r)
CALLS.clear()
r = c.post('/api/personal/generate', headers=u['h'], json={'subject_key': 'math', 'title': r['options'][0]}).get_json()
check('Yaratish boshlandi', r['ok'] and r['topic']['status'] == 'generating', r)
pid = r['topic']['id']
g = c.get('/api/personal', headers=u['h']).get_json()
check('Tayyorlanmoqda ro\'yxatda', g['generating'] and g['generating'][0]['id'] == pid, g['generating'])
for _ in range(50):
    if db('SELECT status FROM personal_topics WHERE id = %s', (pid,), True)[0]['status'] != 'generating':
        break
    time.sleep(0.1)
row = db('SELECT * FROM personal_topics WHERE id = %s', (pid,), True)[0]
check('Dars tayyor: 3 savol, 3 topshiriq', row['status'] == 'ready' and len(json.loads(row['quiz'])) == 3
      and len(json.loads(row['homework'])['tasks']) == 3, (row['status'], row['error']))
for _ in range(50):          # xabar holat "ready" bo'lgandan keyin (o'quvchi tili aniqlangach) yuboriladi
    bot = [p for m, p in CALLS if m == 'sendMessage' and p['chat_id'] == 70001]
    if bot:
        break
    time.sleep(0.1)
check('Botga "Shaxsiy darsingiz tayyor" + tugma', bot and 'Shaxsiy darsingiz tayyor' in bot[-1]['text']
      and 'topic.html?shaxsiy=' in json.dumps(bot[-1]['reply_markup']), bot)
d = c.get('/api/study/dashboard', headers=u['h']).get_json()
check('Bosh sahifada ilova xabari (personal_news)', any(x['id'] == pid and x['status'] == 'ready' for x in d['personal_news']), d.get('personal_news'))
g = c.get('/api/personal', headers=u['h']).get_json()
check('Fan bo\'yicha guruh, limit: 24 soat', g['groups'][0]['key'] == 'math' and g['groups'][0]['topics'][0]['id'] == pid
      and not g['limit']['can'] and g['limit']['seconds_left'] > 23 * 3600, g['limit'])
r = c.post('/api/personal/generate', headers=u['h'], json={'subject_key': 'math', 'title': 'Boshqa mavzu'})
check('24 soatda bitta — ikkinchisi 429', r.status_code == 429 and r.get_json()['code'] == 'limit', r.get_json())
r = c.post('/api/personal/suggest', headers=u['h'], json={'subject_key': 'math', 'text': 'x'})
check('Limit tugaguncha variant ham so\'ralmaydi', r.status_code == 429)
p = c.get(f'/api/personal/{pid}', headers=u['h']).get_json()
check("Dars ochiladi, javoblarsiz", p['ok'] and p['personal'] and len(p['quiz']) == 3 and 'answer' not in json.dumps(p['quiz'])
      and 'answer' not in json.dumps(p['homework']) and p['premium'], p)
check("Boshqa o'quvchi ko'rmaydi", c.get(f'/api/personal/{pid}', headers=v['h']).status_code == 404)
d = c.get('/api/study/dashboard', headers=u['h']).get_json()
check('Ochilgach xabar qaytmaydi', not d['personal_news'])
c.post(f'/api/personal/{pid}/read', headers=u['h'])
r = c.post(f'/api/personal/{pid}/quiz', headers=u['h'], json={'answers': [0, False, 1]}).get_json()
check('Shaxsiy test 1-urinish: 2 to\'g\'ri → +10', r['ok'] and r['correct'] == 2 and r['chaqmoq'] == 10 and not r['passed'], r)
r = c.post(f'/api/personal/{pid}/quiz', headers=u['h'], json={'answers': [0, True, 1]}).get_json()
check('2-urinish: o\'tdi, chaqmoq 0', r['passed'] and r['chaqmoq'] == 0, r)
r = c.post(f'/api/personal/{pid}/homework', headers=u['h'], json={'answers': {'t1': '2/3', 't2': '6', 't3': 'maxraj'}}).get_json()
res = {x['id']: x for x in r['results']}
check('Shaxsiy uy vazifasi: faqat xato javobda to\'g\'ri javob ko\'rsatiladi', not r['passed']
      and res['t2']['correct_answer'] == '5' and res['t1']['correct_answer'] is None and r['chaqmoq'] == 0, r)
r = c.post(f'/api/personal/{pid}/homework', headers=u['h'], json={'answers': {'t1': '2/3', 't2': '5', 't3': 'Maxraj'}}).get_json()
check('Uy vazifasi bajarildi → +15, dars yakunlandi', r['passed'] and r['chaqmoq'] == 15 and r['completion']['completed'], r)
r = c.post(f'/api/personal/{pid}/homework', headers=u['h'], json={'answers': {'t1': '2/3', 't2': '5', 't3': 'Maxraj'}}).get_json()
check('Qayta topshirish chaqmoq bermaydi', r['chaqmoq'] == 0)
check('Chaqmoq: shaxsiy dars 25', withcur(lambda cur, conn: study.chaqmoq_parts(cur, u['id']))['topics'] == 25)
r = c.post('/api/ai/explain', headers=u['h'], json={'personal_id': pid, 'mode': 'full'})
check('Shaxsiy dars uchun AI (kalit yo\'q — 502, lekin 403 emas)', r.status_code == 502, r.status_code)
r = c.post('/api/ai/explain', headers=v['h'], json={'personal_id': pid, 'mode': 'full'})
check('Begona shaxsiy darsga AI yo\'q (404)', r.status_code == 404)
# Yaratilmay qolgan urinish limitga hisoblanmaydi
AI['mode'] = 'bad'
db('UPDATE personal_topics SET created_ms = created_ms - %s WHERE id = %s', (DAY + 1000, pid))
CALLS.clear()
r = c.post('/api/personal/generate', headers=u['h'], json={'subject_key': 'math', 'title': 'Buzuq'}).get_json()
pid2 = r['topic']['id']
for _ in range(50):
    if db('SELECT status FROM personal_topics WHERE id = %s', (pid2,), True)[0]['status'] != 'generating':
        break
    time.sleep(0.1)
check('AI yomon javob — failed', db('SELECT status FROM personal_topics WHERE id = %s', (pid2,), True)[0]['status'] == 'failed')
for _ in range(50):          # bot xabari holat yozilgandan keyin (o'quvchi tili aniqlangach) yuboriladi
    if any("tayyorlab bo'lmadi" in p.get('text', '') for m, p in CALLS if m == 'sendMessage'):
        break
    time.sleep(0.1)
check('Botga "tayyorlab bo\'lmadi"', any("tayyorlab bo'lmadi" in p.get('text', '') for m, p in CALLS if m == 'sendMessage'))
check('Xato urinish limitga hisoblanmaydi', c.get('/api/personal', headers=u['h']).get_json()['limit']['can'])
AI['mode'] = 'ok'
# Server qayta ishga tushib, yarim qolgan yaratish
db("INSERT INTO personal_topics (user_id, subject_key, title, status, created_ms) VALUES (%s, 'math', 'Osilgan', 'generating', %s)",
   (u['id'], clock.now_ms() - 20 * 60 * 1000))
withcur(lambda cur, conn: personal.housekeeping(cur, conn))
check('Osilib qolgan yaratish → failed', db("SELECT status FROM personal_topics WHERE title = 'Osilgan'", fetch=True)[0]['status'] == 'failed')

print('\n=== 7) Emoji va belgi ===')
emo = premium.emoji_catalog()
r = c.post('/api/premium/emoji', headers=w['h'], json={'emoji': emo[0]})
check('Premiumsiz emoji tanlab bo\'lmaydi', r.status_code == 403)
r = c.post('/api/premium/emoji', headers=u['h'], json={'emoji': 'yoq-emoji'})
check('Noto\'g\'ri emoji rad', r.status_code == 403)
r = c.post('/api/premium/emoji', headers=u['h'], json={'emoji': emo[2]}).get_json()
check('Emoji saqlandi', r['ok'] and r['emoji'] == emo[2])
me = c.get('/api/me', headers=u['h']).get_json()['user']['premium']
check('/api/me: premium va emoji', me['active'] and me['emoji'] == emo[2], me)
lb = c.get('/api/study/leaderboard', headers=u['h']).get_json()
mine = lb.get('me') or {}
check('Reytingda premium belgisi va emoji', mine.get('premium') and mine.get('emoji') == emo[2], mine)

print('\n=== 8) Muddat tugashi va eslatmalar ===')
now = clock.now_ms()
db('UPDATE users SET premium_until = %s WHERE id = %s', (now + 2 * DAY, u['id']))
CALLS.clear()
withcur(lambda cur, conn: notify.premium_reminders(cur, conn, now))
withcur(lambda cur, conn: notify.premium_reminders(cur, conn, now + 60000))
soon = [p for m, p in CALLS if m == 'sendMessage' and p['chat_id'] == 70001]
check('Tugashiga 3 kun ichida — bitta eslatma', len(soon) == 1 and 'tugaydi' in soon[0]['text'], soon)
db('UPDATE users SET premium_until = %s WHERE id = %s', (now - 3600 * 1000, u['id']))
CALLS.clear()
withcur(lambda cur, conn: notify.premium_reminders(cur, conn, now))
withcur(lambda cur, conn: notify.premium_reminders(cur, conn, now + 60000))
end = [p for m, p in CALLS if m == 'sendMessage' and p['chat_id'] == 70001]
check('Tugagan kuni — bitta "muddati tugadi"', len(end) == 1 and 'muddati tugadi' in end[0]['text'], end)
check('Tugagach AI yopiq', c.post('/api/ai/explain', headers=u['h'], json={'personal_id': pid, 'mode': 'full'}).status_code == 403)
check('Tugagach yangi dars yaratilmaydi', c.post('/api/personal/suggest', headers=u['h'], json={'subject_key': 'math', 'text': 'kasr'}).status_code == 403)
check('Yaratilgan dars qoladi', c.get(f'/api/personal/{pid}', headers=u['h']).get_json()['ok'])
check('Emoji yashirildi (saqlangan)', c.get('/api/me', headers=u['h']).get_json()['user']['premium']['emoji'] is None)
r = c.post('/api/premium/order', headers=u['h'], json={}).get_json()
check('Tugagach qayta sotib olsa bo\'ladi', r['ok'], r)

print('\n=== 9) Admin ===')
r = c.post('/api/admin/premium/grant', headers=ADM, json={'who': '@premtest', 'days': 7}).get_json()
check('Admin @username bilan 7 kun beradi', r['ok'] and any(a['id'] == u['id'] and a['days_left'] == 7 for a in r['active']), r)
r = c.post('/api/admin/premium/grant', headers=ADM, json={'who': str(w['id']), 'days': 30}).get_json()
check('Admin ID bilan beradi', r['ok'] and r['active_count'] == 3, r.get('active_count'))
r = c.post('/api/admin/premium/revoke', headers=ADM, json={'user_id': w['id']}).get_json()
check('Olib qo\'yish', r['ok'] and r['active_count'] == 2 and r['log'][0]['source'] == 'revoke')
check('Admin: shu oy sotuvlar (karta 2)', r['month']['count'] == 2 and r['month']['sum'] == 2 * 34900, r['month'])
check('Himoyalangan', c.get('/api/admin/premium').status_code == 401)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
