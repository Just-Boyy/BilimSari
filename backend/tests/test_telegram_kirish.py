# -*- coding: utf-8 -*-
"""iPhone'da birinchi ochilish: telegram.org skripti kechiksa/yuklanmasa ham ilova «faqat Telegram» sahifasiga
adashib o'tmasligi — Telegram ma'lumoti kutiladi, o'zimizdagi zaxira nusxa yuklanadi, adashib tushilsa qaytiladi."""
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

import app as A  # noqa: E402

c = A.app.test_client()
fails = []


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:300]}'))
    if not cond:
        fails.append(name)


def fayl(nom):
    return open(os.path.join(BACKEND, nom), encoding='utf-8').read()


print('\n=== Zaxira Telegram skripti ===')
r = c.get('/js/telegram-web-app.js')
check("O'zimizdagi nusxa beriladi", r.status_code == 200 and b'initParams' in r.data and len(r.data) > 50000, r.status_code)
check('Service worker oldindan keshlaydi', "'/js/telegram-web-app.js'" in fayl('sw.js'))

print('\n=== Kutish mantiqi ===')
tg = fayl('js/telegram.js')
check("telegram.js: belgilar, zaxira va kutish", 'function telegramBelgisi' in tg and 'TelegramWebviewProxy' in tg
      and "'/js/telegram-web-app.js'" in tg and 'function tayyor' in tg and 'tayyor: tayyor' in tg)
check('Avtomatik kirish Telegram ma\'lumotini kutadi', 'if (!(await tayyor())) return false;' in tg)
idx = fayl('index.html')
check("Bosh sahifa darhol emas, kutib tekshiradi", 'await BilimSariTG.tayyor()' in idx and 'location.reload()' in idx
      and 'BilimSariTG.isTelegram()' not in idx)
check('Onboarding ham kutadi', 'await BilimSariTG.tayyor()' in fayl('onboarding.html'))
check("Sessiya tugasa Telegram ichida qayta kiradi", 'BilimSariTG.telegramBelgisi()' in fayl('js/api.js'))
k = fayl('telegram-kerak.html')
check("«Faqat Telegram» sahifasi Telegram ichida bo'lsa ilovaga qaytadi", "location.replace('index.html' + location.hash)" in k
      and 'bs_kerak_qaytish' in k)

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
sys.exit(1 if fails else 0)
