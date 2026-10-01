# -*- coding: utf-8 -*-
"""
Yutuqli marafon.

Admin marafon yaratadi: nomi, boshlanish vaqti, necha kun, top nechta o'rin, har o'ringa
sovrin (summa, izoh, ixtiyoriy rasm), kim qatnashadi (hamma / faqat Premium) va g'olib pulni
olish uchun yozadigan Telegram @username. Bir vaqtda faqat bitta marafon bo'ladi (qoralama,
rejalashtirilgan yoki faol) — keyingisi oldingisi tugagach yaratiladi.

Hisob — chaqmoq jurnalidan (jurnal.py), o'quvchi qo'shilgan paytdan (marafon boshlanishidan
oldin emas) marafon tugaguncha olingan chaqmoq:
  * darslar, o'yinlar (24 soatda 3 ta chaqmoqli o'yin), kun savoli — hammasi;
  * shaxsiy darslar — 24 soatda faqat 1 ta darsning chaqmoqi (oldindan yig'ib qo'yib bir
    kunda o'qish foyda bermasin);
  * "faqat Premium" marafonda — faqat Premium faol paytda olinganlari (admin talablarsiz
    qo'shgan o'quvchida — hammasi);
  * admin qo'shgan/ayirgan chaqmoq (marathon_adjust).
Teng bo'lsa — shu songa birinchi yetgan yuqorida.

Tugaganda (rejalashtiruvchi, har daqiqa): g'oliblar (chaqmoqi 0 dan katta top-N) muzlatiladi,
har biriga bot orqali "pulingizni olish uchun @... ga yozing" xabari, hammaga (eslatmani
o'chirganlarga ham) va "Biz haqimizda"dagi kanalga natija e'loni boradi.
"""

import html
import logging
import re
import threading
import time
from datetime import datetime

import broadcast
import dostlar
import photos
import premium
import site_settings
import tgbot
from db import TASHKENT_TZ, as_utc, get_connection
from games import clock

logger = logging.getLogger('bilimsari.marafon')

DAY_MS = 24 * 3600 * 1000
HOUR_MS = 3600 * 1000
MAX_DAYS = 90
MAX_TOP = 100
MAX_ADJUST = 100000
CACHE_MS = 20 * 1000
REMIND_HOUR = 19                 # kechki eslatma (Toshkent vaqti)
PREMIUM_WARN_MS = 3 * DAY_MS     # Premium tugashiga shuncha qolganda ogohlantirish
OPEN = ('draft', 'scheduled', 'active')
_USERNAME = re.compile(r'^[A-Za-z][A-Za-z0-9_]{3,31}$')


class MarafonError(Exception):
    def __init__(self, message, code='bad_request', http_status=400):
        super().__init__(message)
        self.message, self.code, self.http_status = message, code, http_status


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS marathons (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            start_ms BIGINT NOT NULL,
            end_ms BIGINT NOT NULL,
            top_n INTEGER NOT NULL,
            audience TEXT NOT NULL DEFAULT 'all',
            contact TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            rev INTEGER NOT NULL DEFAULT 1,
            created_ms BIGINT NOT NULL,
            started_ms BIGINT,
            finished_ms BIGINT,
            channel_note TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS marathon_prizes (
            marathon_id INTEGER NOT NULL,
            place INTEGER NOT NULL,
            amount BIGINT NOT NULL DEFAULT 0,
            note TEXT,
            image_id INTEGER,
            PRIMARY KEY (marathon_id, place)
        )
    ''')
    # Sovrin rasmlari — Railway diski har deployda tozalanadi, shuning uchun bazada (base64)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS marathon_images (
            id SERIAL PRIMARY KEY,
            mime TEXT NOT NULL,
            data TEXT NOT NULL,
            created_ms BIGINT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS marathon_participants (
            marathon_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_ms BIGINT NOT NULL,
            added_by TEXT NOT NULL DEFAULT 'self',
            waived INTEGER NOT NULL DEFAULT 0,
            removed_ms BIGINT,
            removed_reason TEXT,
            PRIMARY KEY (marathon_id, user_id)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS marathon_adjust (
            id SERIAL PRIMARY KEY,
            marathon_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            note TEXT,
            created_ms BIGINT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS marathon_winners (
            marathon_id INTEGER NOT NULL,
            place INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT,
            photo_url TEXT,
            score INTEGER NOT NULL,
            amount BIGINT NOT NULL DEFAULT 0,
            note TEXT,
            image_id INTEGER,
            notified INTEGER NOT NULL DEFAULT 0,
            paid_ms BIGINT,
            paid_note TEXT,
            PRIMARY KEY (marathon_id, place)
        )
    ''')
    # Bir martalik ishlar (e'lon, eslatmalar) — bir necha worker bo'lsa ham bir marta
    cur.execute('''
        CREATE TABLE IF NOT EXISTS marathon_sent (
            marathon_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            created_ms BIGINT NOT NULL,
            PRIMARY KEY (marathon_id, kind)
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_marathon_part_user ON marathon_participants (user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_marathon_adjust ON marathon_adjust (marathon_id, user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_marathon_winners_user ON marathon_winners (user_id)')
    conn.commit()


# ───────────────────────── Yordamchilar ─────────────────────────

def money(n) -> str:
    return f"{int(n or 0):,}".replace(',', ' ') + " so'm"


def prize_text(p) -> str:
    parts = [money(p['amount'])] if int(p['amount'] or 0) else []
    if p.get('note'):
        parts.append(p['note'])
    return ' + '.join(parts) or 'Sovrin'


def local_text(ms) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, TASHKENT_TZ).strftime('%d.%m.%Y %H:%M')


def parse_local(value) -> int:
    """'2026-10-05T09:00' (Toshkent vaqti) → epoch ms."""
    try:
        dt = datetime.strptime(str(value or '').strip()[:16], '%Y-%m-%dT%H:%M')
    except ValueError:
        raise MarafonError("Boshlanish vaqti noto'g'ri.")
    return int(dt.replace(tzinfo=TASHKENT_TZ).timestamp() * 1000)


def _row(cur, mid):
    cur.execute('SELECT * FROM marathons WHERE id = %s', (mid,))
    m = cur.fetchone()
    if not m:
        raise MarafonError('Marafon topilmadi.', 'not_found', 404)
    return dict(m)


def open_marathon(cur):
    """Hozirgi (qoralama, rejalashtirilgan yoki faol) marafon yoki None."""
    cur.execute("SELECT * FROM marathons WHERE status IN ('draft', 'scheduled', 'active') ORDER BY id DESC LIMIT 1")
    m = cur.fetchone()
    return dict(m) if m else None


def shown_marathon(cur, now):
    """O'quvchilarga ko'rsatiladigan: rejalashtirilgan yoki faol (tugaganlari — tarixda)."""
    cur.execute("SELECT * FROM marathons WHERE status IN ('scheduled', 'active') ORDER BY id DESC LIMIT 1")
    m = cur.fetchone()
    return dict(m) if m else None


def _bump(cur, mid):
    cur.execute('UPDATE marathons SET rev = rev + 1 WHERE id = %s', (mid,))


def prizes(cur, mid) -> list:
    cur.execute('SELECT place, amount, note, image_id FROM marathon_prizes WHERE marathon_id = %s ORDER BY place', (mid,))
    return [{'place': int(r['place']), 'amount': int(r['amount'] or 0), 'note': r['note'] or '',
             'image_id': r['image_id'], 'image_url': image_url(r['image_id'])} for r in cur.fetchall()]


def image_url(image_id):
    return f'/api/marathon/image/{image_id}' if image_id else None


def _claim(cur, conn, mid, kind, now) -> bool:
    cur.execute('INSERT INTO marathon_sent (marathon_id, kind, created_ms) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                (mid, kind, now))
    ok = cur.rowcount == 1
    conn.commit()
    return ok


def channel_chat(cur):
    """'Biz haqimizda'dagi kanal → '@kanal' (yopiq taklif havolasiga bot post qila olmaydi)."""
    url = site_settings.channel_url(cur) or ''
    name = url.rsplit('/', 1)[-1] if url else ''
    return '@' + name if name and _USERNAME.match(name) else None


# ───────────────────────── Admin: yaratish va tahrirlash ─────────────────────────

def _clean(body, m=None, now=None) -> dict:
    """Formadan kelgan qiymatlar. m — tahrirlanayotgan marafon (bo'lmasa — yangi)."""
    now = now or clock.now_ms()
    out = {}
    title = ' '.join(str(body.get('title') or (m or {}).get('title') or '').split())
    if not 3 <= len(title) <= 80:
        raise MarafonError("Marafon nomi 3–80 belgi bo'lsin.")
    out['title'] = title
    desc = str(body.get('description') if body.get('description') is not None else (m or {}).get('description') or '').strip()
    if len(desc) > 1000:
        raise MarafonError("Tavsif juda uzun (1000 belgigacha).")
    out['description'] = desc or None
    try:
        top_n = int(body.get('top_n') or (m or {}).get('top_n') or 0)
    except (TypeError, ValueError):
        top_n = 0
    if not 1 <= top_n <= MAX_TOP:
        raise MarafonError(f"Sovrinli o'rinlar soni 1–{MAX_TOP} bo'lsin.")
    out['top_n'] = top_n
    audience = body.get('audience') or (m or {}).get('audience') or 'all'
    if audience not in ('all', 'premium'):
        raise MarafonError("Qatnashchilar turi noto'g'ri.")
    out['audience'] = audience
    contact = str(body.get('contact') or (m or {}).get('contact') or '').strip()
    contact = re.sub(r'^(?:https?://)?(?:t\.me|telegram\.me)/', '', contact).lstrip('@')
    if not _USERNAME.match(contact):
        raise MarafonError("G'olib yozadigan Telegram username noto'g'ri (masalan: @bilimsari_admin).")
    out['contact'] = contact
    try:
        days = int(body.get('days') or 0) or (round((m['end_ms'] - m['start_ms']) / DAY_MS) if m else 0)
    except (TypeError, ValueError):
        days = 0
    if not 1 <= days <= MAX_DAYS:
        raise MarafonError(f"Davomiyligi 1–{MAX_DAYS} kun bo'lsin.")
    out['days'] = days
    if m and m['status'] == 'active':
        out['start_ms'] = int(m['start_ms'])                 # boshlangan marafonning boshi o'zgarmaydi
    elif body.get('start'):
        out['start_ms'] = parse_local(body.get('start'))
    elif m:
        out['start_ms'] = int(m['start_ms'])
    else:
        raise MarafonError('Boshlanish vaqtini kiriting.')
    out['end_ms'] = out['start_ms'] + days * DAY_MS
    if m and m['status'] == 'active' and out['end_ms'] <= now:
        raise MarafonError("Tugash vaqti o'tib ketgan bo'lib qoladi — kunlar sonini oshiring yoki \"Hozir yakunlash\"ni bosing.")
    raw = body.get('prizes')
    if raw is not None:
        if not isinstance(raw, list):
            raise MarafonError("Sovrinlar ro'yxati noto'g'ri.")
        items = {}
        for p in raw:
            try:
                place, amount = int(p.get('place')), int(p.get('amount') or 0)
            except (TypeError, ValueError, AttributeError):
                raise MarafonError("Sovrin qiymati noto'g'ri.")
            note = ' '.join(str(p.get('note') or '').split())[:120]
            if not 1 <= place <= top_n:
                continue
            if amount < 0 or amount > 10 ** 10:
                raise MarafonError("Sovrin summasi noto'g'ri.")
            items[place] = {'place': place, 'amount': amount, 'note': note}
        out['prizes'] = [items[k] for k in sorted(items)]
    return out


def _save_prizes(cur, mid, items):
    """Sovrinlar (rasmlari saqlanib qoladi)."""
    cur.execute('SELECT place, image_id FROM marathon_prizes WHERE marathon_id = %s', (mid,))
    images = {int(r['place']): r['image_id'] for r in cur.fetchall()}
    cur.execute('DELETE FROM marathon_prizes WHERE marathon_id = %s', (mid,))
    for p in items:
        cur.execute('INSERT INTO marathon_prizes (marathon_id, place, amount, note, image_id) VALUES (%s, %s, %s, %s, %s)',
                    (mid, p['place'], p['amount'], p['note'] or None, images.get(p['place'])))


def create(cur, conn, body, now=None) -> int:
    now = now or clock.now_ms()
    if open_marathon(cur):
        raise MarafonError("Hozirgi marafon tugagach yangisini yaratish mumkin.", 'busy', 409)
    v = _clean(body, None, now)
    cur.execute('''INSERT INTO marathons (title, description, start_ms, end_ms, top_n, audience, contact, status, created_ms)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft', %s) RETURNING id''',
                (v['title'], v['description'], v['start_ms'], v['end_ms'], v['top_n'], v['audience'], v['contact'], now))
    mid = cur.fetchone()['id']
    _save_prizes(cur, mid, v.get('prizes') or [])
    conn.commit()
    return mid


def update(cur, conn, mid, body, now=None):
    now = now or clock.now_ms()
    m = _row(cur, mid)
    if m['status'] not in OPEN:
        raise MarafonError("Tugagan yoki bekor qilingan marafonni o'zgartirib bo'lmaydi.", 'closed', 409)
    v = _clean(body, m, now)
    cur.execute('''UPDATE marathons SET title = %s, description = %s, start_ms = %s, end_ms = %s, top_n = %s,
                                        audience = %s, contact = %s, rev = rev + 1 WHERE id = %s''',
                (v['title'], v['description'], v['start_ms'], v['end_ms'], v['top_n'], v['audience'], v['contact'], mid))
    if 'prizes' in v:
        _save_prizes(cur, mid, v['prizes'])
    cur.execute('DELETE FROM marathon_prizes WHERE marathon_id = %s AND place > %s', (mid, v['top_n']))
    conn.commit()


def _check_ready(cur, m):
    have = {p['place'] for p in prizes(cur, m['id'])}
    missing = [i for i in range(1, int(m['top_n']) + 1) if i not in have]
    if missing:
        raise MarafonError(f"Sovrin kiritilmagan o'rinlar: {', '.join(map(str, missing[:10]))}.")


def schedule(cur, conn, mid, now=None):
    """Qoralama → rejalashtirilgan (vaqti kelganda o'zi boshlanadi)."""
    now = now or clock.now_ms()
    m = _row(cur, mid)
    if m['status'] != 'draft':
        raise MarafonError("Faqat qoralamani rejalashtirish mumkin.", 'bad_state', 409)
    _check_ready(cur, m)
    if int(m['end_ms']) <= now:
        raise MarafonError("Marafon tugash vaqti o'tib ketgan — boshlanish vaqtini o'zgartiring.")
    cur.execute("UPDATE marathons SET status = 'scheduled', rev = rev + 1 WHERE id = %s AND status = 'draft'", (mid,))
    conn.commit()
    tick(cur, conn, now)            # vaqti kelgan bo'lsa — darhol boshlanadi


def start_now(cur, conn, mid, now=None):
    now = now or clock.now_ms()
    m = _row(cur, mid)
    if m['status'] not in ('draft', 'scheduled'):
        raise MarafonError("Marafon allaqachon boshlangan yoki tugagan.", 'bad_state', 409)
    _check_ready(cur, m)
    days = max(1, round((int(m['end_ms']) - int(m['start_ms'])) / DAY_MS))
    cur.execute("UPDATE marathons SET status = 'scheduled', start_ms = %s, end_ms = %s, rev = rev + 1 WHERE id = %s",
                (now, now + days * DAY_MS, mid))
    conn.commit()
    tick(cur, conn, now)


def cancel(cur, conn, mid, now=None):
    now = now or clock.now_ms()
    m = _row(cur, mid)
    if m['status'] not in OPEN:
        raise MarafonError("Bu marafon allaqachon yopilgan.", 'bad_state', 409)
    cur.execute("UPDATE marathons SET status = 'cancelled', finished_ms = %s, rev = rev + 1 WHERE id = %s", (now, mid))
    conn.commit()
    if m['status'] == 'active':
        _to_participants(cur, m, lambda r: f"ℹ️ «{html.escape(m['title'])}» marafoni bekor qilindi.")


def finish_now(cur, conn, mid, now=None):
    now = now or clock.now_ms()
    m = _row(cur, mid)
    if m['status'] != 'active':
        raise MarafonError("Faqat davom etayotgan marafonni yakunlash mumkin.", 'bad_state', 409)
    cur.execute('UPDATE marathons SET end_ms = %s, rev = rev + 1 WHERE id = %s', (now, mid))
    conn.commit()
    tick(cur, conn, now)


def delete_draft(cur, conn, mid):
    m = _row(cur, mid)
    if m['status'] != 'draft':
        raise MarafonError("Faqat qoralamani o'chirish mumkin (boshlanganini — bekor qiling).", 'bad_state', 409)
    cur.execute('SELECT image_id FROM marathon_prizes WHERE marathon_id = %s AND image_id IS NOT NULL', (mid,))
    for r in cur.fetchall():
        cur.execute('DELETE FROM marathon_images WHERE id = %s', (r['image_id'],))
    for table in ('marathon_prizes', 'marathon_participants', 'marathon_adjust', 'marathon_sent'):
        cur.execute(f'DELETE FROM {table} WHERE marathon_id = %s', (mid,))
    cur.execute('DELETE FROM marathons WHERE id = %s', (mid,))
    conn.commit()


def set_prize_image(cur, conn, mid, place, data_url, now=None):
    """Sovrin rasmi (brauzer kichraytirib yuboradi). data_url bo'sh — rasm o'chiriladi."""
    now = now or clock.now_ms()
    m = _row(cur, mid)
    if m['status'] not in OPEN:
        raise MarafonError("Tugagan marafonni o'zgartirib bo'lmaydi.", 'closed', 409)
    cur.execute('SELECT image_id FROM marathon_prizes WHERE marathon_id = %s AND place = %s', (mid, place))
    row = cur.fetchone()
    if not row:
        raise MarafonError("Avval shu o'rin uchun sovrinni saqlang.")
    new_id = None
    if data_url:
        try:
            mime, data = photos._decode(data_url)
        except photos.PhotoError as exc:
            raise MarafonError(str(exc))
        cur.execute('INSERT INTO marathon_images (mime, data, created_ms) VALUES (%s, %s, %s) RETURNING id', (mime, data, now))
        new_id = cur.fetchone()['id']
    cur.execute('UPDATE marathon_prizes SET image_id = %s WHERE marathon_id = %s AND place = %s', (new_id, mid, place))
    if row['image_id']:
        cur.execute('DELETE FROM marathon_images WHERE id = %s', (row['image_id'],))
    _bump(cur, mid)
    conn.commit()
    return image_url(new_id)


def load_image(cur, image_id):
    cur.execute('SELECT mime, data FROM marathon_images WHERE id = %s', (image_id,))
    r = cur.fetchone()
    return (r['mime'], r['data']) if r else None


# ───────────────────────── Qatnashchilar ─────────────────────────

def _participant(cur, mid, uid):
    cur.execute('SELECT * FROM marathon_participants WHERE marathon_id = %s AND user_id = %s', (mid, uid))
    return cur.fetchone()


def eligibility(cur, m, uid, now) -> dict:
    """Qatnasha oladimi: {'joined', 'can_join', 'reason', 'removed'}."""
    part = _participant(cur, m['id'], uid)
    joined = bool(part and not part['removed_ms'])
    removed = bool(part and part['removed_ms'])
    reason = None
    if removed:
        reason = 'removed'
    elif m['status'] not in ('scheduled', 'active') or now >= int(m['end_ms']):
        reason = 'closed'
    elif m['audience'] == 'premium' and not premium.status(cur, uid, now)['active'] and not joined:
        reason = 'premium'
    return {'joined': joined, 'removed': removed, 'removed_reason': part['removed_reason'] if removed else None,
            'can_join': not joined and reason is None, 'reason': reason,
            'waived': bool(part and part['waived'])}


def join(cur, conn, mid, uid, agree, now=None):
    now = now or clock.now_ms()
    m = _row(cur, mid)
    e = eligibility(cur, m, uid, now)
    if e['joined']:
        return
    if not agree:
        raise MarafonError("Qatnashish uchun marafon qoidalariga rozilik bering.", 'agree')
    if e['reason'] == 'removed':
        raise MarafonError("Siz bu marafondan chiqarilgansiz.", 'removed', 403)
    if e['reason'] == 'closed':
        raise MarafonError("Bu marafonga qo'shilib bo'lmaydi.", 'closed', 409)
    if e['reason'] == 'premium':
        raise MarafonError("Bu marafonda faqat Bilim Premium a'zolari qatnasha oladi.", 'premium', 403)
    cur.execute('''INSERT INTO marathon_participants (marathon_id, user_id, joined_ms, added_by)
                   VALUES (%s, %s, %s, 'self') ON CONFLICT DO NOTHING''', (mid, uid, now))
    _bump(cur, mid)
    conn.commit()


def admin_add(cur, conn, mid, uid, now=None):
    """Talablarsiz qo'shish: Premium sharti qo'llanmaydi; faol marafonda boshidan beri sanaladi."""
    now = now or clock.now_ms()
    m = _row(cur, mid)
    if m['status'] not in OPEN:
        raise MarafonError("Tugagan marafonga qo'shib bo'lmaydi.", 'closed', 409)
    cur.execute('SELECT id FROM users WHERE id = %s', (uid,))
    if not cur.fetchone():
        raise MarafonError("Bunday o'quvchi topilmadi.", 'not_found', 404)
    joined = int(m['start_ms']) if m['status'] == 'active' else now
    part = _participant(cur, mid, uid)
    if part:
        cur.execute('''UPDATE marathon_participants SET removed_ms = NULL, removed_reason = NULL, waived = 1
                       WHERE marathon_id = %s AND user_id = %s''', (mid, uid))
    else:
        cur.execute('''INSERT INTO marathon_participants (marathon_id, user_id, joined_ms, added_by, waived)
                       VALUES (%s, %s, %s, 'admin', 1)''', (mid, uid, joined))
    _bump(cur, mid)
    conn.commit()


def admin_remove(cur, conn, mid, uid, reason, now=None):
    now = now or clock.now_ms()
    m = _row(cur, mid)
    part = _participant(cur, mid, uid)
    if not part or part['removed_ms']:
        raise MarafonError("Bu o'quvchi marafonda emas.", 'not_found', 404)
    reason = ' '.join(str(reason or '').split())[:200] or None
    cur.execute('UPDATE marathon_participants SET removed_ms = %s, removed_reason = %s WHERE marathon_id = %s AND user_id = %s',
                (now, reason, mid, uid))
    _bump(cur, mid)
    conn.commit()
    u = _user(cur, uid)
    if u and u['telegram_id']:
        tgbot.send(u['telegram_id'], f"ℹ️ Siz «{html.escape(m['title'])}» marafonidan chiqarildingiz."
                   + (f"\nSabab: {html.escape(reason)}" if reason else ''))


def adjust(cur, conn, mid, uid, amount, note, now=None):
    now = now or clock.now_ms()
    m = _row(cur, mid)
    if m['status'] not in OPEN:
        raise MarafonError("Tugagan marafonda chaqmoqni o'zgartirib bo'lmaydi.", 'closed', 409)
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        raise MarafonError("Chaqmoq soni noto'g'ri.")
    if amount == 0 or abs(amount) > MAX_ADJUST:
        raise MarafonError("Chaqmoq soni noto'g'ri.")
    part = _participant(cur, mid, uid)
    if not part or part['removed_ms']:
        raise MarafonError("Bu o'quvchi marafonda emas.", 'not_found', 404)
    cur.execute('INSERT INTO marathon_adjust (marathon_id, user_id, amount, note, created_ms) VALUES (%s, %s, %s, %s, %s)',
                (mid, uid, amount, ' '.join(str(note or '').split())[:200] or None, now))
    _bump(cur, mid)
    conn.commit()


def _user(cur, uid):
    cur.execute('SELECT id, name, photo_url, telegram_id, notify, created_at, premium_until FROM users WHERE id = %s', (uid,))
    return cur.fetchone()


# ───────────────────────── Hisob (reyting) ─────────────────────────

_CACHE = {}


def _shaxsiy_counted(rows):
    """Shaxsiy darslar: 24 soatda faqat 1 ta dars. rows — bitta o'quvchi, vaqt bo'yicha.
    Qaytaradi: [(amount, created_ms), ...] hisobga o'tganlari va {pid: sanaldimi}."""
    counted, verdict, last_start = [], {}, None
    for r in rows:
        pid = str(r['ref']).split(':')[1] if ':' in str(r['ref']) else str(r['ref'])
        if pid not in verdict:
            ok = last_start is None or int(r['created_ms']) >= last_start + DAY_MS
            verdict[pid] = ok
            if ok:
                last_start = int(r['created_ms'])
        if verdict[pid]:
            counted.append((int(r['amount']), int(r['created_ms'])))
    return counted, verdict, last_start


def standings(cur, m, now=None, fresh=False) -> list:
    """Qatnashchilar reytingi: [{user_id, rank, score, last_ms, joined_ms, parts}], tartiblangan."""
    now = now or clock.now_ms()
    key = (m['id'], int(m['rev']))
    hit = _CACHE.get(m['id'])
    if not fresh and hit and hit[0] == key and now - hit[1] < CACHE_MS:
        return hit[2]
    until = min(now + 1, int(m['end_ms']))     # hozirgi millisekund ham kiradi, tugash vaqti — yo'q
    cur.execute('SELECT user_id, joined_ms FROM marathon_participants WHERE marathon_id = %s AND removed_ms IS NULL',
                (m['id'],))
    people = {int(r['user_id']): {'user_id': int(r['user_id']), 'joined_ms': int(r['joined_ms']), 'score': 0,
                                  'last_ms': int(r['joined_ms']),
                                  'parts': {'dars': 0, 'shaxsiy': 0, 'oyin': 0, 'kun': 0, 'admin': 0}}
              for r in cur.fetchall()}
    if people:
        base = ('''FROM chaqmoq_log l JOIN marathon_participants p ON p.user_id = l.user_id AND p.marathon_id = %s
                   AND p.removed_ms IS NULL
                   WHERE l.created_ms >= %s AND l.created_ms < %s AND l.created_ms >= p.joined_ms
                     AND (%s = 0 OR l.premium = 1 OR p.waived = 1)''')
        params = [m['id'], int(m['start_ms']), until, int(m['audience'] == 'premium')]
        cur.execute(f"SELECT l.user_id, l.source, SUM(l.amount) AS s, MAX(l.created_ms) AS last {base} "
                    f"AND l.source != 'shaxsiy' GROUP BY l.user_id, l.source", params)
        for r in cur.fetchall():
            p = people.get(int(r['user_id']))
            if p:
                p['parts'][r['source'] if r['source'] in p['parts'] else 'dars'] += int(r['s'] or 0)
                p['score'] += int(r['s'] or 0)
                p['last_ms'] = max(p['last_ms'], int(r['last'] or 0))
        cur.execute(f"SELECT l.user_id, l.ref, l.amount, l.created_ms {base} AND l.source = 'shaxsiy' "
                    f"ORDER BY l.user_id, l.created_ms, l.id", params)
        by_user = {}
        for r in cur.fetchall():
            by_user.setdefault(int(r['user_id']), []).append(r)
        for uid, rows in by_user.items():
            p = people.get(uid)
            if not p:
                continue
            for amount, at in _shaxsiy_counted(rows)[0]:
                p['parts']['shaxsiy'] += amount
                p['score'] += amount
                p['last_ms'] = max(p['last_ms'], at)
        cur.execute('''SELECT user_id, SUM(amount) AS s, MAX(created_ms) AS last FROM marathon_adjust
                       WHERE marathon_id = %s GROUP BY user_id''', (m['id'],))
        for r in cur.fetchall():
            p = people.get(int(r['user_id']))
            if p:
                p['parts']['admin'] += int(r['s'] or 0)
                p['score'] += int(r['s'] or 0)
                p['last_ms'] = max(p['last_ms'], int(r['last'] or 0))
    rows = sorted(people.values(), key=lambda p: (-p['score'], p['last_ms'], p['user_id']))
    for i, p in enumerate(rows):
        p['rank'] = i + 1
    _CACHE[m['id']] = (key, now, rows)
    if len(_CACHE) > 20:
        _CACHE.clear()
    return rows


def personal_note(cur, uid, pid, now=None):
    """Shaxsiy dars chaqmoqi marafonga sanaldimi — o'quvchiga aytish uchun. None — marafonda emas."""
    now = now or clock.now_ms()
    cur.execute("""SELECT m.* FROM marathons m JOIN marathon_participants p ON p.marathon_id = m.id
                   WHERE m.status = 'active' AND p.user_id = %s AND p.removed_ms IS NULL LIMIT 1""", (uid,))
    m = cur.fetchone()
    if not m:
        return None
    cur.execute("""SELECT l.ref, l.amount, l.created_ms FROM chaqmoq_log l JOIN marathon_participants p
                   ON p.user_id = l.user_id AND p.marathon_id = %s
                   WHERE l.user_id = %s AND l.source = 'shaxsiy' AND l.created_ms >= %s AND l.created_ms >= p.joined_ms
                   AND l.created_ms < %s ORDER BY l.created_ms, l.id""", (m['id'], uid, int(m['start_ms']), int(m['end_ms'])))
    counted, verdict, last_start = _shaxsiy_counted(cur.fetchall())
    ok = verdict.get(str(pid))
    if ok is None:
        return None
    if ok:
        return {'counted': True, 'text': f"«{m['title']}» marafoniga qo'shildi."}
    nxt = (last_start or now) + DAY_MS
    return {'counted': False, 'next_ms': nxt,
            'text': ("Marafonda shaxsiy darslardan 24 soatda faqat 1 ta darsning chaqmoqi sanaladi — bu dars "
                     "chaqmoqi umumiy hisobingizga qo'shildi, marafonga esa qo'shilmadi.")}


# ───────────────────────── O'quvchi uchun ko'rinish ─────────────────────────

def _cards(cur, ids, now):
    ids = sorted({int(i) for i in ids})
    if not ids:
        return {}
    cur.execute(f"SELECT id, name, photo_url FROM users WHERE id IN ({', '.join(['%s'] * len(ids))})", ids)
    rows = [{'id': int(r['id']), 'user_id': int(r['id']), 'name': r['name'] or "O'quvchi", 'photo_url': r['photo_url']}
            for r in cur.fetchall()]
    premium.decorate(cur, rows, now=now)
    return {r['id']: r for r in rows}


def public_info(cur, m, now) -> dict:
    pz = prizes(cur, m['id'])
    return {
        'id': m['id'], 'title': m['title'], 'description': m['description'] or '', 'status': m['status'],
        'start_ms': int(m['start_ms']), 'end_ms': int(m['end_ms']), 'top_n': int(m['top_n']),
        'audience': m['audience'], 'prizes': [{k: p[k] for k in ('place', 'amount', 'note', 'image_url')} for p in pz],
        'prize_fund': sum(p['amount'] for p in pz), 'now': now,
    }


def view(cur, uid, now=None, limit=100) -> dict:
    """Reyting sahifasining "Marafon" bo'limi."""
    now = now or clock.now_ms()
    m = shown_marathon(cur, now)
    history = past_list(cur, uid)
    if not m:
        return {'marathon': None, 'history': history}
    info = public_info(cur, m, now)
    friends = set(dostlar.friend_ids(cur, uid))
    st = standings(cur, m, now)
    e = eligibility(cur, m, uid, now)
    mine = next((p for p in st if p['user_id'] == uid), None)
    shown = st[:limit] + ([mine] if mine and mine['rank'] > limit else [])
    cards = _cards(cur, [p['user_id'] for p in shown], now)
    top = []
    for p in shown:
        c = cards.get(p['user_id'])
        if not c:
            continue
        top.append(dict(c, rank=p['rank'], score=p['score'], me=p['user_id'] == uid, friend=p['user_id'] in friends))
    me = dict(e, premium=premium.status(cur, uid, now)['active'])
    if mine:
        above = st[mine['rank'] - 2] if mine['rank'] > 1 else None
        me.update(rank=mine['rank'], score=mine['score'],
                  to_next=(above['score'] - mine['score'] + 1) if above else 0)
        top_n = int(m['top_n'])
        if mine['rank'] > top_n and len(st) >= top_n:
            me['to_top'] = st[top_n - 1]['score'] - mine['score'] + 1
    return {'marathon': info, 'top': top, 'participants': len(st), 'me': me, 'history': history}


def past_list(cur, uid, limit=30) -> list:
    """Marafonlar tarixi: tugaganlari (yangisi birinchi), o'quvchining o'rni bilan."""
    cur.execute("SELECT id, title, start_ms, end_ms, top_n FROM marathons WHERE status = 'finished' "
                "ORDER BY end_ms DESC, id DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    if not rows:
        return []
    ids = [r['id'] for r in rows]
    marks = ', '.join(['%s'] * len(ids))
    cur.execute(f'SELECT marathon_id, COALESCE(SUM(amount), 0) AS fund FROM marathon_prizes WHERE marathon_id IN ({marks}) '
                f'GROUP BY marathon_id', ids)
    funds = {r['marathon_id']: int(r['fund'] or 0) for r in cur.fetchall()}
    cur.execute(f'SELECT marathon_id, place FROM marathon_winners WHERE marathon_id IN ({marks}) AND user_id = %s', ids + [uid])
    mine = {r['marathon_id']: int(r['place']) for r in cur.fetchall()}
    return [{'id': r['id'], 'title': r['title'], 'start_ms': int(r['start_ms']), 'end_ms': int(r['end_ms']),
             'top_n': int(r['top_n']), 'prize_fund': funds.get(r['id'], 0), 'my_place': mine.get(r['id'])} for r in rows]


def past_view(cur, mid, uid, now=None) -> dict:
    """Tugagan marafon: g'oliblar va sovrinlari."""
    now = now or clock.now_ms()
    m = _row(cur, mid)
    if m['status'] != 'finished':
        raise MarafonError('Marafon topilmadi.', 'not_found', 404)
    friends = set(dostlar.friend_ids(cur, uid))
    cur.execute('SELECT * FROM marathon_winners WHERE marathon_id = %s ORDER BY place', (mid,))
    winners = [{'place': int(w['place']), 'user_id': int(w['user_id']), 'name': w['name'] or "O'quvchi",
                'photo_url': w['photo_url'], 'score': int(w['score']), 'amount': int(w['amount'] or 0),
                'note': w['note'] or '', 'me': int(w['user_id']) == uid, 'friend': int(w['user_id']) in friends}
               for w in cur.fetchall()]
    return {'marathon': public_info(cur, m, now), 'winners': winners,
            'me': {'place': next((w['place'] for w in winners if w['me']), None)}}


def banner(cur, uid, now=None):
    """Bosh sahifa banneri uchun qisqa ma'lumot (yoki None)."""
    now = now or clock.now_ms()
    m = shown_marathon(cur, now)
    if not m or m['status'] == 'finished':
        return None
    info = public_info(cur, m, now)
    st = standings(cur, m, now) if m['status'] == 'active' else []
    mine = next((p for p in st if p['user_id'] == uid), None)
    return {'id': m['id'], 'title': m['title'], 'status': m['status'], 'start_ms': info['start_ms'],
            'end_ms': info['end_ms'], 'prize_fund': info['prize_fund'], 'top_n': info['top_n'],
            'rank': mine['rank'] if mine else None, 'score': mine['score'] if mine else None,
            'joined': bool(mine) or eligibility(cur, m, uid, now)['joined'], 'now': now}


# ───────────────────────── Admin ko'rinishi ─────────────────────────

def _flags(cur, m, uid, u):
    """Admin uchun shubhali belgilar."""
    out = []
    try:
        created = as_utc(u.get('created_at')) if u else None
        created_ms = int(created.timestamp() * 1000) if created else None
    except (TypeError, ValueError, OSError, AttributeError):
        created_ms = None
    if created_ms and created_ms >= int(m['start_ms']):
        out.append('Yangi akkaunt (marafon boshlangandan keyin ochilgan)')
    # Chaqmoqli o'yinlarning ko'pchiligi bitta raqib bilan
    cur.execute('''SELECT c.session_id FROM game_chances c WHERE c.user_id = %s AND c.used_ms >= %s AND c.used_ms < %s''',
                (uid, int(m['start_ms']), int(m['end_ms'])))
    sessions = [r['session_id'] for r in cur.fetchall()]
    if len(sessions) >= 4:
        marks = ', '.join(['%s'] * len(sessions))
        cur.execute(f'SELECT user_id, COUNT(*) AS n FROM game_chances WHERE session_id IN ({marks}) AND user_id != %s '
                    f'GROUP BY user_id ORDER BY n DESC LIMIT 1', sessions + [uid])
        top = cur.fetchone()
        if top and int(top['n']) * 10 >= len(sessions) * 7:
            out.append(f"Chaqmoqli o'yinlarning {int(top['n'])}/{len(sessions)} tasi bitta raqib bilan (ID {top['user_id']})")
    return out


def admin_view(cur, now=None) -> dict:
    now = now or clock.now_ms()
    m = open_marathon(cur)
    cur.execute("SELECT id, title, status, start_ms, end_ms, finished_ms FROM marathons "
                "WHERE status IN ('finished', 'cancelled') ORDER BY id DESC LIMIT 20")
    history = [{'id': r['id'], 'title': r['title'], 'status': r['status'], 'start_ms': int(r['start_ms']),
                'end_ms': int(r['end_ms'])} for r in cur.fetchall()]
    out = {'marathon': None, 'history': history, 'now': now, 'channel': channel_chat(cur)}
    if not m:
        return out
    out['marathon'] = dict(public_info(cur, m, now), contact=m['contact'], rev=int(m['rev']),
                           prizes_full=prizes(cur, m['id']), channel_note=m['channel_note'])
    st = standings(cur, m, now, fresh=True)
    cur.execute('SELECT * FROM marathon_participants WHERE marathon_id = %s', (m['id'],))
    parts = {int(r['user_id']): r for r in cur.fetchall()}
    ids = list(parts)
    users = {}
    if ids:
        cur.execute(f"SELECT id, name, username, telegram_id, created_at FROM users WHERE id IN ({', '.join(['%s'] * len(ids))})",
                    ids)
        users = {int(r['id']): r for r in cur.fetchall()}
    rows = []
    for p in st:
        u = users.get(p['user_id']) or {}
        part = parts.get(p['user_id']) or {}
        rows.append({'rank': p['rank'], 'user_id': p['user_id'], 'name': u.get('name') or '—',
                     'username': u.get('username'), 'score': p['score'], 'parts': p['parts'],
                     'joined_ms': p['joined_ms'], 'added_by': part.get('added_by'), 'waived': bool(part.get('waived')),
                     'flags': _flags(cur, m, p['user_id'], u) if p['rank'] <= int(m['top_n']) + 10 else []})
    removed = [{'user_id': uid, 'name': (users.get(uid) or {}).get('name') or '—', 'reason': r['removed_reason'],
                'removed_ms': int(r['removed_ms'])} for uid, r in parts.items() if r['removed_ms']]
    out.update(standings=rows, removed=removed)
    return out


def admin_user(cur, mid, uid, now=None) -> dict:
    """Bitta qatnashchi: kunma-kun, manbalar bo'yicha chaqmoq va admin o'zgartirishlari."""
    now = now or clock.now_ms()
    m = _row(cur, mid)
    part = _participant(cur, mid, uid)
    if not part:
        raise MarafonError("Bu o'quvchi marafonda emas.", 'not_found', 404)
    until = min(now + 1, int(m['end_ms']))     # hozirgi millisekund ham kiradi, tugash vaqti — yo'q
    cur.execute('''SELECT source, ref, amount, premium, created_ms FROM chaqmoq_log
                   WHERE user_id = %s AND created_ms >= %s AND created_ms < %s ORDER BY created_ms, id''',
                (uid, max(int(m['start_ms']), int(part['joined_ms'])), until))
    rows = cur.fetchall()
    verdict = _shaxsiy_counted([r for r in rows if r['source'] == 'shaxsiy'])[1]
    days = {}
    for r in rows:
        counted = (m['audience'] != 'premium' or r['premium'] or part['waived'])
        if r['source'] == 'shaxsiy':
            counted = counted and verdict.get(str(r['ref']).split(':')[1] if ':' in str(r['ref']) else str(r['ref']), False)
        day = datetime.fromtimestamp(int(r['created_ms']) / 1000, TASHKENT_TZ).date().isoformat()
        d = days.setdefault(day, {'day': day, 'dars': 0, 'shaxsiy': 0, 'oyin': 0, 'kun': 0, 'rad': 0})
        if counted:
            d[r['source'] if r['source'] in d else 'dars'] += int(r['amount'])
        else:
            d['rad'] += int(r['amount'])
    cur.execute('SELECT amount, note, created_ms FROM marathon_adjust WHERE marathon_id = %s AND user_id = %s ORDER BY id',
                (mid, uid))
    adjusts = [{'amount': int(a['amount']), 'note': a['note'], 'created_ms': int(a['created_ms'])} for a in cur.fetchall()]
    u = _user(cur, uid)
    return {'user_id': uid, 'name': (u or {}).get('name'), 'days': [days[k] for k in sorted(days)], 'adjust': adjusts,
            'joined_ms': int(part['joined_ms']), 'added_by': part['added_by'], 'waived': bool(part['waived']),
            'removed_reason': part['removed_reason'], 'flags': _flags(cur, m, uid, u)}


def mark_paid(cur, conn, mid, uid, note, now=None):
    now = now or clock.now_ms()
    m = _row(cur, mid)
    cur.execute('SELECT * FROM marathon_winners WHERE marathon_id = %s AND user_id = %s', (mid, uid))
    w = cur.fetchone()
    if not w:
        raise MarafonError("Bu o'quvchi g'oliblar ro'yxatida yo'q.", 'not_found', 404)
    if w['paid_ms']:
        raise MarafonError("Bu g'olibga pul allaqachon o'tkazilgan deb belgilangan.", 'already', 409)
    cur.execute('UPDATE marathon_winners SET paid_ms = %s, paid_note = %s WHERE marathon_id = %s AND user_id = %s',
                (now, ' '.join(str(note or '').split())[:200] or None, mid, uid))
    conn.commit()
    u = _user(cur, uid)
    if u and u['telegram_id']:
        tgbot.send(u['telegram_id'], f"✅ «{html.escape(m['title'])}» marafoni sovrini ({html.escape(prize_text(w))}) "
                                     f"sizga o'tkazildi. Tabriklaymiz!", 'Ilovani ochish', 'leaderboard.html?tab=marafon')


def results(cur, mid) -> list:
    cur.execute('SELECT * FROM marathon_winners WHERE marathon_id = %s ORDER BY place', (mid,))
    return [{'place': int(w['place']), 'user_id': int(w['user_id']), 'name': w['name'], 'score': int(w['score']),
             'amount': int(w['amount'] or 0), 'note': w['note'] or '', 'notified': bool(w['notified']),
             'paid_ms': int(w['paid_ms']) if w['paid_ms'] else None, 'paid_note': w['paid_note']}
            for w in cur.fetchall()]


# ───────────────────────── Xabarlar ─────────────────────────

def _send_url(chat_id, text, button_text, url) -> bool:
    res = tgbot.tg_api('sendMessage', {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML',
                                       'reply_markup': {'inline_keyboard': [[{'text': button_text, 'url': url}]]}})
    return bool(res and res.get('ok'))


def _post_channel(cur, conn, m, text):
    chat = channel_chat(cur)
    if not chat:
        note = "Kanal havolasi yo'q yoki yopiq kanal — e'lon kanalga yuborilmadi."
    else:
        ok = _send_url(chat, text, 'Ilovani ochish', f'https://t.me/{tgbot.BOT_USERNAME}?start=marafon')
        note = f"Kanalga yuborildi ({chat})." if ok else \
            f"{chat} kanaliga yuborilmadi — botni kanalga admin qilib qo'shing ('Xabar joylash' ruxsati bilan)."
    cur.execute('UPDATE marathons SET channel_note = %s WHERE id = %s', (note, m['id']))
    conn.commit()


def _prize_lines(pz, limit=10) -> str:
    lines = [f"{p['place']}-o'rin — {html.escape(prize_text(p))}" for p in pz[:limit]]
    if len(pz) > limit:
        lines.append(f"… va yana {len(pz) - limit} ta sovrinli o'rin")
    return '\n'.join(lines)


def announce_start(cur, conn, m, now):
    pz = prizes(cur, m['id'])
    fund = sum(p['amount'] for p in pz)
    who = "faqat Bilim Premium a'zolari" if m['audience'] == 'premium' else 'hamma'
    days = max(1, round((int(m['end_ms']) - int(m['start_ms'])) / DAY_MS))
    text = (f"🏁 <b>«{html.escape(m['title'])}» yutuqli marafoni boshlandi!</b>\n\n"
            + (f"💰 Sovrin jamg'armasi: <b>{money(fund)}</b>\n" if fund else '')
            + f"🏆 Top-{m['top_n']} sovrin oladi:\n{_prize_lines(pz)}\n\n"
            f"⏳ {days} kun — {local_text(m['end_ms'])} gacha (Toshkent vaqti)\n"
            f"👥 Qatnashadi: {who}\n\n"
            "Darslar, o'yinlar va kun savolidan olgan chaqmoqlaringiz sanaladi. "
            "Qatnashish: Reyting → Marafon → «Qatnashish».")
    try:
        broadcast.start(cur, conn, text, now, html=True, button='Marafonga qatnashish',
                        path='leaderboard.html?tab=marafon', everyone=True, queue=True)
    except broadcast.BroadcastError:
        logger.warning('Marafon e\'loni navbatga qo\'yilmadi', exc_info=True)
    _post_channel(cur, conn, m, text)


def finalize(cur, conn, m, now) -> list:
    """Tugagan marafon: g'oliblarni muzlatadi (bir marta — CAS), xabarlarni yuboradi."""
    cur.execute("UPDATE marathons SET status = 'finished', finished_ms = %s, rev = rev + 1 "
                "WHERE id = %s AND status = 'active'", (now, m['id']))
    if cur.rowcount != 1:
        conn.rollback()
        return []
    m = dict(m, rev=int(m['rev']) + 1)
    st = standings(cur, m, int(m['end_ms']), fresh=True)
    pz = {p['place']: p for p in prizes(cur, m['id'])}
    winners = [p for p in st if p['score'] > 0][:int(m['top_n'])]
    cards = _cards(cur, [w['user_id'] for w in winners], now)
    for w in winners:
        prize = pz.get(w['rank']) or {'amount': 0, 'note': '', 'image_id': None}
        c = cards.get(w['user_id']) or {}
        cur.execute('''INSERT INTO marathon_winners (marathon_id, place, user_id, name, photo_url, score, amount, note, image_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (m['id'], w['rank'], w['user_id'], c.get('name'), c.get('photo_url'), w['score'],
                     prize['amount'], prize.get('note') or None, prize.get('image_id')))
    conn.commit()
    threading.Thread(target=_notify_winners, args=(m['id'],), name='bilimsari-marafon-golib', daemon=True).start()
    lines = [f"{w['rank']}. {html.escape((cards.get(w['user_id']) or {}).get('name') or 'O‘quvchi')} — "
             f"{w['score']} chaqmoq" for w in winners[:10]]
    text = (f"🏁 <b>«{html.escape(m['title'])}» marafoni yakunlandi!</b>\n\n"
            + ("🏆 G'oliblar:\n" + '\n'.join(lines) if lines else "Bu safar g'olib bo'lmadi.")
            + ("\n…" if len(winners) > 10 else '')
            + "\n\nHammaga rahmat! Keyingi marafonda omad!")
    try:
        broadcast.start(cur, conn, text, now, html=True, button='Natijalar', path='leaderboard.html?tab=marafon',
                        everyone=True, queue=True)
    except broadcast.BroadcastError:
        logger.warning('Marafon natijasi navbatga qo\'yilmadi', exc_info=True)
    _post_channel(cur, conn, m, text)
    return winners


def _notify_winners(mid):
    """G'oliblarga xabar — eslatmani o'chirgan bo'lsa ham (pul haqida). Fonda, o'z ulanishi bilan."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        m = _row(cur, mid)
        cur.execute('SELECT * FROM marathon_winners WHERE marathon_id = %s AND notified = 0 ORDER BY place', (mid,))
        for w in cur.fetchall():
            u = _user(cur, w['user_id'])
            if not u or not u['telegram_id']:
                continue
            text = (f"🏆 <b>Tabriklaymiz!</b> Siz «{html.escape(m['title'])}» marafonida <b>{w['place']}-o'rinni</b> "
                    f"egalladingiz ({w['score']} chaqmoq)!\n\nSovrin: <b>{html.escape(prize_text(w))}</b>\n\n"
                    f"Pulingizni kartaga olish uchun @{html.escape(m['contact'])} ga yozing.")
            if _send_url(u['telegram_id'], text, f"@{m['contact']} ga yozish", f"https://t.me/{m['contact']}"):
                cur.execute('UPDATE marathon_winners SET notified = 1 WHERE marathon_id = %s AND place = %s',
                            (mid, w['place']))
                conn.commit()
            time.sleep(0.05)
    except Exception:  # noqa: BLE001
        conn.rollback()
        logger.exception("Marafon g'oliblariga xabar yuborilmadi")
    finally:
        cur.close()
        conn.close()


def _to_participants(cur, m, make_text, only_notify=True, button='Marafon', path='leaderboard.html?tab=marafon'):
    """Qatnashchilarga shaxsiy xabar — fonda (ko'p bo'lsa so'rovni ushlab turmasin)."""
    st = {p['user_id']: p for p in standings(cur, m, fresh=True)}
    cur.execute('''SELECT u.id, u.telegram_id, u.notify FROM marathon_participants p JOIN users u ON u.id = p.user_id
                   WHERE p.marathon_id = %s AND p.removed_ms IS NULL AND u.telegram_id IS NOT NULL''', (m['id'],))
    targets = [(r['telegram_id'], make_text(st.get(int(r['id']))))
               for r in cur.fetchall() if not only_notify or int(r['notify'] if r['notify'] is not None else 1)]
    targets = [t for t in targets if t[1]]

    def run():
        for chat, text in targets:
            try:
                tgbot.send(chat, text, button, path)
            except Exception:  # noqa: BLE001
                logger.warning('Marafon xabari yuborilmadi', exc_info=True)
            time.sleep(0.05)

    threading.Thread(target=run, name='bilimsari-marafon', daemon=True).start()
    return len(targets)


def _place_text(m, p) -> str:
    return f"Siz hozir <b>{p['rank']}-o'rindasiz</b> ({p['score']} chaqmoq)." if p else ''


def _gap_text(m, st_list, p) -> str:
    top_n = int(m['top_n'])
    if p['rank'] <= top_n:
        return " Sovrinli o'rindasiz — shunday davom eting!"
    if len(st_list) >= top_n:
        need = st_list[top_n - 1]['score'] - p['score'] + 1
        return f" Top-{top_n} ga kirish uchun yana {need} chaqmoq kerak."
    return ''


def reminders(cur, conn, m, now):
    """Kechki eslatma (har kuni), tugashiga 24 soat va 1 soat qolganda, Premium tugayotganda."""
    end = int(m['end_ms'])
    local = datetime.fromtimestamp(now / 1000, TASHKENT_TZ)
    title = html.escape(m['title'])

    def text_for(extra):
        st_list = standings(cur, m, now, fresh=True)       # faqat xabar yuboriladigan paytda hisoblanadi

        def make(p):
            if not p:
                return None
            return f"🏃 «{title}» marafoni: {_place_text(m, p)}{_gap_text(m, st_list, p)}{extra}"
        return make

    if end - HOUR_MS <= now < end and _claim(cur, conn, m['id'], 'end1', now):
        _to_participants(cur, m, text_for(' ⏰ Marafon tugashiga 1 soat qoldi!'))
    elif end - DAY_MS <= now < end - HOUR_MS and _claim(cur, conn, m['id'], 'end24', now):
        _to_participants(cur, m, text_for(' ⏳ Marafon tugashiga 24 soat qoldi.'))
    elif (local.hour >= REMIND_HOUR and now < end - DAY_MS and now - int(m['start_ms']) > 6 * HOUR_MS
          and _claim(cur, conn, m['id'], 'daily:' + local.date().isoformat(), now)):
        days_left = max(1, round((end - now) / DAY_MS))
        _to_participants(cur, m, text_for(f' Marafon tugashiga {days_left} kun qoldi.'))
    if m['audience'] == 'premium':
        cur.execute('''SELECT u.id, u.telegram_id, u.premium_until FROM marathon_participants p JOIN users u ON u.id = p.user_id
                       WHERE p.marathon_id = %s AND p.removed_ms IS NULL AND p.waived = 0 AND u.telegram_id IS NOT NULL
                         AND u.premium_until IS NOT NULL AND u.premium_until > %s AND u.premium_until < %s
                         AND u.premium_until < %s''', (m['id'], now, now + PREMIUM_WARN_MS, end))
        for r in cur.fetchall():
            if _claim(cur, conn, m['id'], f"prem:{r['id']}:{r['premium_until']}", now):
                tgbot.send(r['telegram_id'], f"⚠️ Bilim Premium'ingiz {local_text(r['premium_until'])} da tugaydi. "
                                             f"Premium tugasa, «{title}» marafonida yangi chaqmoqlar sanalmay qoladi.",
                           'Premiumni uzaytirish', 'premium.html')


def tick(cur, conn, now=None):
    """Rejalashtiruvchi (har daqiqa) va admin amallaridan keyin: boshlash, eslatmalar, yakunlash."""
    now = now or clock.now_ms()
    cur.execute("SELECT * FROM marathons WHERE status IN ('scheduled', 'active') ORDER BY id")
    for m in [dict(r) for r in cur.fetchall()]:
        if m['status'] == 'scheduled' and now >= int(m['start_ms']):
            cur.execute("UPDATE marathons SET status = 'active', started_ms = %s, rev = rev + 1 "
                        "WHERE id = %s AND status = 'scheduled'", (now, m['id']))
            took = cur.rowcount == 1
            conn.commit()
            if took:
                m.update(status='active', started_ms=now, rev=int(m['rev']) + 1)
                if _claim(cur, conn, m['id'], 'start', now):
                    announce_start(cur, conn, m, now)
        if m['status'] == 'active':
            if now >= int(m['end_ms']):
                finalize(cur, conn, m, now)
            else:
                try:
                    reminders(cur, conn, m, now)
                except Exception:  # noqa: BLE001
                    conn.rollback()
                    logger.exception('Marafon eslatmalari xatosi')


def run_tick():
    """notify.tick uchun: o'z ulanishi bilan."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        tick(cur, conn)
    except Exception:  # noqa: BLE001
        conn.rollback()
        logger.exception('Marafon tick xatosi')
    finally:
        cur.close()
        conn.close()


def cleanup_user(cur, uid):
    cur.execute('DELETE FROM marathon_participants WHERE user_id = %s', (uid,))
    cur.execute('DELETE FROM marathon_adjust WHERE user_id = %s', (uid,))
