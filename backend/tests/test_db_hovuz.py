# -*- coding: utf-8 -*-
"""Ko'p oqimli server (gunicorn gthread): baza ulanishlari navbati — bo'sh ulanish kutiladi (xato emas),
ichma-ich ulanish olgan oqim qotib qolmaydi, ulanishlar soni chegaradan oshmaydi, hammasi qaytariladi.
Haqiqiy bazaga ulanmaydi — soxta hovuz ishlatiladi."""
import os
import sys
import threading
import time

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.environ.get('DATABASE_URL'):
    sys.exit('XATO: testlar prod bazasida ishga tushirilmaydi — DATABASE_URL ni olib tashlang '
             '(tests/run_all.py har bir testni vaqtinchalik SQLite bazada ishlatadi).')
sys.path.insert(0, BACKEND)

import psycopg2.pool  # noqa: E402

fails = []
holat = {'band': 0, 'eng_kop': 0}
qulf = threading.Lock()


def check(name, cond, extra=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else f'  -> {str(extra)[:300]}'))
    if not cond:
        fails.append(name)


class SoxtaKursor:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a):
        time.sleep(0.001)


class SoxtaUlanish:
    closed = 0

    def cursor(self, *a, **k):
        return SoxtaKursor()

    def rollback(self):
        pass


class SoxtaHovuz:
    def __init__(self, minconn, maxconn, *a, **k):
        self.maxconn = maxconn

    def getconn(self):
        with qulf:
            if holat['band'] >= self.maxconn:
                raise psycopg2.pool.PoolError('connection pool exhausted')
            holat['band'] += 1
            holat['eng_kop'] = max(holat['eng_kop'], holat['band'])
        return SoxtaUlanish()

    def putconn(self, raw, close=False):
        with qulf:
            holat['band'] -= 1


psycopg2.pool.ThreadedConnectionPool = SoxtaHovuz
os.environ['DATABASE_URL'] = 'postgresql://soxta/baza'
os.environ['DB_POOL_MAX'] = '4'
import db  # noqa: E402

print('\n=== 40 oqim, har biri ulanish oladi; yarmi ichma-ich ikkinchisini ham ===')
xatolar = []


def ish(i):
    try:
        for _ in range(5):
            c = db.get_connection()
            time.sleep(0.01)
            if i % 2 == 0:              # masalan: so'rov ichida onlayn belgisi yoziladi
                c2 = db.get_connection()
                time.sleep(0.005)
                c2.close()
            c.close()
    except Exception as e:  # noqa: BLE001
        xatolar.append(repr(e))


t0 = time.time()
oqimlar = [threading.Thread(target=ish, args=(i,)) for i in range(40)]
[t.start() for t in oqimlar]
[t.join(timeout=60) for t in oqimlar]
check("Hech bir oqim qotib qolmadi", not any(t.is_alive() for t in oqimlar))
check("Xato yo'q (bo'sh ulanish kutildi, «pool exhausted» emas)", not xatolar, xatolar[:3])
check(f"Bir vaqtda ulanishlar chegaradan oshmadi (eng ko'pi {holat['eng_kop']} ≤ 4 + {db.NESTED_EXTRA})",
      holat["eng_kop"] <= 4 + db.NESTED_EXTRA, holat)
check("Hammasi hovuzga qaytdi", holat['band'] == 0 and not db._ushlagan, (holat, db._ushlagan))
check("Semafor to'liq bo'shadi", all(db._pg_sem.acquire(blocking=False) for _ in range(4))
      and not db._pg_sem.acquire(blocking=False))
for _ in range(4):
    db._pg_sem.release()

print('\n=== Ikki marta yopish va yopilmay qolgan ulanish ===')
c = db.get_connection()
c.close()
c.close()
check("Ikki marta yopish semaforni buzmaydi", holat['band'] == 0 and all(db._pg_sem.acquire(blocking=False) for _ in range(4)))
for _ in range(4):
    db._pg_sem.release()
c = db.get_connection()
del c                                   # kod xatosi: close() chaqirilmadi
import gc  # noqa: E402
gc.collect()
check("Yopilmay qolgan ulanish ham qaytariladi", holat['band'] == 0 and not db._ushlagan, (holat, db._ushlagan))
print(f'  ({time.time() - t0:.1f} s)')

print('\n' + ('HAMMASI OK' if not fails else f'{len(fails)} ta XATO: {fails}'))
sys.exit(1 if fails else 0)
