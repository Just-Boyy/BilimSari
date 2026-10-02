# -*- coding: utf-8 -*-
"""Prod tekshiruvlari uchun umumiy yordamchi: admin tokeni va mehmon (sinov) hisobi.

Prod'da /api/guest faqat admin tokeni bilan ishlaydi. Parol muhit o'zgaruvchisidan olinadi
(hech qachon chop etilmaydi):
    export ADMIN_PW="$(railway variables --service backend --json | python -c 'import json,sys;print(json.load(sys.stdin)["ADMIN_PASSWORD"])')"
    python tests/prod/prod_smoke.py
"""
import os

import requests

B = os.environ.get('BILIMSARI_URL', 'https://backend-production-ec58b.up.railway.app')
_token = []


def admin_token() -> str:
    if not _token:
        r = requests.post(B + '/api/admin/login', json={'password': os.environ['ADMIN_PW']}, timeout=30)
        _token.append(r.json()['token'])
    return _token[0]


def admin_headers() -> dict:
    return {'Authorization': 'Bearer ' + admin_token()}
