# -*- coding: utf-8 -*-
"""
Admin boshqaruvi (admin panel → «Boshqaruv»):

  * Texnik tanaffus — botni va/yoki ilovani vaqtincha to'xtatish. Muddat tugasa o'zi yoqiladi.
    Adminlar to'xtatilgan paytda ham bot va ilovadan foydalanadi (sinab ko'rish uchun).
  * Funksiya kalitlari — o'yinlar, kun savoli, do'kon, AI, shaxsiy darslar, do'stlar, marafon,
    ro'yxatdan o'tish va eslatmalar alohida yopiladi.
  * Ilova ichidagi e'lon (bosh sahifa tepasida, o'zbekcha/ruscha).
  * O'quvchini bloklash (muddatli yoki muddatsiz) va admin bonusi (chaqmoq ±).

Holat pay_settings jadvalida bitta JSON kalitda. Har worker uni CACHE_S soniya keshlaydi — har so'rovda
bazaga bormaydi; admin o'zgartirsa, o'sha worker darhol, ikkinchisi ko'pi bilan CACHE_S da biladi.
"""

import html
import json
import logging
import re
import time
from datetime import datetime

from db import TASHKENT_TZ, add_column_if_missing, get_connection
from games import clock

logger = logging.getLogger('bilimsari.boshqaruv')

KEY = 'control'
CACHE_S = 5
BAN_FOREVER_MS = 253402300799000          # 9999-yil — "muddatsiz"
MAX_MINUTES = 30 * 24 * 60
TARGETS = ('bot', 'app')
KINDS = ('info', 'warn', 'success')

FEATURES = {
    'games': "Bilim o'yinlari (yangi o'yin boshlash)",
    'daily': 'Kun savoli',
    'shop': "Do'kon: fan va Premium sotib olish",
    'ai': 'AI tushuntirish',
    'personal': 'Shaxsiy darslar yaratish',
    'friends': "Do'stlar: so'rov, chaqiruv, shikoyat",
    'marathon': "Marafonga qo'shilish",
    'registration': "Yangi o'quvchilar ro'yxatdan o'tishi",
    'notifications': 'Bot eslatmalari va ommaviy xabarlar',
}
# Funksiya yopilganda qaysi so'rovlar rad etiladi. Ko'pchiligida faqat yangi amal (POST) yopiladi:
# boshlangan o'yin oxirigacha o'ynaladi, tarix va reytinglar ko'rinib turadi.
_FEATURE_RULES = [
    ('games', 'POST', re.compile(r'^/api/games/(rooms|rooms/join|rooms/[^/]+/(start|rematch)|matchmaking)$')),
    ('daily', None, re.compile(r'^/api/study/daily(/|$)')),
    ('shop', 'POST', re.compile(r'^/api/(pay/(orders|quote)|premium/order)$')),
    ('ai', 'POST', re.compile(r'^/api/ai/(tutor|explain)$')),
    ('personal', 'POST', re.compile(r'^/api/personal/(suggest|generate)$')),
    ('friends', 'POST', re.compile(r'^/api/friends/[^/]+$')),
    ('marathon', 'POST', re.compile(r'^/api/marathon/join$')),
]

# O'quvchiga ko'rinadigan xabarlar (ruschasi js/i18n.js da)
MSG_BANNED = 'Akkauntingiz bloklangan.'
MSG_MAINTENANCE = 'Ilovada texnik ishlar olib borilmoqda.'
MSG_FEATURE_OFF = "Bu bo'lim vaqtincha yopilgan. Birozdan keyin qayta urinib ko'ring."
MSG_REGISTRATION = "Hozircha yangi o'quvchilar qabul qilinmayapti. Birozdan keyin qayta urinib ko'ring."


class ControlError(Exception):
    def __init__(self, message, http_status=400):
        super().__init__(message)
        self.message = message
        self.http_status = http_status


def ensure_tables(cur, conn):
    add_column_if_missing(cur, conn, 'users', 'banned_until', 'BIGINT')
    add_column_if_missing(cur, conn, 'users', 'ban_reason', 'TEXT')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS chaqmoq_bonus (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            note TEXT,
            created_ms BIGINT NOT NULL
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_chaqmoq_bonus_user ON chaqmoq_bonus (user_id)')
    conn.commit()


def _clean(value, limit) -> str:
    """Ortiqcha bo'shliqlarsiz matn; qator ko'chishlari saqlanadi."""
    lines = [' '.join(x.split()) for x in str(value or '').replace('\r', '').split('\n')]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines).strip())[:limit]


def _minutes(value) -> int:
    try:
        n = int(value or 0)
    except (TypeError, ValueError):
        raise ControlError("Muddat noto'g'ri.")
    if n < 0 or n > MAX_MINUTES:
        raise ControlError("Muddat 0 dan 30 kungacha bo'lishi mumkin.")
    return n


# ───────────────────────── Holat (kesh bilan) ─────────────────────────

_cache = {'t': 0.0, 'v': None}


def _empty() -> dict:
    return {'pause': {}, 'features': {}, 'announcement': None}


def _load(cur) -> dict:
    cur.execute('SELECT value FROM pay_settings WHERE key = %s', (KEY,))
    row = cur.fetchone()
    try:
        data = json.loads(row['value']) if row and row['value'] else {}
    except (TypeError, ValueError):
        data = {}
    out = _empty()
    out.update({k: v for k, v in data.items() if k in out and v is not None})
    return out


def state(fresh=False) -> dict:
    """Joriy holat (o'zgartirmang — nusxa emas). Baza vaqtincha ishlamasa — oxirgi ma'lum holat."""
    now = time.monotonic()
    if not fresh and _cache['v'] is not None and now - _cache['t'] < CACHE_S:
        return _cache['v']
    try:
        conn = get_connection()
        cur = conn.cursor()
        try:
            value = _load(cur)
        finally:
            cur.close()
            conn.close()
    except Exception:  # noqa: BLE001
        logger.warning('Boshqaruv holati o\'qilmadi', exc_info=True)
        return _cache['v'] or _empty()
    _cache.update(t=now, v=value)
    return value


def version() -> str:
    """Boshqaruv holatining versiyasi (tanaffus, kalitlar, e'lon) — jonli yangilanish uchun."""
    import hashlib   # noqa: PLC0415
    return hashlib.md5(json.dumps(state(), sort_keys=True, default=str).encode()).hexdigest()[:12]


def _save(cur, conn, data):
    cur.execute('DELETE FROM pay_settings WHERE key = %s', (KEY,))
    cur.execute('INSERT INTO pay_settings (key, value) VALUES (%s, %s)', (KEY, json.dumps(data, ensure_ascii=False)))
    conn.commit()
    _cache.update(t=time.monotonic(), v=data)


def _is_admin_tg(tg_id) -> bool:
    import admin_auth   # noqa: PLC0415 — admin_auth → auth_core → boshqaruv aylanasidan qochish
    return admin_auth.is_admin_telegram(tg_id)


def is_admin_user(user) -> bool:
    return bool(user) and _is_admin_tg(user.get('telegram_id'))


# ───────────────────────── Texnik tanaffus ─────────────────────────

def pause_info(kind, now=None, st=None):
    """Faol tanaffus ({since_ms, until_ms, message}) yoki None — muddati o'tgan bo'lsa ham None."""
    p = (st or state()).get('pause', {}).get(kind)
    if not p:
        return None
    until = p.get('until_ms')
    if until and (now or clock.now_ms()) >= int(until):
        return None
    return p


def bot_paused(now=None) -> bool:
    return pause_info('bot', now) is not None


def app_paused(now=None) -> bool:
    return pause_info('app', now) is not None


def set_pause(cur, conn, targets, minutes, message, now=None) -> dict:
    now = now or clock.now_ms()
    targets = [t for t in (targets or []) if t in TARGETS]
    if not targets:
        raise ControlError("Nimani to'xtatishni tanlang: bot yoki ilova.")
    minutes = _minutes(minutes)
    entry = {'since_ms': now, 'until_ms': now + minutes * 60000 if minutes else None,
             'message': _clean(message, 500)}
    data = _load(cur)
    for t in targets:
        data['pause'][t] = dict(entry)
    _save(cur, conn, data)
    return data


def resume(cur, conn, targets) -> dict:
    data = _load(cur)
    for t in targets or TARGETS:
        data['pause'].pop(t, None)
    _save(cur, conn, data)
    return data


def notifications_off(now=None) -> bool:
    """Rejalashtirilgan eslatmalar va ommaviy xabarlar yuborilmaydi (bot to'xtatilgan yoki kalit o'chiq)."""
    return bot_paused(now) or not feature_on('notifications')


# ───────────────────────── Funksiya kalitlari ─────────────────────────

def feature_on(key, st=None) -> bool:
    return (st or state()).get('features', {}).get(key, True) is not False


def feature_for(method, path):
    for key, m, rx in _FEATURE_RULES:
        if (m is None or m == method) and rx.match(path or ''):
            return key
    return None


def set_features(cur, conn, changes) -> dict:
    if not isinstance(changes, dict) or not changes:
        raise ControlError("O'zgarish yo'q.")
    data = _load(cur)
    for key, on in changes.items():
        if key not in FEATURES:
            raise ControlError(f"Noma'lum funksiya: {key}")
        if on:
            data['features'].pop(key, None)
        else:
            data['features'][key] = False
    _save(cur, conn, data)
    return data


# ───────────────────────── E'lon ─────────────────────────

def set_announcement(cur, conn, text, text_ru, kind, minutes, now=None) -> dict:
    now = now or clock.now_ms()
    text = _clean(text, 600)
    if not text:
        raise ControlError("E'lon matnini yozing.")
    minutes = _minutes(minutes)
    data = _load(cur)
    data['announcement'] = {'id': now, 'text': text, 'text_ru': _clean(text_ru, 600) or None,
                            'kind': kind if kind in KINDS else 'info',
                            'until_ms': now + minutes * 60000 if minutes else None}
    _save(cur, conn, data)
    return data


def clear_announcement(cur, conn) -> dict:
    data = _load(cur)
    data['announcement'] = None
    _save(cur, conn, data)
    return data


def announcement(lang='uz', now=None):
    """O'quvchiga ko'rinadigan e'lon (tilida) yoki None."""
    a = state().get('announcement')
    if not a or (a.get('until_ms') and (now or clock.now_ms()) >= int(a['until_ms'])):
        return None
    text = a.get('text_ru') if lang == 'ru' and a.get('text_ru') else a.get('text')
    return {'id': a.get('id'), 'kind': a.get('kind') or 'info', 'text': text}


# ───────────────────────── Bloklash ─────────────────────────

def ban_info(user, now=None):
    """{'until_ms': ms | None (muddatsiz), 'reason'} yoki None."""
    until = (user or {}).get('banned_until')
    if not until or int(until) <= (now or clock.now_ms()):
        return None
    return {'until_ms': None if int(until) >= BAN_FOREVER_MS else int(until), 'reason': user.get('ban_reason') or ''}


def ban(cur, conn, uid, minutes, reason, now=None) -> dict:
    now = now or clock.now_ms()
    minutes = _minutes(minutes) if minutes else 0
    until = now + minutes * 60000 if minutes else BAN_FOREVER_MS
    reason = _clean(reason, 300)
    cur.execute('UPDATE users SET banned_until = %s, ban_reason = %s WHERE id = %s', (until, reason or None, uid))
    if cur.rowcount != 1:
        raise ControlError('Foydalanuvchi topilmadi.', 404)
    conn.commit()
    _banned['t'] = 0.0
    return {'until_ms': None if until >= BAN_FOREVER_MS else until, 'reason': reason}


def unban(cur, conn, uid):
    cur.execute('UPDATE users SET banned_until = NULL, ban_reason = NULL WHERE id = %s', (uid,))
    if cur.rowcount != 1:
        raise ControlError('Foydalanuvchi topilmadi.', 404)
    conn.commit()
    _banned['t'] = 0.0


_banned = {'t': 0.0, 'ids': frozenset()}


def banned_ids(cur) -> frozenset:
    """Hozir bloklangan o'quvchilar — reytinglardan chiqariladi (CACHE_S keshlanadi)."""
    now = time.monotonic()
    if now - _banned['t'] < CACHE_S:
        return _banned['ids']
    try:
        cur.execute('SELECT id FROM users WHERE banned_until IS NOT NULL AND banned_until > %s', (clock.now_ms(),))
        ids = frozenset(int(r['id']) for r in cur.fetchall())
    except Exception:  # noqa: BLE001 — ustun hali yo'q bo'lsa ham reyting ishlasin
        logger.warning("Bloklanganlar ro'yxati o'qilmadi", exc_info=True)
        return _banned['ids']
    _banned.update(t=now, ids=ids)
    return ids


def banned_list(cur, now=None) -> list:
    cur.execute('''SELECT id, name, username, banned_until, ban_reason FROM users
                   WHERE banned_until IS NOT NULL AND banned_until > %s ORDER BY banned_until''', (now or clock.now_ms(),))
    return [dict(ban_info(r, now) or {}, id=r['id'], name=r['name'], username=r['username']) for r in cur.fetchall()]


# ───────────────────────── So'rov va bot darvozasi ─────────────────────────

def check_request(user, method, path, now=None):
    """auth_required'dan chaqiriladi: None — so'rov davom etadi, aks holda (javob, http status)."""
    if is_admin_user(user):
        return None
    now = now or clock.now_ms()
    info = ban_info(user, now)
    if info:
        return dict(info, ok=False, code='banned', error=MSG_BANNED), 403
    st = state()
    p = pause_info('app', now, st)
    if p:
        return {'ok': False, 'code': 'maintenance', 'error': MSG_MAINTENANCE, 'message': p.get('message') or '',
                'until_ms': p.get('until_ms')}, 423
    key = feature_for(method, path)
    if key and not feature_on(key, st):
        return {'ok': False, 'code': 'feature_off', 'feature': key, 'error': MSG_FEATURE_OFF}, 423
    return None


def bot_gate(tg_id, now=None):
    """Bot yangilanishi uchun: None — odatdagidek ishlanadi; ('pause', info) yoki ('banned', info)."""
    if not tg_id or _is_admin_tg(tg_id):
        return None
    p = pause_info('bot', now)
    if p:
        return 'pause', p
    try:
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute('SELECT banned_until, ban_reason FROM users WHERE telegram_id = %s ORDER BY id DESC LIMIT 1',
                        (tg_id,))
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()
    except Exception:  # noqa: BLE001
        return None
    info = ban_info(row, now)
    return ('banned', info) if info else None


def time_text(ms, now=None) -> str:
    """Toshkent vaqti: bugun bo'lsa 14:30, aks holda 05.10.2026 14:30."""
    dt = datetime.fromtimestamp(int(ms) / 1000, TASHKENT_TZ)
    today = datetime.fromtimestamp((now or clock.now_ms()) / 1000, TASHKENT_TZ).date()
    return dt.strftime('%H:%M') if dt.date() == today else dt.strftime('%d.%m.%Y %H:%M')


def pause_text(p, lang='uz') -> str:
    msg = html.escape(p.get('message') or '')
    t = time_text(p['until_ms']) if p.get('until_ms') else None
    if lang == 'ru':
        lines = ['🛠 <b>В BilimSari идут технические работы.</b>', msg,
                 f'Бот снова заработает примерно в <b>{t}</b>.' if t else 'Бот скоро снова заработает.',
                 'Спасибо за терпение!']
    else:
        lines = ["🛠 <b>BilimSari'da texnik ishlar olib borilmoqda.</b>", msg,
                 f'Bot taxminan <b>{t}</b> da qayta ishga tushadi.' if t else 'Bot tez orada qayta ishga tushadi.',
                 'Sabringiz uchun rahmat!']
    return '\n'.join(x for x in lines if x)


def banned_text(info, lang='uz') -> str:
    reason = html.escape(info.get('reason') or '')
    t = time_text(info['until_ms']) if info.get('until_ms') else None
    if lang == 'ru':
        lines = ['⛔ <b>Ваш аккаунт заблокирован.</b>', f'Причина: {reason}' if reason else '',
                 f'Блокировка до <b>{t}</b>.' if t else 'Срок: бессрочно.']
    else:
        lines = ['⛔ <b>Akkauntingiz bloklangan.</b>', f'Sabab: {reason}' if reason else '',
                 f'Blok <b>{t}</b> gacha.' if t else 'Muddat: muddatsiz.']
    return '\n'.join(x for x in lines if x)


# ───────────────────────── Admin bonusi (chaqmoq) ─────────────────────────

def add_bonus(cur, conn, uid, amount, note, now=None) -> int:
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        raise ControlError("Chaqmoq soni butun son bo'lishi kerak.")
    if not amount or abs(amount) > 100000:
        raise ControlError("Chaqmoq soni 1 dan 100 000 gacha (ayirish uchun minus bilan) bo'lishi kerak.")
    cur.execute('SELECT id FROM users WHERE id = %s', (uid,))
    if not cur.fetchone():
        raise ControlError('Foydalanuvchi topilmadi.', 404)
    cur.execute('INSERT INTO chaqmoq_bonus (user_id, amount, note, created_ms) VALUES (%s, %s, %s, %s)',
                (uid, amount, _clean(note, 200) or None, now or clock.now_ms()))
    conn.commit()
    import jurnal   # noqa: PLC0415
    jurnal.VERSION[0] += 1          # umumiy reyting keshi yangilansin
    return amount


def bonus_total(cur, uid) -> int:
    cur.execute('SELECT COALESCE(SUM(amount), 0) AS s FROM chaqmoq_bonus WHERE user_id = %s', (uid,))
    return int(cur.fetchone()['s'] or 0)


def bonus_by_user(cur) -> dict:
    cur.execute('SELECT user_id, SUM(amount) AS s FROM chaqmoq_bonus GROUP BY user_id')
    return {int(r['user_id']): int(r['s'] or 0) for r in cur.fetchall()}


def bonus_list(cur, uid, limit=20) -> list:
    cur.execute('SELECT amount, note, created_ms FROM chaqmoq_bonus WHERE user_id = %s ORDER BY id DESC LIMIT %s',
                (uid, limit))
    return [{'amount': int(r['amount']), 'note': r['note'] or '', 'created_ms': int(r['created_ms'])}
            for r in cur.fetchall()]


def cleanup_user(cur, uid):
    cur.execute('DELETE FROM chaqmoq_bonus WHERE user_id = %s', (uid,))
