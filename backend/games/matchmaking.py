# -*- coding: utf-8 -*-
"""
Random raqib qidirish (matchmaking).

Navbat bazada (game_queue) — bir nechta gunicorn worker orasida umumiy.
Moslik: o'yin turi va fan har doim bir xil; qiyinlik va mavzu boshida ham
mos bo'lishi kerak, RELAX_AFTER_MS dan keyin esa talab yumshatiladi.
Taxminiy mahorat (so'nggi o'yinlardagi aniqlik) yaqinlari birinchi tanlanadi.

Javobdagi holat maydoni `result` (`status` emas): js/api.js javobning `status`ini HTTP
kodi bilan almashtiradi.

Juftlikni ikki kishi bir vaqtda "egallab" olmasligi uchun ikkala navbat qatori
bitta UPDATE bilan (status='waiting' sharti ostida) olinadi — faqat ikkala
qator ham yangilansa, room yaratiladi. Raqibning shaxsiy ma'lumotlari
ko'rsatilmaydi: roomda faqat ism (birinchi so'z) va daraja ko'rinadi.
"""

import logging

from games import catalog, clock, rooms
from games.errors import GameError

logger = logging.getLogger('bilimsari.games')

QUEUE_TTL_MS = 12 * 1000      # shu vaqt so'rov kelmasa — qidiruvdan chiqib ketgan
RELAX_AFTER_MS = 15 * 1000    # keyin qiyinlik/mavzu talabi yumshatiladi
TIMEOUT_MS = 90 * 1000


def _skill(cur, user_id) -> int:
    cur.execute('SELECT accuracy FROM game_results WHERE user_id = %s ORDER BY created_ms DESC LIMIT 20',
                (user_id,))
    rows = cur.fetchall()
    return round(sum(int(r['accuracy']) for r in rows) / len(rows)) if rows else 50


def start(cur, conn, user, raw) -> dict:
    settings = catalog.validate_settings(cur, dict(raw or {}, max_players=2))
    now = clock.now_ms()
    rooms.leave_all(cur, user['id'], now)
    cur.execute(
        '''INSERT INTO game_queue (user_id, game_type, subject, topic, difficulty, question_count, skill,
                                   status, room_code, created_ms, seen_ms)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 'waiting', NULL, %s, %s)
           ON CONFLICT (user_id) DO UPDATE SET game_type = EXCLUDED.game_type, subject = EXCLUDED.subject,
               topic = EXCLUDED.topic, difficulty = EXCLUDED.difficulty,
               question_count = EXCLUDED.question_count, skill = EXCLUDED.skill, status = 'waiting',
               room_code = NULL, created_ms = EXCLUDED.created_ms, seen_ms = EXCLUDED.seen_ms''',
        (user['id'], settings['game_type'], settings['subject'], settings['topic'], settings['difficulty'],
         settings['question_count'], _skill(cur, user['id']), now, now),
    )
    rooms.presence_touch(cur, user['id'], now)
    conn.commit()
    return poll(cur, conn, user)


def _finish_entry(cur, conn, user_id):
    cur.execute('DELETE FROM game_queue WHERE user_id = %s', (user_id,))
    conn.commit()


def poll(cur, conn, user) -> dict:
    now = clock.now_ms()
    cur.execute('SELECT * FROM game_queue WHERE user_id = %s', (user['id'],))
    me = cur.fetchone()
    if not me:
        return {'result': 'idle'}
    if me['status'] == 'matched':
        _finish_entry(cur, conn, user['id'])
        return {'result': 'matched', 'code': me['room_code']}
    waited = now - int(me['created_ms'])
    if waited > TIMEOUT_MS:
        _finish_entry(cur, conn, user['id'])
        return {'result': 'timeout'}

    cur.execute('UPDATE game_queue SET seen_ms = %s WHERE user_id = %s', (now, user['id']))
    rooms.presence_touch(cur, user['id'], now)
    conn.commit()

    code = _try_match(cur, conn, user, me, now)
    if code:
        _finish_entry(cur, conn, user['id'])
        return {'result': 'matched', 'code': code}
    return {'result': 'searching', 'waited_ms': waited, 'relaxed': waited >= RELAX_AFTER_MS,
            'timeout_ms': TIMEOUT_MS}


def cancel(cur, conn, user) -> dict:
    cur.execute('SELECT status, room_code FROM game_queue WHERE user_id = %s', (user['id'],))
    me = cur.fetchone()
    _finish_entry(cur, conn, user['id'])
    if me and me['status'] == 'matched':
        # Bekor qilishdan bir lahza oldin raqib topilgan — roomga yo'naltiramiz
        return {'result': 'matched', 'code': me['room_code']}
    return {'result': 'cancelled'}


def _try_match(cur, conn, user, me, now):
    cur.execute(
        '''SELECT * FROM game_queue
           WHERE status = 'waiting' AND user_id != %s AND game_type = %s AND subject = %s AND seen_ms >= %s
           ORDER BY created_ms LIMIT 25''',
        (user['id'], me['game_type'], me['subject'], now - QUEUE_TTL_MS),
    )
    i_relaxed = now - int(me['created_ms']) >= RELAX_AFTER_MS
    candidates = []
    for c in cur.fetchall():
        relaxed = i_relaxed or now - int(c['created_ms']) >= RELAX_AFTER_MS
        if not relaxed and (c['difficulty'] != me['difficulty'] or (c['topic'] or None) != (me['topic'] or None)):
            continue
        candidates.append(c)
    candidates.sort(key=lambda c: (abs(int(c['skill']) - int(me['skill'])) // 15, int(c['created_ms'])))

    for c in candidates:
        try:
            code = rooms.generate_code(cur)
            cur.execute(
                "UPDATE game_queue SET status = 'matched', room_code = %s "
                "WHERE user_id IN (%s, %s) AND status = 'waiting'",
                (code, user['id'], c['user_id']),
            )
            if cur.rowcount != 2:
                conn.rollback()
                continue
            cur.execute('SELECT id, name FROM users WHERE id IN (%s, %s)', (c['user_id'], user['id']))
            people = {r['id']: r for r in cur.fetchall()}
            if len(people) != 2:
                conn.rollback()
                continue
            # Uzoqroq kutgan o'yinchi host, o'yin uning sozlamalari bilan
            settings = {'game_type': c['game_type'], 'subject': c['subject'], 'topic': c['topic'],
                        'difficulty': c['difficulty'], 'question_count': int(c['question_count'])}
            rooms.create_random_room(cur, code, people[c['user_id']], people[user['id']], settings, now)
            conn.commit()
            return code
        except GameError:
            conn.rollback()
        except Exception:  # noqa: BLE001 — masalan, parallel so'rovlarda deadlock; keyingi poll qayta urinadi
            conn.rollback()
            logger.exception('Matchmaking xatosi')
    return None
