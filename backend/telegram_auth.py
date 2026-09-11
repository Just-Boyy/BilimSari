"""Telegram Mini App initData validation"""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400):
    """
    Validate Telegram WebApp initData.
    Returns parsed user dict or None if invalid.
    """
    if not init_data or not bot_token:
        return None

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop('hash', None)
    if not received_hash:
        return None

    # Data-check-string
    check_list = [f'{k}={v}' for k, v in sorted(parsed.items())]
    data_check_string = '\n'.join(check_list)

    secret_key = hmac.new(
        b'WebAppData',
        bot_token.encode(),
        hashlib.sha256
    ).digest()
    calculated = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        return None

    # Auth date freshness
    try:
        auth_date = int(parsed.get('auth_date', '0'))
    except ValueError:
        return None
    if abs(time.time() - auth_date) > max_age_seconds:
        return None

    user_raw = parsed.get('user')
    if not user_raw:
        return None
    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        return None

    return {
        'telegram_id': user.get('id'),
        'first_name': user.get('first_name') or '',
        'last_name': user.get('last_name') or '',
        'username': user.get('username') or '',
        'language_code': user.get('language_code') or 'uz',
        'photo_url': user.get('photo_url'),
    }
