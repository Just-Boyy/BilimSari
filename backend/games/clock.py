# -*- coding: utf-8 -*-
"""
O'yin vaqti — epoch millisekund (int).

Vaqt shu modul orqali olinadi (clock.now_ms()), shunda testlarda soatni
almashtirib, taymerlarni kutmasdan tekshirish mumkin. Millisekund butun son
sifatida saqlanadi: SQLite TIMESTAMP soniyagacha yaxlitlaydi, tez javob
bonusi va muddatlar uchun esa aniqlik kerak.
"""

import time
from datetime import datetime, timedelta

from db import TASHKENT_TZ


def now_ms() -> int:
    return int(time.time() * 1000)


def period_start_ms(period: str, now: int) -> int:
    """Toshkent vaqti bo'yicha davr boshi: day | week (dushanba) | month | all."""
    local = datetime.fromtimestamp(now / 1000, TASHKENT_TZ)
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == 'day':
        start = midnight
    elif period == 'week':
        start = midnight - timedelta(days=midnight.weekday())
    elif period == 'month':
        start = midnight.replace(day=1)
    else:
        return 0
    return int(start.timestamp() * 1000)


def tashkent_date(ms: int):
    return datetime.fromtimestamp(int(ms) / 1000, TASHKENT_TZ).date()
