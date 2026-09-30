# -*- coding: utf-8 -*-
"""
Do'stlar API (biznes-logika dostlar.py'da).

  /api/friends                — ro'yxat, kelgan/yuborilgan so'rovlar, o'yinga chaqiruvlar
  /api/friends/search?q=      — ID, @username yoki ism bo'yicha qidiruv
  /api/friends/request|respond|cancel|remove|invite|report
  /api/friends/leaderboard    — do'stlar orasidagi reyting
  /api/friends/feed           — do'stlar faolligi
  /api/admin/reports          — admin: shikoyatlar
"""

from flask import Blueprint, jsonify, request

import admin_audit
import dostlar
import rate_limit
from admin_auth import admin_required
from auth_core import auth_required
from db import get_connection

bp = Blueprint('dostlar', __name__, url_prefix='/api/friends')
admin_bp = Blueprint('dostlar_admin', __name__, url_prefix='/api/admin/reports')


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


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        raise dostlar.DostError("Noto'g'ri qiymat.")


def _uid():
    return int(request.user['id'])


@bp.route('', methods=['GET'])
@auth_required
def overview():
    conn, cur = _conn()
    try:
        return jsonify(dict(dostlar.overview(cur, _uid()), ok=True))
    finally:
        _close(conn, cur)


@bp.route('/invites', methods=['GET'])
@auth_required
def invites():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'invites': dostlar.invites(cur, _uid())})
    finally:
        _close(conn, cur)


@bp.route('/search', methods=['GET'])
@auth_required
def search():
    if not rate_limit.hit(f'friend_search:{_uid()}', 60, 60):
        return jsonify({'ok': False, 'error': "Juda ko'p qidiruv. Birozdan keyin urinib ko'ring."}), 429
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'results': dostlar.search(cur, _uid(), request.args.get('q'))})
    finally:
        _close(conn, cur)


@bp.route('/<action>', methods=['POST'])
@auth_required
def action(action):
    body = _body()
    conn, cur = _conn()
    try:
        me = _uid()
        if action == 'request':
            res = dostlar.send_request(cur, conn, me, _int(body.get('user_id')))
        elif action == 'respond':
            res = dostlar.respond(cur, conn, me, _int(body.get('request_id')), bool(body.get('accept')))
        elif action == 'cancel':
            dostlar.cancel(cur, conn, me, _int(body.get('request_id')))
            res = {'state': 'none'}
        elif action == 'remove':
            dostlar.remove(cur, conn, me, _int(body.get('user_id')))
            res = {'state': 'none'}
        elif action == 'invite':
            res = dostlar.invite(cur, conn, me, _int(body.get('user_id')), body.get('code'))
        elif action == 'report':
            dostlar.report(cur, conn, me, _int(body.get('user_id')), body.get('reason'), body.get('note'))
            res = {}
        else:
            return jsonify({'ok': False, 'error': "Noma'lum amal"}), 404
        return jsonify(dict(res, ok=True))
    except dostlar.DostError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/leaderboard', methods=['GET'])
@auth_required
def leaderboard():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'rows': dostlar.leaderboard(cur, _uid())})
    finally:
        _close(conn, cur)


@bp.route('/feed', methods=['GET'])
@auth_required
def feed():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'events': dostlar.feed(cur, _uid())})
    finally:
        _close(conn, cur)


# ───────────────────────── Admin: shikoyatlar ─────────────────────────

@admin_bp.route('', methods=['GET'])
@admin_required
def admin_list():
    conn, cur = _conn()
    try:
        return jsonify(dict(dostlar.admin_reports(cur), ok=True))
    finally:
        _close(conn, cur)


@admin_bp.route('/<int:report_id>/<act>', methods=['POST'])
@admin_required
def admin_resolve(report_id, act):
    conn, cur = _conn()
    try:
        dostlar.resolve(cur, conn, report_id, act, 'Admin panel')
        admin_audit.log('report_' + act, detail=f'report_id={report_id}')
        return jsonify(dict(dostlar.admin_reports(cur), ok=True))
    except dostlar.DostError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@admin_bp.route('/unblock/<int:user_id>', methods=['POST'])
@admin_required
def admin_unblock(user_id):
    conn, cur = _conn()
    try:
        dostlar.set_blocked(cur, conn, user_id, False)
        admin_audit.log('friends_unblock', detail=f'user_id={user_id}')
        return jsonify(dict(dostlar.admin_reports(cur), ok=True))
    finally:
        _close(conn, cur)
