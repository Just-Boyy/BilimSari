# -*- coding: utf-8 -*-
"""
Game Hub API — /api/games/*.

Hammasi o'quvchi tokeni bilan (auth_required). Holatni o'zgartiruvchi
amallar yangi room holatini darhol qaytaradi — mijoz keyingi poll'ni kutmaydi.
Xatolar foydalanuvchiga tushunarli o'zbekcha matn bilan qaytadi.
"""

import logging
import os
import random
from functools import wraps

from flask import Blueprint, jsonify, request

import rate_limit
from auth_core import auth_required
from db import get_connection
from games import catalog, clock, matchmaking, rooms, stats
from games.errors import GameError

logger = logging.getLogger('bilimsari.games')

bp = Blueprint('games', __name__, url_prefix='/api/games')

BOT_USERNAME = os.environ.get('BOT_USERNAME', 'bilimsaribot').lstrip('@')
CLEANUP_CHANCE = 0.1   # lobby so'rovlarining ~10% ida eski roomlar tozalanadi


def endpoint(fn):
    """Baza ulanishini ochadi/yopadi va xatolarni JSON javobga aylantiradi."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        conn = get_connection()
        cur = conn.cursor()
        try:
            data = fn(cur, conn, *args, **kwargs) or {}
            data['ok'] = True
            return jsonify(data)
        except GameError as exc:
            conn.rollback()
            return jsonify({'ok': False, 'error': exc.message, 'code': exc.code}), exc.http_status
        except Exception:  # noqa: BLE001
            conn.rollback()
            logger.exception('Game API xatosi: %s', request.path)
            return jsonify({'ok': False, 'code': 'server_error',
                            'error': "Serverda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."}), 500
        finally:
            try:
                cur.close()
                conn.close()
            except Exception:  # noqa: BLE001
                pass
    return wrapper


def _limit(bucket, limit, window, message):
    if not rate_limit.hit(bucket, limit, window):
        raise GameError('rate_limit', message, 429)


def _body() -> dict:
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


def _uid() -> int:
    return request.user['id']


# ───────────────────────── Katalog va lobby ─────────────────────────

@bp.route('/catalog', methods=['GET'])
@auth_required
@endpoint
def catalog_view(cur, conn):
    return {
        'games': catalog.public_catalog(),
        'difficulties': [{'key': k, 'name': v} for k, v in catalog.DIFFICULTIES.items()],
        'player_limits': list(catalog.PLAYER_LIMITS),
        'bot': BOT_USERNAME,
    }


@bp.route('/topics', methods=['GET'])
@auth_required
@endpoint
def topics_view(cur, conn):
    game_type = request.args.get('game')
    subject = request.args.get('subject')
    game = catalog.GAMES.get(game_type)
    if not game or subject not in game['subjects']:
        raise GameError('bad_request', "O'yin yoki fan noto'g'ri tanlangan.")
    generated = catalog.generated_topics(game_type, subject)
    return {'topics': generated if generated is not None else catalog.curriculum_topics(cur, subject)}


@bp.route('/lobby', methods=['GET'])
@auth_required
@endpoint
def lobby_view(cur, conn):
    now = clock.now_ms()
    rooms.presence_touch(cur, _uid(), now)
    conn.commit()
    if random.random() < CLEANUP_CHANCE:
        rooms.cleanup(cur, conn, now)
    return {
        'online': rooms.online_count(cur, now),
        'rooms': rooms.public_rooms(cur, now),
        'my_room': rooms.my_room(cur, _uid()),
    }


# ───────────────────────── Roomlar ─────────────────────────

@bp.route('/rooms', methods=['POST'])
@auth_required
@endpoint
def create_room_view(cur, conn):
    _limit(f'game_create:{_uid()}', 12, 600, "Juda ko'p room yaratildi. Birozdan so'ng urinib ko'ring.")
    # Har bir room avtomatik ochiq — lobbydagi "Faol roomlar"da hamma uchun ko'rinadi
    code = rooms.create_room(cur, conn, request.user, _body(), is_public=True)
    return {'code': code, 'state': rooms.state(cur, conn, request.user, code)}


@bp.route('/rooms/join', methods=['POST'])
@auth_required
@endpoint
def join_room_view(cur, conn):
    _limit(f'game_join:{_uid()}', 20, 300, "Juda ko'p urinish. Birozdan so'ng qayta urinib ko'ring.")
    code = rooms.join_room(cur, conn, request.user, _body().get('code'))
    return {'code': code, 'state': rooms.state(cur, conn, request.user, code)}


@bp.route('/rooms/<code>', methods=['GET'])
@auth_required
@endpoint
def room_state_view(cur, conn, code):
    return {'state': rooms.state(cur, conn, request.user, code, request.args.get('since'))}


@bp.route('/rooms/<code>/ready', methods=['POST'])
@auth_required
@endpoint
def ready_view(cur, conn, code):
    rooms.set_ready(cur, conn, request.user, code, bool(_body().get('ready', True)))
    return {'state': rooms.state(cur, conn, request.user, code)}


@bp.route('/rooms/<code>/settings', methods=['POST'])
@auth_required
@endpoint
def settings_view(cur, conn, code):
    rooms.update_settings(cur, conn, request.user, code, _body())
    return {'state': rooms.state(cur, conn, request.user, code)}


@bp.route('/rooms/<code>/kick', methods=['POST'])
@auth_required
@endpoint
def kick_view(cur, conn, code):
    rooms.kick(cur, conn, request.user, code, _body().get('pid'))
    return {'state': rooms.state(cur, conn, request.user, code)}


@bp.route('/rooms/<code>/start', methods=['POST'])
@auth_required
@endpoint
def start_view(cur, conn, code):
    rooms.start(cur, conn, request.user, code)
    return {'state': rooms.state(cur, conn, request.user, code)}


@bp.route('/rooms/<code>/rematch', methods=['POST'])
@auth_required
@endpoint
def rematch_view(cur, conn, code):
    rooms.rematch(cur, conn, request.user, code)
    return {'state': rooms.state(cur, conn, request.user, code)}


@bp.route('/rooms/<code>/answer', methods=['POST'])
@auth_required
@endpoint
def answer_view(cur, conn, code):
    body = _body()
    rooms.answer(cur, conn, request.user, code, body.get('q'), body.get('answer'))
    return {'accepted': True, 'state': rooms.state(cur, conn, request.user, code)}


@bp.route('/rooms/<code>/leave', methods=['POST'])
@auth_required
@endpoint
def leave_view(cur, conn, code):
    rooms.leave_room(cur, conn, request.user, code)
    return {'left': True}


# ───────────────────────── Random raqib ─────────────────────────

@bp.route('/matchmaking', methods=['GET', 'POST', 'DELETE'])
@auth_required
@endpoint
def matchmaking_view(cur, conn):
    if request.method == 'POST':
        _limit(f'game_mm:{_uid()}', 20, 600, "Juda ko'p qidiruv. Birozdan so'ng urinib ko'ring.")
        return matchmaking.start(cur, conn, request.user, _body())
    if request.method == 'DELETE':
        return matchmaking.cancel(cur, conn, request.user)
    return matchmaking.poll(cur, conn, request.user)


# ───────────────────────── Reyting va statistika ─────────────────────────

@bp.route('/leaderboard', methods=['GET'])
@auth_required
@endpoint
def leaderboard_view(cur, conn):
    return stats.leaderboard(cur, _uid(), request.args.get('period', 'week'),
                             request.args.get('scope', 'global'), request.args.get('subject'))


@bp.route('/me', methods=['GET'])
@auth_required
@endpoint
def me_view(cur, conn):
    return {'stats': stats.my_stats(cur, _uid())}
