# -*- coding: utf-8 -*-
"""
Hamkorlik dasturi API (biznes-logika partners.py'da).

  /api/partner             — hamkorning o'z statistikasi (profil sahifasi uchun)
  /api/admin/partners      — admin: hamkorlar, pog'onalar, to'lovlarni yozib borish
"""

from flask import Blueprint, jsonify, request

import admin_audit
import partners
from admin_auth import admin_required
from auth_core import auth_required
from db import get_connection
from premium_api import _find_user

bp = Blueprint('partner', __name__, url_prefix='/api')
admin_bp = Blueprint('partner_admin', __name__, url_prefix='/api/admin/partners')


def _conn():
    conn = get_connection()
    return conn, conn.cursor()


def _close(conn, cur):
    try:
        cur.close()
        conn.close()
    except Exception:  # noqa: BLE001
        pass


def _body():
    return request.get_json(silent=True) or {}


def _fail(exc):
    return jsonify({'ok': False, 'error': exc.message, 'code': exc.code}), exc.http_status


@bp.route('/partner', methods=['GET'])
@auth_required
def my_partner():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'partner': partners.mine(cur, request.user['id'])})
    finally:
        _close(conn, cur)


# ───────────────────────── Admin ─────────────────────────

def _list(cur, **extra):
    return jsonify(dict(partners.admin_list(cur), ok=True, **extra))


@admin_bp.route('', methods=['GET'])
@admin_required
def admin_list():
    conn, cur = _conn()
    try:
        return _list(cur)
    finally:
        _close(conn, cur)


@admin_bp.route('', methods=['POST'])
@admin_required
def admin_create():
    body = _body()
    conn, cur = _conn()
    try:
        user = _find_user(cur, body.get('who'))
        if not user:
            return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi. Ilovadagi ID, Telegram ID yoki @username '
                                                  'ni tekshiring.'}), 404
        code = partners.create(cur, conn, user, body.get('code'), body.get('commission'), body.get('discount'))
        admin_audit.log('partner_create', detail=f"user_id={user['id']} kod={code}")
        return _list(cur, code=code)
    except partners.PartnerError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@admin_bp.route('/tiers', methods=['POST'])
@admin_required
def admin_tiers():
    conn, cur = _conn()
    try:
        t = partners.save_tiers(cur, conn, _body())
        admin_audit.log('partner_tiers', detail=f"{t['tier1_sales']}:+{t['tier1_bonus']} {t['tier2_sales']}:+{t['tier2_bonus']}")
        return _list(cur)
    except partners.PartnerError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@admin_bp.route('/<int:user_id>', methods=['GET'])
@admin_required
def admin_detail(user_id):
    conn, cur = _conn()
    try:
        return jsonify(dict(partners.admin_detail(cur, user_id), ok=True))
    except partners.PartnerError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@admin_bp.route('/<int:user_id>/<action>', methods=['POST'])
@admin_required
def admin_action(user_id, action):
    body = _body()
    conn, cur = _conn()
    try:
        if action == 'update':
            partners.update(cur, conn, user_id, body)
            admin_audit.log('partner_update', detail=f"user_id={user_id} komissiya={body.get('commission')}% "
                                                     f"chegirma={body.get('discount')}%")
        elif action == 'toggle':
            active = partners.toggle(cur, conn, user_id)
            admin_audit.log('partner_toggle', detail=f"user_id={user_id} " + ('yoqildi' if active else "to'xtatildi"))
        elif action == 'delete':
            partners.delete(cur, conn, user_id)
            admin_audit.log('partner_delete', detail=f'user_id={user_id}')
        elif action == 'payout':
            res = partners.record_payout(cur, conn, user_id, body.get('amount'), body.get('note'), 'Admin panel')
            admin_audit.log('partner_payout', detail=f"user_id={user_id} {res['amount']} so'm")
        else:
            return jsonify({'ok': False, 'error': "Noma'lum amal"}), 404
        return _list(cur)
    except partners.PartnerError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@admin_bp.route('/payouts/<int:payout_id>/delete', methods=['POST'])
@admin_required
def admin_payout_delete(payout_id):
    conn, cur = _conn()
    try:
        partners.delete_payout(cur, conn, payout_id)
        admin_audit.log('partner_payout_delete', detail=f'payout_id={payout_id}')
        return _list(cur)
    except partners.PartnerError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)
