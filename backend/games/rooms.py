# -*- coding: utf-8 -*-
"""
Room tizimi: kod, o'yinchilar, host huquqlari, muddat va tozalash.

Room holatlari:
    waiting → playing → finished → (host "Yana o'ynash") → waiting ...
    uzoq harakatsiz → expired;  hamma chiqib ketsa → cancelled

Barcha tekshiruvlar serverda: faqat host sozlaydi/boshlaydi/chiqaradi,
to'la roomga qo'shilib bo'lmaydi, chiqarilgan o'yinchi qaytib kira olmaydi.
Mijozga o'yinchilarning faqat ismi (birinchi so'z) va darajasi ko'rinadi —
Telegram ID, username yoki rasm ochilmaydi.
"""

import math
import re
import secrets

from games import catalog, clock, engine
from games.errors import GameError

ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'   # 0/O, 1/I/L yo'q — adashtirmaydi
CODE_LENGTH = 6
CODE_RE = re.compile(r'^[A-Z0-9]{6}$')

WAITING_TTL_MS = 20 * 60 * 1000       # kutish zali harakatsiz qolsa
FINISHED_TTL_MS = 30 * 60 * 1000      # natijalar ko'rinib turadigan vaqt
PLAYING_STALE_MS = 10 * 60 * 1000     # hech kim so'rov yubormay qo'ygan o'yin
DELETE_AFTER_MS = 24 * 60 * 60 * 1000
SEEN_THROTTLE_MS = 4 * 1000
COUNTDOWN_MS = 4 * 1000               # 3, 2, 1, GO!
OFFLINE_MS = engine.OFFLINE_MS

ROOM_COLS = ('id, code, host_user_id, game_type, subject, topic, difficulty, question_count, '
             'max_players, is_public, source, status, session_id, version, created_ms, activity_ms')
PLAYER_COLS = 'id, room_id, user_id, name, level, ready, state, joined_ms, seen_ms, left_ms'


def normalize_code(raw) -> str:
    return re.sub(r'[^A-Za-z0-9]', '', str(raw or ''))[:12].upper()


def generate_code(cur) -> str:
    for _ in range(12):
        code = ''.join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
        cur.execute('SELECT 1 FROM game_rooms WHERE code = %s', (code,))
        if not cur.fetchone():
            return code
    raise GameError('server_busy', "Room yaratib bo'lmadi. Qayta urinib ko'ring.", 503)


def first_name(full) -> str:
    parts = str(full or '').strip().split()
    return (parts[0] if parts else "O'yinchi")[:20]


def level_for_xp(xp) -> int:
    return 1 + int(math.sqrt(max(0, int(xp or 0)) / 100))


def _user_level(cur, user_id) -> int:
    cur.execute('SELECT COALESCE(SUM(xp), 0) AS xp FROM game_results WHERE user_id = %s', (user_id,))
    return level_for_xp(cur.fetchone()['xp'])


def load_room(cur, code):
    cur.execute(f'SELECT {ROOM_COLS} FROM game_rooms WHERE code = %s', (code,))
    return cur.fetchone()


def load_players(cur, room_id) -> list:
    cur.execute(f'SELECT {PLAYER_COLS} FROM game_room_players WHERE room_id = %s ORDER BY joined_ms, id',
                (room_id,))
    return cur.fetchall()


def _active(players):
    return [p for p in players if p['state'] == 'active']


def _is_online(p, now) -> bool:
    return now - int(p['seen_ms']) <= OFFLINE_MS


def _bump(cur, room_id, now, **extra):
    """Room versiyasini oshiradi — mijozlar keyingi so'rovda yangi holatni oladi.
    extra kalitlari faqat shu moduldagi doimiy ustun nomlari."""
    sets, params = ['version = version + 1', 'activity_ms = %s'], [now]
    for col, value in extra.items():
        sets.append(f'{col} = %s')
        params.append(value)
    params.append(room_id)
    cur.execute(f'UPDATE game_rooms SET {", ".join(sets)} WHERE id = %s', params)


PRESENCE_THROTTLE_MS = 20 * 1000


def presence_touch(cur, user_id, now):
    """Onlayn belgisi. Lobby har necha soniyada so'raydi — yozuv faqat 20 s
    da bir yangilanadi (online_count 60 s oynasini ishlatadi)."""
    cur.execute(
        '''INSERT INTO game_presence (user_id, seen_ms) VALUES (%s, %s)
           ON CONFLICT (user_id) DO UPDATE SET seen_ms = EXCLUDED.seen_ms
           WHERE game_presence.seen_ms < %s''',
        (user_id, now, now - PRESENCE_THROTTLE_MS),
    )


def _remove_player(cur, room, user_id, now, new_state):
    cur.execute('UPDATE game_room_players SET state = %s, ready = 0, left_ms = %s WHERE room_id = %s AND user_id = %s',
                (new_state, now, room['id'], user_id))
    extra = {}
    cur.execute(
        '''SELECT user_id FROM game_room_players WHERE room_id = %s AND state = 'active'
           ORDER BY joined_ms, id''',
        (room['id'],),
    )
    remaining = [r['user_id'] for r in cur.fetchall()]
    if room['host_user_id'] == user_id and remaining:
        extra['host_user_id'] = remaining[0]      # hostlik eng oldin kirganga o'tadi
        cur.execute('UPDATE game_room_players SET ready = 1 WHERE room_id = %s AND user_id = %s',
                    (room['id'], remaining[0]))
    if not remaining and room['status'] in ('waiting', 'finished'):
        extra['status'] = 'cancelled'
    _bump(cur, room['id'], now, **extra)


def leave_all(cur, user_id, now, keep_room_id=None):
    """Foydalanuvchi bir vaqtda faqat bitta faol roomda bo'ladi."""
    cur.execute(
        f'''SELECT {', '.join('r.' + c.strip() for c in ROOM_COLS.split(','))}
            FROM game_rooms r JOIN game_room_players p ON p.room_id = r.id
            WHERE p.user_id = %s AND p.state = 'active' AND r.status IN ('waiting', 'playing', 'finished')''',
        (user_id,),
    )
    for room in cur.fetchall():
        if room['id'] != keep_room_id:
            _remove_player(cur, room, user_id, now, 'left')


def _upsert_player(cur, room_id, user, now, ready):
    cur.execute(
        '''INSERT INTO game_room_players (room_id, user_id, name, level, ready, state, joined_ms, seen_ms)
           VALUES (%s, %s, %s, %s, %s, 'active', %s, %s)
           ON CONFLICT (room_id, user_id) DO UPDATE SET state = 'active', ready = EXCLUDED.ready,
               name = EXCLUDED.name, level = EXCLUDED.level, joined_ms = EXCLUDED.joined_ms,
               seen_ms = EXCLUDED.seen_ms, left_ms = NULL''',
        (room_id, user['id'], first_name(user.get('name')), _user_level(cur, user['id']), int(ready), now, now),
    )


def _insert_room(cur, code, host_id, settings, is_public, source, now) -> int:
    cur.execute(
        '''INSERT INTO game_rooms (code, host_user_id, game_type, subject, topic, difficulty, question_count,
                                   max_players, is_public, source, status, version, created_ms, activity_ms)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'waiting', 1, %s, %s) RETURNING id''',
        (code, host_id, settings['game_type'], settings['subject'], settings['topic'], settings['difficulty'],
         settings['question_count'], settings['max_players'], int(bool(is_public)), source, now, now),
    )
    return cur.fetchone()['id']


def create_room(cur, conn, user, raw_settings, is_public=False, source='create') -> str:
    settings = catalog.validate_settings(cur, raw_settings)
    now = clock.now_ms()
    leave_all(cur, user['id'], now)
    code = generate_code(cur)
    room_id = _insert_room(cur, code, user['id'], settings, is_public, source, now)
    _upsert_player(cur, room_id, user, now, ready=True)
    presence_touch(cur, user['id'], now)
    conn.commit()
    return code


def create_random_room(cur, code, host, guest, settings, now) -> int:
    """Matchmaking: ikki o'yinchi uchun yopiq room va darhol countdown."""
    settings = dict(settings, max_players=2)
    room_id = _insert_room(cur, code, host['id'], settings, False, 'random', now)
    _upsert_player(cur, room_id, host, now, ready=True)
    _upsert_player(cur, room_id, guest, now, ready=True)
    room = load_room(cur, code)
    session_id = engine.create_session(cur, room, 6 * 1000)
    _bump(cur, room_id, now, status='playing', session_id=session_id)
    return room_id


def _expire_if_needed(cur, conn, room, now):
    idle = now - int(room['activity_ms'])
    new = None
    if room['status'] == 'waiting' and idle > WAITING_TTL_MS:
        new = 'expired'
    elif room['status'] == 'finished' and idle > FINISHED_TTL_MS:
        new = 'expired'
    elif room['status'] == 'playing' and idle > PLAYING_STALE_MS:
        new = 'cancelled'
    if new:
        cur.execute('UPDATE game_rooms SET status = %s, version = version + 1 WHERE id = %s AND status = %s',
                    (new, room['id'], room['status']))
        conn.commit()
        room['status'] = new


def _room_or_404(cur, code):
    code = normalize_code(code)
    if not CODE_RE.match(code):
        raise GameError('invalid_code', "Room kodi 6 ta harf va raqamdan iborat bo'ladi.", 400)
    room = load_room(cur, code)
    if not room:
        raise GameError('room_not_found', "Room topilmadi. Kodni tekshirib, qayta kiriting.", 404)
    return room


def _closed_error(room):
    if room['status'] == 'expired':
        return GameError('room_expired', "Bu roomning muddati tugagan. Yangi room yarating.", 410)
    return GameError('room_closed', "Bu room yopilgan.", 410)


def join_room(cur, conn, user, raw_code) -> str:
    room = _room_or_404(cur, raw_code)
    now = clock.now_ms()
    _expire_if_needed(cur, conn, room, now)
    if room['status'] in ('expired', 'cancelled'):
        raise _closed_error(room)

    players = load_players(cur, room['id'])
    mine = next((p for p in players if p['user_id'] == user['id']), None)
    if mine and mine['state'] == 'kicked':
        raise GameError('kicked', "Host sizni bu roomdan chiqargan.", 403)
    if mine and mine['state'] == 'active':
        return room['code']
    if room['status'] == 'playing':
        raise GameError('room_started', "Bu roomda o'yin allaqachon boshlangan.", 409)
    if len(_active(players)) >= int(room['max_players']):
        raise GameError('room_full', "Bu room to'liq.", 409)

    leave_all(cur, user['id'], now, keep_room_id=room['id'])
    _upsert_player(cur, room['id'], user, now, ready=False)
    # Bir vaqtda ikki kishi oxirgi joyga qo'shilsa — kechroq kelgani qaytariladi
    cur.execute("SELECT user_id FROM game_room_players WHERE room_id = %s AND state = 'active' ORDER BY joined_ms, id",
                (room['id'],))
    order = [r['user_id'] for r in cur.fetchall()]
    if user['id'] in order and order.index(user['id']) >= int(room['max_players']):
        conn.rollback()
        raise GameError('room_full', "Bu room to'liq.", 409)
    _bump(cur, room['id'], now)
    presence_touch(cur, user['id'], now)
    conn.commit()
    return room['code']


def _member(cur, room, user_id, players=None):
    players = players if players is not None else load_players(cur, room['id'])
    mine = next((p for p in players if p['user_id'] == user_id), None)
    if mine and mine['state'] == 'kicked':
        raise GameError('kicked', "Host sizni bu roomdan chiqargan.", 403)
    if not mine or mine['state'] != 'active':
        raise GameError('not_member', "Siz bu roomda emassiz. Kod orqali qayta qo'shiling.", 403)
    return players, mine


def _host_only(room, user_id):
    if room['host_user_id'] != user_id:
        raise GameError('not_host', "Buni faqat room egasi (host) qila oladi.", 403)


def _waiting_only(room):
    if room['status'] != 'waiting':
        raise GameError('not_waiting', "Bu amal faqat o'yin boshlanishidan oldin mumkin.", 409)


def leave_room(cur, conn, user, code):
    room = _room_or_404(cur, code)
    _, mine = _member(cur, room, user['id'])
    _remove_player(cur, room, user['id'], clock.now_ms(), 'left')
    conn.commit()


def set_ready(cur, conn, user, code, ready):
    room = _room_or_404(cur, code)
    _waiting_only(room)
    _, mine = _member(cur, room, user['id'])
    cur.execute('UPDATE game_room_players SET ready = %s WHERE id = %s', (int(bool(ready)), mine['id']))
    _bump(cur, room['id'], clock.now_ms())
    conn.commit()


def update_settings(cur, conn, user, code, raw):
    raw = raw or {}
    room = _room_or_404(cur, code)
    _host_only(room, user['id'])
    _waiting_only(room)
    players, _ = _member(cur, room, user['id'])
    settings = catalog.validate_settings(cur, dict(raw, game=raw.get('game') or room['game_type']))
    if settings['max_players'] < len(_active(players)):
        raise GameError('bad_settings', "Roomda o'yinchilar bu limitdan ko'p.")
    cur.execute(
        '''UPDATE game_rooms SET game_type = %s, subject = %s, topic = %s, difficulty = %s, question_count = %s,
                  max_players = %s, is_public = %s WHERE id = %s''',
        (settings['game_type'], settings['subject'], settings['topic'], settings['difficulty'],
         settings['question_count'], settings['max_players'],
         int(bool(raw.get('public', room['is_public']))), room['id']),
    )
    # Sozlama o'zgardi — hamma qaytadan "Tayyor" bosadi
    cur.execute('UPDATE game_room_players SET ready = 0 WHERE room_id = %s AND user_id != %s',
                (room['id'], room['host_user_id']))
    _bump(cur, room['id'], clock.now_ms())
    conn.commit()


def kick(cur, conn, user, code, pid):
    room = _room_or_404(cur, code)
    _host_only(room, user['id'])
    if room['status'] == 'playing':
        raise GameError('not_waiting', "O'yin davomida o'yinchini chiqarib bo'lmaydi.", 409)
    players, _ = _member(cur, room, user['id'])
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        raise GameError('bad_request', "O'yinchi topilmadi.")
    target = next((p for p in players if p['id'] == pid and p['state'] == 'active'), None)
    if not target:
        raise GameError('not_found', "O'yinchi topilmadi.", 404)
    if target['user_id'] == user['id']:
        raise GameError('bad_request', "O'zingizni chiqara olmaysiz.")
    _remove_player(cur, room, target['user_id'], clock.now_ms(), 'kicked')
    conn.commit()


def start(cur, conn, user, code):
    room = _room_or_404(cur, code)
    _host_only(room, user['id'])
    _waiting_only(room)
    players, _ = _member(cur, room, user['id'])
    now = clock.now_ms()
    ok, hint = _start_check(room, players, now)
    if not ok:
        raise GameError('cannot_start', hint, 409)
    # Oflayn (ilovani yopib qo'ygan) o'yinchilar o'yinga kiritilmaydi
    for p in _active(players):
        if not _is_online(p, now):
            _remove_player(cur, room, p['user_id'], now, 'left')
    session_id = engine.create_session(cur, room, COUNTDOWN_MS)
    _bump(cur, room['id'], now, status='playing', session_id=session_id)
    conn.commit()


def answer(cur, conn, user, code, q_index, raw):
    room = _room_or_404(cur, code)
    players, mine = _member(cur, room, user['id'])
    if room['status'] != 'playing' or not room['session_id']:
        raise GameError('not_playing', "O'yin hozir davom etmayapti.", 409)
    session = engine.load_session(cur, room['session_id'])
    engine.submit_answer(cur, conn, room, session, players, mine, q_index, raw)


def rematch(cur, conn, user, code):
    room = _room_or_404(cur, code)
    _host_only(room, user['id'])
    if room['status'] != 'finished':
        raise GameError('not_finished', "Yangi o'yinni faqat oldingisi tugagach boshlash mumkin.", 409)
    _member(cur, room, user['id'])
    _bump(cur, room['id'], clock.now_ms(), status='waiting')
    conn.commit()


def _start_check(room, players, now):
    if room['status'] != 'waiting':
        return False, ''
    online = [p for p in _active(players) if _is_online(p, now)]
    if len(online) < 2:
        return False, "Boshlash uchun kamida 2 ta o'yinchi kerak."
    waiting = [p for p in online if not p['ready'] and p['user_id'] != room['host_user_id']]
    if waiting:
        return False, f"{len(waiting)} ta o'yinchi hali tayyor emas."
    return True, ''


def _display_names(players) -> dict:
    """user_id → ism. Bir xil ismlar farqlanadi: "Ali", "Ali (2)"."""
    names, used = {}, {}
    for p in players:
        base = p['name'] or "O'yinchi"
        used[base] = used.get(base, 0) + 1
        names[p['user_id']] = base if used[base] == 1 else f'{base} ({used[base]})'
    return names


def _touch(cur, conn, room, mine, now):
    if now - int(mine['seen_ms']) < SEEN_THROTTLE_MS:
        return
    cur.execute('UPDATE game_room_players SET seen_ms = %s WHERE id = %s', (now, mine['id']))
    cur.execute('UPDATE game_rooms SET activity_ms = %s WHERE id = %s', (now, room['id']))
    presence_touch(cur, mine['user_id'], now)
    conn.commit()
    mine['seen_ms'] = now
    room['activity_ms'] = now


def state(cur, conn, user, code, since=None) -> dict:
    """Room holati (poll). since — oldingi javobdagi etag; o'zgarish bo'lmasa
    qisqa javob qaytadi (trafik va baza yuklamasi kamayadi)."""
    room = _room_or_404(cur, code)
    now = clock.now_ms()
    players, mine = _member(cur, room, user['id'])
    _touch(cur, conn, room, mine, now)
    _expire_if_needed(cur, conn, room, now)

    session = None
    if room['session_id'] and room['status'] in ('playing', 'finished'):
        session = engine.load_session(cur, room['session_id'])
    if session and room['status'] == 'playing':
        session, moved = engine.tick(cur, conn, room, session, players, now)
        if moved:
            room = load_room(cur, room['code'])

    etag = f"{room['version']}.{session['version'] if session else 0}.{now // 5000}"
    if since and since == etag:
        return {'same': True, 'etag': etag, 'now': now}

    game = catalog.GAMES[room['game_type']]
    everyone = [p for p in players if p['state'] != 'kicked']
    names = _display_names(everyone)
    active = _active(players)
    live = session and room['status'] in ('playing', 'finished') and session['id'] == room['session_id']
    scores = engine.scores(cur, session['id']) if live else {}
    answered = engine.answered_users(cur, session) if live else set()
    host_id = room['host_user_id']
    ok, hint = _start_check(room, players, now)
    return {
        'etag': etag,
        'now': now,
        'code': room['code'],
        'status': room['status'],
        'source': room['source'],
        'game': {'type': room['game_type'], 'name': game['name'], 'icon': game['icon'],
                 'renderer': game['renderer'], 'mode': game['mode'], 'rules': game['rules']},
        'settings': catalog.describe_settings(cur, room),
        'players': [{
            'pid': p['id'],
            'name': names[p['user_id']],
            'level': int(p['level']),
            'ready': bool(p['ready']) or p['user_id'] == host_id,
            'host': p['user_id'] == host_id,
            'online': _is_online(p, now),
            'me': p['user_id'] == user['id'],
            'score': scores.get(p['user_id'], 0),
            'answered': p['user_id'] in answered,
        } for p in active],
        'me': {'pid': mine['id'], 'host': user['id'] == host_id,
               'ready': bool(mine['ready']) or user['id'] == host_id},
        'can_start': ok,
        'start_hint': hint,
        'session': engine.session_payload(cur, session, players, mine, now, names) if live else None,
    }


# ───────────────────────── Lobby ─────────────────────────

def my_room(cur, user_id):
    cur.execute(
        '''SELECT r.code, r.status FROM game_rooms r JOIN game_room_players p ON p.room_id = r.id
           WHERE p.user_id = %s AND p.state = 'active' AND r.status IN ('waiting', 'playing', 'finished')
           ORDER BY r.activity_ms DESC LIMIT 1''',
        (user_id,),
    )
    row = cur.fetchone()
    return {'code': row['code'], 'status': row['status']} if row else None


def public_rooms(cur, now, limit=12) -> list:
    cur.execute(
        '''SELECT r.id, r.code, r.game_type, r.subject, r.difficulty, r.max_players, r.question_count,
                  (SELECT COUNT(*) FROM game_room_players p WHERE p.room_id = r.id AND p.state = 'active') AS players,
                  (SELECT h.name FROM game_room_players h WHERE h.room_id = r.id AND h.user_id = r.host_user_id) AS host
           FROM game_rooms r
           WHERE r.status = 'waiting' AND r.is_public = 1 AND r.activity_ms >= %s
           ORDER BY r.created_ms DESC LIMIT %s''',
        (now - 10 * 60 * 1000, limit * 2),
    )
    out = []
    for r in cur.fetchall():
        if int(r['players']) >= int(r['max_players']) or r['game_type'] not in catalog.GAMES:
            continue
        game = catalog.GAMES[r['game_type']]
        out.append({
            'code': r['code'], 'game': r['game_type'], 'game_name': game['name'], 'icon': game['icon'],
            'subject_name': catalog.subject_info(r['subject'])['name'],
            'difficulty_name': catalog.DIFFICULTIES.get(r['difficulty'], r['difficulty']),
            'players': int(r['players']), 'max_players': int(r['max_players']),
            'question_count': int(r['question_count']), 'host': r['host'] or "O'yinchi",
        })
        if len(out) >= limit:
            break
    return out


def online_count(cur, now) -> int:
    cur.execute('SELECT COUNT(*) AS n FROM game_presence WHERE seen_ms >= %s', (now - 60 * 1000,))
    return int(cur.fetchone()['n'] or 0)


def cleanup(cur, conn, now):
    """Eski roomlarni yopadi va o'chiradi. Natijalar (game_results) statistika
    uchun saqlanib qoladi."""
    cur.execute("UPDATE game_rooms SET status = 'expired', version = version + 1 "
                "WHERE status = 'waiting' AND activity_ms < %s", (now - WAITING_TTL_MS,))
    cur.execute("UPDATE game_rooms SET status = 'expired', version = version + 1 "
                "WHERE status = 'finished' AND activity_ms < %s", (now - FINISHED_TTL_MS,))
    cur.execute("UPDATE game_rooms SET status = 'cancelled', version = version + 1 "
                "WHERE status = 'playing' AND activity_ms < %s", (now - PLAYING_STALE_MS,))
    cur.execute("SELECT id FROM game_rooms WHERE status IN ('expired', 'cancelled') AND activity_ms < %s LIMIT 200",
                (now - DELETE_AFTER_MS,))
    old = [r['id'] for r in cur.fetchall()]
    if old:
        marks = ', '.join(['%s'] * len(old))
        cur.execute(f'DELETE FROM game_answers WHERE session_id IN (SELECT id FROM game_sessions WHERE room_id IN ({marks}))', old)
        cur.execute(f'DELETE FROM game_sessions WHERE room_id IN ({marks})', old)
        cur.execute(f'DELETE FROM game_room_players WHERE room_id IN ({marks})', old)
        cur.execute(f'DELETE FROM game_rooms WHERE id IN ({marks})', old)
    cur.execute('DELETE FROM game_queue WHERE seen_ms < %s', (now - 10 * 60 * 1000,))
    cur.execute('DELETE FROM game_presence WHERE seen_ms < %s', (now - DELETE_AFTER_MS,))
    conn.commit()
