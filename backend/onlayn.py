# -*- coding: utf-8 -*-
"""O'quvchi oxirgi marta qachon faol bo'lgani (users.last_seen_ms) — do'stlar ro'yxatidagi
"onlayn" belgisi uchun. Har bir API so'rovida emas: har worker'da bir o'quvchi uchun
daqiqasiga ko'pi bilan bir marta yoziladi."""

import logging
import time

from db import get_connection

logger = logging.getLogger('bilimsari.onlayn')
THROTTLE_S = 60
_last = {}


def touch(user_id):
    now = time.time()
    uid = int(user_id)
    if now - _last.get(uid, 0) < THROTTLE_S:
        return
    _last[uid] = now
    if len(_last) > 20000:                        # xotira cheksiz o'smasin
        _last.clear()
        _last[uid] = now
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('UPDATE users SET last_seen_ms = %s WHERE id = %s', (int(now * 1000), uid))
        conn.commit()
    except Exception:  # noqa: BLE001  (faollik belgisi asosiy so'rovni buzmasin)
        conn.rollback()
        logger.warning('last_seen_ms yozilmadi', exc_info=True)
    finally:
        cur.close()
        conn.close()
