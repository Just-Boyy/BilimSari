# -*- coding: utf-8 -*-
"""
To'lov API: o'quvchi uchun /api/pay/*, admin panel uchun /api/admin/pay/*.
Biznes-logika payments.py'da.
"""

import admin_audit
import curriculum as cur_mod
import payments
import rate_limit
from admin_auth import admin_required
from auth_core import auth_required
from db import get_connection
from flask import Blueprint, Response, jsonify, request
from tgbot import BOT_USERNAME

bp = Blueprint('pay', __name__, url_prefix='/api/pay')
admin_bp = Blueprint('pay_admin', __name__, url_prefix='/api/admin/pay')


def _conn():
    conn = get_connection()
    return conn, conn.cursor()


def _close(conn, cur):
    try:
        cur.close()
        conn.close()
    except Exception:  # noqa: BLE001
        pass


def _fail(exc: payments.PayError):
    return jsonify({'ok': False, 'error': exc.message, 'code': exc.code}), exc.http_status


def _body():
    return request.get_json(silent=True) or {}


# ───────────────────────── O'quvchi ─────────────────────────

@bp.route('/shop', methods=['GET'])
@auth_required
def shop():
    """Do'kon: yopiq fanlar, narxlar, faol buyurtma."""
    conn, cur = _conn()
    try:
        uid = request.user['id']
        settings = payments.get_settings(cur)
        active = payments.active_order(cur, uid)
        return jsonify({
            'ok': True,
            'subjects': [dict(cur_mod.subject_meta(k), key=k) for k in payments.locked_subjects(cur, uid)],
            'prices': {k: settings[k] for k in ('price_single', 'price_three', 'price_all')},
            'active_order': payments.order_public(active) if active else None,
            'telegram': bool(request.user.get('telegram_id')),
            'configured': bool(settings['card_number']),
            'bot': BOT_USERNAME,
        })
    finally:
        _close(conn, cur)


@bp.route('/quote', methods=['POST'])
@auth_required
def quote():
    conn, cur = _conn()
    try:
        body = _body()
        return jsonify(dict(payments.quote(cur, request.user['id'], body.get('keys'), body.get('promo')), ok=True))
    except payments.PayError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/orders', methods=['POST'])
@auth_required
def create_order():
    if not rate_limit.hit(f'order:{request.user["id"]}', 10, 3600):
        return jsonify({'ok': False, 'error': "Juda ko'p urinish. Birozdan keyin qayta urinib ko'ring."}), 429
    conn, cur = _conn()
    try:
        body = _body()
        order, sent = payments.create_order(cur, conn, request.user, body.get('keys'), body.get('promo'))
        return jsonify({'ok': True, 'order': payments.order_public(order), 'bot_sent': sent, 'bot': BOT_USERNAME})
    except payments.PayError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/orders', methods=['GET'])
@auth_required
def my_orders():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'orders': payments.user_orders(cur, request.user['id'])})
    finally:
        _close(conn, cur)


@bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@auth_required
def cancel(order_id):
    conn, cur = _conn()
    try:
        if not payments.cancel_order(cur, conn, order_id, request.user['id']):
            return jsonify({'ok': False, 'error': "Bu buyurtmani bekor qilib bo'lmaydi."}), 409
        return jsonify({'ok': True})
    finally:
        _close(conn, cur)


# ───────────────────────── Admin panel ─────────────────────────

@admin_bp.route('/overview', methods=['GET'])
@admin_required
def admin_overview():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'stats': payments.overview(cur), 'settings': payments.get_settings(cur),
                        'promos': payments.list_promos(cur), 'reasons': payments.REJECT_REASONS})
    finally:
        _close(conn, cur)


@admin_bp.route('/orders', methods=['GET'])
@admin_required
def admin_orders():
    status = request.args.get('status') or None
    if status not in (None, payments.PENDING, payments.APPROVED, payments.REJECTED,
                      payments.AWAITING, payments.EXPIRED):
        status = None
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1
    conn, cur = _conn()
    try:
        return jsonify(dict(payments.admin_orders(cur, status, page), ok=True))
    finally:
        _close(conn, cur)


@admin_bp.route('/orders/<int:order_id>/receipt', methods=['GET'])
@admin_required
def admin_receipt(order_id):
    conn, cur = _conn()
    try:
        found = payments.receipt_file(cur, order_id)
    finally:
        _close(conn, cur)
    if not found:
        return jsonify({'ok': False, 'error': 'Chek topilmadi'}), 404
    mime, data = found
    return Response(data, mimetype=mime, headers={'Cache-Control': 'private, max-age=3600'})


@admin_bp.route('/orders/<int:order_id>/<action>', methods=['POST'])
@admin_required
def admin_decide(order_id, action):
    if action not in ('approve', 'reject'):
        return jsonify({'ok': False, 'error': "Noma'lum amal"}), 404
    conn, cur = _conn()
    try:
        ok, message = payments.decide(cur, conn, order_id, action == 'approve', 'Admin panel',
                                      _body().get('reason'))
        if not ok:
            return jsonify({'ok': False, 'error': message}), 409
        admin_audit.log(f'payment_{action}', detail=f'order_id={order_id}')
        return jsonify({'ok': True, 'message': message})
    finally:
        _close(conn, cur)


@admin_bp.route('/settings', methods=['POST'])
@admin_required
def admin_settings():
    conn, cur = _conn()
    try:
        settings = payments.save_settings(cur, conn, _body())
        admin_audit.log('payment_settings', detail='karta/narxlar yangilandi')
        return jsonify({'ok': True, 'settings': settings})
    except payments.PayError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@admin_bp.route('/promos', methods=['POST'])
@admin_required
def admin_create_promo():
    conn, cur = _conn()
    try:
        code = payments.create_promo(cur, conn, _body())
        admin_audit.log('promo_create', detail=code)
        return jsonify({'ok': True, 'promos': payments.list_promos(cur)})
    except payments.PayError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@admin_bp.route('/promos/<code>/toggle', methods=['POST'])
@admin_required
def admin_toggle_promo(code):
    conn, cur = _conn()
    try:
        if not payments.toggle_promo(cur, conn, code):
            return jsonify({'ok': False, 'error': 'Promo-kod topilmadi'}), 404
        return jsonify({'ok': True, 'promos': payments.list_promos(cur)})
    finally:
        _close(conn, cur)
