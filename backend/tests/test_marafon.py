# -*- coding: utf-8 -*-
"""Yutuqli marafon: jurnal, admin, qatnashish, hisob qoidalari, admin amallari, yakunlash, xabarlar."""
import base64
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
import daily  # noqa: E402
import jurnal  # noqa: E402
import marafon  # noqa: E402
import site_settings  # noqa: E402
import tgbot  # noqa: E402
from auth_core import create_token  # noqa: E402
from db import get_connection  # noqa: E402
from games import clock  # noqa: E402

SENT = []


def fake_tg(method, payload):
    SENT.append((method, payload))
    return {'ok': True, 'result': {'message_id': 1}}


tgbot.tg_api = fake_tg
T = [int(time.time() * 1000)]
clock.now_ms = lambda: T[0]
DAY = 24 * 3600 * 1000
HOUR = 3600 * 1000
c = A.app.test_client()
fails = []


def adv(ms):
    T[0] += ms


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:500]}'))
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


def mk(name, tg, username=None):
    uid = db("INSERT INTO users (name, onboarded, chosen_subject_key, telegram_id, username, notify) "
             "VALUES (%s, TRUE, 'math', %s, %s, 1) RETURNING id", (name, tg, username), True)[0]['id']
    return {'id': uid, 'h': {'Authorization': 'Bearer ' + create_token(uid)}, 'name': name, 'tg': tg}


def log(u, amount, source, ref):
    return withcur(lambda cur, conn: (jurnal.add(cur, u['id'], amount, source, ref, T[0]), conn.commit())[0])


def msgs_to(tg):
    return [p for m, p in SENT if m == 'sendMessage' and str(p.get('chat_id')) == str(tg)]


def adm(method, path, **kw):
    r = getattr(c, method)('/api/admin/marathon' + path, headers=ADM, **kw)
    return r.status_code, r.get_json()


def stu(u, method, path, **kw):
    r = getattr(c, method)('/api/marathon' + path, headers=u['h'], **kw)
    return r.status_code, r.get_json()


def local_str(ms):
    from datetime import datetime
    from db import TASHKENT_TZ
    return datetime.fromtimestamp(ms / 1000, TASHKENT_TZ).strftime('%Y-%m-%dT%H:%M')


def wait_threads():
    time.sleep(0.6)


ADM = {'Authorization': 'Bearer ' + admin_auth.make_admin_token()}
ali, bek, sam, dil, eko = mk('Ali', 96001, 'ali_m'), mk('Bek', 96002, 'bek_m'), mk('Sam', 96003), mk('Dil', 96004), mk('Eko', 96005)
withcur(lambda cur, conn: site_settings.put(cur, conn, site_settings.CHANNEL_KEY, 'https://t.me/bilimsari_test'))

print('— Chaqmoq jurnali (hook\'lar)')
Tp = db("SELECT id, slug, grade, quiz FROM topics WHERE subject_key = 'math' ORDER BY grade, seq LIMIT 1", (), True)[0]
quiz = json.loads(Tp['quiz']) if isinstance(Tp['quiz'], str) else Tp['quiz']
right = [q['answer'] for q in quiz]
c.post('/api/study/lesson-read', headers=eko['h'], json={'grade': Tp['grade'], 'subject_key': 'math', 'slug': Tp['slug']})
r = c.post('/api/study/quiz', headers=eko['h'], json={'grade': Tp['grade'], 'subject_key': 'math', 'slug': Tp['slug'], 'answers': right}).get_json()
lg = db("SELECT source, ref, amount FROM chaqmoq_log WHERE user_id = %s", (eko['id'],), True)
check('Dars testi → jurnal (dars, +15)', r['chaqmoq'] == 15 and any(x['source'] == 'dars' and x['amount'] == 15 and x['ref'].endswith(':quiz') for x in lg), (r.get('chaqmoq'), lg))
c.post('/api/study/quiz', headers=eko['h'], json={'grade': Tp['grade'], 'subject_key': 'math', 'slug': Tp['slug'], 'answers': right})
check('Qayta topshirish jurnalga yozilmaydi', db("SELECT COUNT(*) AS n FROM chaqmoq_log WHERE user_id = %s", (eko['id'],), True)[0]['n'] == 1)
c.get('/api/study/daily', headers=eko['h'])
ans = withcur(lambda cur, conn: daily._question(cur, conn, daily.today(T[0]), T[0])['answer'])
c.post('/api/study/daily/answer', headers=eko['h'], json={'answer': ans})
check('Kun savoli → jurnal (kun, +5)', db("SELECT COUNT(*) AS n FROM chaqmoq_log WHERE user_id = %s AND source = 'kun' AND amount = 5", (eko['id'],), True)[0]['n'] == 1)

print('— Admin: yaratish')
start = T[0] + HOUR
body = {'title': 'Oktabr marafoni', 'description': 'Eng faol o\'quvchilar uchun', 'start': local_str(start), 'days': 7,
        'top_n': 3, 'audience': 'all', 'contact': '@bilimsari_admin',
        'prizes': [{'place': 1, 'amount': 3000000}, {'place': 2, 'amount': 2000000, 'note': 'Premium 1 oy'}]}
s, d = adm('post', '', json=dict(body, title='ab'))
check('Qisqa nom — xato', s == 400, d)
s, d = adm('post', '', json=dict(body, contact='no'))
check("Noto'g'ri username — xato", s == 400, d)
s, d = adm('post', '', json=body)
m = d['marathon']
mid = m['id']
check('Qoralama yaratildi', s == 200 and m['status'] == 'draft' and m['contact'] == 'bilimsari_admin' and m['top_n'] == 3
      and m['prize_fund'] == 5000000 and abs(m['end_ms'] - m['start_ms'] - 7 * DAY) < 1000, m)
s, d = adm('post', '', json=body)
check('Ikkinchi marafon — busy', s == 409 and d['code'] == 'busy', d)
s, d = adm('post', f'/{mid}/schedule')
check("3-o'rin sovrinisiz rejalashtirilmaydi", s == 400 and '3' in d['error'], d)
s, d = adm('post', f'/{mid}/update', json={'prizes': body['prizes'] + [{'place': 3, 'amount': 1000000}]})
check('Sovrinlar yangilandi (fond 6 mln)', s == 200 and d['marathon']['prize_fund'] == 6000000, d.get('marathon'))
png = 'data:image/png;base64,' + base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'\x00' * 64).decode()
s, d = adm('post', f'/{mid}/image', json={'place': 1, 'image': png})
img = d.get('image_url')
check('Sovrin rasmi yuklandi', s == 200 and img and img.startswith('/api/marathon/image/'), d)
r = c.get(img)
check('Rasm ochiq (kesh bilan)', r.status_code == 200 and r.mimetype == 'image/png' and 'immutable' in r.headers.get('Cache-Control', ''))
s, d = stu(ali, 'get', '')
check("Qoralama o'quvchiga ko'rinmaydi", d['marathon'] is None, d)
SENT.clear()
s, d = adm('post', f'/{mid}/schedule')
check('Rejalashtirildi', s == 200 and d['marathon']['status'] == 'scheduled', d.get('marathon', {}).get('status'))
s, d = stu(ali, 'get', '')
check("Rejalashtirilgan — ko'rinadi, qo'shilsa bo'ladi", d['marathon'] and d['marathon']['status'] == 'scheduled'
      and d['me']['can_join'] and d['marathon']['prizes'][0]['image_url'] == img, d)

print('— Qatnashish')
s, d = stu(ali, 'post', '/join', json={'id': mid})
check('Rozilik bermasa — xato', s == 400 and d['code'] == 'agree', d)
s, d = stu(ali, 'post', '/join', json={'id': mid, 'agree': True})
check("Ali qo'shildi (boshlanishidan oldin)", s == 200 and d['me']['joined'] and not d['me']['can_join'], d.get('me'))
log(ali, 15, 'dars', 'dars:x:quiz:before')
adv(HOUR + 60 * 1000)
withcur(lambda cur, conn: marafon.tick(cur, conn, T[0]))
st = db('SELECT status FROM marathons WHERE id = %s', (mid,), True)[0]['status']
check("Vaqti keldi — o'zi boshlandi", st == 'active', st)
b = db('SELECT * FROM broadcasts ORDER BY id DESC LIMIT 1', (), True)
check("Boshlanish e'loni: hammaga, HTML, tugma bilan", b and b[0]['everyone'] == 1 and b[0]['html'] == 1
      and 'boshlandi' in b[0]['text'] and 'marafon' in (b[0]['button_path'] or ''), b[0] if b else None)
ch = [p for mt, p in SENT if mt == 'sendMessage' and p.get('chat_id') == '@bilimsari_test']
check("Kanalga e'lon (url tugma)", ch and 'url' in ch[0]['reply_markup']['inline_keyboard'][0][0], ch)
withcur(lambda cur, conn: marafon.tick(cur, conn, T[0]))
check("E'lon bir marta", len([1 for mt, p in SENT if p.get('chat_id') == '@bilimsari_test']) == 1)
for u in (bek, sam):
    stu(u, 'post', '/join', json={'id': mid, 'agree': True})

print('— Hisob qoidalari')
adv(1000)
log(ali, 30, 'oyin', 'oyin:1')
log(bek, 15, 'dars', 'dars:t1:quiz')
adv(1000)
log(bek, 15, 'dars', 'dars:t1:uy')
log(sam, 5, 'kun', 'kun:1')
log(dil, 50, 'dars', 'dars:z:quiz')            # qatnashmaydi
adv(21000)                                      # reyting keshi (20 s) yangilansin
s, d = stu(ali, 'get', '')
top = {x['name']: x for x in d['top']}
check("Boshlanishdan oldingi chaqmoq sanalmaydi; Ali 30", top['Ali']['score'] == 30, top)
check("Teng (30) — birinchi yetgan (Ali) yuqorida", [x['name'] for x in d['top']][:2] == ['Ali', 'Bek'], [x['name'] for x in d['top']])
check('Dil (qatnashmagan) reytingda yo\'q', 'Dil' not in top)
check("Sam: 3-o'rin, keyingi o'ringa 26 kerak", d['top'][2]['name'] == 'Sam' and True, d['top'])
s, d = stu(sam, 'get', '')
check("Sam 'me': rank 3, to_next 26", d['me']['rank'] == 3 and d['me']['to_next'] == 26, d['me'])
# Shaxsiy darslar: 24 soatda 1 ta
log(sam, 15, 'shaxsiy', 'shaxsiy:101:quiz')
adv(HOUR)
log(sam, 15, 'shaxsiy', 'shaxsiy:101:uy')           # o'sha dars — sanaladi
log(sam, 15, 'shaxsiy', 'shaxsiy:102:quiz')         # 24 soat o'tmagan — sanalmaydi
st = withcur(lambda cur, conn: marafon.standings(cur, marafon._row(cur, mid), T[0], fresh=True))
sam_row = next(x for x in st if x['user_id'] == sam['id'])
check('Shaxsiy: 1-dars (30) sanaldi, 2-dars sanalmadi', sam_row['parts']['shaxsiy'] == 30 and sam_row['score'] == 35, sam_row)
note = withcur(lambda cur, conn: marafon.personal_note(cur, sam['id'], 102, T[0]))
check("O'quvchiga aytiladi: 2-dars sanalmadi", note and not note['counted'] and '24 soat' in note['text'], note)
adv(DAY)
log(sam, 15, 'shaxsiy', 'shaxsiy:103:quiz')         # 24 soatdan keyin — sanaladi
st = withcur(lambda cur, conn: marafon.standings(cur, marafon._row(cur, mid), T[0], fresh=True))
check("24 soatdan keyin yangi dars sanaladi (45)", next(x for x in st if x['user_id'] == sam['id'])['parts']['shaxsiy'] == 45)

print("— Admin amallari")
s, d = adm('post', f'/{mid}/adjust', json={'who': '@bek_m', 'amount': 100, 'note': 'Bonus'})
rows = {x['name']: x for x in d['standings']}
check("Chaqmoq qo'shish (+100, @username bilan)", s == 200 and rows['Bek']['score'] == 130 and rows['Bek']['parts']['admin'] == 100, rows.get('Bek'))
s, d = adm('post', f'/{mid}/adjust', json={'who': str(bek['id']), 'amount': -30})
check('Chaqmoq ayirish (-30)', {x['name']: x for x in d['standings']}['Bek']['score'] == 100)
s, d = adm('post', f'/{mid}/adjust', json={'who': str(dil['id']), 'amount': 10})
check("Qatnashmayotganga qo'shib bo'lmaydi", s == 404, d)
SENT.clear()
s, d = adm('post', f'/{mid}/remove', json={'who': str(sam['id']), 'reason': 'Qoida buzildi'})
check('Chiqarish: reytingdan yo\'qoladi, sababi saqlanadi', s == 200 and all(x['name'] != 'Sam' for x in d['standings'])
      and d['removed'][0]['reason'] == 'Qoida buzildi', d.get('removed'))
check('Chiqarilganga bot xabari', msgs_to(96003) and 'chiqarildingiz' in msgs_to(96003)[-1]['text'])
s, d = stu(sam, 'post', '/join', json={'id': mid, 'agree': True})
check("Chiqarilgan o'zi qayta qo'shila olmaydi", s == 403 and d['code'] == 'removed', d)
s, d = adm('post', f'/{mid}/add', json={'who': str(dil['id'])})
dil_row = {x['name']: x for x in d['standings']}.get('Dil')
check("Admin talablarsiz qo'shdi — boshidan sanaladi (Dil 50)", dil_row and dil_row['score'] == 50 and dil_row['waived'], dil_row)
s, d = adm('post', f'/{mid}/user', json={'who': str(bek['id'])})
u = d['user']
check('Batafsil: kunma-kun manbalar va admin o\'zgartirishlari', s == 200 and u['days'] and u['days'][0]['dars'] == 30
      and len(u['adjust']) == 2, u)
s, d = adm('post', f'/{mid}/update', json={'title': 'Oktabr marafoni 2026', 'start': '2020-01-01T00:00', 'days': 10})
check("Faol marafonni tahrirlash: nom, muddat (boshi o'zgarmaydi)", s == 200 and d['marathon']['title'] == 'Oktabr marafoni 2026'
      and d['marathon']['start_ms'] == m['start_ms'] and abs(d['marathon']['end_ms'] - m['start_ms'] - 10 * DAY) < 1000, d.get('marathon'))

print('— Faqat Premium marafon qoidasi (hisobda)')
db("UPDATE marathons SET audience = 'premium', rev = rev + 1 WHERE id = %s", (mid,))
st = withcur(lambda cur, conn: marafon.standings(cur, marafon._row(cur, mid), T[0], fresh=True))
by = {x['user_id']: x for x in st}
check("Premiumsiz olingan chaqmoq sanalmaydi (Ali 0), talablarsiz qo'shilgan Dil — sanaladi (50)",
      by[ali['id']]['score'] == 0 and by[dil['id']]['score'] == 50, {k: v['score'] for k, v in by.items()})
s, d = stu(eko, 'get', '')
check("Premiumsiz o'quvchi qo'shila olmaydi (reason=premium)", d['me']['reason'] == 'premium' and not d['me']['can_join'], d['me'])
s, d = stu(eko, 'post', '/join', json={'id': mid, 'agree': True})
check("Premiumsiz join — 403", s == 403 and d['code'] == 'premium', d)
c.post('/api/admin/premium/grant', headers=ADM, json={'who': str(eko['id']), 'days': 30})
s, d = stu(eko, 'post', '/join', json={'id': mid, 'agree': True})
check("Premium olgach qo'shildi", s == 200 and d['me']['joined'], d.get('me'))
log(eko, 20, 'oyin', 'oyin:77')
by = {x['user_id']: x for x in withcur(lambda cur, conn: marafon.standings(cur, marafon._row(cur, mid), T[0], fresh=True))}
check("Premium paytida olingan chaqmoq sanaladi (Eko 20)", by[eko['id']]['score'] == 20, by.get(eko['id']))
db("UPDATE marathons SET audience = 'all', rev = rev + 1 WHERE id = %s", (mid,))

print('— Banner, do\'st belgisi')
db('INSERT INTO friendships (user_a, user_b, created_ms) VALUES (%s, %s, 1)', tuple(sorted((ali['id'], bek['id']))))
s, d = stu(ali, 'get', '')
check("Do'st ismi yonida 'friend'", {x['name']: x for x in d['top']}['Bek']['friend'] is True)
s, d = stu(ali, 'get', '/banner')
bn = d['banner']
check('Banner: fond, rank, joined', bn and bn['prize_fund'] == 6000000 and bn['joined'] and bn['rank'], bn)

print('— Eslatmalar')
SENT.clear()
e = db('SELECT end_ms FROM marathons WHERE id = %s', (mid,), True)[0]['end_ms']
T[0] = e - DAY + 1000
withcur(lambda cur, conn: marafon.tick(cur, conn, T[0]))
wait_threads()
check("Tugashiga 24 soat — qatnashchilarga", any('24 soat qoldi' in p['text'] for p in msgs_to(96001)), msgs_to(96001)[-1:] if msgs_to(96001) else None)
n1 = len(SENT)
withcur(lambda cur, conn: marafon.tick(cur, conn, T[0] + 60000))
wait_threads()
check('24 soat eslatmasi bir marta', len(SENT) == n1)
T[0] = e - HOUR + 1000
withcur(lambda cur, conn: marafon.tick(cur, conn, T[0]))
wait_threads()
check("Tugashiga 1 soat", any('1 soat qoldi' in p['text'] for p in msgs_to(96002)))

print('— Yakunlash')
SENT.clear()
T[0] = e + 1000
withcur(lambda cur, conn: marafon.tick(cur, conn, T[0]))
wait_threads()
mm = db('SELECT status FROM marathons WHERE id = %s', (mid,), True)[0]
check('Marafon tugadi', mm['status'] == 'finished')
w = db('SELECT * FROM marathon_winners WHERE marathon_id = %s ORDER BY place', (mid,), True)
check("G'oliblar: faqat chaqmoqi > 0, top-3", [x['user_id'] for x in w] == [bek['id'], dil['id'], ali['id']]
      and [x['amount'] for x in w] == [3000000, 2000000, 1000000], [(x['user_id'], x['score']) for x in w])
wm = msgs_to(96002)
check("G'olibga: o'rin, sovrin, @contact ga yozish (url tugma)", wm and "1-o'rinni" in wm[0]['text'] and '3 000 000' in wm[0]['text']
      and 'bilimsari_admin' in wm[0]['text'] and wm[0]['reply_markup']['inline_keyboard'][0][0]['url'] == 'https://t.me/bilimsari_admin', wm)
check("Xabar yuborilgani belgilandi", all(x['notified'] for x in db('SELECT notified FROM marathon_winners WHERE marathon_id = %s', (mid,), True)))
b = db('SELECT * FROM broadcasts ORDER BY id DESC LIMIT 1', (), True)[0]
check("Natija e'loni: hammaga", b['everyone'] == 1 and 'yakunlandi' in b['text'] and 'Bek' in b['text'], b['text'][:200])
check("Kanalga natija", any(p.get('chat_id') == '@bilimsari_test' and 'yakunlandi' in p['text'] for mt, p in SENT))
withcur(lambda cur, conn: marafon.tick(cur, conn, T[0] + 60000))
check("Yakunlash bir marta", len(db('SELECT * FROM marathon_winners WHERE marathon_id = %s', (mid,), True)) == 3)
s, d = stu(bek, 'get', '')
check("Tugagan marafon tepada yo'q, tarixda bor (Bek 1-o'rin, fond 6 mln)", d['marathon'] is None and d['history'][0]['id'] == mid
      and d['history'][0]['my_place'] == 1 and d['history'][0]['prize_fund'] == 6000000, d)
s, d = stu(bek, 'get', f'/history/{mid}')
check("Tarix: g'oliblar va o'z o'rni", s == 200 and d['winners'][0]['name'] == 'Bek' and d['me']['place'] == 1
      and d['marathon']['title'] == 'Oktabr marafoni 2026', d)
check("Tarix: tugamagan/yo'q marafon — 404", stu(bek, 'get', '/history/999999')[0] == 404)
y = c.get('/api/study/achievements', headers=bek['h']).get_json()
keys = {x['key'] for x in (y.get('items') or y.get('achievements') or []) if x.get('unlocked') or x.get('unlocked_ms')}
check("Nishonlar: Marafon g'olibi + sovrindori", {'marafon_1', 'marafon_sovrin'} <= keys, sorted(keys))
s, d = stu(sam, 'get', '/banner')
check('Tugagach banner yo\'q', d['banner'] is None)

print("— To'lov belgisi")
SENT.clear()
s, d = adm('post', f'/{mid}/paid', json={'who': str(bek['id']), 'note': 'Karta 8600...'})
check("To'landi — g'olibga xabar", s == 200 and msgs_to(96002) and "o'tkazildi" in msgs_to(96002)[-1]['text'], d)
s, d = adm('post', f'/{mid}/paid', json={'who': str(bek['id'])})
check('Ikkinchi marta — xato', s == 409, d)
s, d = adm('post', f'/{mid}/results')
check("Natijalar: to'langan belgisi", d['results'][0]['paid_ms'] and not d['results'][1]['paid_ms'], d['results'])
s, d = adm('get', '')
check("Admin: hozirgi marafon yo'q, tarixda bor", d['marathon'] is None and d['history'][0]['id'] == mid, d)

print('— Yangi marafon, bekor qilish, qoralamani o\'chirish')
s, d = adm('post', '', json=dict(body, title='Noyabr', start=local_str(T[0] + DAY)))
m2 = d['marathon']['id']
s, d = adm('post', f'/{m2}/delete')
check("Qoralama o'chirildi", s == 200 and d['marathon'] is None)
s, d = adm('post', '', json=dict(body, title='Dekabr', prizes=body['prizes'] + [{'place': 3, 'amount': 5}]))
m3 = d['marathon']['id']
s, d = adm('post', f'/{m3}/start')
check('Hozir boshlash', s == 200 and d['marathon']['status'] == 'active', d.get('marathon'))
s, d = adm('post', f'/{m3}/delete')
check("Boshlanganni o'chirib bo'lmaydi", s == 409)
s, d = adm('post', f'/{m3}/cancel')
check('Bekor qilindi', s == 200 and d['marathon'] is None)
s, d = adm('post', '', json=dict(body, title='Yanvar', prizes=body['prizes'] + [{'place': 3, 'amount': 5}]))
m4 = d['marathon']['id']
adm('post', f'/{m4}/start')
stu(ali, 'post', '/join', json={'id': m4, 'agree': True})
adv(1000)
log(ali, 10, 'kun', 'kun:yanvar')
adv(1000)
s, d = adm('post', f'/{m4}/finish')
check('Hozir yakunlash — Ali g\'olib', s == 200 and d['marathon'] is None
      and db('SELECT user_id FROM marathon_winners WHERE marathon_id = %s', (m4,), True)[0]['user_id'] == ali['id'])
check("Audit jurnali", db("SELECT COUNT(*) AS n FROM admin_audit_log WHERE action LIKE 'marathon_%%'", (), True)[0]['n'] >= 8)
r = c.delete(f"/api/admin/users/{dil['id']}", headers=ADM)
check("O'quvchi o'chirilganda jurnal va qatnashuv tozalanadi", r.status_code == 200
      and not db('SELECT 1 FROM chaqmoq_log WHERE user_id = %s', (dil['id'],), True)
      and not db('SELECT 1 FROM marathon_participants WHERE user_id = %s', (dil['id'],), True))
check('401 tokensiz', c.get('/api/admin/marathon').status_code == 401 and c.get('/api/marathon').status_code == 401)
print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
