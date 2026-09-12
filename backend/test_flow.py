# -*- coding: utf-8 -*-
"""
BilimSari — to'liq o'quv oqimi testi.

Ishga tushirish:  python test_flow.py
Baza: SQLite (DATABASE_URL bo'lmasa). Test o'z bazasini yaratadi va o'chiradi.
"""

import json
import os
import sys
import tempfile
from datetime import timedelta

sys.stdout.reconfigure(encoding='utf-8')

# Test uchun alohida baza
_tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
_tmp.close()
os.environ['SQLITE_PATH'] = _tmp.name
os.environ.pop('DATABASE_URL', None)

import app as A  # noqa: E402
import study  # noqa: E402
from db import get_connection, utc_now  # noqa: E402

A.init_db()
client = A.app.test_client()

PASSED = []
FAILED = []


def check(name, condition, detail=''):
    if condition:
        PASSED.append(name)
        print(f'  ✓ {name}')
    else:
        FAILED.append(f'{name} — {detail}')
        print(f'  ✗ {name}  → {detail}')


def call(method, path, token=None, **kwargs):
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    fn = getattr(client, method)
    res = fn(path, headers=headers, **kwargs)
    try:
        return res.status_code, res.get_json()
    except Exception:
        return res.status_code, {}


print('\n═══ 1. RO\'YXATDAN O\'TISH ═══')
code, data = call('post', '/api/register', json={
    'name': 'Test O\'quvchi', 'email': 'test@bilimsari.uz', 'password': 'parol123'})
check('Ro\'yxatdan o\'tish', code == 201 and data.get('ok'), f'{code} {data}')
TOKEN = data.get('token')
USER_ID = data['user']['id']

code, data = call('get', '/api/me', TOKEN)
check('Token ishlaydi', data.get('ok'), str(data))
check('Boshida sinf tanlanmagan', data['user'].get('grade') is None, str(data['user']))


print('\n═══ 2. SINF TANLASH ═══')
code, data = call('get', '/api/study/grades')
grades = data.get('grades', [])
check('11 ta sinf ko\'rsatiladi', len(grades) == 11, str(len(grades)))
check('1-sinfda dars bor', grades[0]['available'] and grades[0]['topic_count'] == 19,
      str(grades[0]))
check('3-sinf hozircha bo\'sh', not grades[2]['available'], str(grades[2]))

code, data = call('post', '/api/study/grade', TOKEN, json={'grade': 99})
check('Noto\'g\'ri sinf rad etiladi', code == 400, f'{code} {data}')

code, data = call('post', '/api/study/grade', TOKEN, json={'grade': 1})
check('1-sinf tanlandi', data.get('ok') and data.get('grade') == 1, str(data))


print('\n═══ 3. FANLAR ═══')
code, data = call('get', '/api/study/subjects', TOKEN)
subs = data.get('subjects', [])
check('1-sinfda 4 ta fan', len(subs) == 4, str([s['name'] for s in subs]))
check('Matematika birinchi', subs[0]['key'] == 'math', str(subs[0]))
check('Boshida progress 0%', subs[0]['percent'] == 0, str(subs[0]['percent']))
check('Matematikada 6 mavzu', subs[0]['total_topics'] == 6, str(subs[0]['total_topics']))


print('\n═══ 4. MAVZULAR KETMA-KETLIGI ═══')
code, data = call('get', '/api/study/topics/math', TOKEN)
topics = data.get('topics', [])
check('6 ta mavzu', len(topics) == 6, str(len(topics)))
check('1-mavzu ochiq', topics[0]['state'] == 'current', topics[0]['state'])
check('2-mavzu qulflangan', topics[1]['state'] == 'locked', topics[1]['state'])
check('6-mavzu qulflangan', topics[5]['state'] == 'locked', topics[5]['state'])

# Qulflangan mavzuni ochishga urinish
code, data = call('get', '/api/study/topic/math/qoshish-ayirish', TOKEN)
check('Qulflangan mavzu ochilmaydi', code == 403 and data.get('code') == 'locked',
      f'{code} {data.get("code")}')


print('\n═══ 5. DARSNI OCHISH ═══')
code, data = call('get', '/api/study/topic/math/sonlar', TOKEN)
check('1-mavzu ochildi', data.get('ok'), str(data.get('error')))
check('Dars matni bor', len(data.get('lesson', [])) >= 5, str(len(data.get('lesson', []))))
check('Quiz savollari bor', len(data.get('quiz', [])) == 6, str(len(data.get('quiz', []))))
check('Uyga vazifa bor', len(data['homework']['tasks']) == 4, str(data['homework']))

# XAVFSIZLIK: to'g'ri javob frontendga yuborilmasligi kerak
raw = json.dumps(data, ensure_ascii=False)
check('To\'g\'ri javoblar yuborilmaydi',
      all('answer' not in q for q in data['quiz']) and '"answer"' not in raw,
      'javob sizib chiqdi!')
check('Uy ishi javoblari yuborilmaydi',
      all('answer' not in t for t in data['homework']['tasks']), 'javob sizib chiqdi!')

code, data = call('post', '/api/study/lesson-read', TOKEN,
                  json={'subject_key': 'math', 'slug': 'sonlar'})
check('Dars o\'qildi deb belgilandi', data.get('ok'), str(data))


print('\n═══ 6. QUIZ ═══')
# Ataylab noto'g'ri javoblar
code, data = call('post', '/api/study/quiz', TOKEN, json={
    'subject_key': 'math', 'slug': 'sonlar', 'answers': [0, 0, 0, False, 'xxx', 0]})
check('Quizdan yiqildi', data.get('ok') and not data.get('passed'), str(data.get('percent')))
check('Qayta urinish xabari', 'qayta' in data.get('message', '').lower(), data.get('message'))
check('Tushuntirish beriladi', bool(data['results'][0].get('explain')), str(data['results'][0]))

# To'g'ri javoblar
code, data = call('post', '/api/study/quiz', TOKEN, json={
    'subject_key': 'math', 'slug': 'sonlar', 'answers': [1, 1, 1, True, '6', 1]})
check('Quizdan o\'tdi', data.get('passed') and data.get('percent') == 100,
      f'{data.get("percent")}%')
check('Uy ishi hali topshirilmagan',
      data['completion'] and not data['completion'].get('completed')
      and data['completion']['needs']['homework'], str(data.get('completion')))


print('\n═══ 7. UYGA VAZIFA ═══')
code, data = call('post', '/api/study/homework', TOKEN, json={
    'subject_key': 'math', 'slug': 'sonlar',
    'answers': {'h1': '5', 'h2': '3', 'h3': '10', 'h4': 'Derazalarni sanadim, 4 ta'}})
check('Noto\'g\'ri uy ishi qabul qilinmaydi', not data.get('passed'), str(data.get('message')))

code, data = call('post', '/api/study/homework', TOKEN, json={
    'subject_key': 'math', 'slug': 'sonlar',
    'answers': {'h1': '6', 'h2': '3', 'h3': '10', 'h4': 'Derazalarni sanadim, 4 ta'}})
check('To\'g\'ri uy ishi qabul qilindi', data.get('passed'), str(data.get('message')))


print('\n═══ 8. MAVZU YAKUNLANDI ═══')
completion = data.get('completion') or {}
check('Mavzu tugallandi', completion.get('completed'), str(completion))
check('Tabrik xabari', 'Tabriklaymiz' in completion.get('message', ''), completion.get('message'))
check('24 soatlik vaqt belgilandi', bool(completion.get('next_unlock_at')), str(completion))

code, data = call('get', '/api/study/topics/math', TOKEN)
topics = data.get('topics', [])
check('1-mavzu "completed"', topics[0]['state'] == 'completed', topics[0]['state'])
check('Progress 17%', data.get('percent') == 17, str(data.get('percent')))


print('\n═══ 9. 24 SOATLIK KUTISH ═══')
check('2-mavzu kutishda', topics[1]['state'] == 'cooldown', topics[1]['state'])
cd = data.get('cooldown') or {}
check('Kutish faol', cd.get('active'), str(cd))
check('Qolgan vaqt ~24 soat', 23 * 3600 < cd.get('seconds_left', 0) <= 24 * 3600,
      str(cd.get('seconds_left')))
check('Vaqt o\'zbekcha yoziladi', 'soat' in cd.get('text', ''), cd.get('text'))

code, data = call('get', '/api/study/topic/math/qoshish-ayirish', TOKEN)
check('Kutish vaqtida mavzu ochilmaydi', code == 403 and data.get('code') == 'cooldown',
      f'{code} {data.get("code")}')
check('Kutish xabari aniq', 'soat' in data.get('error', ''), data.get('error'))

# Boshqa FAN ham qulflanadi (kuniga 1 mavzu — global qoida)
code, data = call('get', '/api/study/topics/uzbek', TOKEN)
check('Boshqa fan ham kutishda', data['topics'][0]['state'] == 'cooldown',
      data['topics'][0]['state'])


print('\n═══ 10. BRAUZERNI ALDASH MUMKIN EMAS ═══')
# Yangi "qurilma" — yangi sessiya, localStorage yo'q
code, data = call('post', '/api/login', json={
    'email': 'test@bilimsari.uz', 'password': 'parol123'})
TOKEN2 = data.get('token')
check('Boshqa qurilmadan kirish', bool(TOKEN2), str(data))

code, data = call('get', '/api/study/topics/math', TOKEN2)
check('Yangi sessiyada ham kutish saqlanadi',
      data['topics'][1]['state'] == 'cooldown', data['topics'][1]['state'])
check('Yangi sessiyada progress saqlanadi',
      data['topics'][0]['state'] == 'completed', data['topics'][0]['state'])

# To'g'ridan-to'g'ri quiz yuborish ham ishlamaydi
code, data = call('post', '/api/study/quiz', TOKEN2, json={
    'subject_key': 'math', 'slug': 'ondan-katta-sonlar', 'answers': [1, 0, 1, True, '13', 1]})
check('Qulflangan mavzuga quiz yuborib bo\'lmaydi', code == 403, f'{code} {data.get("code")}')


print('\n═══ 11. 24 SOAT O\'TGANDAN KEYIN ═══')
conn = get_connection()
cur = conn.cursor()
cur.execute(
    'UPDATE user_progress SET completed_at = %s WHERE user_id = %s AND status = %s',
    (utc_now() - timedelta(hours=24, minutes=1), USER_ID, 'completed'))
conn.commit()
cur.close()
conn.close()
print('  (bazadagi tugatish vaqti 24 soat orqaga surildi)')

code, data = call('get', '/api/study/topics/math', TOKEN)
check('Kutish tugadi', not data['cooldown']['active'], str(data['cooldown']))
check('2-mavzu ochildi', data['topics'][1]['state'] == 'current', data['topics'][1]['state'])
check('3-mavzu hali qulflangan', data['topics'][2]['state'] == 'locked', data['topics'][2]['state'])

code, data = call('get', '/api/study/topic/math/qoshish-ayirish', TOKEN)
check('2-mavzuni ochish mumkin', data.get('ok'), str(data.get('error')))


print('\n═══ 12. IKKINCHI MAVZUNI YAKUNLASH ═══')
call('post', '/api/study/lesson-read', TOKEN, json={'subject_key': 'math', 'slug': 'qoshish-ayirish'})
code, data = call('post', '/api/study/quiz', TOKEN, json={
    'subject_key': 'math', 'slug': 'qoshish-ayirish', 'answers': [1, 1, 2, True, '3', 0]})
check('2-mavzu quizidan o\'tdi', data.get('passed'), str(data.get('percent')))

code, data = call('post', '/api/study/homework', TOKEN, json={
    'subject_key': 'math', 'slug': 'qoshish-ayirish',
    'answers': {'h1': '8', 'h2': '3', 'h3': '7', 'h4': '3', 'h5': '2+2=4'}})
check('2-mavzu uy ishi qabul qilindi', data.get('passed'), str(data.get('message')))
check('2-mavzu yakunlandi', (data.get('completion') or {}).get('completed'),
      str(data.get('completion')))

code, data = call('get', '/api/study/topics/math', TOKEN)
check('3-mavzu endi kutishda', data['topics'][2]['state'] == 'cooldown',
      data['topics'][2]['state'])
check('Progress 33%', data.get('percent') == 33, str(data.get('percent')))


print('\n═══ 13. DASHBOARD ═══')
code, data = call('get', '/api/study/dashboard', TOKEN)
check('Dashboard ishlaydi', data.get('ok'), str(data))
check('Sinf ko\'rsatiladi', data.get('grade') == 1, str(data.get('grade')))
check('2 ta mavzu tugallangan', data['stats']['completed_topics'] == 2, str(data['stats']))
check('Umumiy progress hisoblanadi', data['stats']['percent'] == 11, str(data['stats']))
check('Bugungi dars ko\'rsatiladi', bool(data.get('today')), str(data.get('today')))
check('Dashboardda kutish bor', data['cooldown']['active'], str(data['cooldown']))


print('\n═══ 14. BO\'SH HOLATLAR ═══')
code, data = call('post', '/api/register', json={
    'name': 'Test 2', 'email': 'test2@bilimsari.uz', 'password': 'parol123'})
TOKEN3 = data['token']
code, data = call('get', '/api/study/subjects', TOKEN3)
check('Sinfsiz foydalanuvchi 409 oladi', code == 409 and data.get('code') == 'no_grade',
      f'{code} {data.get("code")}')

call('post', '/api/study/grade', TOKEN3, json={'grade': 7})
code, data = call('get', '/api/study/subjects', TOKEN3)
check('Bo\'sh sinf uchun xabar bor',
      data.get('ok') and data['subjects'] == [] and 'tayyorlanmoqda' in data['empty_message'],
      str(data))


print('\n═══ 15. CHEKKA HOLAT: ikkita mavzuni parallel boshlash ═══')
# Yangi foydalanuvchi: ikkita fandan bittadan mavzuni OCHADI (kutish hali yo'q),
# keyin bittasini yakunlaydi. Ikkinchisi allaqachon boshlangani uchun ochiq qoladi —
# lekin uni YAKUNLASH 24 soatlik qoida bilan to'silishi kerak.
code, data = call('post', '/api/register', json={
    'name': 'Chekka', 'email': 'chekka@bilimsari.uz', 'password': 'parol123'})
T4 = data['token']
call('post', '/api/study/grade', T4, json={'grade': 1})

call('get', '/api/study/topic/math/sonlar', T4)          # boshlandi
call('get', '/api/study/topic/uzbek/tovush-harf', T4)    # bu ham boshlandi

# 1-mavzuni to'liq yakunlaymiz
call('post', '/api/study/lesson-read', T4, json={'subject_key': 'math', 'slug': 'sonlar'})
call('post', '/api/study/quiz', T4, json={
    'subject_key': 'math', 'slug': 'sonlar', 'answers': [1, 1, 1, True, '6', 1]})
code, data = call('post', '/api/study/homework', T4, json={
    'subject_key': 'math', 'slug': 'sonlar',
    'answers': {'h1': '6', 'h2': '3', 'h3': '10', 'h4': 'sanadim'}})
check('Math mavzusi yakunlandi', (data.get('completion') or {}).get('completed'),
      str(data.get('completion')))

# Boshlangan ikkinchi mavzu hali ochiq bo'lishi kerak (davom ettirish mumkin)
code, data = call('get', '/api/study/topic/uzbek/tovush-harf', T4)
check('Boshlangan mavzu ochiq qoladi', data.get('ok'), f'{code} {data.get("code")}')

# Lekin uni YAKUNLASH to'silishi kerak
call('post', '/api/study/lesson-read', T4, json={'subject_key': 'uzbek', 'slug': 'tovush-harf'})
call('post', '/api/study/quiz', T4, json={
    'subject_key': 'uzbek', 'slug': 'tovush-harf', 'answers': [1, 1, 1, True, 1, '3']})
code, data = call('post', '/api/study/homework', T4, json={
    'subject_key': 'uzbek', 'slug': 'tovush-harf',
    'answers': {'h1': '5', 'h2': '2', 'h3': '29', 'h4': 'a-l-i'}})
comp = data.get('completion') or {}
check('Uy ishi qabul qilindi', data.get('passed'), str(data.get('message')))
check('Ikkinchi mavzu YAKUNLANMAYDI', not comp.get('completed'), str(comp))
check('Sabab — 24 soatlik qoida', comp.get('blocked_by_cooldown'), str(comp))
check('Sabab tushunarli yozilgan',
      'bitta mavzu' in (comp.get('message') or ''), comp.get('message'))

code, data = call('get', '/api/study/dashboard', T4)
check('Kuniga faqat 1 mavzu hisoblanadi',
      data['stats']['completed_topics'] == 1, str(data['stats']))


print('\n═══ 16. AI YORDAMCHI ═══')
code, data = call('get', '/api/ai/status')
check('AI status endpointi ishlaydi', data.get('ok'), str(data))
code, data = call('post', '/api/ai/explain', json={'subject_key': 'math', 'slug': 'sonlar'})
check('AI auth talab qiladi', code == 401, f'{code}')


# ───────────────────────── Natija ─────────────────────────
print('\n' + '═' * 55)
print(f'  O\'TDI: {len(PASSED)}     YIQILDI: {len(FAILED)}')
print('═' * 55)
if FAILED:
    print('\nYiqilgan testlar:')
    for f in FAILED:
        print(f'  • {f}')

try:
    os.unlink(_tmp.name)
except OSError:
    pass

sys.exit(1 if FAILED else 0)
