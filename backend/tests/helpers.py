"""Testlar uchun to'g'ri imzolangan Telegram initData yasovchi yordamchi."""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from app.config import settings


def build_init_data(
    telegram_id: int,
    first_name: str = "Test",
    username: str = "testuser",
    language_code: str = "uz",
    auth_date: int | None = None,
) -> str:
    user = {"id": telegram_id, "first_name": first_name, "username": username, "language_code": language_code}
    params = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": f"AA{telegram_id}",
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    params["hash"] = computed_hash
    return urlencode(params)
