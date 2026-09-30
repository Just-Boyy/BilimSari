# -*- coding: utf-8 -*-
"""
Admin panel API — foydalanuvchilar, fanlar, to'lovlar boshqaruvi.

Talabalar tizimidan butunlay alohida: alohida token turi (admin_auth.py),
o'z login yo'li (parol — ADMIN_PASSWORD muhit o'zgaruvchisi).
"""

import csv
import hmac
import html
import io
import os
from datetime import timedelta

from flask import Blueprint, Response, jsonify, request

import admin_audit
import admin_auth
import alerts
import analytics
import backup
import broadcast
import curriculum as cur_mod
import dostlar
import jurnal
import marafon
import lesson_edit
import payments
import rate_limit
import site_settings
import study
import tgbot
from admin_auth import (
    ADMIN_PASSWORD, admin_required, is_admin_telegram, make_admin_token, revoke_all_sessions,
)
from db import as_utc, get_connection, iso_utc, to_tashkent, utc_now
from games import clock
from games import rooms as game_rooms
from telegram_auth import validate_init_data

bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

# Admin login uchun IP bo'yicha urinish cheklovi — parol o'zi cheksiz
# taxmin qilinishining oldini oladi (hmac.compare_digest faqat vaqt
# hujumidan himoyalaydi, urinishlar sonini cheklamaydi). Bazada saqlanadi,
# shunda bir necha gunicorn worker orasida ham real chegara bo'lib qoladi.
LOGIN_RATE_LIMIT = int(os.environ.get('ADMIN_LOGIN_RATE_LIMIT', '5'))
LOGIN_RATE_WINDOW = int(os.environ.get('ADMIN_LOGIN_RATE_WINDOW', '900'))  # 15 daqiqa

# Telegram orqali admin kirishda initData qancha "yangi" bo'lishi kerak.
# O'quvchi kirishidagi 24 soatdan qattiqroq — admin huquqi kattaroq.
ADMIN_INITDATA_MAX_AGE = 60 * 60  # 1 soat


def _client_ip():
    fwd = request.headers.get('X-Forwarded-For', '')
    if fwd:
        return fwd.split(',')[0].strip()
    return request.remote_addr or 'unknown'


@bp.route('/login', methods=['POST'])
def admin_login():
    if not ADMIN_PASSWORD:
        return jsonify({
            'ok': False,
            'error': "Admin paneli hali sozlanmagan (ADMIN_PASSWORD muhit o'zgaruvchisi yo'q)",
        }), 503

    ip = _client_ip()
    bucket = f'admin_login:{ip}'
    if rate_limit.is_blocked(bucket, LOGIN_RATE_LIMIT, LOGIN_RATE_WINDOW):
        return jsonify({
            'ok': False,
            'error': "Juda ko'p noto'g'ri urinish. 15 daqiqadan so'ng qayta urinib ko'ring.",
            'code': 'rate_limit',
        }), 429

    body = request.get_json(silent=True) or {}
    password = body.get('password') or ''
    if not hmac.compare_digest(password, ADMIN_PASSWORD):
        rate_limit.record(bucket)
        return jsonify({'ok': False, 'error': "Parol noto'g'ri"}), 401

    admin_audit.log('login', ip=ip)
    return jsonify({'ok': True, 'token': make_admin_token()})


@bp.route('/telegram-login', methods=['POST'])
def admin_telegram_login():
    """Admin panelga parolsiz kirish — faqat ADMIN_TELEGRAM_IDS ro'yxatidagi
    Telegram foydalanuvchilari uchun. initData'ning HMAC imzosi bot tokeni
    bilan tekshiriladi, shuning uchun Telegram ID'ni soxtalashtirib bo'lmaydi.

    Parol kirishidagi urinish cheklovi bu yerda yo'q: HMAC imzoni taxmin
    qilib bo'lmaydi, cheklov esa bir IP'dagi boshqa odamlar tufayli haqiqiy
    adminni ham bloklab qo'yardi.

    Barcha rad javoblari 403 (401 emas) — aks holda js/admin.js mavjud
    yaroqli admin tokenni o'chirib yuborardi."""
    if not BOT_TOKEN:
        return jsonify({'ok': False, 'error': "BOT_TOKEN sozlanmagan", 'code': 'no_bot'}), 503

    body = request.get_json(silent=True) or {}
    tg_user = validate_init_data(body.get('initData') or '', BOT_TOKEN, ADMIN_INITDATA_MAX_AGE)
    if not tg_user:
        return jsonify({
            'ok': False,
            'error': "Telegram sessiyasi eskirgan. Ilovani yopib, qayta oching.",
            'code': 'bad_init_data',
        }), 403
    if not is_admin_telegram(tg_user.get('telegram_id')):
        return jsonify({
            'ok': False,
            'error': "Bu Telegram hisobida admin huquqi yo'q.",
            'code': 'not_admin',
        }), 403

    admin_audit.log('login_telegram', detail=f"telegram_id={tg_user['telegram_id']}", ip=_client_ip())
    return jsonify({'ok': True, 'token': make_admin_token()})


@bp.route('/revoke-sessions', methods=['POST'])
@admin_required
def revoke_sessions():
    revoke_all_sessions()
    admin_audit.log('revoke_sessions', ip=_client_ip())
    return jsonify({'ok': True})


@bp.route('/audit', methods=['GET'])
@admin_required
def audit_log():
    try:
        limit = min(200, max(1, int(request.args.get('limit', 100))))
    except ValueError:
        limit = 100
    return jsonify({'ok': True, 'items': admin_audit.recent(limit)})


@bp.route('/stats', methods=['GET'])
@admin_required
def stats():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT COUNT(*) AS n FROM users')
        total_users = cur.fetchone()['n']

        today = to_tashkent(utc_now()).date()
        days_range = [today - timedelta(days=i) for i in range(13, -1, -1)]
        signup_buckets = {d.isoformat(): 0 for d in days_range}

        cur.execute('SELECT created_at, telegram_id, onboarded FROM users')
        users_today = users_7d = telegram_users = onboarded_users = 0
        for row in cur.fetchall():
            if row['telegram_id']:
                telegram_users += 1
            if row['onboarded']:
                onboarded_users += 1
            dt = to_tashkent(as_utc(row['created_at']))
            if not dt:
                continue
            delta = (today - dt.date()).days
            if delta == 0:
                users_today += 1
            if 0 <= delta < 7:
                users_7d += 1
            key = dt.date().isoformat()
            if key in signup_buckets:
                signup_buckets[key] += 1

        cur.execute('SELECT COUNT(*) AS n FROM user_progress WHERE status = %s', (study.STATUS_COMPLETED,))
        total_completed = cur.fetchone()['n']

        completion_buckets = {d.isoformat(): 0 for d in days_range}
        cur.execute(
            'SELECT completed_at FROM user_progress WHERE status = %s AND completed_at IS NOT NULL',
            (study.STATUS_COMPLETED,)
        )
        completions_today = 0
        for row in cur.fetchall():
            dt = to_tashkent(as_utc(row['completed_at']))
            if not dt:
                continue
            if dt.date() == today:
                completions_today += 1
            key = dt.date().isoformat()
            if key in completion_buckets:
                completion_buckets[key] += 1

        cur.execute('SELECT COUNT(*) AS n FROM subject_purchases')
        total_purchases = cur.fetchone()['n']

        cur.execute('SELECT subject_key, COUNT(*) AS n FROM subject_purchases GROUP BY subject_key')
        purchases_by_subject = {row['subject_key']: row['n'] for row in cur.fetchall()}

        cur.execute(
            'SELECT chosen_subject_key, COUNT(*) AS n FROM users '
            'WHERE chosen_subject_key IS NOT NULL GROUP BY chosen_subject_key'
        )
        chosen_by_subject = {row['chosen_subject_key']: row['n'] for row in cur.fetchall()}

        subjects = []
        for key, meta in cur_mod.SUBJECT_CATALOG.items():
            subjects.append({
                'key': key,
                'name': meta['name'],
                'chosen_free': chosen_by_subject.get(key, 0),
                'purchases': purchases_by_subject.get(key, 0),
            })
        subjects.sort(key=lambda s: -(s['chosen_free'] + s['purchases']))

        return jsonify({
            'ok': True,
            'total_users': total_users,
            'users_today': users_today,
            'users_7d': users_7d,
            'telegram_users': telegram_users,
            'other_users': total_users - telegram_users,
            'onboarded_users': onboarded_users,
            'total_completed_topics': total_completed,
            'completions_today': completions_today,
            'total_purchases': total_purchases,
            # Haqiqiy tushum — admin tasdiqlagan to'lovlar (paket va promo-kod chegirmalari bilan)
            'revenue': payments.overview(cur)['all']['sum'],
            'subject_price': study.SUBJECT_PRICE,
            'subjects': subjects,
            'signups_14d': [{'date': d.isoformat(), 'n': signup_buckets[d.isoformat()]} for d in days_range],
            'completions_14d': [{'date': d.isoformat(), 'n': completion_buckets[d.isoformat()]} for d in days_range],
            'bot_configured': bool(BOT_TOKEN),
        })
    finally:
        cur.close()
        conn.close()


@bp.route('/stats/detail', methods=['GET'])
@admin_required
def stats_detail():
    """Batafsil statistika: faol o'quvchilar, qaytganlar, mashhur fanlar, do'kon konversiyasi."""
    try:
        days = int(request.args.get('days', 30))
    except ValueError:
        days = 30
    conn = get_connection()
    cur = conn.cursor()
    try:
        return jsonify(dict(analytics.report(cur, days), ok=True))
    finally:
        cur.close()
        conn.close()


@bp.route('/users', methods=['GET'])
@admin_required
def users_list():
    q = (request.args.get('q') or '').strip().lower()
    purchased_only = request.args.get('purchased_only') == '1'
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1
    per_page = 30
    offset = (page - 1) * per_page

    conn = get_connection()
    cur = conn.cursor()
    try:
        where_parts = []
        params = []
        if q:
            where_parts.append("(LOWER(name) LIKE %s OR LOWER(COALESCE(email, '')) LIKE %s)")
            like = f'%{q}%'
            params += [like, like]
        if purchased_only:
            where_parts.append('EXISTS (SELECT 1 FROM subject_purchases sp WHERE sp.user_id = users.id)')
        where = ('WHERE ' + ' AND '.join(where_parts)) if where_parts else ''

        cur.execute(f'SELECT COUNT(*) AS n FROM users {where}', params)
        total = cur.fetchone()['n']

        cur.execute(
            f'''SELECT id, name, email, telegram_id, chosen_subject_key, onboarded, created_at
                FROM users {where}
                ORDER BY id DESC
                LIMIT %s OFFSET %s''',
            params + [per_page, offset]
        )
        rows = cur.fetchall()

        ids = [row['id'] for row in rows]
        completed_map, purchase_map = {}, {}
        if ids:
            placeholders = ','.join(['%s'] * len(ids))
            cur.execute(
                f'''SELECT user_id, COUNT(*) AS n FROM user_progress
                    WHERE user_id IN ({placeholders}) AND status = %s
                    GROUP BY user_id''',
                ids + [study.STATUS_COMPLETED]
            )
            completed_map = {row['user_id']: row['n'] for row in cur.fetchall()}

            cur.execute(
                f'''SELECT user_id, COUNT(*) AS n FROM subject_purchases
                    WHERE user_id IN ({placeholders}) GROUP BY user_id''',
                ids
            )
            purchase_map = {row['user_id']: row['n'] for row in cur.fetchall()}

        users = [{
            'id': row['id'],
            'name': row['name'],
            'email': row['email'],
            'telegram_id': row['telegram_id'],
            'chosen_subject_key': row['chosen_subject_key'],
            'onboarded': bool(row['onboarded']),
            'created_at': iso_utc(as_utc(row['created_at'])),
            'completed_topics': completed_map.get(row['id'], 0),
            'purchases': purchase_map.get(row['id'], 0),
        } for row in rows]

        return jsonify({'ok': True, 'users': users, 'total': total, 'page': page, 'per_page': per_page})
    finally:
        cur.close()
        conn.close()


@bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def user_detail(user_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''SELECT id, name, email, telegram_id, username, grade, chosen_subject_key,
                      onboarded, created_at, photo_url
               FROM users WHERE id = %s''',
            (user_id,)
        )
        user = cur.fetchone()
        if not user:
            return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi'}), 404

        cur.execute('SELECT id, subject_key FROM topics')
        totals = {}
        for row in cur.fetchall():
            totals[row['subject_key']] = totals.get(row['subject_key'], 0) + 1

        cur.execute(
            '''SELECT t.subject_key, COUNT(*) AS n
               FROM user_progress p JOIN topics t ON t.id = p.topic_id
               WHERE p.user_id = %s AND p.status = %s
               GROUP BY t.subject_key''',
            (user_id, study.STATUS_COMPLETED)
        )
        completed = {row['subject_key']: row['n'] for row in cur.fetchall()}

        cur.execute('SELECT subject_key, purchased_at FROM subject_purchases WHERE user_id = %s', (user_id,))
        purchases = {row['subject_key']: iso_utc(as_utc(row['purchased_at'])) for row in cur.fetchall()}

        progress = []
        for key, meta in cur_mod.SUBJECT_CATALOG.items():
            total = totals.get(key, 0)
            if not total:
                continue
            progress.append({
                'key': key,
                'name': meta['name'],
                'completed': completed.get(key, 0),
                'total': total,
                'free_choice': key == user['chosen_subject_key'],
                'unlocked': key == user['chosen_subject_key'] or key in purchases,
                'purchased_at': purchases.get(key),
            })

        return jsonify({
            'ok': True,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'telegram_id': user['telegram_id'],
                'username': user['username'],
                'chosen_subject_key': user['chosen_subject_key'],
                'onboarded': bool(user['onboarded']),
                'created_at': iso_utc(as_utc(user['created_at'])),
                'photo_url': user['photo_url'],
            },
            'progress': progress,
        })
    finally:
        cur.close()
        conn.close()


@bp.route('/users/<int:user_id>/topics/<subject_key>', methods=['GET'])
@admin_required
def user_subject_topics(user_id, subject_key):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM users WHERE id = %s', (user_id,))
        if not cur.fetchone():
            return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi'}), 404

        cur.execute(
            '''SELECT t.id, t.title, t.duration, p.status, p.quiz_score, p.completed_at
               FROM topics t
               LEFT JOIN user_progress p ON p.topic_id = t.id AND p.user_id = %s
               WHERE t.subject_key = %s
               ORDER BY t.grade, t.seq''',
            (user_id, subject_key)
        )
        topics = [{
            'id': r['id'],
            'seq': i,
            'title': r['title'],
            'duration': r['duration'],
            'status': r['status'] or 'locked',
            'quiz_score': r['quiz_score'],
            'completed_at': iso_utc(as_utc(r['completed_at'])),
        } for i, r in enumerate(cur.fetchall(), start=1)]

        return jsonify({'ok': True, 'topics': topics, 'subject_name': cur_mod.subject_meta(subject_key)['name']})
    finally:
        cur.close()
        conn.close()


@bp.route('/users/<int:user_id>/unlock', methods=['POST'])
@admin_required
def grant_unlock(user_id):
    body = request.get_json(silent=True) or {}
    subject_key = (body.get('subject_key') or '').strip()
    if subject_key not in cur_mod.SUBJECT_CATALOG:
        return jsonify({'ok': False, 'error': "Noto'g'ri fan"}), 400

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM users WHERE id = %s', (user_id,))
        if not cur.fetchone():
            return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi'}), 404
        cur.execute(
            'INSERT INTO subject_purchases (user_id, subject_key) VALUES (%s, %s) '
            'ON CONFLICT (user_id, subject_key) DO NOTHING',
            (user_id, subject_key)
        )
        conn.commit()
        admin_audit.log('grant_unlock', detail=f'user_id={user_id} subject={subject_key}', ip=_client_ip())
        return jsonify({'ok': True})
    finally:
        cur.close()
        conn.close()


@bp.route('/users/<int:user_id>/unlock/<subject_key>', methods=['DELETE'])
@admin_required
def revoke_unlock(user_id, subject_key):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'DELETE FROM subject_purchases WHERE user_id = %s AND subject_key = %s',
            (user_id, subject_key)
        )
        conn.commit()
        admin_audit.log('revoke_unlock', detail=f'user_id={user_id} subject={subject_key}', ip=_client_ip())
        return jsonify({'ok': True})
    finally:
        cur.close()
        conn.close()


@bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, name FROM users WHERE id = %s', (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi'}), 404
        cur.execute('DELETE FROM user_progress WHERE user_id = %s', (user_id,))
        cur.execute('DELETE FROM subject_purchases WHERE user_id = %s', (user_id,))
        cur.execute('DELETE FROM tokens WHERE user_id = %s', (user_id,))
        # O'yin ma'lumotlari: avval faol roomlardan to'g'ri chiqariladi (hostlik
        # boshqaga o'tadi), keyin natijalar reytingda egasiz qolmasligi uchun o'chiriladi
        game_rooms.leave_all(cur, user_id, clock.now_ms())
        for table in ('game_room_players', 'game_answers', 'game_results', 'game_queue', 'game_presence',
                      'game_topic_stats', 'notify_log', 'daily_answers', 'user_achievements', 'user_photos',
                      'personal_topics', 'premium_log', 'activity_days'):
            cur.execute(f'DELETE FROM {table} WHERE user_id = %s', (user_id,))
        # Hamkor bo'lsa — kodi o'chiriladi (sotuv va to'lov tarixi pul hisobi sifatida qoladi)
        cur.execute('UPDATE promo_codes SET active = 0 WHERE partner_user_id = %s', (user_id,))
        dostlar.cleanup_user(cur, user_id)
        jurnal.cleanup_user(cur, user_id)
        marafon.cleanup_user(cur, user_id)
        cur.execute('DELETE FROM game_chances WHERE user_id = %s', (user_id,))
        cur.execute('DELETE FROM game_chance_state WHERE user_id = %s', (user_id,))
        cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        admin_audit.log('delete_user', detail=f'user_id={user_id} name={user["name"]}', ip=_client_ip())
        return jsonify({'ok': True})
    finally:
        cur.close()
        conn.close()


@bp.route('/subjects', methods=['GET'])
@admin_required
def subjects_list():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT subject_key, COUNT(*) AS n FROM topics GROUP BY subject_key')
        topic_counts = {row['subject_key']: row['n'] for row in cur.fetchall()}

        cur.execute('SELECT subject_key, COUNT(*) AS n FROM subject_purchases GROUP BY subject_key')
        purchase_counts = {row['subject_key']: row['n'] for row in cur.fetchall()}

        cur.execute(
            'SELECT chosen_subject_key, COUNT(*) AS n FROM users '
            'WHERE chosen_subject_key IS NOT NULL GROUP BY chosen_subject_key'
        )
        chosen_counts = {row['chosen_subject_key']: row['n'] for row in cur.fetchall()}

        cur.execute(
            '''SELECT t.subject_key, COUNT(*) AS n FROM user_progress p
               JOIN topics t ON t.id = p.topic_id
               WHERE p.status = %s GROUP BY t.subject_key''',
            (study.STATUS_COMPLETED,)
        )
        completed_counts = {row['subject_key']: row['n'] for row in cur.fetchall()}

        subjects = []
        for key, meta in cur_mod.SUBJECT_CATALOG.items():
            purchases = purchase_counts.get(key, 0)
            subjects.append({
                'key': key,
                'name': meta['name'],
                'icon': meta.get('icon'),
                'color': meta.get('color'),
                'topics': topic_counts.get(key, 0),
                'chosen_free': chosen_counts.get(key, 0),
                'purchases': purchases,
                'completed_topics': completed_counts.get(key, 0),
                'revenue': purchases * study.SUBJECT_PRICE,
            })

        return jsonify({'ok': True, 'subjects': subjects, 'subject_price': study.SUBJECT_PRICE})
    finally:
        cur.close()
        conn.close()


@bp.route('/subjects/<subject_key>/topics', methods=['GET'])
@admin_required
def subject_topics(subject_key):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'SELECT id, title, duration FROM topics WHERE subject_key = %s ORDER BY grade, seq',
            (subject_key,)
        )
        rows = cur.fetchall()
        edited = lesson_edit.overrides(cur)
        topics = [{
            'id': r['id'], 'seq': i,          # fan bo'yicha ketma-ket raqam (o'quvchi ko'radigandek)
            'title': r['title'], 'duration': r['duration'], 'edited': r['id'] in edited,
        } for i, r in enumerate(rows, start=1)]
        return jsonify({'ok': True, 'topics': topics, 'subject_name': cur_mod.subject_meta(subject_key)['name']})
    finally:
        cur.close()
        conn.close()


@bp.route('/topics/<topic_id>', methods=['GET'])
@admin_required
def topic_get(topic_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        topic = lesson_edit.get(cur, topic_id)
        if not topic:
            return jsonify({'ok': False, 'error': 'Mavzu topilmadi'}), 404
        return jsonify({'ok': True, 'topic': topic})
    finally:
        cur.close()
        conn.close()


@bp.route('/topics/<topic_id>', methods=['PUT'])
@admin_required
def topic_save(topic_id):
    """Mavzu matni va test savollarini saqlash (kod yangilansa ham saqlanib qoladi)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        topic = lesson_edit.save(cur, conn, topic_id, request.get_json(silent=True) or {})
    except lesson_edit.EditError as exc:
        conn.rollback()
        return jsonify({'ok': False, 'error': exc.message}), 400
    finally:
        cur.close()
        conn.close()
    admin_audit.log('topic_edit', detail=f'{topic_id}: {topic["title"]}', ip=_client_ip())
    return jsonify({'ok': True, 'topic': topic})


@bp.route('/topics/<topic_id>/reset', methods=['POST'])
@admin_required
def topic_reset(topic_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        topic = lesson_edit.reset(cur, conn, topic_id)
    except lesson_edit.EditError as exc:
        conn.rollback()
        return jsonify({'ok': False, 'error': exc.message}), 400
    finally:
        cur.close()
        conn.close()
    admin_audit.log('topic_reset', detail=topic_id, ip=_client_ip())
    return jsonify({'ok': True, 'topic': topic})


@bp.route('/activity', methods=['GET'])
@admin_required
def activity_feed():
    try:
        limit = min(100, max(1, int(request.args.get('limit', 50))))
    except ValueError:
        limit = 50

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''SELECT p.completed_at, u.id AS user_id, u.name, t.subject_key, t.title
               FROM user_progress p
               JOIN users u ON u.id = p.user_id
               JOIN topics t ON t.id = p.topic_id
               WHERE p.status = %s AND p.completed_at IS NOT NULL
               ORDER BY p.completed_at DESC
               LIMIT %s''',
            (study.STATUS_COMPLETED, limit)
        )
        items = []
        for row in cur.fetchall():
            meta = cur_mod.subject_meta(row['subject_key'])
            items.append({
                'user_id': row['user_id'],
                'user_name': row['name'],
                'subject_name': meta['name'],
                'topic_title': row['title'],
                'completed_at': iso_utc(as_utc(row['completed_at'])),
            })
        return jsonify({'ok': True, 'items': items})
    finally:
        cur.close()
        conn.close()


@bp.route('/broadcast', methods=['POST'])
@admin_required
def broadcast_start():
    """Ommaviy xabarni fonda boshlaydi va darhol javob qaytaradi — jarayonni
    GET /broadcast/<id> orqali kuzatiladi (broadcast.py)."""
    if not BOT_TOKEN:
        return jsonify({'ok': False, 'error': "BOT_TOKEN sozlanmagan — bot ulanmagan"}), 503
    message = ((request.get_json(silent=True) or {}).get('message') or '').strip()
    conn = get_connection()
    cur = conn.cursor()
    try:
        info = broadcast.start(cur, conn, message)
    except broadcast.BroadcastError as exc:
        return jsonify({'ok': False, 'error': exc.message}), exc.http_status
    finally:
        cur.close()
        conn.close()
    admin_audit.log('broadcast', detail=f'id={info["id"]} total={info["total"]} message={message[:120]!r}',
                    ip=_client_ip())
    return jsonify(dict(info, ok=True))


@bp.route('/broadcast/<int:bid>', methods=['GET'])
@admin_required
def broadcast_status(bid):
    conn = get_connection()
    cur = conn.cursor()
    try:
        info = broadcast.get(cur, bid)
    finally:
        cur.close()
        conn.close()
    if not info:
        return jsonify({'ok': False, 'error': 'Topilmadi'}), 404
    return jsonify(dict(info, ok=True))


# ───────────────────────── Tizim: zaxira nusxa va xatolar ─────────────────────────

@bp.route('/system', methods=['GET'])
@admin_required
def system_info():
    conn = get_connection()
    cur = conn.cursor()
    try:
        return jsonify({
            'ok': True,
            'bot': bool(BOT_TOKEN),
            'owners': len(admin_auth.ADMIN_TELEGRAM_IDS),
            'backup_hour': backup.BACKUP_HOUR,
            'backups': backup.history(cur),
            'errors': alerts.recent(cur),
            'error_counts': alerts.counts(cur),
            'channel_url': site_settings.channel_url(cur),
        })
    finally:
        cur.close()
        conn.close()


@bp.route('/channel', methods=['POST'])
@admin_required
def set_channel():
    """"Biz haqimizda" bosilganda ochiladigan Telegram kanal (bo'sh — o'chiriladi)."""
    try:
        url = site_settings.normalize_channel((request.get_json(silent=True) or {}).get('url'))
    except ValueError as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 400
    conn = get_connection()
    cur = conn.cursor()
    try:
        site_settings.put(cur, conn, site_settings.CHANNEL_KEY, url)
    finally:
        cur.close()
        conn.close()
    admin_audit.log('channel_set', detail=url or "o'chirildi", ip=_client_ip())
    return jsonify({'ok': True, 'channel_url': url})


@bp.route('/backup', methods=['POST'])
@admin_required
def backup_now():
    """Hozir zaxira nusxa olish — fayl egalarning Telegram chatiga boradi."""
    if not BOT_TOKEN:
        return jsonify({'ok': False, 'error': "BOT_TOKEN sozlanmagan — faylni yuborib bo'lmaydi"}), 503
    if not rate_limit.hit('backup_now', 6, 3600):
        return jsonify({'ok': False, 'error': "Soatiga 6 martadan ko'p emas. Birozdan keyin urinib ko'ring."}), 429
    info = backup.run('manual')
    admin_audit.log('backup_now', detail=f'size={info["size"]} rows={info["rows"]} sent={info["sent"]}',
                    ip=_client_ip())
    return jsonify(dict(info, ok=True))


@bp.route('/backup/download', methods=['POST'])
@admin_required
def backup_download():
    """To'liq zaxira nusxani (barcha jadvallar, sessiyalar va darslar ham) fayl sifatida
    yuklab berish — bazani boshqa serverga ko'chirish uchun. Faqat egasi: admin paroli
    qayta so'raladi (Telegram orqali kirgan qo'shimcha adminlar ham ololmaydi)."""
    password = str((request.get_json(silent=True) or {}).get('password') or '')
    if not ADMIN_PASSWORD or not hmac.compare_digest(password, ADMIN_PASSWORD):
        return jsonify({'ok': False, 'error': "Parol noto'g'ri"}), 403
    if not rate_limit.hit('backup_download', 10, 3600):
        return jsonify({'ok': False, 'error': "Soatiga 10 martadan ko'p emas."}), 429
    conn = get_connection()
    cur = conn.cursor()
    try:
        data = backup.dump(cur, full=True)
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    blob = backup.pack(data)
    rows = sum(len(t['rows']) for t in data['tables'].values())
    admin_audit.log('backup_download', detail=f'size={len(blob)} tables={len(data["tables"])} rows={rows}',
                    ip=_client_ip())
    stamp = data['created'][:16].replace(':', '').replace('T', '-')
    return Response(blob, mimetype='application/gzip', headers={
        'Content-Disposition': f'attachment; filename="bilimsari-toliq-{stamp}.json.gz"',
        'Cache-Control': 'no-store', 'X-Tables': str(len(data['tables'])), 'X-Rows': str(rows),
    })


@bp.route('/errors/test', methods=['POST'])
@admin_required
def errors_test():
    if not rate_limit.hit('errors_test', 5, 3600):
        return jsonify({'ok': False, 'error': "Juda ko'p urinish. Birozdan keyin qayta urinib ko'ring."}), 429
    sent = alerts.send_test()
    if not sent:
        return jsonify({'ok': False, 'error': "Xabar yuborilmadi — egasi botda /start bosganini tekshiring."}), 502
    return jsonify({'ok': True, 'sent': sent})


@bp.route('/errors/clear', methods=['POST'])
@admin_required
def errors_clear():
    conn = get_connection()
    cur = conn.cursor()
    try:
        alerts.clear(cur, conn)
    finally:
        cur.close()
        conn.close()
    admin_audit.log('errors_clear', ip=_client_ip())
    return jsonify({'ok': True})


# ───────────────────────── Adminlar ─────────────────────────

def _admins_payload(cur):
    extra = {}
    cur.execute('SELECT telegram_id, name FROM bot_admins')
    for r in cur.fetchall():
        extra[int(r['telegram_id'])] = r['name']
    ids = sorted(set(extra) | admin_auth.ADMIN_TELEGRAM_IDS)
    names = {}
    if ids:
        marks = ', '.join(['%s'] * len(ids))
        cur.execute(f'SELECT telegram_id, name, username FROM users WHERE telegram_id IN ({marks})', ids)
        names = {int(r['telegram_id']): r for r in cur.fetchall()}
    return [{
        'telegram_id': tid,
        'name': (names.get(tid) or {}).get('name') or extra.get(tid) or 'Admin',
        'username': (names.get(tid) or {}).get('username'),
        'owner': admin_auth.is_owner(tid),
    } for tid in ids]


@bp.route('/admins', methods=['GET'])
@admin_required
def admins_list():
    conn = get_connection()
    cur = conn.cursor()
    try:
        return jsonify({'ok': True, 'admins': _admins_payload(cur)})
    finally:
        cur.close()
        conn.close()


@bp.route('/admins', methods=['POST'])
@admin_required
def admins_add():
    """Admin qo'shish: @username, Telegram ID yoki ilovadagi o'quvchi ID si.
    Odam botda /start bosgan bo'lishi kerak — aks holda unga cheklar yetib bormaydi."""
    who = str((request.get_json(silent=True) or {}).get('who') or '').strip()
    conn = get_connection()
    cur = conn.cursor()
    try:
        row = None
        if who.startswith('@') or (who and not who.isdigit()):
            cur.execute('SELECT id, name, telegram_id FROM users WHERE LOWER(username) = %s AND telegram_id IS NOT NULL',
                        (who.lstrip('@').lower(),))
            row = cur.fetchone()
        elif who.isdigit():
            cur.execute('SELECT id, name, telegram_id FROM users WHERE telegram_id = %s', (int(who),))
            row = cur.fetchone()
            if not row:
                cur.execute('SELECT id, name, telegram_id FROM users WHERE id = %s AND telegram_id IS NOT NULL',
                            (int(who),))
                row = cur.fetchone()
        if not row:
            return jsonify({'ok': False, 'error': "Bunday foydalanuvchi topilmadi. U BilimSari'ni Telegram orqali "
                                                  "ochgan bo'lishi kerak (@username, Telegram ID yoki ilovadagi ID)."}), 404
        tid = int(row['telegram_id'])
        if admin_auth.is_admin_telegram(tid):
            return jsonify({'ok': False, 'error': 'Bu odam allaqachon admin.'}), 409
        cur.execute('INSERT INTO bot_admins (telegram_id, name, added_ms) VALUES (%s, %s, %s)',
                    (tid, row['name'], clock.now_ms()))
        conn.commit()
        admin_auth.extra_admin_ids(refresh=True)
        ok, _ = tgbot.send(tid, "👨‍💼 Siz <b>BilimSari</b> admini qilib tayinlandingiz.\n"
                                "Endi to'lov cheklari va o'quvchilar savollari sizga ham keladi.",
                           'Admin panel', 'admin.html')
        admin_audit.log('admin_add', detail=f'telegram_id={tid} name={row["name"]}', ip=_client_ip())
        return jsonify({'ok': True, 'admins': _admins_payload(cur), 'notified': ok})
    finally:
        cur.close()
        conn.close()


@bp.route('/admins/<int:tid>', methods=['DELETE'])
@admin_required
def admins_remove(tid):
    if admin_auth.is_owner(tid):
        return jsonify({'ok': False, 'error': "Asosiy adminni (ega) olib tashlab bo'lmaydi."}), 400
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM bot_admins WHERE telegram_id = %s', (tid,))
        removed = cur.rowcount
        conn.commit()
        admin_auth.extra_admin_ids(refresh=True)
        if not removed:
            return jsonify({'ok': False, 'error': 'Admin topilmadi'}), 404
        admin_audit.log('admin_remove', detail=f'telegram_id={tid}', ip=_client_ip())
        return jsonify({'ok': True, 'admins': _admins_payload(cur)})
    finally:
        cur.close()
        conn.close()


@bp.route('/users/<int:user_id>/message', methods=['POST'])
@admin_required
def message_user(user_id):
    """Admin o'quvchiga birinchi bo'lib yozadi (bot orqali). O'quvchining
    javobi odatdagidek jonli chat bo'lib adminlarga keladi."""
    text = str((request.get_json(silent=True) or {}).get('text') or '').strip()
    if not text:
        return jsonify({'ok': False, 'error': "Xabar matni bo'sh"}), 400
    if len(text) > 3500:
        return jsonify({'ok': False, 'error': 'Xabar juda uzun (3500 belgigacha)'}), 400
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT name, telegram_id FROM users WHERE id = %s', (user_id,))
        u = cur.fetchone()
    finally:
        cur.close()
        conn.close()
    if not u:
        return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi'}), 404
    if not u['telegram_id']:
        return jsonify({'ok': False, 'error': "Bu o'quvchi Telegram orqali kirmagan — unga yozib bo'lmaydi."}), 400
    ok, code = tgbot.send(u['telegram_id'], "👨‍💼 <b>Admin:</b>\n" + html.escape(text))
    if not ok:
        return jsonify({'ok': False, 'error': "Yuborilmadi — o'quvchi botni bloklagan yoki ishga tushirmagan."
                        if code == 403 else 'Telegram xatosi, qayta urinib ko\'ring.'}), 502
    admin_audit.log('message_user', detail=f'user_id={user_id} text={text[:80]!r}', ip=_client_ip())
    return jsonify({'ok': True})


@bp.route('/users/export.csv', methods=['GET'])
@admin_required
def export_users_csv():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''SELECT id, name, email, telegram_id, chosen_subject_key, onboarded, created_at
               FROM users ORDER BY id'''
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['ID', 'Ism', 'Email', 'Telegram ID', 'Tanlagan fan', 'Onboarded', "Ro'yxatdan o'tgan"])
    for row in rows:
        writer.writerow([
            row['id'], row['name'], row['email'] or '', row['telegram_id'] or '',
            row['chosen_subject_key'] or '',
            'ha' if row['onboarded'] else "yo'q", iso_utc(as_utc(row['created_at'])) or '',
        ])
    return Response(buf.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=foydalanuvchilar.csv',
    })


@bp.route('/purchases/export.csv', methods=['GET'])
@admin_required
def export_purchases_csv():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''SELECT sp.user_id, sp.subject_key, sp.purchased_at, u.name, u.email, u.telegram_id
               FROM subject_purchases sp JOIN users u ON u.id = sp.user_id
               ORDER BY sp.purchased_at DESC'''
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Foydalanuvchi ID', 'Ism', 'Email/Telegram', 'Fan', 'Summasi', 'Sana'])
    for row in rows:
        meta = cur_mod.subject_meta(row['subject_key'])
        writer.writerow([
            row['user_id'], row['name'],
            row['email'] or (f"tg:{row['telegram_id']}" if row['telegram_id'] else ''),
            meta['name'], study.SUBJECT_PRICE, iso_utc(as_utc(row['purchased_at'])) or '',
        ])
    return Response(buf.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=tolovlar.csv',
    })


@bp.route('/purchases', methods=['GET'])
@admin_required
def purchases_list():
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1
    per_page = 40
    offset = (page - 1) * per_page

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT COUNT(*) AS n FROM subject_purchases')
        total = cur.fetchone()['n']

        cur.execute(
            '''SELECT sp.user_id, sp.subject_key, sp.purchased_at, u.name, u.email, u.telegram_id
               FROM subject_purchases sp
               JOIN users u ON u.id = sp.user_id
               ORDER BY sp.purchased_at DESC
               LIMIT %s OFFSET %s''',
            (per_page, offset)
        )
        purchases = []
        for row in cur.fetchall():
            meta = cur_mod.subject_meta(row['subject_key'])
            purchases.append({
                'user_id': row['user_id'],
                'user_name': row['name'],
                'user_email': row['email'],
                'telegram_id': row['telegram_id'],
                'subject_key': row['subject_key'],
                'subject_name': meta['name'],
                'purchased_at': iso_utc(as_utc(row['purchased_at'])),
                'amount': study.SUBJECT_PRICE,
            })

        return jsonify({
            'ok': True,
            'purchases': purchases,
            'total': total,
            'page': page,
            'per_page': per_page,
            'revenue_total': total * study.SUBJECT_PRICE,
        })
    finally:
        cur.close()
        conn.close()
