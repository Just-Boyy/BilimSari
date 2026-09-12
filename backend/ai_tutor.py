# -*- coding: utf-8 -*-
"""
BilimSari AI yordamchisi (Google Gemini).

Muhim: AI — QO'SHIMCHA yordamchi. Rasmiy dars matni curriculum/ papkasida
turadi, AI uni almashtirmaydi. AI faqat o'quvchi hozir o'qiyotgan
sinf + fan + mavzu doirasida tushuntiradi.
"""

import os
import time
from collections import defaultdict, deque

import requests
from flask import Blueprint, jsonify, request

import curriculum as cur_mod
import study
from auth_core import auth_required
from db import get_connection

bp = Blueprint('ai', __name__, url_prefix='/api/ai')

GOOGLE_AI_API_KEY = (
    os.environ.get('GOOGLE_AI_API_KEY')
    or os.environ.get('GEMINI_API_KEY')
    or os.environ.get('GOOGLE_API_KEY')
    or ''
)
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')

# Oddiy tezlik cheklovi: bitta foydalanuvchi daqiqada N ta so'rov
RATE_LIMIT = int(os.environ.get('AI_RATE_LIMIT', '12'))
RATE_WINDOW = 60
_hits = defaultdict(deque)


def _rate_ok(user_id) -> bool:
    now = time.time()
    q = _hits[user_id]
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return False
    q.append(now)
    return True


def _system_prompt(lang, grade=None, subject=None, topic=None):
    level = f"{grade}-sinf o'quvchisi" if grade else "maktab o'quvchisi"
    if lang == 'ru':
        base = (
            'Ты — дружелюбный помощник учителя платформы BilimSari. '
            f'Твой собеседник — {level}. Отвечай кратко, простыми словами, по-русски.'
        )
    elif lang == 'en':
        base = (
            'You are a friendly teaching assistant on the BilimSari platform. '
            f'You are talking to a {level}. Answer briefly and simply in English.'
        )
    else:
        base = (
            "Sen BilimSari platformasidagi do'stona o'qituvchi yordamchisisan. "
            f"Suhbatdoshing — {level}. Javobni QISQA, ODDIY o'zbek tilida yoz. "
            "Murakkab atamalardan qoch, hayotiy misollar keltir. "
            "Javob 200 so'zdan oshmasin."
        )

    if subject and topic:
        base += (
            f"\n\nO'quvchi hozir shu mavzuni o'qiyapti:\n"
            f"Fan: {subject}\nMavzu: {topic}\n"
            "FAQAT shu mavzu doirasida javob ber. Boshqa mavzuga o'tma. "
            "Yangi dars yaratma — mavjud mavzuni tushuntir."
        )
    base += "\n\nZararli yoki noto'g'ri maslahat berma. Savol o'qishga aloqasiz bo'lsa, xushmuomalalik bilan mavzuga qaytar."
    return base


def _topic_context(user_id, grade, subject_key, slug):
    """Mavzu matnini bazadan olib, AI uchun kontekst tayyorlaydi."""
    if not (grade and subject_key and slug):
        return None, None, None
    conn = get_connection()
    cur = conn.cursor()
    try:
        tid = cur_mod.topic_id(int(grade), subject_key, slug)
        cur.execute('SELECT * FROM topics WHERE id = %s', (tid,))
        row = cur.fetchone()
        if not row:
            return None, None, None
        meta = cur_mod.subject_meta(subject_key)
        blocks = study._json(row['lesson'], [])
        parts = []
        for b in blocks:
            if b.get('title'):
                parts.append(b['title'])
            if b.get('body'):
                parts.append(b['body'])
            if b.get('items'):
                parts.extend(b['items'])
        text = '\n'.join(parts)[:4000]
        return meta['name'], row['title'], text
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


def _call_gemini(system, user_content, max_tokens=900):
    if not GOOGLE_AI_API_KEY:
        return None, ('AI hozircha ulanmagan. Administrator GOOGLE_AI_API_KEY ni '
                      'sozlashi kerak (aistudio.google.com).')

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{GEMINI_MODEL}:generateContent'
    )
    payload = {
        'system_instruction': {'parts': [{'text': system}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_content}]}],
        'generationConfig': {'temperature': 0.6, 'maxOutputTokens': max_tokens},
    }
    try:
        r = requests.post(
            url,
            json=payload,
            headers={'x-goog-api-key': GOOGLE_AI_API_KEY},
            timeout=45,
        )
        data = r.json() if r.content else {}
        if r.status_code != 200:
            err = (data.get('error') or {}) if isinstance(data, dict) else {}
            detail = err.get('message') if isinstance(err, dict) else str(err)
            return None, f'AI xatosi ({r.status_code}): {detail or r.text[:200]}'
        cands = data.get('candidates') or []
        parts = ((cands[0] if cands else {}).get('content') or {}).get('parts') or []
        reply = ''.join(p.get('text', '') for p in parts if isinstance(p, dict)).strip()
        return (reply, None) if reply else (None, "AI bo'sh javob qaytardi")
    except requests.Timeout:
        return None, 'AI javob bermadi (vaqt tugadi). Qayta urinib ko\'ring.'
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


@bp.route('/tutor', methods=['POST'])
@auth_required
def tutor():
    """O'quvchining savoliga javob — hozirgi mavzu doirasida."""
    body = request.get_json(silent=True) or {}
    message = (body.get('message') or '').strip()
    lang = (body.get('lang') or 'uz')[:5]

    if not message:
        return jsonify({'ok': False, 'error': "Savolingizni yozing"}), 400
    if len(message) > 1500:
        return jsonify({'ok': False, 'error': 'Savol juda uzun'}), 400
    if not _rate_ok(request.user['id']):
        return jsonify({
            'ok': False,
            'error': "Juda ko'p so'rov yubordingiz. Bir daqiqadan so'ng urinib ko'ring.",
            'code': 'rate_limit',
        }), 429

    grade = body.get('grade') or request.user.get('grade')
    subject_name, topic_title, lesson_text = _topic_context(
        request.user['id'], grade, body.get('subject_key'), body.get('slug')
    )

    system = _system_prompt(lang, grade, subject_name, topic_title)
    user_content = message
    if lesson_text:
        user_content = (
            f"Dars matni (shu asosda javob ber):\n{lesson_text}\n\n"
            f"O'quvchining savoli:\n{message}"
        )

    reply, error = _call_gemini(system, user_content)
    if error:
        return jsonify({'ok': False, 'error': error, 'reply': None}), 502
    return jsonify({'ok': True, 'reply': reply})


@bp.route('/explain', methods=['POST'])
@auth_required
def explain():
    """
    «AI yordamida tushuntirish» tugmasi.

    Rasmiy darsni oddiyroq qilib qayta tushuntiradi. Bu QO'SHIMCHA material —
    rasmiy dars o'rnini bosmaydi va bazaga dars sifatida saqlanmaydi.
    """
    body = request.get_json(silent=True) or {}
    lang = (body.get('lang') or 'uz')[:5]
    mode = (body.get('mode') or 'simple')[:20]

    if not _rate_ok(request.user['id']):
        return jsonify({
            'ok': False,
            'error': "Juda ko'p so'rov yubordingiz. Bir daqiqadan so'ng urinib ko'ring.",
            'code': 'rate_limit',
        }), 429

    grade = body.get('grade') or request.user.get('grade')
    subject_name, topic_title, lesson_text = _topic_context(
        request.user['id'], grade, body.get('subject_key'), body.get('slug')
    )
    if not topic_title:
        return jsonify({'ok': False, 'error': 'Mavzu topilmadi'}), 404

    asks = {
        'simple': "Shu mavzuni yanada ODDIY qilib, boshqacha so'zlar bilan tushuntir. "
                  "Kichik bolaga aytayotgandek yoz.",
        'examples': "Shu mavzu bo'yicha 3 ta YANGI, oddiy misol yoz va ularni "
                    "qadam-baqadam yech.",
        'summary': "Shu mavzuning eng muhim 5 ta fikrini qisqa ro'yxat qilib yoz.",
    }
    ask = asks.get(mode, asks['simple'])

    system = _system_prompt(lang, grade, subject_name, topic_title)
    user_content = f"Rasmiy dars matni:\n{lesson_text}\n\nVazifa: {ask}"

    reply, error = _call_gemini(system, user_content, max_tokens=1100)
    if error:
        return jsonify({'ok': False, 'error': error, 'reply': None}), 502
    return jsonify({
        'ok': True,
        'reply': reply,
        'mode': mode,
        'topic': topic_title,
        'subject': subject_name,
        'disclaimer': "Bu — AI qo'shimcha tushuntirishi. Rasmiy dars yuqorida.",
    })


@bp.route('/status', methods=['GET'])
def status():
    return jsonify({'ok': True, 'enabled': bool(GOOGLE_AI_API_KEY), 'model': GEMINI_MODEL})
