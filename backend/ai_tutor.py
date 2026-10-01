# -*- coding: utf-8 -*-
"""
BilimSari AI yordamchisi (Google Gemini).

Muhim: AI — QO'SHIMCHA yordamchi. Rasmiy dars matni curriculum/ papkasida
turadi, AI uni almashtirmaydi. AI faqat o'quvchi hozir o'qiyotgan
sinf + fan + mavzu doirasida tushuntiradi.
"""

import json
import logging
import os
import re
import time

import requests
from flask import Blueprint, jsonify, request

import curriculum as cur_mod
import rate_limit
import til
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

# AI xizmatlari navbati: Gemini (o'zbek tilini eng yaxshi biladi) → OpenRouter'ning bepul
# modellari → DeepSeek (pullik, balans bo'lsa). Birida limit tugasa yoki band bo'lsa — keyingisiga.
#
# OpenRouter: bepul modellarga kuniga 50 so'rov (Toshkent 05:00 da yangilanadi), daqiqasiga 20.
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_MODELS = [m.strip() for m in os.environ.get(
    'OPENROUTER_MODELS',
    'google/gemma-4-31b-it:free,qwen/qwen3.8-27b:free,nvidia/nemotron-3-super-120b-a12b:free,openrouter/free',
).split(',') if m.strip()]
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
OPENROUTER_MAX_TOKENS = 16384

# DeepSeek — kunlik limiti yo'q, pul hisobdagi balansdan yechiladi (balans bo'lmasa — 402).
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-flash')
DEEPSEEK_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com').rstrip('/') + '/chat/completions'
DEEPSEEK_MAX_TOKENS = 8192

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
    # Sinf tushunchasi olib tashlangach (2026-09-30): eski prompt "7-sinf o'quvchisi" degan edi —
    # o'shanda saqlangan va sinf tilga olingan javoblar o'chiriladi (so'ralganda qayta yoziladi).
    # Faqat sanadan oldingilar — yangi javoblarga tegilmaydi.
    cur.execute("DELETE FROM ai_explanations WHERE created_at < '2026-09-30 18:30:00' "
                "AND (reply LIKE '%%-sinf%%' OR reply LIKE '%%класс%%' OR LOWER(reply) LIKE '%%grade%%')")
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


PREMIUM_ERROR = {'ok': False, 'error': 'AI tushuntirish faqat Bilim Premium bilan ishlaydi.',
                 'code': 'premium_required'}


def _premium_ok(user_id) -> bool:
    import premium
    conn = get_connection()
    cur = conn.cursor()
    try:
        return premium.is_active(premium.until(cur, user_id))
    finally:
        cur.close()
        conn.close()


def _personal_context(user_id, pid):
    import personal
    conn = get_connection()
    cur = conn.cursor()
    try:
        return personal.ai_context(cur, user_id, pid)
    finally:
        cur.close()
        conn.close()


def _rate_ok(user_id) -> bool:
    return rate_limit.hit(f'ai:{user_id}', RATE_LIMIT, RATE_WINDOW)


def _system_prompt(lang, subject=None, topic=None, qisqa=True):
    if lang == 'ru':
        uzunlik = 'Отвечай кратко (до 200 слов).' if qisqa else 'Javob to\'liq va batafsil bo\'lishi mumkin.'
        base = (
            'Ты — дружелюбный помощник учителя платформы BilimSari. '
            f'Твой собеседник — школьник. Отвечай простыми словами, по-русски. {uzunlik}'
        )
    elif lang == 'en':
        uzunlik = 'Keep it under 200 words.' if qisqa else 'A fuller, more detailed answer is fine here.'
        base = (
            'You are a friendly teaching assistant on the BilimSari platform. '
            f'You are talking to a school student. Answer simply in English. {uzunlik}'
        )
    else:
        uzunlik = "Javob 200 so'zdan oshmasin." if qisqa else (
            "Javob to'liq va batafsil bo'lishi mumkin — uzunlikdan qo'rqma, "
            "lekin bo'sh gap bilan cho'zma, har bir gap foydali bo'lsin."
        )
        base = (
            "Sen BilimSari platformasidagi do'stona o'qituvchi yordamchisisan. "
            f"Suhbatdoshing — maktab o'quvchisi. Javobni ODDIY o'zbek tilida yoz. "
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
        row = til.topic(row)                     # ruscha interfeysda — ruscha dars matni
        blocks = row['lesson']
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


# ───────────────────────── Gemini chaqiruvi ─────────────────────────
#
# Bepul tarifda har bir modelga kuniga cheklangan so'rov beriladi (masalan, 20 ta) va
# modellar ba'zan "band" (503) deydi. Shuning uchun bir nechta model navbat bilan
# ishlatiladi: limiti tugagan (429) model 30 daqiqaga, band (5xx) model 1 daqiqaga
# chetga olinadi va keyingisi sinaladi. Asosiy model — GEMINI_MODEL.
GEMINI_FALLBACK_MODELS = [m.strip() for m in os.environ.get(
    'GEMINI_FALLBACK_MODELS',
    'gemini-3.5-flash,gemini-3.7-flash,gemini-3.8-flash,gemini-flash-latest,gemini-3.1-flash-lite',
).split(',') if m.strip()]
RETRY_STATUSES = (429, 500, 502, 503, 504)
QUOTA_REST_S = 30 * 60
BUSY_REST_S = 60
_dam = {}          # model → shu vaqtgacha (time.time()) ishlatilmaydi


def _navbat(faqat_tayyor=False) -> list:
    barcha = [GEMINI_MODEL] + [m for m in GEMINI_FALLBACK_MODELS if m != GEMINI_MODEL]
    hozir = time.time()
    tayyor = [m for m in barcha if _dam.get(m, 0) <= hozir]
    return tayyor if faqat_tayyor else (tayyor or barcha)


def _matn(data) -> str:
    cands = data.get('candidates') or []
    parts = ((cands[0] if cands else {}).get('content') or {}).get('parts') or []
    return ''.join(p.get('text', '') for p in parts if isinstance(p, dict)).strip()


def _gemini(payload, parse, timeout, attempts, waits, budget):
    """Umumiy chaqiruv: (natija, xato). parse(matn) — natija yoki ValueError."""
    if not GOOGLE_AI_API_KEY:
        return None, ('AI hozircha ulanmagan. Administrator GOOGLE_AI_API_KEY ni '
                      'sozlashi kerak (aistudio.google.com).')
    oxir = time.time() + budget
    error = None
    for i in range(max(1, attempts)):
        qolgan = oxir - time.time()
        if qolgan < 3:
            break
        navbat = _navbat(faqat_tayyor=True)
        if not navbat:
            break                                   # hamma model limitda yoki band — keyingi xizmatga
        model = navbat[i % len(navbat)]
        retry = True
        try:
            r = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                              json=payload, headers={'x-goog-api-key': GOOGLE_AI_API_KEY},
                              timeout=min(timeout, qolgan))
        except requests.Timeout:
            error = "AI javob bermadi (vaqt tugadi). Qayta urinib ko'ring."
        except requests.RequestException as exc:
            error = str(exc)
        else:
            if r.status_code == 200:
                try:
                    return parse(_matn(r.json())), None
                except (ValueError, TypeError):
                    error = "AI javobi noto'g'ri formatda."
            else:
                error = f'AI xatosi ({r.status_code}, {model})'
                if r.status_code == 429:
                    _dam[model] = time.time() + QUOTA_REST_S
                elif r.status_code == 404:
                    _dam[model] = time.time() + 24 * 3600      # bunday model yo'q
                elif r.status_code in RETRY_STATUSES:
                    _dam[model] = time.time() + BUSY_REST_S
                else:
                    retry = False
                if r.status_code in (429, 404):
                    continue                                    # kutmasdan boshqa modelga
        if not retry:
            break
        if i + 1 < attempts:
            time.sleep(min(waits[min(i, len(waits) - 1)], max(0, oxir - time.time() - 3)))
    _kvota_ogohlantir()
    return None, error


_ogohlantirildi = {'kun': None}


def _kvota_ogohlantir():
    """Asosiy modelning kunlik limiti tugagan bo'lsa — egaga kuniga bir marta xabar (alerts.py)."""
    kun = time.strftime('%Y-%m-%d')
    if _dam.get(GEMINI_MODEL, 0) - time.time() > BUSY_REST_S and _ogohlantirildi['kun'] != kun:
        _ogohlantirildi['kun'] = kun
        logging.getLogger('bilimsari.ai').error(
            "Gemini: %s modelining bepul kunlik limiti tugadi (Toshkent vaqti bilan soat 12:00 da "
            "yangilanadi) — AI tushuntirish va shaxsiy darslar zaxira modellar va OpenRouter orqali "
            "ishlayapti.", GEMINI_MODEL)


def _text_parse(text):
    if not text:
        raise ValueError("bo'sh javob")
    return text


def _json_parse(text):
    t = re.sub(r'^```(?:json)?\s*|\s*```$', '', (text or '').strip())
    try:
        return json.loads(t)
    except ValueError:
        a, b = t.find('{'), t.rfind('}')             # ba'zi modellar JSON atrofiga izoh yozadi
        if a >= 0 and b > a:
            return json.loads(t[a:b + 1])
        raise


# ───────────────────────── OpenRouter va DeepSeek (OpenAI formati) ─────────────────────────

_ogohlantirildi_xizmat = {}


def _xizmat_ogohlantir(nom, code):
    """Kalit noto'g'ri (401) yoki balans tugagan (402) — egaga kuniga bir marta xabar."""
    kun = time.strftime('%Y-%m-%d')
    if _ogohlantirildi_xizmat.get(nom) != kun:
        _ogohlantirildi_xizmat[nom] = kun
        logging.getLogger('bilimsari.ai').error(
            '%s: %s — AI boshqa xizmatlar orqali ishlayapti.', nom,
            "balans tugadi (402), hisobni to'ldiring" if code == 402 else f"API kalit noto'g'ri ({code})")


def _chat(nom, url, kalit, modellar, system, user_content, max_tokens, max_out, json_mode, parse,
          timeout, attempts, waits, budget):
    """OpenAI formatidagi xizmat: modellar navbat bilan. (natija, xato). Kalit bo'lmasa — (None, None)."""
    if not kalit or not modellar:
        return None, None
    messages = ([{'role': 'system', 'content': system}] if system else []) + \
        [{'role': 'user', 'content': user_content}]
    headers = {'Authorization': f'Bearer {kalit}'}
    if 'openrouter' in url:
        headers.update({'HTTP-Referer': 'https://bilimsari.uz', 'X-Title': 'BilimSari'})
    oxir = time.time() + budget
    error = None
    for i in range(max(1, attempts)):
        qolgan = oxir - time.time()
        if qolgan < 3:
            break
        hozir = time.time()
        tayyor = [m for m in modellar if _dam.get(f'{nom}:{m}', 0) <= hozir] or modellar
        model = tayyor[i % len(tayyor)]
        body = {'model': model, 'messages': messages, 'stream': False,
                'max_tokens': min(int(max_tokens), max_out), 'temperature': 0.5 if json_mode else 0.6}
        if json_mode:
            body['response_format'] = {'type': 'json_object'}
        try:
            r = requests.post(url, json=body, headers=headers, timeout=min(timeout, qolgan))
        except requests.Timeout:
            error = "AI javob bermadi (vaqt tugadi). Qayta urinib ko'ring."
        except requests.RequestException as exc:
            error = str(exc)
        else:
            if r.status_code == 200:
                try:
                    data = r.json()
                    text = (((data.get('choices') or [{}])[0].get('message') or {}).get('content') or '').strip()
                    return parse(text), None
                except (ValueError, TypeError, AttributeError):
                    error = "AI javobi noto'g'ri formatda."
                    _dam[f'{nom}:{model}'] = time.time() + BUSY_REST_S
                    continue                                   # boshqa model yaxshiroq yozishi mumkin
            error = f'{nom} xatosi ({r.status_code}, {model})'
            if r.status_code in (401, 402):
                _xizmat_ogohlantir(nom, r.status_code)
                return None, error                          # kalit/balans — qayta urinish foydasiz
            if r.status_code == 429:
                _dam[f'{nom}:{model}'] = time.time() + QUOTA_REST_S
                continue
            if r.status_code in (400, 404):
                _dam[f'{nom}:{model}'] = time.time() + 10 * 60   # bu modelga mos kelmadi — boshqasi
                if len(modellar) > 1:
                    continue
                return None, error
            if r.status_code in RETRY_STATUSES:
                _dam[f'{nom}:{model}'] = time.time() + BUSY_REST_S
            else:
                return None, error
        if i + 1 < attempts:
            time.sleep(min(waits[min(i, len(waits) - 1)], max(0, oxir - time.time() - 3)))
    return None, error


def _ai(system, user_content, max_tokens, json_mode, parse, gemini_payload, timeout, attempts, waits, budget):
    """Xizmatlar navbati: Gemini → OpenRouter → DeepSeek. (natija, xato)."""
    if not (GOOGLE_AI_API_KEY or OPENROUTER_API_KEY or DEEPSEEK_API_KEY):
        return None, ('AI hozircha ulanmagan. Administrator GOOGLE_AI_API_KEY yoki OPENROUTER_API_KEY ni '
                      'sozlashi kerak.')
    oxir = time.time() + budget
    xato = None
    if GOOGLE_AI_API_KEY:
        res, xato = _gemini(gemini_payload, parse, timeout, attempts, waits, budget * 0.5)
        if res is not None:
            return res, None
    if OPENROUTER_API_KEY:
        res, err = _chat('OpenRouter', OPENROUTER_URL, OPENROUTER_API_KEY, OPENROUTER_MODELS, system, user_content,
                         max_tokens, OPENROUTER_MAX_TOKENS, json_mode, parse, timeout, max(4, attempts), waits,
                         max(5, (oxir - time.time()) * 0.8))
        if res is not None:
            return res, None
        xato = err or xato
    if DEEPSEEK_API_KEY:
        res, err = _chat('DeepSeek', DEEPSEEK_URL, DEEPSEEK_API_KEY, [DEEPSEEK_MODEL], system, user_content,
                         max_tokens, DEEPSEEK_MAX_TOKENS, json_mode, parse, timeout, 2, waits,
                         max(5, oxir - time.time()))
        if res is not None:
            return res, None
        xato = err or xato
    return None, xato


def _call_gemini(system, user_content, max_tokens=900):
    """Matnli javob (AI tushuntirish). So'rov ichida — 55 soniyagacha."""
    payload = {
        'system_instruction': {'parts': [{'text': system}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_content}]}],
        'generationConfig': {'temperature': 0.6, 'maxOutputTokens': max_tokens},
    }
    return _ai(system, user_content, max_tokens, False, _text_parse, payload,
               timeout=40, attempts=4, waits=(1, 2), budget=55)


def call_gemini_json(prompt, system=None, max_tokens=8192, timeout=120, attempts=3, waits=(2, 5, 10, 20), budget=600):
    """JSON javob kutiladigan so'rov (shaxsiy darslar). (obyekt, xato) qaytaradi."""
    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.5, 'maxOutputTokens': max_tokens,
                             'responseMimeType': 'application/json'},
    }
    if system:
        payload['system_instruction'] = {'parts': [{'text': system}]}
    return _ai(system, prompt, max_tokens, True, _json_parse, payload, timeout, attempts, waits, budget)


@bp.route('/tutor', methods=['POST'])
@auth_required
def tutor():
    """O'quvchining savoliga javob — hozirgi mavzu doirasida."""
    body = request.get_json(silent=True) or {}
    message = (body.get('message') or '').strip()
    lang = (body.get('lang') or 'uz')[:5]

    if not _premium_ok(request.user['id']):
        return jsonify(PREMIUM_ERROR), 403
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

    system = _system_prompt(lang, subject_name, topic_title)
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

    if not _premium_ok(request.user['id']):
        return jsonify(PREMIUM_ERROR), 403

    grade = body.get('grade') or request.user.get('grade')
    subject_key = body.get('subject_key')
    slug = body.get('slug')
    personal_id = body.get('personal_id')
    if personal_id:
        # Shaxsiy dars — faqat egasi uchun; kesh kaliti "p<id>"
        subject_name, topic_title, lesson_text = _personal_context(request.user['id'], int(personal_id))
        if not topic_title:
            return jsonify({'ok': False, 'error': 'Mavzu topilmadi'}), 404
        grade, subject_key, slug = None, None, None
        tid = f'p{int(personal_id)}'
        cached = _get_cached_explanation(tid, mode, lang)
        if cached:
            return jsonify({'ok': True, 'reply': cached, 'mode': mode, 'subject': subject_name, 'cached': True,
                            'disclaimer': "Bu — AI qo'shimcha tushuntirishi. Asosiy dars yuqorida."})

    # Kesh — Gemini'ga murojaat qilishdan OLDIN tekshiriladi, shuning uchun
    # keshdan qaytgan javob tezlik cheklovini (rate limit) ham sarflamaydi.
    if not personal_id:
        tid = cur_mod.topic_id(int(grade), subject_key, slug) if (grade and subject_key and slug) else None
    if tid and not personal_id:
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

    if not personal_id:
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

    system = _system_prompt(lang, subject_name, topic_title, qisqa=(mode != 'full'))
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
    navbat = [n for n, k in (('gemini', GOOGLE_AI_API_KEY), ('openrouter', OPENROUTER_API_KEY),
                             ('deepseek', DEEPSEEK_API_KEY)) if k]
    return jsonify({'ok': True, 'enabled': bool(navbat), 'providers': navbat, 'model': GEMINI_MODEL})
