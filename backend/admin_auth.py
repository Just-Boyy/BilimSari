# -*- coding: utf-8 -*-
"""
Admin panel autentifikatsiyasi — o'quvchilar tizimidan butunlay alohida.

Bitta umumiy parol (ADMIN_PASSWORD muhit o'zgaruvchisi) + imzolangan token
(baza va sessiya kerak emas). Token js/admin.js tomonidan localStorage'da
alohida kalit ostida saqlanadi va "Authorization: Bearer <token>" bilan
yuboriladi — students tokenlari bilan aralashmaydi.
"""

import os
import time
from functools import wraps

from flask import jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from auth_core import SECRET
from db import get_connection

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
ADMIN_TOKEN_MAX_AGE = 60 * 60 * 24 * 14  # 14 kun

_serializer = URLSafeTimedSerializer(SECRET, salt='bilimsari-admin-panel')


def ensure_table(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admin_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
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
