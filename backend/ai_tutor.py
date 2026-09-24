# -*- coding: utf-8 -*-
"""
BilimSari AI yordamchisi (Google Gemini).

Muhim: AI — QO'SHIMCHA yordamchi. Rasmiy dars matni curriculum/ papkasida
turadi, AI uni almashtirmaydi. AI faqat o'quvchi hozir o'qiyotgan
sinf + fan + mavzu doirasida tushuntiradi.
"""

import os

import requests
from flask import Blueprint, jsonify, request

import curriculum as cur_mod
import rate_limit
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

# Oddiy tezlik cheklovi: bitta foydalanuvchi daqiqada N ta so'rov. Bazada
# saqlanadi (rate_limit.py) — gunicorn bir necha worker bilan ishlaganda ham
# real chegara aynan shu son bo'lib qoladi.
RATE_LIMIT = int(os.environ.get('AI_RATE_LIMIT', '12'))
RATE_WINDOW = 60


# ───────────────────────── Javoblar keshi ─────────────────────────
#
# "AI yordamida tushuntirish" tugmasidagi savol har doim bir xil (mavzu +
# rejim + til bo'yicha aniqlanadi) — turli o'quvchilar bir xil mavzuda bir
# xil tugmani bossa, Gemini'ga qayta-qayta bir xil so'rov yuborishning
# hojati yo'q. Birinchi so'ragan uchun javob generatsiya qilinadi va
# saqlanadi, qolganlar uchun bazadan darhol qaytariladi — na kvota
# sarflanadi, na kutish bo'ladi.

def ensure_cache_table(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ai_explanations (
            topic_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            lang TEXT NOT NULL,
            reply TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            PRIMARY KEY (topic_id, mode, lang)
        )
    ''')
    conn.commit()


def _get_cached_explanation(topic_id, mode, lang):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'SELECT reply FROM ai_explanations WHERE topic_id = %s AND mode = %s AND lang = %s',
            (topic_id, mode, lang),
        )
        row = cur.fetchone()
        return row['reply'] if row else None
    finally:
        cur.close()
        conn.close()


def _save_cached_explanation(topic_id, mode, lang, reply):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO ai_explanations (topic_id, mode, lang, reply) VALUES (%s, %s, %s, %s) '
            'ON CONFLICT (topic_id, mode, lang) DO UPDATE SET reply = EXCLUDED.reply',
            (topic_id, mode, lang, reply),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def _rate_ok(user_id) -> bool:
    return rate_limit.hit(f'ai:{user_id}', RATE_LIMIT, RATE_WINDOW)


def _system_prompt(lang, grade=None, subject=None, topic=None, qisqa=True):
    level = f"{grade}-sinf o'quvchisi" if grade else "maktab o'quvchisi"
    if lang == 'ru':
        uzunlik = 'Отвечай кратко (до 200 слов).' if qisqa else 'Javob to\'liq va batafsil bo\'lishi mumkin.'
        base = (
            'Ты — дружелюбный помощник учителя платформы BilimSari. '
            f'Твой собеседник — {level}. Отвечай простыми словами, по-русски. {uzunlik}'
        )
    elif lang == 'en':
        uzunlik = 'Keep it under 200 words.' if qisqa else 'A fuller, more detailed answer is fine here.'
        base = (
            'You are a friendly teaching assistant on the BilimSari platform. '
            f'You are talking to a {level}. Answer simply in English. {uzunlik}'
        )
    else:
        uzunlik = "Javob 200 so'zdan oshmasin." if qisqa else (
            "Javob to'liq va batafsil bo'lishi mumkin — uzunlikdan qo'rqma, "
            "lekin bo'sh gap bilan cho'zma, har bir gap foydali bo'lsin."
        )
        base = (
            "Sen BilimSari platformasidagi do'stona o'qituvchi yordamchisisan. "
            f"Suhbatdoshing — {level}. Javobni ODDIY o'zbek tilida yoz. "
            f"Murakkab atamalardan qoch, hayotiy misollar keltir. {uzunlik}"
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

    grade = body.get('grade') or request.user.get('grade')
    subject_key = body.get('subject_key')
    slug = body.get('slug')

    # Kesh — Gemini'ga murojaat qilishdan OLDIN tekshiriladi, shuning uchun
    # keshdan qaytgan javob tezlik cheklovini (rate limit) ham sarflamaydi.
    tid = cur_mod.topic_id(int(grade), subject_key, slug) if (grade and subject_key and slug) else None
    if tid:
        cached = _get_cached_explanation(tid, mode, lang)
        if cached:
            meta = cur_mod.subject_meta(subject_key)
            return jsonify({
                'ok': True,
                'reply': cached,
                'mode': mode,
                'subject': meta['name'],
                'disclaimer': "Bu — AI qo'shimcha tushuntirishi. Rasmiy dars yuqorida.",
                'cached': True,
            })

    if not _rate_ok(request.user['id']):
        return jsonify({
            'ok': False,
            'error': "Juda ko'p so'rov yubordingiz. Bir daqiqadan so'ng urinib ko'ring.",
            'code': 'rate_limit',
        }), 429

    subject_name, topic_title, lesson_text = _topic_context(request.user['id'], grade, subject_key, slug)
    if not topic_title:
        return jsonify({'ok': False, 'error': 'Mavzu topilmadi'}), 404

    asks = {
        'simple': "Shu mavzuni yanada ODDIY qilib, boshqacha so'zlar bilan tushuntir. "
                  "Kichik bolaga aytayotgandek yoz.",
        'full': "Shu mavzuni TO'LIQROQ va CHUQURROQ tushuntir — qo'shimcha tafsilotlar, "
                "nima uchun shunday ekanligi va qanday ishlashi haqida batafsil yoz. "
                "Rasmiy darsda aytilmagan foydali qo'shimchalar ber, lekin baribir tushunarli yoz.",
        'examples': "Shu mavzu bo'yicha 3 ta YANGI, oddiy misol yoz va ularni "
                    "qadam-baqadam yech.",
        'summary': "Shu mavzuning eng muhim 5 ta fikrini qisqa ro'yxat qilib yoz.",
    }
    ask = asks.get(mode, asks['simple'])

    system = _system_prompt(lang, grade, subject_name, topic_title, qisqa=(mode != 'full'))
    user_content = f"Rasmiy dars matni:\n{lesson_text}\n\nVazifa: {ask}"

    reply, error = _call_gemini(system, user_content, max_tokens=8192)
    if error:
        return jsonify({'ok': False, 'error': error, 'reply': None}), 502

    if tid:
        _save_cached_explanation(tid, mode, lang, reply)

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
