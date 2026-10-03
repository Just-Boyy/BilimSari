# -*- coding: utf-8 -*-
"""
Admin panel autentifikatsiyasi — o'quvchilar tizimidan butunlay alohida.

Bitta umumiy parol (ADMIN_PASSWORD muhit o'zgaruvchisi) + imzolangan token
(baza va sessiya kerak emas). Token js/admin.js tomonidan localStorage'da
alohida kalit ostida saqlanadi va "Authorization: Bearer <token>" bilan
yuboriladi — students tokenlari bilan aralashmaydi.
"""

import os
import secrets
import time
from functools import wraps

from flask import jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from auth_core import SECRET
from db import get_connection

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
ADMIN_TOKEN_MAX_AGE = 60 * 60 * 24 * 14  # 14 kun

# Shu Telegram ID'lar admin panelga parolsiz, Telegram orqali kira oladi
# (imzolangan initData tekshiriladi — ID'ni soxtalashtirib bo'lmaydi).
ADMIN_TELEGRAM_IDS = {
    int(x) for x in os.environ.get('ADMIN_TELEGRAM_IDS', '5771496552').split(',')
    if x.strip().isdigit()
}


_extra_cache = {'ids': set(), 'at': 0.0}
EXTRA_CACHE_S = 20


def extra_admin_ids(refresh=False) -> set:
    """Admin panelda qo'shilgan adminlar (bot_admins jadvali). Har so'rovda
    bazaga bormaslik uchun 20 soniya keshlanadi."""
    if refresh or time.time() - _extra_cache['at'] > EXTRA_CACHE_S:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute('SELECT telegram_id FROM bot_admins')
            _extra_cache['ids'] = {int(r['telegram_id']) for r in cur.fetchall()}
        except Exception:  # noqa: BLE001  (jadval hali yaratilmagan bo'lishi mumkin)
            conn.rollback()
        finally:
            cur.close()
            conn.close()
        _extra_cache['at'] = time.time()
    return _extra_cache['ids']


def admin_ids() -> list:
    """Barcha adminlar: egalar (ADMIN_TELEGRAM_IDS) + panelda qo'shilganlar."""
    return sorted(ADMIN_TELEGRAM_IDS | extra_admin_ids())


def is_owner(telegram_id) -> bool:
    try:
        return int(telegram_id) in ADMIN_TELEGRAM_IDS
    except (TypeError, ValueError):
        return False


def is_admin_telegram(telegram_id) -> bool:
    try:
        tid = int(telegram_id)
    except (TypeError, ValueError):
        return False
    return tid in ADMIN_TELEGRAM_IDS or tid in extra_admin_ids()

_serializer = URLSafeTimedSerializer(SECRET, salt='bilimsari-admin-panel')


def ensure_table(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admin_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    # Qo'shimcha adminlar (egalar — ADMIN_TELEGRAM_IDS muhit o'zgaruvchisida)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bot_admins (
            telegram_id BIGINT PRIMARY KEY,
            name TEXT,
            added_ms BIGINT NOT NULL
        )
    ''')
    conn.commit()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _min_issued_at() -> int:
    """Shu vaqtdan OLDIN (millisekund) chiqarilgan admin tokenlar endi
    yaroqsiz — "Barcha seanslarni tugatish" shu qiymatni hozirgi vaqtga
    o'rnatadi. Millisekund aniqligi + qat'iy `>` solishtirish ketma-ket
    so'rovlar bir xil soniyaga tushib qolganda ham noto'g'ri tasdiqlashning
    oldini oladi."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT value FROM admin_settings WHERE key = 'token_min_iat'")
        row = cur.fetchone()
        return int(row['value']) if row else 0
    finally:
        cur.close()
        conn.close()


def revoke_all_sessions():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO admin_settings (key, value) VALUES ('token_min_iat', %s) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
            (str(_now_ms()),)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def make_admin_token() -> str:
    return _serializer.dumps({'admin': True, 'iat': _now_ms()})


# Ilovadagi «Admin panel» tugmasi panelni tashqi brauzerda ochadi. Telegram'ning initData'si
# brauzerga o'tmaydi — shuning uchun ilova ichida imzolangan, 2 daqiqa amal qiladigan bir martalik
# kod olinadi va havolaning # qismida (serverga yuborilmaydi) brauzerga uzatiladi.
HANDOFF_MAX_AGE = 120


def make_handoff_code(tg_id) -> str:
    return _serializer.dumps({'h': secrets.token_hex(8), 'tg': int(tg_id)}, salt='admin-handoff')


def redeem_handoff_code(code) -> bool:
    """Kod yaroqli, muddati o'tmagan, hali ishlatilmagan va egasi hali admin bo'lsa — True (bir marta)."""
    try:
        data = _serializer.loads(str(code or ''), max_age=HANDOFF_MAX_AGE, salt='admin-handoff')
    except (BadSignature, SignatureExpired):
        return False
    if not isinstance(data, dict) or not data.get('h') or not is_admin_telegram(data.get('tg')):
        return False
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = _now_ms()
        cur.execute("INSERT INTO admin_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING",
                    ('handoff:' + data['h'], str(now)))
        fresh = cur.rowcount == 1
        cur.execute("DELETE FROM admin_settings WHERE key LIKE 'handoff:%%' AND value < %s", (str(now - 86400000),))
        conn.commit()
        return fresh
    finally:
        cur.close()
        conn.close()


def verify_admin_token(token: str) -> bool:
    if not token:
        return False
    try:
        data = _serializer.loads(token, max_age=ADMIN_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return False
    if not (isinstance(data, dict) and data.get('admin')):
        return False
    return int(data.get('iat', 0)) > _min_issued_at()


def admin_token_from_request():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    return None


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not verify_admin_token(admin_token_from_request()):
            return jsonify({
                'ok': False,
                'error': 'Admin avtorizatsiyasi talab qilinadi',
                'code': 'unauthorized',
            }), 401
        return fn(*args, **kwargs)
    return wrapper
