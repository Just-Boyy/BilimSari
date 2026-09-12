# -*- coding: utf-8 -*-
"""
Autentifikatsiya yadrosi — token yaratish/tekshirish.

app.py ham, study_api.py ham shu moduldan foydalanadi, shunda bir xil kod
ikki joyda takrorlanmaydi.
"""

import hashlib
import hmac
import os
import secrets
from datetime import timedelta
from functools import wraps

from flask import jsonify, request

from db import get_connection, utc_now

SECRET = os.environ.get('SECRET_KEY', 'bilimsari-dev-secret-change-me')
TOKEN_DAYS = 30

# Parol hashlash: PBKDF2-HMAC-SHA256, har foydalanuvchi uchun alohida salt.
_PBKDF2_ROUNDS = 120_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), (salt + SECRET).encode('utf-8'), _PBKDF2_ROUNDS
    ).hex()
    return f'pbkdf2${_PBKDF2_ROUNDS}${salt}${digest}'


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith('pbkdf2$'):
        try:
            _, rounds, salt, digest = stored.split('$', 3)
            calc = hashlib.pbkdf2_hmac(
                'sha256', password.encode('utf-8'), (salt + SECRET).encode('utf-8'), int(rounds)
            ).hex()
            return hmac.compare_digest(calc, digest)
        except (ValueError, TypeError):
            return False
    # Eski format (sha256) — kirishga ruxsat beramiz, keyin yangilanadi
    legacy = hashlib.sha256((password + SECRET).encode()).hexdigest()
    return hmac.compare_digest(legacy, stored)


def needs_rehash(stored: str) -> bool:
    return bool(stored) and not stored.startswith('pbkdf2$')


def create_token(user_id: int) -> str:
    token = secrets.token_hex(32)
    expires = utc_now() + timedelta(days=TOKEN_DAYS)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO tokens (token, user_id, expires_at) VALUES (%s, %s, %s)',
        (token, user_id, expires),
    )
    conn.commit()
    cur.close()
    conn.close()
    return token


def get_user_by_token(token: str):
    if not token:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''SELECT u.id, u.name, u.email, u.grade, u.photo_url, u.telegram_id
           FROM tokens t
           JOIN users u ON u.id = t.user_id
           WHERE t.token = %s AND t.expires_at > NOW()''',
        (token,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def token_from_request():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    return None


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_user_by_token(token_from_request())
        if not user:
            return jsonify({
                'ok': False,
                'error': 'Avtorizatsiya talab qilinadi',
                'code': 'unauthorized',
            }), 401
        request.user = user
        return fn(*args, **kwargs)
    return wrapper
