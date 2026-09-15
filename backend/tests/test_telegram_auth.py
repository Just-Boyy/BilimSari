import time

import pytest

from app.security.telegram_auth import InitDataValidationError, validate_init_data
from tests.helpers import build_init_data


def test_valid_init_data_passes():
    init_data = build_init_data(telegram_id=555111222)
    result = validate_init_data(init_data)
    assert result["telegram_id"] == 555111222
    assert result["username"] == "testuser"


def test_tampered_hash_fails():
    init_data = build_init_data(telegram_id=555111222)
    tampered = init_data[:-1] + ("0" if init_data[-1] != "0" else "1")
    with pytest.raises(InitDataValidationError):
        validate_init_data(tampered)


def test_expired_auth_date_fails():
    old_timestamp = int(time.time()) - 90_000  # 24 soatdan ko'proq oldin
    init_data = build_init_data(telegram_id=555111222, auth_date=old_timestamp)
    with pytest.raises(InitDataValidationError):
        validate_init_data(init_data, max_age_seconds=86_400)
