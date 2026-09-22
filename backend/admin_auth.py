# -*- coding: utf-8 -*-
"""
Admin panel autentifikatsiyasi — o'quvchilar tizimidan butunlay alohida.

Bitta umumiy parol (ADMIN_PASSWORD muhit o'zgaruvchisi) + imzolangan token
(baza va sessiya kerak emas). Token js/admin.js tomonidan localStorage'da
alohida kalit ostida saqlanadi va "Authorization: Bearer <token>" bilan
yuboriladi — students tokenlari bilan aralashmaydi.
"""

import os
from functools import wraps

from flask import jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from auth_core import SECRET

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
ADMIN_TOKEN_MAX_AGE = 60 * 60 * 24 * 14  # 14 kun

_serializer = URLSafeTimedSerializer(SECRET, salt='bilimsari-admin-panel')


def make_admin_token() -> str:
    return _serializer.dumps({'admin': True})


def verify_admin_token(token: str) -> bool:
    if not token:
        return False
    try:
        data = _serializer.loads(token, max_age=ADMIN_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return False
    return bool(isinstance(data, dict) and data.get('admin'))


def admin_token_from_request():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    # CSV eksport havolalari kabi oddiy <a href> yuklab olishlar Authorization
    # sarlavhasini yubora olmaydi — shunday hollarda ?token= orqali qabul qilinadi.
    return request.args.get('token')


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
