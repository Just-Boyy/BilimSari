"""Telegram Mini App initData tekshiruvi.

Rasmiy algoritm (https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app):
1. `hash` maydonini ajratib olish.
2. Qolgan kalit=qiymat juftlarini kalit bo'yicha saralab, "\n" bilan birlashtirish (data-check-string).
3. secret_key = HMAC-SHA256(key=b"WebAppData", msg=bot_token)
4. computed_hash = HMAC-SHA256(key=secret_key, msg=data_check_string) (hex)
5. computed_hash va yuborilgan hash'ni doimiy vaqtli solishtirish (hmac.compare_digest).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.config import settings


class InitDataValidationError(Exception):
    pass


def validate_init_data(init_data: str, max_age_seconds: int = 86_400) -> dict:
    if not init_data:
        raise InitDataValidationError("init_data bo'sh")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise InitDataValidationError("hash maydoni topilmadi")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))

    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise InitDataValidationError("Imzo mos kelmadi (hash noto'g'ri)")

    auth_date = parsed.get("auth_date")
    if auth_date is not None and (time.time() - int(auth_date)) > max_age_seconds:
        raise InitDataValidationError("initData muddati o'tgan")

    user_raw = parsed.get("user")
    user = json.loads(user_raw) if user_raw else None
    if not user or "id" not in user:
        raise InitDataValidationError("Foydalanuvchi ma'lumoti topilmadi")

    return {
        "telegram_id": user["id"],
        "username": user.get("username"),
        "first_name": user.get("first_name"),
        "language_code": user.get("language_code"),
        "auth_date": auth_date,
    }
