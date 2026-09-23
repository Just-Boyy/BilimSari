# -*- coding: utf-8 -*-
"""
BilimSari — o'qish API si (/api/study/*).

Barcha progress shu yerda tekshiriladi. Frontend faqat natijani ko'rsatadi —
qulf, 24 soatlik kutish va javoblarni baholash serverda hal qilinadi.
"""

import curriculum as cur_mod
import study
from auth_core import auth_required
from db import get_connection
from flask import Blueprint, jsonify, request

bp = Blueprint('study', __name__, url_prefix='/api/study')


def _conn():
    conn = get_connection()
    return conn, conn.cursor()


def _close(conn, cur):
    try:
        cur.close()
        conn.close()
    except Exception:
        pass


def _fail(exc: study.StudyError):
    payload = {'ok': False, 'error': exc.message, 'code': exc.code}
    payload.update(exc.extra)
    return jsonify(payload), exc.http_status


# DIQQAT: sinf tushunchasi olib tashlangan — barcha foydalanuvchilarga bitta
# umumiy dastur (barcha sinflardan yig'ilgan mavzular) ko'rsatiladi. Har bir
# mavzu o'zining asl `grade`sini saqlaydi (ID va tartib uchun ishlatiladi),
# lekin foydalanuvchidan endi sinf so'ralmaydi.


@bp.route('/grades', methods=['GET'])
def grades():
    """Eskirgan: endi ishlatilmaydi (sinf tanlash olib tashlangan)."""
    return jsonify({'ok': True, 'grades': cur_mod.grades_overview()})


@bp.route('/subjects', methods=['GET'])
@auth_required
def subjects():
    conn, cur = _conn()
    try:
        items = study.subjects_overview(cur, request.user['id'])
        return jsonify({
            'ok': True,
            'subjects': items,
            'empty_message': 'Hozircha fanlar tayyorlanmoqda. Tez orada qo\'shiladi.' if not items else '',
        })
    finally:
        _close(conn, cur)


@bp.route('/dashboard', methods=['GET'])
@auth_required
def dashboard():
    conn, cur = _conn()
    try:
        data = study.dashboard(cur, request.user['id'])
        data['ok'] = True
        data['needs_onboarding'] = (
            not bool(request.user.get('onboarded')) or not request.user.get('chosen_subject_key')
        )
        data['user'] = {
            'id': request.user['id'],
            'name': request.user.get('name'),
            'photo_url': request.user.get('photo_url'),
        }
        return jsonify(data)
    finally:
        _close(conn, cur)


@bp.route('/subjects/<subject_key>/choose', methods=['POST'])
@auth_required
def choose_subject(subject_key):
    conn, cur = _conn()
    try:
        study.choose_subject(cur, conn, request.user['id'], subject_key)
        return jsonify({'ok': True, 'chosen_subject_key': subject_key})
    except study.StudyError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/subjects/<subject_key>/unlock', methods=['POST'])
@auth_required
def unlock_subject(subject_key):
    """DEMO to'lov — hozircha haqiqiy to'lov tizimi yo'q, so'rov kelsa fan ochiladi."""
    conn, cur = _conn()
    try:
        study.unlock_subject(cur, conn, request.user['id'], subject_key)
        return jsonify({'ok': True, 'subject_key': subject_key})
    except study.StudyError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


def _grade_or_400(raw):
    """Endi bitta 'foydalanuvchi sinfi' yo'q — har bir mavzu o'z grade'ini
    o'zi bilan olib yuradi (frontend uni mavzular ro'yxatidan oladi)."""
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise study.StudyError(
            "Mavzu ma'lumoti yetarli emas (grade)", code='bad_topic', http_status=400
        )


# ───────────────────────── Mavzular ─────────────────────────

@bp.route('/topics/<subject_key>', methods=['GET'])
@auth_required
def topics(subject_key):
    conn, cur = _conn()
    try:
        if not study.is_subject_unlocked(cur, request.user['id'], subject_key):
            cur.execute('SELECT name FROM subjects WHERE subject_key = %s LIMIT 1', (subject_key,))
            row = cur.fetchone()
            return jsonify({
                'ok': False,
                'error': 'Bu fan qulflangan. Ochish uchun sotib oling.',
                'code': 'subject_locked',
                'subject_key': subject_key,
                'subject_name': (row or {}).get('name') or subject_key,
                'price': study.SUBJECT_PRICE,
            }), 403
        subject, items = study.subject_topics(cur, request.user['id'], subject_key)
        if subject is None:
            return jsonify({
                'ok': False,
                'error': "Bu fan topilmadi yoki mavzular hali tayyorlanmagan.",
                'code': 'empty_subject',
                'topics': [],
            }), 404
        done = sum(1 for t in items if t['state'] == study.STATUS_COMPLETED)
        return jsonify({
            'ok': True,
            'subject': {
                'key': subject['subject_key'],
                'name': subject['name'],
                'icon': subject['icon'],
                'image': subject.get('image'),
                'color': subject['color'],
            },
            'topics': items,
            'completed': done,
            'total': len(items),
            'percent': round(done * 100 / len(items)) if items else 0,
            'cooldown': study.cooldown_state(cur, request.user['id']),
        })
    finally:
        _close(conn, cur)


@bp.route('/topic/<subject_key>/<slug>', methods=['GET'])
@auth_required
def topic(subject_key, slug):
    conn, cur = _conn()
    try:
        grade = _grade_or_400(request.args.get('grade'))
        tid = cur_mod.topic_id(grade, subject_key, slug)
        data = study.topic_payload(cur, conn, request.user['id'], tid)
        data['ok'] = True
        return jsonify(data)
    except study.StudyError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/lesson-read', methods=['POST'])
@auth_required
def lesson_read():
    body = request.get_json(silent=True) or {}
    conn, cur = _conn()
    try:
        grade = _grade_or_400(body.get('grade'))
        tid = cur_mod.topic_id(grade, body.get('subject_key'), body.get('slug'))
        study.mark_lesson_read(cur, conn, request.user['id'], tid)
        return jsonify({'ok': True})
    except study.StudyError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


# ───────────────────────── Quiz ─────────────────────────

@bp.route('/quiz', methods=['POST'])
@auth_required
def quiz():
    body = request.get_json(silent=True) or {}
    conn, cur = _conn()
    try:
        grade = _grade_or_400(body.get('grade'))
        tid = cur_mod.topic_id(grade, body.get('subject_key'), body.get('slug'))
        result = study.grade_quiz(cur, conn, request.user['id'], tid, body.get('answers'))
        result['ok'] = True
        return jsonify(result)
    except study.StudyError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


# ───────────────────────── Uyga vazifa ─────────────────────────

@bp.route('/homework', methods=['POST'])
@auth_required
def homework():
    body = request.get_json(silent=True) or {}
    conn, cur = _conn()
    try:
        grade = _grade_or_400(body.get('grade'))
        tid = cur_mod.topic_id(grade, body.get('subject_key'), body.get('slug'))
        result = study.submit_homework(cur, conn, request.user['id'], tid, body.get('answers'))
        result['ok'] = True
        return jsonify(result)
    except study.StudyError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


# ───────────────────────── Kutish holati ─────────────────────────

@bp.route('/cooldown', methods=['GET'])
@auth_required
def cooldown():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'cooldown': study.cooldown_state(cur, request.user['id'])})
    finally:
        _close(conn, cur)


@bp.route('/leaderboard', methods=['GET'])
@auth_required
def leaderboard():
    conn, cur = _conn()
    try:
        data = study.leaderboard(cur, request.user['id'])
        data['ok'] = True
        return jsonify(data)
    finally:
        _close(conn, cur)
