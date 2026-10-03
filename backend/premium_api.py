# -*- coding: utf-8 -*-
"""
Bilim Premium va shaxsiy darslar API.

  /api/premium            — holat, narx, sotib olish (karta), emoji tanlash
  /api/personal           — shaxsiy darslar: ro'yxat, mavzu variantlari, yaratish, o'qish
  /api/admin/premium      — admin panel: faol premiumlar, qo'lda berish/olib qo'yish
"""

import html

from flask import Blueprint, jsonify, request

import admin_audit
import partners
import payments
import marafon
import personal
import premium
import rate_limit
import tgbot
from admin_auth import admin_required
from auth_core import auth_required
from db import get_connection
from games import clock

bp = Blueprint('premium', __name__, url_prefix='/api')
admin_bp = Blueprint('premium_admin', __name__, url_prefix='/api/admin/premium')


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


# ───────────────────────── Premium ─────────────────────────

@bp.route('/premium', methods=['GET'])
@auth_required
def premium_info():
    conn, cur = _conn()
    try:
        uid = request.user['id']
        settings = payments.get_settings(cur)
        active = payments.active_order(cur, uid)
        return jsonify({
            'ok': True,
            'premium': premium.status(cur, uid),   # 'status' emas — api.js uni HTTP kodi bilan almashtiradi
            'price': settings['premium_price'],
            'days': premium.DAYS,
            'plans': _plans(settings),
            'personal_hours': int(personal.GENERATE_EVERY_MS // (3600 * 1000)),
            'members': _members(cur),
            'active_order': payments.order_public(active) if active and payments.is_premium(active) else None,
            'other_order': bool(active) and not payments.is_premium(active),
            'saved_promo': partners.saved_promo(cur, request.user),
            'last': next((v for k, v in payments.subject_statuses(cur, uid).items() if k in premium.PLANS), None),
            'emoji': premium.emoji_catalog(),
            'frames': [{'key': k, 'name': n} for k, n in premium.FRAMES],
            'telegram': bool(request.user.get('telegram_id')),
            'configured': bool(settings['card_number']),
        })
    finally:
        _close(conn, cur)


def _members(cur) -> int:
    """Hozir Premium'i faol o'quvchilar soni (sahifada 10 tadan oshsa ko'rsatiladi)."""
    cur.execute('SELECT COUNT(*) AS n FROM users WHERE premium_until > %s', (clock.now_ms(),))
    return int(cur.fetchone()['n'])


def _plans(settings) -> list:
    """Sotuvdagi tariflar: narxi, oyiga necha so'm va 1 oylikka nisbatan tejash foizi."""
    base = int(settings.get('premium_price') or 0)
    out = []
    for key, (days, months, name, name_ru, setting) in premium.PLANS.items():
        price = int(settings.get(setting) or 0)
        if price <= 0:
            continue
        full = base * months
        out.append({'key': key, 'days': days, 'months': months, 'name': name, 'price': price,
                    'per_month': int(round(price / months / 100.0)) * 100,
                    'saving': max(0, int(round((full - price) * 100 / full))) if full and months > 1 else 0})
    return out


@bp.route('/premium/order', methods=['POST'])
@auth_required
def premium_order():
    if not rate_limit.hit(f'order:{request.user["id"]}', 10, 3600):
        return jsonify({'ok': False, 'error': "Juda ko'p urinish. Birozdan keyin qayta urinib ko'ring."}), 429
    conn, cur = _conn()
    try:
        plan = _body().get('plan') or premium.ITEM
        if plan not in premium.PLANS:
            return jsonify({'ok': False, 'error': "Tarif noto'g'ri.", 'code': 'bad_plan'}), 400
        order, sent = payments.create_order(cur, conn, request.user, [plan], _body().get('promo'))
        return jsonify({'ok': True, 'order': payments.order_public(order), 'bot_sent': sent, 'bot': tgbot.BOT_USERNAME})
    except payments.PayError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/premium/emoji', methods=['POST'])
@auth_required
def premium_emoji():
    key = _body().get('emoji') or None
    conn, cur = _conn()
    try:
        premium.set_emoji(cur, conn, request.user['id'], key)
        return jsonify({'ok': True, 'emoji': key})
    except ValueError as exc:
        return jsonify({'ok': False, 'error': str(exc), 'code': 'premium_required'}), 403
    finally:
        _close(conn, cur)


@bp.route('/premium/frame', methods=['POST'])
@auth_required
def premium_frame():
    key = _body().get('frame')
    conn, cur = _conn()
    try:
        premium.set_frame(cur, conn, request.user['id'], key)
        return jsonify({'ok': True, 'frame': key})
    except ValueError as exc:
        return jsonify({'ok': False, 'error': str(exc), 'code': 'premium_required'}), 403
    finally:
        _close(conn, cur)


# ───────────────────────── Shaxsiy darslar ─────────────────────────

@bp.route('/personal', methods=['GET'])
@auth_required
def personal_list():
    conn, cur = _conn()
    try:
        return jsonify(dict(personal.overview(cur, request.user['id']), ok=True))
    finally:
        _close(conn, cur)


@bp.route('/personal/seen', methods=['POST'])
@auth_required
def personal_seen():
    conn, cur = _conn()
    try:
        personal.mark_seen(cur, conn, request.user['id'], _body().get('ids'))
        return jsonify({'ok': True})
    finally:
        _close(conn, cur)


@bp.route('/personal/suggest', methods=['POST'])
@auth_required
def personal_suggest():
    if not rate_limit.hit(f'personal-suggest:{request.user["id"]}', 20, 3600):
        return jsonify({'ok': False, 'error': "Juda ko'p urinish. Birozdan keyin qayta urinib ko'ring."}), 429
    body = _body()
    conn, cur = _conn()
    try:
        return jsonify(dict(personal.suggest(cur, request.user['id'], body.get('subject_key'), body.get('text')), ok=True))
    except personal.PersonalError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/personal/generate', methods=['POST'])
@auth_required
def personal_generate():
    body = _body()
    conn, cur = _conn()
    try:
        item = personal.generate(cur, conn, request.user, body.get('subject_key'), body.get('title'))
        return jsonify({'ok': True, 'topic': item})
    except personal.PersonalError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/personal/<int:pid>', methods=['GET'])
@auth_required
def personal_get(pid):
    conn, cur = _conn()
    try:
        return jsonify(dict(personal.payload(cur, conn, request.user['id'], pid), ok=True))
    except personal.PersonalError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/personal/<int:pid>/read', methods=['POST'])
@auth_required
def personal_read(pid):
    conn, cur = _conn()
    try:
        personal.mark_read(cur, conn, request.user['id'], pid)
        return jsonify({'ok': True})
    except personal.PersonalError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/personal/<int:pid>/quiz', methods=['POST'])
@auth_required
def personal_quiz(pid):
    conn, cur = _conn()
    try:
        res = personal.grade_quiz(cur, conn, request.user['id'], pid, _body().get('answers'))
        if res.get('chaqmoq'):
            res['marafon'] = marafon.personal_note(cur, request.user['id'], pid)
        return jsonify(dict(res, ok=True))
    except personal.PersonalError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/personal/<int:pid>/homework', methods=['POST'])
@auth_required
def personal_homework(pid):
    conn, cur = _conn()
    try:
        res = personal.submit_homework(cur, conn, request.user['id'], pid, _body().get('answers'))
        if res.get('chaqmoq'):
            res['marafon'] = marafon.personal_note(cur, request.user['id'], pid)
        return jsonify(dict(res, ok=True))
    except personal.PersonalError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


# ───────────────────────── Admin ─────────────────────────

def _find_user(cur, who):
    who = str(who or '').strip()
    if who.startswith('@') or (who and not who.isdigit()):
        cur.execute('SELECT id, name, telegram_id FROM users WHERE LOWER(username) = %s', (who.lstrip('@').lower(),))
        return cur.fetchone()
    if who.isdigit():
        cur.execute('SELECT id, name, telegram_id FROM users WHERE id = %s', (int(who),))
        row = cur.fetchone()
        if not row:
            cur.execute('SELECT id, name, telegram_id FROM users WHERE telegram_id = %s', (int(who),))
            row = cur.fetchone()
        return row
    return None


def _overview(cur, **extra):
    settings = payments.get_settings(cur)
    return jsonify(dict(premium.admin_overview(cur), ok=True, **extra,
                        settings={k: settings[k] for k in ('premium_price', 'premium_price_3', 'premium_price_12')}))


@admin_bp.route('', methods=['GET'])
@admin_required
def admin_premium():
    conn, cur = _conn()
    try:
        return _overview(cur)
    finally:
        _close(conn, cur)


@admin_bp.route('/grant', methods=['POST'])
@admin_required
def admin_grant():
    body = _body()
    try:
        days = int(body.get('days') or premium.DAYS)
    except (TypeError, ValueError):
        days = 0
    if not 1 <= days <= 366:
        return jsonify({'ok': False, 'error': "Kunlar soni 1 dan 366 gacha bo'lsin."}), 400
    conn, cur = _conn()
    try:
        row = _find_user(cur, body.get('who'))
        if not row:
            return jsonify({'ok': False, 'error': "Foydalanuvchi topilmadi (ilovadagi ID, Telegram ID yoki @username)."}), 404
        until = premium.grant(cur, row['id'], days, 'admin', note=body.get('note'))
        conn.commit()
        if row['telegram_id']:
            tgbot.send(row['telegram_id'], tgbot.L(
                f"🎁 Sizga <b>Bilim Premium</b> {days} kunga berildi!\n"
                "AI tushuntirish, shaxsiy darslar, emoji va avatar ramkasi ochildi.",
                f"🎁 Вам подарен <b>Bilim Premium</b> на {days} {tgbot.kun_ru(days)}!\n"
                "Объяснения ИИ, личные уроки, эмодзи и рамка аватара открыты."),
                tgbot.L('Shaxsiy darslarim', 'Мои личные уроки'), 'shaxsiy.html')
        admin_audit.log('premium_grant', detail=f'user_id={row["id"]} days={days} name={html.escape(row["name"])}')
        return _overview(cur, until_ms=until)
    finally:
        _close(conn, cur)


@admin_bp.route('/revoke', methods=['POST'])
@admin_required
def admin_revoke():
    try:
        uid = int(_body().get('user_id'))
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': "Foydalanuvchi ko'rsatilmagan."}), 400
    conn, cur = _conn()
    try:
        premium.revoke(cur, uid, clock.now_ms(), note='admin')
        conn.commit()
        admin_audit.log('premium_revoke', detail=f'user_id={uid}')
        return _overview(cur)
    finally:
        _close(conn, cur)
