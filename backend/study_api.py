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


def _require_grade(cur, user_id):
    grade = study.get_user_grade(cur, user_id)
    if not grade:
        raise study.StudyError(
            'Avval sinfingizni tanlang', code='no_grade', http_status=409
        )
    return grade


# ───────────────────────── Sinflar va fanlar ─────────────────────────

@bp.route('/grades', methods=['GET'])
def grades():
    """Onboarding: mavjud sinflar ro'yxati. Auth talab qilinmaydi."""
    return jsonify({'ok': True, 'grades': cur_mod.grades_overview()})


@bp.route('/grade', methods=['POST'])
@auth_required
def choose_grade():
    body = request.get_json(silent=True) or {}
    conn, cur = _conn()
    try:
        grade = study.set_user_grade(cur, conn, request.user['id'], body.get('grade'))
        return jsonify({'ok': True, 'grade': grade})
    except study.StudyError as exc:
        return _fail(exc)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': "Sinf noto'g'ri", 'code': 'bad_grade'}), 400
    finally:
        _close(conn, cur)


@bp.route('/subjects', methods=['GET'])
@auth_required
def subjects():
    conn, cur = _conn()
    try:
        grade = request.args.get('grade') or study.get_user_grade(cur, request.user['id'])
        if not grade:
            return jsonify({'ok': False, 'error': 'Avval sinfingizni tanlang',
                            'code': 'no_grade'}), 409
        items = study.subjects_overview(cur, request.user['id'], int(grade))
        return jsonify({
            'ok': True,
            'grade': int(grade),
            'subjects': items,
            'empty_message': (
                f'Hozircha {grade}-sinf uchun fanlar tayyorlanmoqda. '
                'Tez orada qo\'shiladi.'
            ) if not items else '',
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
        data['user'] = {
            'id': request.user['id'],
            'name': request.user.get('name'),
            'photo_url': request.user.get('photo_url'),
        }
        return jsonify(data)
    finally:
        _close(conn, cur)


# ───────────────────────── Mavzular ─────────────────────────

@bp.route('/topics/<subject_key>', methods=['GET'])
@auth_required
def topics(subject_key):
    conn, cur = _conn()
    try:
        grade = int(request.args.get('grade') or _require_grade(cur, request.user['id']))
        subject, items = study.subject_topics(cur, request.user['id'], grade, subject_key)
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
            'grade': grade,
            'subject': {
                'key': subject['subject_key'],
                'name': subject['name'],
                'icon': subject['icon'],
                'color': subject['color'],
            },
            'topics': items,
            'completed': done,
            'total': len(items),
            'percent': round(done * 100 / len(items)) if items else 0,
            'cooldown': study.cooldown_state(cur, request.user['id']),
        })
    except study.StudyError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


@bp.route('/topic/<subject_key>/<slug>', methods=['GET'])
@auth_required
def topic(subject_key, slug):
    conn, cur = _conn()
    try:
        grade = int(request.args.get('grade') or _require_grade(cur, request.user['id']))
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
        grade = int(body.get('grade') or _require_grade(cur, request.user['id']))
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
        grade = int(body.get('grade') or _require_grade(cur, request.user['id']))
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
        grade = int(body.get('grade') or _require_grade(cur, request.user['id']))
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
