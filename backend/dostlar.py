# -*- coding: utf-8 -*-
"""
Do'stlar: so'rov yuborish/qabul qilish, qidiruv (ID, @username yoki ism), do'stlar ro'yxati
(onlayn holati bilan), do'stlar reytingi, faollik lentasi, o'yinga chaqirish va shikoyatlar.

Chat yo'q (egasining qarori). Hammasi bepul. Bir o'quvchida ko'pi bilan 50 ta do'st.
Shikoyatni admin ko'rib chiqadi; kerak bo'lsa o'quvchining do'stlik imkonini yopadi
(users.friends_blocked) — u so'rov yubora olmaydi va qidiruvda chiqmaydi.
"""

import html
import logging
from datetime import datetime, timezone

import admin_auth
import achievements
import boshqaruv
import premium
import study
import tgbot
from db import add_column_if_missing
from games import clock

logger = logging.getLogger('bilimsari.dostlar')

MAX_FRIENDS = 50
MAX_PENDING_OUT = 30
REQUESTS_PER_DAY = 20
ONLINE_MS = 5 * 60 * 1000              # shu vaqt ichida faol bo'lsa — "onlayn"
INVITE_TTL_MS = 15 * 60 * 1000         # o'yinga chaqiruv shu vaqt amal qiladi
INVITE_REPEAT_MS = 2 * 60 * 1000       # bir do'stni qayta chaqirish oralig'i
REPORTS_PER_DAY = 5
FEED_DAYS = 7
DAY_MS = 24 * 3600 * 1000

REPORT_REASONS = {
    'ism': 'Nomaqbul ism',
    'rasm': 'Nomaqbul rasm',
    'haqorat': 'Haqorat yoki bezorilik',
    'boshqa': 'Boshqa',
}


class DostError(Exception):
    def __init__(self, message, code='bad_request', http_status=400):
        super().__init__(message)
        self.message, self.code, self.http_status = message, code, http_status


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS friend_requests (
            id SERIAL PRIMARY KEY,
            from_id INTEGER NOT NULL,
            to_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_ms BIGINT NOT NULL,
            decided_ms BIGINT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS friendships (
            user_a INTEGER NOT NULL,
            user_b INTEGER NOT NULL,
            created_ms BIGINT NOT NULL,
            PRIMARY KEY (user_a, user_b)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS friend_invites (
            id SERIAL PRIMARY KEY,
            from_id INTEGER NOT NULL,
            to_id INTEGER NOT NULL,
            room_code TEXT NOT NULL,
            created_ms BIGINT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_reports (
            id SERIAL PRIMARY KEY,
            reporter_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            note TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            action TEXT,
            resolved_by TEXT,
            created_ms BIGINT NOT NULL,
            resolved_ms BIGINT
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_friend_req_to ON friend_requests (to_id, status)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_friend_req_from ON friend_requests (from_id, status)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_friendships_b ON friendships (user_b)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_friend_inv_to ON friend_invites (to_id, created_ms)')
    conn.commit()
    add_column_if_missing(cur, conn, 'users', 'last_seen_ms', 'BIGINT')
    add_column_if_missing(cur, conn, 'users', 'friends_blocked', 'INTEGER NOT NULL DEFAULT 0')


# ───────────────────────── Yordamchilar ─────────────────────────

def _pair(x, y):
    x, y = int(x), int(y)
    return (x, y) if x < y else (y, x)


def friend_ids(cur, uid) -> list:
    cur.execute('SELECT user_a, user_b FROM friendships WHERE user_a = %s OR user_b = %s', (uid, uid))
    return [r['user_b'] if r['user_a'] == uid else r['user_a'] for r in cur.fetchall()]


def count(cur, uid) -> int:
    cur.execute('SELECT COUNT(*) AS n FROM friendships WHERE user_a = %s OR user_b = %s', (uid, uid))
    return int(cur.fetchone()['n'])


def are_friends(cur, x, y) -> bool:
    a, b = _pair(x, y)
    cur.execute('SELECT 1 FROM friendships WHERE user_a = %s AND user_b = %s', (a, b))
    return cur.fetchone() is not None


def _pending(cur, from_id, to_id):
    cur.execute("SELECT * FROM friend_requests WHERE from_id = %s AND to_id = %s AND status = 'pending'",
                (from_id, to_id))
    return cur.fetchone()


def relation(cur, me, other) -> dict:
    """{'state': self|friend|outgoing|incoming|none, 'request_id'}"""
    if int(me) == int(other):
        return {'state': 'self'}
    if are_friends(cur, me, other):
        return {'state': 'friend'}
    out = _pending(cur, me, other)
    if out:
        return {'state': 'outgoing', 'request_id': out['id']}
    inc = _pending(cur, other, me)
    if inc:
        return {'state': 'incoming', 'request_id': inc['id']}
    return {'state': 'none'}


def _cards(cur, ids, now=None) -> dict:
    """{id: kartochka} — ism, rasm, Premium emoji/ramka, onlayn holati."""
    ids = sorted({int(i) for i in ids if i})
    if not ids:
        return {}
    now = now or clock.now_ms()
    cur.execute(f"SELECT id, name, photo_url, last_seen_ms FROM users WHERE id IN ({', '.join(['%s'] * len(ids))})", ids)
    rows = [{'id': int(r['id']), 'user_id': int(r['id']), 'name': r['name'] or "O'quvchi", 'photo_url': r['photo_url'],
             'last_seen_ms': int(r['last_seen_ms']) if r['last_seen_ms'] else None,
             'online': bool(r['last_seen_ms'] and now - int(r['last_seen_ms']) < ONLINE_MS)} for r in cur.fetchall()]
    premium.decorate(cur, rows, now=now)
    for r in rows:
        r.pop('user_id', None)
    return {r['id']: r for r in rows}


def _user(cur, uid):
    cur.execute('SELECT id, name, telegram_id, notify, friends_blocked, lang FROM users WHERE id = %s', (uid,))
    return cur.fetchone()


def _ism(row, default="Do'stingiz"):
    return html.escape(((row and row['name']) or default).split()[0])


def _bot(row, text, button, path) -> bool:
    """Bot orqali xabar (eslatmalar yoqilgan bo'lsa). Yuborilmasa ham asosiy amal buzilmaydi."""
    if not row or not row['telegram_id'] or not int(row['notify'] if row['notify'] is not None else 1):
        return False
    if boshqaruv.bot_paused():
        return False                   # admin botni vaqtincha to'xtatgan
    try:
        lang = 'ru' if row.get('lang') == 'ru' else 'uz'
        return bool(tgbot.send(row['telegram_id'], text, button, path, lang=lang)[0])
    except Exception:  # noqa: BLE001
        logger.warning("Do'stlar xabari yuborilmadi", exc_info=True)
        return False


# ───────────────────────── Qidiruv ─────────────────────────

def search(cur, me, q, limit=20) -> list:
    """ID (#15 yoki 15), @username yoki ism bo'yicha. O'zi va do'stlik imkoni yopilganlar chiqmaydi."""
    q = ' '.join(str(q or '').split())[:40]
    if not q:
        return []
    base = 'SELECT id, name FROM users WHERE id != %s AND COALESCE(friends_blocked, 0) = 0 AND onboarded = TRUE'
    digits = q.lstrip('#')
    if digits.isascii() and digits.isdigit():
        if len(digits) > 9:                       # INTEGER chegarasidan katta — bunday ID yo'q
            return []
        cur.execute(base + ' AND id = %s', (me, int(digits)))
        ids = [r['id'] for r in cur.fetchall()]
    elif q.startswith('@'):
        name = q[1:].lower()
        if len(name) < 2:
            return []
        cur.execute(base + ' AND LOWER(username) LIKE %s ORDER BY LENGTH(username), id LIMIT %s',
                    (me, name.replace('%', '') + '%', limit))
        ids = [r['id'] for r in cur.fetchall()]
    else:
        if len(q) < 2:
            return []
        low = q.lower().replace('%', '')
        cur.execute(base + ' AND LOWER(name) LIKE %s ORDER BY CASE WHEN LOWER(name) LIKE %s THEN 0 ELSE 1 END, id LIMIT %s',
                    (me, '%' + low + '%', low + '%', limit))
        ids = [r['id'] for r in cur.fetchall()]
    cards = _cards(cur, ids)
    out = []
    for i in ids:
        c = cards.get(int(i))
        if c:
            out.append(dict(c, relation=relation(cur, me, i)))
    return out


# ───────────────────────── So'rovlar ─────────────────────────

def send_request(cur, conn, me, to, now=None) -> dict:
    now = now or clock.now_ms()
    to = int(to)
    if to == int(me):
        raise DostError("O'zingizga so'rov yubora olmaysiz.")
    target = _user(cur, to)
    if not target:
        raise DostError("Bunday o'quvchi topilmadi.", 'not_found', 404)
    mine = _user(cur, me)
    if mine and int(mine['friends_blocked'] or 0):
        raise DostError("Sizda do'stlik imkoni vaqtincha yopilgan.", 'blocked', 403)
    if are_friends(cur, me, to):
        raise DostError("Siz allaqachon do'stsiz.", 'already')
    inc = _pending(cur, to, me)
    if inc:                                       # u allaqachon so'rov yuborgan — darhol do'st bo'lamiz
        return respond(cur, conn, me, inc['id'], True, now)
    if _pending(cur, me, to):
        raise DostError("So'rov allaqachon yuborilgan.", 'already')
    if count(cur, me) >= MAX_FRIENDS:
        raise DostError(f"Sizda {MAX_FRIENDS} ta do'st bor — bu eng ko'pi.", 'limit')
    if count(cur, to) >= MAX_FRIENDS:
        raise DostError("Bu o'quvchining do'stlari soni to'lgan.", 'limit')
    cur.execute("SELECT COUNT(*) AS n FROM friend_requests WHERE from_id = %s AND status = 'pending'", (me,))
    if int(cur.fetchone()['n']) >= MAX_PENDING_OUT:
        raise DostError("Javob kutilayotgan so'rovlaringiz juda ko'p. Avval ular javob bersin.", 'limit')
    cur.execute('SELECT COUNT(*) AS n FROM friend_requests WHERE from_id = %s AND created_ms >= %s', (me, now - DAY_MS))
    if int(cur.fetchone()['n']) >= REQUESTS_PER_DAY:
        raise DostError("Bugun juda ko'p so'rov yubordingiz. Ertaga yana urinib ko'ring.", 'limit', 429)
    cur.execute("INSERT INTO friend_requests (from_id, to_id, status, created_ms) VALUES (%s, %s, 'pending', %s)",
                (me, to, now))
    conn.commit()
    req = _pending(cur, me, to)
    kim = _ism(mine, "O'quvchi")
    _bot(target, tgbot.L(f"👋 <b>{kim}</b> sizga do'stlik so'rovi yubordi.", f"👋 <b>{kim}</b> отправил(а) вам заявку в друзья."),
         tgbot.L("Ko'rish", 'Посмотреть'), 'dostlar.html?tab=sorovlar')
    return {'state': 'outgoing', 'request_id': req['id'] if req else None}


def respond(cur, conn, me, request_id, accept, now=None) -> dict:
    now = now or clock.now_ms()
    cur.execute("SELECT * FROM friend_requests WHERE id = %s AND to_id = %s AND status = 'pending'", (request_id, me))
    req = cur.fetchone()
    if not req:
        raise DostError("So'rov topilmadi yoki allaqachon javob berilgan.", 'not_found', 404)
    if accept:
        if count(cur, me) >= MAX_FRIENDS:
            raise DostError(f"Sizda {MAX_FRIENDS} ta do'st bor — bu eng ko'pi.", 'limit')
        if count(cur, req['from_id']) >= MAX_FRIENDS:
            raise DostError("Bu o'quvchining do'stlari soni to'lgan.", 'limit')
        a, b = _pair(me, req['from_id'])
        cur.execute('INSERT INTO friendships (user_a, user_b, created_ms) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                    (a, b, now))
    cur.execute('UPDATE friend_requests SET status = %s, decided_ms = %s WHERE id = %s',
                ('accepted' if accept else 'declined', now, request_id))
    if accept:                                    # teskari yo'nalishdagi ochiq so'rov ham yopiladi
        cur.execute("UPDATE friend_requests SET status = 'accepted', decided_ms = %s "
                    "WHERE from_id = %s AND to_id = %s AND status = 'pending'", (now, me, req['from_id']))
    conn.commit()
    if accept:
        kim = _ism(_user(cur, me))
        _bot(_user(cur, req['from_id']), tgbot.L(f"🤝 <b>{kim}</b> do'stlik so'rovingizni qabul qildi!",
                                                 f"🤝 <b>{kim}</b> принял(а) вашу заявку в друзья!"),
             tgbot.L("Do'stlar", 'Друзья'), 'dostlar.html')
    return {'state': 'friend' if accept else 'none'}


def cancel(cur, conn, me, request_id):
    cur.execute("UPDATE friend_requests SET status = 'cancelled' WHERE id = %s AND from_id = %s AND status = 'pending'",
                (request_id, me))
    ok = cur.rowcount == 1
    conn.commit()
    if not ok:
        raise DostError("So'rov topilmadi.", 'not_found', 404)


def remove(cur, conn, me, other):
    a, b = _pair(me, other)
    cur.execute('DELETE FROM friendships WHERE user_a = %s AND user_b = %s', (a, b))
    ok = cur.rowcount == 1
    conn.commit()
    if not ok:
        raise DostError("Bu o'quvchi do'stingiz emas.", 'not_found', 404)


# ───────────────────────── Ro'yxat, reyting, lenta ─────────────────────────

def overview(cur, me, now=None) -> dict:
    now = now or clock.now_ms()
    ids = friend_ids(cur, me)
    cur.execute("SELECT id, from_id, created_ms FROM friend_requests WHERE to_id = %s AND status = 'pending' "
                "ORDER BY created_ms DESC", (me,))
    inc = cur.fetchall()
    cur.execute("SELECT id, to_id, created_ms FROM friend_requests WHERE from_id = %s AND status = 'pending' "
                "ORDER BY created_ms DESC", (me,))
    out = cur.fetchall()
    cards = _cards(cur, ids + [r['from_id'] for r in inc] + [r['to_id'] for r in out], now)
    friends = [cards[i] for i in ids if i in cards]
    friends.sort(key=lambda c: (not c['online'], -(c['last_seen_ms'] or 0), c['name']))
    return {
        'friends': friends,
        'incoming': [dict(cards[r['from_id']], request_id=r['id'], at_ms=int(r['created_ms']))
                     for r in inc if r['from_id'] in cards],
        'outgoing': [dict(cards[r['to_id']], request_id=r['id'], at_ms=int(r['created_ms']))
                     for r in out if r['to_id'] in cards],
        'count': len(friends), 'max': MAX_FRIENDS,
        'invites': invites(cur, me, now),
    }


def leaderboard(cur, me) -> list:
    """Faqat do'stlar va o'zi orasidagi chaqmoq reytingi."""
    circle = set(friend_ids(cur, me)) | {int(me)}
    board = study.leaderboard(cur, me, limit=10 ** 6)
    score = {int(e['user_id']): int(e['chaqmoq']) for e in board['top'] if int(e['user_id']) in circle}
    cards = _cards(cur, circle)
    rows = [dict(cards[i], chaqmoq=score.get(i, 0), me=(i == int(me))) for i in circle if i in cards]
    rows.sort(key=lambda r: (-r['chaqmoq'], r['name']))
    for i, r in enumerate(rows, start=1):
        r['rank'] = i
    return rows


def feed(cur, me, now=None, limit=40) -> list:
    """Do'stlarning oxirgi 7 kundagi yutuqlari: mavzu, nishon, o'yin g'alabasi, kun savoli."""
    now = now or clock.now_ms()
    ids = friend_ids(cur, me)
    if not ids:
        return []
    since = now - FEED_DAYS * DAY_MS
    marks = ', '.join(['%s'] * len(ids))
    ev = []
    since_dt = datetime.fromtimestamp(since / 1000, timezone.utc).replace(tzinfo=None)
    cur.execute(f'''SELECT p.user_id, p.completed_at, t.title FROM user_progress p JOIN topics t ON t.id = p.topic_id
                    WHERE p.user_id IN ({marks}) AND p.status = %s AND p.completed_at >= %s
                    ORDER BY p.completed_at DESC LIMIT 60''', ids + [study.STATUS_COMPLETED, since_dt])
    for r in cur.fetchall():
        at = r['completed_at']
        if isinstance(at, str):
            try:
                at = datetime.fromisoformat(at)
            except ValueError:
                continue
        ms = int(at.replace(tzinfo=timezone.utc).timestamp() * 1000) if at else since
        ev.append({'user': r['user_id'], 'kind': 'mavzu', 'ms': ms, 'text': f"«{r['title']}» mavzusini tugatdi"})
    titles = {k: (t, achievements.TIERS.get(k, 'oltin')) for k, t, _d, _i, _m, _g in achievements.ACHIEVEMENTS}
    cur.execute(f'SELECT user_id, key, unlocked_ms FROM user_achievements WHERE user_id IN ({marks}) AND unlocked_ms >= %s',
                ids + [since])
    for r in cur.fetchall():
        if r['key'] in titles:
            t, tier = titles[r['key']]
            ev.append({'user': r['user_id'], 'kind': 'nishon', 'ms': int(r['unlocked_ms']), 'tier': tier,
                       'text': f"«{t}» nishonini oldi"})
    cur.execute(f'SELECT user_id, created_ms FROM game_results WHERE user_id IN ({marks}) AND won = 1 AND created_ms >= %s',
                ids + [since])
    for r in cur.fetchall():
        ev.append({'user': r['user_id'], 'kind': 'oyin', 'ms': int(r['created_ms']), 'text': "bilim bellashuvida g'olib bo'ldi"})
    cur.execute(f'SELECT user_id, answered_ms FROM daily_answers WHERE user_id IN ({marks}) AND correct = 1 '
                f'AND answered_ms >= %s', ids + [since])
    for r in cur.fetchall():
        ev.append({'user': r['user_id'], 'kind': 'kun', 'ms': int(r['answered_ms']), 'text': "kun savoliga to'g'ri javob berdi"})
    ev.sort(key=lambda e: -e['ms'])
    ev = ev[:limit]
    cards = _cards(cur, [e['user'] for e in ev], now)
    return [dict(e, user=cards[e['user']]) for e in ev if e['user'] in cards]


# ───────────────────────── O'yinga chaqirish ─────────────────────────

def invite(cur, conn, me, friend, code, now=None) -> dict:
    now = now or clock.now_ms()
    friend = int(friend)
    if not are_friends(cur, me, friend):
        raise DostError("Faqat do'stlaringizni chaqira olasiz.", 'not_friend', 403)
    code = str(code or '').strip().upper()
    cur.execute('SELECT id, code, status, game_type, subject FROM game_rooms WHERE code = %s', (code,))
    room = cur.fetchone()
    if not room or room['status'] != 'waiting':
        raise DostError("Bu o'yin allaqachon boshlangan yoki yopilgan.", 'room_closed', 409)
    cur.execute("SELECT user_id FROM game_room_players WHERE room_id = %s AND state = 'active'", (room['id'],))
    inside = {int(r['user_id']) for r in cur.fetchall()}
    if int(me) not in inside:
        raise DostError("Siz bu o'yinda emassiz.", 'not_in_room', 403)
    if friend in inside:
        raise DostError("Do'stingiz allaqachon shu o'yinda.", 'already')
    cur.execute('SELECT 1 FROM friend_invites WHERE from_id = %s AND to_id = %s AND created_ms >= %s',
                (me, friend, now - INVITE_REPEAT_MS))
    if cur.fetchone():
        raise DostError("Bu do'stingizni hozirgina chaqirdingiz — biroz kuting.", 'too_soon', 429)
    cur.execute('INSERT INTO friend_invites (from_id, to_id, room_code, created_ms) VALUES (%s, %s, %s, %s)',
                (me, friend, code, now))
    conn.commit()
    # Botga xabar — do'st ilovada bo'lmasa ham ko'rsin (eslatmalar yoqilgan bo'lsa)
    from games import catalog
    game = catalog.GAMES.get(room['game_type'], {}).get('name', "O'yin")
    subject = catalog.subject_info(room['subject'])['name'] if room['subject'] else ''
    kim = _ism(_user(cur, me))
    text = tgbot.L(f"🎮 <b>{kim}</b> sizni o'yinga chaqirdi: <b>{html.escape(game)}"
                   + (f" • {html.escape(subject)}" if subject else '') + f"</b>\nRoom kodi: <b>{code}</b>",
                   f"🎮 <b>{kim}</b> зовёт вас в игру: <b>{html.escape(game)}"
                   + (f" • {html.escape(tgbot.fan_ru(subject))}" if subject else '') + f"</b>\nКод комнаты: <b>{code}</b>")
    return {'sent': _bot(_user(cur, friend), text, tgbot.L("Qo'shilish", 'Присоединиться'), f'games.html?kod={code}')}


def invites(cur, me, now=None) -> list:
    """Menga kelgan, hali amal qiladigan (xona ochiq) chaqiruvlar."""
    now = now or clock.now_ms()
    cur.execute('''SELECT i.id, i.from_id, i.room_code, i.created_ms, r.game_type, r.id AS room_id FROM friend_invites i
                   JOIN game_rooms r ON r.code = i.room_code
                   WHERE i.to_id = %s AND i.created_ms >= %s AND r.status = 'waiting'
                   ORDER BY i.created_ms DESC''', (me, now - INVITE_TTL_MS))
    rows, seen = [], set()
    for r in cur.fetchall():
        if r['room_code'] in seen:
            continue
        cur.execute("SELECT 1 FROM game_room_players WHERE room_id = %s AND user_id = %s AND state = 'active'",
                    (r['room_id'], me))
        if cur.fetchone():
            continue
        seen.add(r['room_code'])
        rows.append(r)
    cards = _cards(cur, [r['from_id'] for r in rows], now)
    from games import catalog
    return [{'id': r['id'], 'code': r['room_code'], 'at_ms': int(r['created_ms']),
             'game': catalog.GAMES.get(r['game_type'], {}).get('name', "O'yin"), 'from': cards[r['from_id']]}
            for r in rows if r['from_id'] in cards]


# ───────────────────────── Shikoyatlar ─────────────────────────

def report(cur, conn, me, target, reason, note=None, now=None):
    now = now or clock.now_ms()
    if reason not in REPORT_REASONS:
        raise DostError('Sababni tanlang.')
    if int(target) == int(me):
        raise DostError("O'zingizga shikoyat qila olmaysiz.")
    if not _user(cur, target):
        raise DostError("Bunday o'quvchi topilmadi.", 'not_found', 404)
    cur.execute('SELECT COUNT(*) AS n FROM user_reports WHERE reporter_id = %s AND created_ms >= %s', (me, now - DAY_MS))
    if int(cur.fetchone()['n']) >= REPORTS_PER_DAY:
        raise DostError("Bugun juda ko'p shikoyat yubordingiz.", 'limit', 429)
    cur.execute("SELECT 1 FROM user_reports WHERE reporter_id = %s AND target_id = %s AND status = 'open'", (me, target))
    if cur.fetchone():
        raise DostError("Bu o'quvchi haqida shikoyatingiz allaqachon ko'rib chiqilmoqda.", 'already')
    note = ' '.join(str(note or '').split())[:300] or None
    cur.execute('INSERT INTO user_reports (reporter_id, target_id, reason, note, created_ms) VALUES (%s, %s, %s, %s, %s)',
                (me, target, reason, note, now))
    conn.commit()
    try:
        cur.execute('SELECT id, name FROM users WHERE id IN (%s, %s)', (me, target))
        names = {r['id']: r['name'] for r in cur.fetchall()}
        text = (f"🚩 <b>Shikoyat</b>: {html.escape(names.get(int(target)) or '?')} (ID {target})\n"
                f"Sabab: {html.escape(REPORT_REASONS[reason])}" + (f"\nIzoh: {html.escape(note)}" if note else '') +
                f"\nKimdan: {html.escape(names.get(int(me)) or '?')} (ID {me})")
        for admin in admin_auth.admin_ids():
            tgbot.send(admin, text, 'Admin panel', 'admin.html')
    except Exception:  # noqa: BLE001  (xabar yuborilmasa ham shikoyat saqlangan)
        logger.warning('Shikoyat haqida xabar yuborilmadi', exc_info=True)


def admin_reports(cur) -> dict:
    cur.execute('''SELECT r.*, t.name AS target_name, t.photo_url AS target_photo, COALESCE(t.friends_blocked, 0) AS blocked,
                          p.name AS reporter_name
                   FROM user_reports r LEFT JOIN users t ON t.id = r.target_id LEFT JOIN users p ON p.id = r.reporter_id
                   ORDER BY CASE WHEN r.status = 'open' THEN 0 ELSE 1 END, r.created_ms DESC LIMIT 100''')
    items = [{'id': r['id'], 'target_id': r['target_id'], 'target_name': r['target_name'], 'target_photo': r['target_photo'],
              'blocked': bool(r['blocked']), 'reporter_id': r['reporter_id'], 'reporter_name': r['reporter_name'],
              'reason': REPORT_REASONS.get(r['reason'], r['reason']), 'note': r['note'], 'status': r['status'],
              'action': r['action'], 'created_ms': int(r['created_ms']),
              'resolved_ms': int(r['resolved_ms']) if r['resolved_ms'] else None} for r in cur.fetchall()]
    cur.execute('SELECT id, name FROM users WHERE COALESCE(friends_blocked, 0) = 1 ORDER BY name')
    blocked = [{'id': r['id'], 'name': r['name']} for r in cur.fetchall()]
    return {'reports': items, 'open': sum(1 for i in items if i['status'] == 'open'), 'blocked': blocked}


def resolve(cur, conn, report_id, action, by, now=None):
    now = now or clock.now_ms()
    if action not in ('dismiss', 'block'):
        raise DostError("Noma'lum amal.")
    cur.execute('SELECT target_id, status FROM user_reports WHERE id = %s', (report_id,))
    row = cur.fetchone()
    if not row:
        raise DostError('Shikoyat topilmadi.', 'not_found', 404)
    if row['status'] != 'open':                   # ikki marta bosilsa — jurnalga ikki yozuv tushmasin
        raise DostError("Bu shikoyat allaqachon ko'rib chiqilgan.", 'already')
    if action == 'block':
        set_blocked(cur, conn, row['target_id'], True)
        # Shu o'quvchi haqidagi barcha ochiq shikoyatlar yopiladi
        cur.execute("UPDATE user_reports SET status = 'resolved', action = 'block', resolved_by = %s, resolved_ms = %s "
                    "WHERE target_id = %s AND status = 'open'", (by, now, row['target_id']))
    cur.execute("UPDATE user_reports SET status = 'resolved', action = %s, resolved_by = %s, resolved_ms = %s WHERE id = %s",
                (action, by, now, report_id))
    conn.commit()


def set_blocked(cur, conn, uid, blocked):
    cur.execute('UPDATE users SET friends_blocked = %s WHERE id = %s', (1 if blocked else 0, uid))
    if blocked:                                   # u yuborgan ochiq so'rovlar bekor qilinadi
        cur.execute("UPDATE friend_requests SET status = 'cancelled' WHERE from_id = %s AND status = 'pending'", (uid,))
    conn.commit()


def cleanup_user(cur, uid):
    """Foydalanuvchi o'chirilganda (commit — chaqiruvchida)."""
    cur.execute('DELETE FROM friendships WHERE user_a = %s OR user_b = %s', (uid, uid))
    cur.execute('DELETE FROM friend_requests WHERE from_id = %s OR to_id = %s', (uid, uid))
    cur.execute('DELETE FROM friend_invites WHERE from_id = %s OR to_id = %s', (uid, uid))
    cur.execute('DELETE FROM user_reports WHERE reporter_id = %s OR target_id = %s', (uid, uid))


def housekeeping(cur, conn, now=None):
    now = now or clock.now_ms()
    cur.execute('DELETE FROM friend_invites WHERE created_ms < %s', (now - 7 * DAY_MS,))
    cur.execute("DELETE FROM friend_requests WHERE status != 'pending' AND COALESCE(decided_ms, created_ms) < %s",
                (now - 90 * DAY_MS,))
    conn.commit()

