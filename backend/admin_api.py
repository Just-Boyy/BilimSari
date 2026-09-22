# -*- coding: utf-8 -*-
"""
Admin panel API — foydalanuvchilar, fanlar, to'lovlar boshqaruvi.

Talabalar tizimidan butunlay alohida: alohida token turi (admin_auth.py),
o'z login yo'li (parol — ADMIN_PASSWORD muhit o'zgaruvchisi).
"""

import csv
import hmac
import io
import os
import time
from datetime import timedelta

import requests
from flask import Blueprint, Response, jsonify, request

import curriculum as cur_mod
import study
from admin_auth import ADMIN_PASSWORD, admin_required, make_admin_token
from db import as_utc, get_connection, iso_utc, to_tashkent, utc_now

bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')


@bp.route('/login', methods=['POST'])
def admin_login():
    if not ADMIN_PASSWORD:
        return jsonify({
            'ok': False,
            'error': "Admin paneli hali sozlanmagan (ADMIN_PASSWORD muhit o'zgaruvchisi yo'q)",
        }), 503

    body = request.get_json(silent=True) or {}
    password = body.get('password') or ''
    if not hmac.compare_digest(password, ADMIN_PASSWORD):
        return jsonify({'ok': False, 'error': "Parol noto'g'ri"}), 401

    return jsonify({'ok': True, 'token': make_admin_token()})


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

        cur.execute('SELECT grade, COUNT(*) AS n FROM users WHERE grade IS NOT NULL GROUP BY grade')
        by_grade = {str(row['grade']): row['n'] for row in cur.fetchall()}

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
            'revenue': total_purchases * study.SUBJECT_PRICE,
            'subject_price': study.SUBJECT_PRICE,
            'by_grade': by_grade,
            'subjects': subjects,
            'signups_14d': [{'date': d.isoformat(), 'n': signup_buckets[d.isoformat()]} for d in days_range],
            'completions_14d': [{'date': d.isoformat(), 'n': completion_buckets[d.isoformat()]} for d in days_range],
            'bot_configured': bool(BOT_TOKEN),
        })
    finally:
        cur.close()
        conn.close()


@bp.route('/users', methods=['GET'])
@admin_required
def users_list():
    q = (request.args.get('q') or '').strip().lower()
    grade_filter = request.args.get('grade')
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
        if grade_filter:
            try:
                grade_int = int(grade_filter)
            except ValueError:
                grade_int = None
            if grade_int is not None:
                where_parts.append('grade = %s')
                params.append(grade_int)
        if purchased_only:
            where_parts.append('EXISTS (SELECT 1 FROM subject_purchases sp WHERE sp.user_id = users.id)')
        where = ('WHERE ' + ' AND '.join(where_parts)) if where_parts else ''

        cur.execute(f'SELECT COUNT(*) AS n FROM users {where}', params)
        total = cur.fetchone()['n']

        cur.execute(
            f'''SELECT id, name, email, telegram_id, grade, chosen_subject_key, onboarded, created_at
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
            'grade': row['grade'],
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
                'grade': user['grade'],
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
        cur.execute('SELECT grade FROM users WHERE id = %s', (user_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi'}), 404
        grade = row['grade'] or 7

        cur.execute(
            '''SELECT t.id, t.seq, t.title, t.duration, p.status, p.quiz_score, p.completed_at
               FROM topics t
               LEFT JOIN user_progress p ON p.topic_id = t.id AND p.user_id = %s
               WHERE t.subject_key = %s AND t.grade = %s
               ORDER BY t.seq''',
            (user_id, subject_key, grade)
        )
        topics = [{
            'id': r['id'],
            'seq': r['seq'],
            'title': r['title'],
            'duration': r['duration'],
            'status': r['status'] or 'locked',
            'quiz_score': r['quiz_score'],
            'completed_at': iso_utc(as_utc(r['completed_at'])),
        } for r in cur.fetchall()]

        return jsonify({'ok': True, 'topics': topics, 'subject_name': cur_mod.subject_meta(subject_key)['name']})
    finally:
        cur.close()
        conn.close()


@bp.route('/users/<int:user_id>/grade', methods=['POST'])
@admin_required
def set_grade(user_id):
    body = request.get_json(silent=True) or {}
    grade = body.get('grade')
    if grade is not None:
        try:
            grade = int(grade)
        except (TypeError, ValueError):
            return jsonify({'ok': False, 'error': "Sinf raqam bo'lishi kerak"}), 400
        if grade not in cur_mod.GRADES:
            return jsonify({'ok': False, 'error': "Noto'g'ri sinf"}), 400

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM users WHERE id = %s', (user_id,))
        if not cur.fetchone():
            return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi'}), 404
        cur.execute('UPDATE users SET grade = %s WHERE id = %s', (grade, user_id))
        conn.commit()
        return jsonify({'ok': True})
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
        cur.execute('SELECT id FROM users WHERE id = %s', (user_id,))
        if not cur.fetchone():
            return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi'}), 404
        cur.execute('DELETE FROM user_progress WHERE user_id = %s', (user_id,))
        cur.execute('DELETE FROM subject_purchases WHERE user_id = %s', (user_id,))
        cur.execute('DELETE FROM tokens WHERE user_id = %s', (user_id,))
        cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
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
            'SELECT id, grade, seq, title, duration FROM topics WHERE subject_key = %s ORDER BY grade, seq',
            (subject_key,)
        )
        topics = [{
            'id': r['id'], 'grade': r['grade'], 'seq': r['seq'],
            'title': r['title'], 'duration': r['duration'],
        } for r in cur.fetchall()]
        return jsonify({'ok': True, 'topics': topics, 'subject_name': cur_mod.subject_meta(subject_key)['name']})
    finally:
        cur.close()
        conn.close()


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
def broadcast():
    body = request.get_json(silent=True) or {}
    message = (body.get('message') or '').strip()
    if not message:
        return jsonify({'ok': False, 'error': "Xabar matni bo'sh"}), 400
    if len(message) > 3500:
        return jsonify({'ok': False, 'error': 'Xabar juda uzun (3500 belgigacha)'}), 400
    if not BOT_TOKEN:
        return jsonify({'ok': False, 'error': "BOT_TOKEN sozlanmagan — bot ulanmagan"}), 503

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL')
        chat_ids = [row['telegram_id'] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    sent = failed = 0
    for chat_id in chat_ids:
        try:
            r = requests.post(url, json={'chat_id': chat_id, 'text': message}, timeout=10)
            if r.status_code == 200 and (r.json() or {}).get('ok'):
                sent += 1
            else:
                failed += 1
        except Exception:
            failed += 1
        time.sleep(0.05)

    return jsonify({'ok': True, 'sent': sent, 'failed': failed, 'total': len(chat_ids)})


@bp.route('/users/export.csv', methods=['GET'])
@admin_required
def export_users_csv():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''SELECT id, name, email, telegram_id, grade, chosen_subject_key, onboarded, created_at
               FROM users ORDER BY id'''
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['ID', 'Ism', 'Email', 'Telegram ID', 'Sinf', 'Tanlagan fan', 'Onboarded', "Ro'yxatdan o'tgan"])
    for row in rows:
        writer.writerow([
            row['id'], row['name'], row['email'] or '', row['telegram_id'] or '',
            row['grade'] or '', row['chosen_subject_key'] or '',
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
