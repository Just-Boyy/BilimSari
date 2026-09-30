# -*- coding: utf-8 -*-
"""
Yutuqli marafon API (biznes-logika marafon.py'da).

  /api/marathon              — reyting sahifasining "Marafon" bo'limi
  /api/marathon/banner       — bosh sahifa banneri
  /api/marathon/join         — qatnashish (qoidalarga rozilik bilan)
  /api/marathon/image/<id>   — sovrin rasmi
  /api/admin/marathon/...    — admin: yaratish, tahrirlash, boshqarish, g'oliblar
"""

import base64

from flask import Blueprint, Response, jsonify, request

import admin_audit
import marafon
import rate_limit
from admin_auth import admin_required
from auth_core import auth_required
from db import get_connection
from games import clock
from premium_api import _find_user

bp = Blueprint('marafon', __name__, url_prefix='/api/marathon')
admin_bp = Blueprint('marafon_admin', __name__, url_prefix='/api/admin/marathon')


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


def _uid():
    return int(request.user['id'])


@bp.route('', methods=['GET'])
@auth_required
def view():
    conn, cur = _conn()
    try:
        return jsonify(dict(marafon.view(cur, _uid()), ok=True))
    finally:
        _close(conn, cur)


@bp.route('/banner', methods=['GET'])
@auth_required
def banner():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'banner': marafon.banner(cur, _uid())})
    finally:
        _close(conn, cur)


@bp.route('/join', methods=['POST'])
@auth_required
def join():
    if not rate_limit.hit(f'marafon_join:{_uid()}', 20, 60):
        return jsonify({'ok': False, 'error': "Juda ko'p urinish. Birozdan keyin urinib ko'ring."}), 429
    body = _body()
    conn, cur = _conn()
    try:
        try:
            mid = int(body.get('id'))
        except (TypeError, ValueError):
            return jsonify({'ok': False, 'error': 'Marafon topilmadi.', 'code': 'not_found'}), 404
        marafon.join(cur, conn, mid, _uid(), bool(body.get('agree')))
        return jsonify(dict(marafon.view(cur, _uid()), ok=True))
    except marafon.MarafonError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/image/<int:image_id>', methods=['GET'])
def image(image_id):
    """Sovrin rasmi. Rasm almashsa id ham o'zgaradi — uzoq keshlash xavfsiz."""
    conn, cur = _conn()
    try:
        found = marafon.load_image(cur, image_id)
    finally:
        _close(conn, cur)
    if not found:
        return jsonify({'ok': False, 'error': 'Rasm topilmadi'}), 404
    mime, data = found
    resp = Response(base64.b64decode(data), mimetype=mime)
    resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resp


# ───────────────────────── Admin ─────────────────────────

def _admin_ok(**extra):
    conn, cur = _conn()
    try:
        return jsonify(dict(marafon.admin_view(cur), ok=True, **extra))
    finally:
        _close(conn, cur)


@admin_bp.route('', methods=['GET'])
@admin_required
def admin_view():
    return _admin_ok()


@admin_bp.route('', methods=['POST'])
@admin_required
def admin_create():
    conn, cur = _conn()
    try:
        mid = marafon.create(cur, conn, _body())
        admin_audit.log('marathon_create', detail=f'id={mid}')
    except marafon.MarafonError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)
    return _admin_ok()


@admin_bp.route('/<int:mid>/<action>', methods=['POST'])
@admin_required
def admin_action(mid, action):
    body = _body()
    conn, cur = _conn()
    extra = {}
    try:
        if action == 'update':
            marafon.update(cur, conn, mid, body)
        elif action == 'schedule':
            marafon.schedule(cur, conn, mid)
        elif action == 'start':
            marafon.start_now(cur, conn, mid)
        elif action == 'finish':
            marafon.finish_now(cur, conn, mid)
        elif action == 'cancel':
            marafon.cancel(cur, conn, mid)
        elif action == 'delete':
            marafon.delete_draft(cur, conn, mid)
        elif action == 'image':
            try:
                place = int(body.get('place'))
            except (TypeError, ValueError):
                raise marafon.MarafonError("O'rin noto'g'ri.")
            extra['image_url'] = marafon.set_prize_image(cur, conn, mid, place, body.get('image'))
        elif action in ('add', 'remove', 'adjust', 'paid', 'user'):
            who = body.get('user_id') if body.get('user_id') is not None else body.get('who')
            u = _find_user(cur, who)
            if not u:
                raise marafon.MarafonError("Bunday o'quvchi topilmadi (ID yoki @username).", 'not_found', 404)
            uid = int(u['id'])
            if action == 'add':
                marafon.admin_add(cur, conn, mid, uid)
            elif action == 'remove':
                marafon.admin_remove(cur, conn, mid, uid, body.get('reason'))
            elif action == 'adjust':
                marafon.adjust(cur, conn, mid, uid, body.get('amount'), body.get('note'))
            elif action == 'paid':
                marafon.mark_paid(cur, conn, mid, uid, body.get('note'))
            else:
                return jsonify({'ok': True, 'user': marafon.admin_user(cur, mid, uid)})
            extra['user_id'] = uid
        elif action == 'results':
            return jsonify({'ok': True, 'results': marafon.results(cur, mid), 'marathon': marafon.public_info(
                cur, marafon._row(cur, mid), clock.now_ms())})
        else:
            return jsonify({'ok': False, 'error': "Noma'lum amal"}), 404
        admin_audit.log('marathon_' + action, detail=f"id={mid}" + (f" user_id={extra['user_id']}" if 'user_id' in extra else '')
                        + (f" amount={body.get('amount')}" if action == 'adjust' else ''))
    except marafon.MarafonError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)
    return _admin_ok(**extra)
