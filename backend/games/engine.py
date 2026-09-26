# -*- coding: utf-8 -*-
"""
O'yin mexanizmi — butunlay server tomonida (server-authoritative).

Holat mashinasi (game_sessions.phase):
    countdown → question → reveal → question → ... → finished

Fon jarayoni (worker/cron) yo'q: holat har bir so'rovda (poll yoki javob)
server vaqtiga qarab "dangasa" (lazy) oldinga suriladi — tick(). Bir nechta
gunicorn worker bir vaqtda surmoqchi bo'lsa, optimistik versiya (CAS:
... WHERE version = eski) faqat bittasiga ruxsat beradi.

Adolatli o'yin:
  * ball faqat serverda hisoblanadi — mijoz ball yubormaydi;
  * to'g'ri javob savol yopilmaguncha mijozga yuborilmaydi;
  * muddat va "tez javob" vaqti server soati bilan o'lchanadi;
  * (session, user, savol) noyob — bitta savolga ikki marta javob yo'q.
"""

import json

from games import catalog, clock, questions
from games.errors import GameError

POINTS_CORRECT = 10
POINTS_FAST = 5
FAST_RATIO = 0.4          # vaqtning birinchi 40% ida to'g'ri javob — tez
POINTS_PER_PAIR = 2       # Memory/Match: qisman to'g'ri juftlik uchun
BONUS_COMPLETE = 20       # savollarning kamida yarmiga javob bergan
BONUS_WIN = 30            # 1-o'rin (kamida 2 ishtirokchi)
DAILY_XP_CAP = 600        # kuniga hisobga o'tadigan ball chegarasi
REVEAL_MS = catalog.REVEAL_SECONDS * 1000
GRACE_MS = 800            # tarmoq kechikishi uchun kichik zaxira
OFFLINE_MS = 15 * 1000    # shuncha vaqt so'rov kelmasa — "oflayn"
GONE_MS = 45 * 1000       # shuncha vaqt yo'q bo'lsa — o'yinni tark etgan

SESSION_COLS = ('id, room_id, game_type, subject, topic, difficulty, mode, total, phase, q_index, '
                'phase_started_ms, phase_ends_ms, version, started_ms, finished_ms, end_reason')

# Savollar sessiya davomida o'zgarmaydi — har bir poll'da bazadan katta JSON
# o'qimaslik uchun worker xotirasida saqlanadi.
_QCACHE = {}


def _cache_put(session_id, qs):
    if len(_QCACHE) > 300:
        _QCACHE.clear()
    _QCACHE[session_id] = qs


def questions_for(cur, session_id) -> list:
    qs = _QCACHE.get(session_id)
    if qs is None:
        cur.execute('SELECT questions FROM game_sessions WHERE id = %s', (session_id,))
        row = cur.fetchone()
        qs = json.loads(row['questions']) if row else []
        _cache_put(session_id, qs)
    return qs


def load_session(cur, session_id):
    cur.execute(f'SELECT {SESSION_COLS} FROM game_sessions WHERE id = %s', (session_id,))
    return cur.fetchone()


def time_limit_ms(session) -> int:
    return catalog.GAMES[session['game_type']]['time_limit'] * 1000


def create_session(cur, room, countdown_ms) -> int:
    settings = {
        'game_type': room['game_type'],
        'subject': room['subject'],
        'topic': room['topic'],
        'difficulty': room['difficulty'],
        'question_count': int(room['question_count']),
    }
    qs = questions.build(cur, settings)
    if not qs:
        raise GameError('no_questions', "Bu sozlamalar uchun savol topilmadi. Boshqa fan yoki mavzuni tanlang.", 422)
    now = clock.now_ms()
    cur.execute(
        '''INSERT INTO game_sessions (room_id, game_type, subject, topic, difficulty, mode, total, questions,
                                      phase, q_index, phase_started_ms, phase_ends_ms, version, started_ms)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'countdown', 0, %s, %s, 1, %s) RETURNING id''',
        (room['id'], room['game_type'], room['subject'], room['topic'], room['difficulty'],
         catalog.GAMES[room['game_type']]['mode'], len(qs), json.dumps(qs, ensure_ascii=False),
         now, now + countdown_ms, now),
    )
    session_id = cur.fetchone()['id']
    _cache_put(session_id, qs)
    return session_id


def _cas(cur, session, changes: dict) -> bool:
    """Optimistik yangilash: faqat versiya o'zgarmagan bo'lsa. Ustun nomlari
    faqat shu moduldagi doimiy kalitlar — foydalanuvchi kiritmasi emas."""
    sets = ', '.join(f'{col} = %s' for col in changes)
    cur.execute(
        f'UPDATE game_sessions SET {sets}, version = version + 1 WHERE id = %s AND version = %s',
        (*changes.values(), session['id'], session['version']),
    )
    if cur.rowcount != 1:
        return False
    session.update(changes)
    session['version'] = int(session['version']) + 1
    return True


def _alive(players, now, window):
    return [p for p in players if p['state'] == 'active' and now - int(p['seen_ms']) <= window]


def _start_question(cur, session, index, now) -> bool:
    return _cas(cur, session, {
        'phase': 'question', 'q_index': index,
        'phase_started_ms': now, 'phase_ends_ms': now + time_limit_ms(session) + GRACE_MS,
    })


def _score_question(cur, session, q_index):
    """Savol yopilganda ballarni hisoblaydi. Quick Answer'da faqat birinchi
    to'g'ri javob (server qabul qilgan vaqt bo'yicha) ball oladi."""
    fast_ms = time_limit_ms(session) * FAST_RATIO
    cur.execute(
        '''SELECT id, correct, partial, elapsed_ms FROM game_answers
           WHERE session_id = %s AND q_index = %s ORDER BY answered_ms, id''',
        (session['id'], q_index),
    )
    first_taken = False
    for a in cur.fetchall():
        points = 0
        if a['correct']:
            if session['mode'] != 'first' or not first_taken:
                points = POINTS_CORRECT + (POINTS_FAST if int(a['elapsed_ms']) <= fast_ms else 0)
                first_taken = True
        elif a['partial']:
            points = int(a['partial']) * POINTS_PER_PAIR
        if points:
            cur.execute('UPDATE game_answers SET points = %s WHERE id = %s', (points, a['id']))


def _reveal(cur, session, now) -> bool:
    q_index = session['q_index']
    if not _cas(cur, session, {'phase': 'reveal', 'phase_started_ms': now, 'phase_ends_ms': now + REVEAL_MS}):
        return False
    _score_question(cur, session, q_index)
    return True


def tick(cur, conn, room, session, players, now=None):
    """Vaqt o'tgan bo'lsa, fazani oldinga suradi. (sessiya, o'zgardimi)."""
    now = now or clock.now_ms()
    moved = False
    for _ in range(64):
        phase = session['phase']
        if phase in ('finished', 'cancelled'):
            break
        if len(_alive(players, now, GONE_MS)) < 2:
            ok = _finish(cur, room, session, players, now, 'players_left')
        elif now < int(session['phase_ends_ms']):
            break
        elif phase == 'countdown':
            ok = _start_question(cur, session, 0, now)
        elif phase == 'question':
            ok = _reveal(cur, session, now)
        elif session['q_index'] + 1 < session['total']:
            ok = _start_question(cur, session, session['q_index'] + 1, now)
        else:
            ok = _finish(cur, room, session, players, now, 'completed')
        if ok:
            conn.commit()
            moved = True
        else:
            conn.rollback()
            session = load_session(cur, session['id'])
    return session, moved


def submit_answer(cur, conn, room, session, players, me, q_index, raw):
    now = clock.now_ms()
    session, _ = tick(cur, conn, room, session, players, now)
    try:
        q_index = int(q_index)
    except (TypeError, ValueError):
        raise GameError('bad_answer', "Savol raqami noto'g'ri.")
    if session['phase'] != 'question' or q_index != session['q_index']:
        raise GameError('too_late', "Bu savolning vaqti tugadi.", 409)

    q = questions_for(cur, session['id'])[q_index]
    correct, partial, stored = questions.evaluate(q, raw)
    elapsed = max(0, now - int(session['phase_started_ms']))
    cur.execute(
        '''INSERT INTO game_answers (session_id, user_id, q_index, answer, correct, partial, points, answered_ms, elapsed_ms)
           VALUES (%s, %s, %s, %s, %s, %s, 0, %s, %s)
           ON CONFLICT (session_id, user_id, q_index) DO NOTHING''',
        (session['id'], me['user_id'], q_index, json.dumps(stored), int(correct), int(partial), now, elapsed),
    )
    if cur.rowcount != 1:
        conn.rollback()
        raise GameError('already_answered', "Siz bu savolga javob bergansiz.", 409)
    cur.execute('UPDATE game_sessions SET version = version + 1 WHERE id = %s', (session['id'],))
    conn.commit()

    # Erta yopish: Quick Answer'da to'g'ri javob kelsa yoki hamma javob bersa
    fresh = load_session(cur, session['id'])
    if fresh and fresh['phase'] == 'question' and fresh['q_index'] == q_index:
        done = fresh['mode'] == 'first' and correct
        if not done:
            cur.execute('SELECT COUNT(*) AS n FROM game_answers WHERE session_id = %s AND q_index = %s',
                        (session['id'], q_index))
            done = int(cur.fetchone()['n']) >= max(1, len(_alive(players, now, OFFLINE_MS)))
        if done and _reveal(cur, fresh, clock.now_ms()):
            conn.commit()
        else:
            conn.rollback()


def _today_xp(cur, user_id, now) -> int:
    cur.execute(
        'SELECT COALESCE(SUM(xp), 0) AS xp FROM game_results WHERE user_id = %s AND created_ms >= %s',
        (user_id, clock.period_start_ms('day', now)),
    )
    return int(cur.fetchone()['xp'] or 0)


def session_members(players, session):
    """Shu o'yinda qatnashganlar: hozir roomda yoki o'yin boshlangandan keyin chiqib ketgan."""
    started = int(session['started_ms'])
    return [p for p in players
            if p['state'] == 'active' or (p['state'] == 'left' and int(p['left_ms'] or 0) >= started)]


def _finish(cur, room, session, players, now, reason) -> bool:
    prev_phase, prev_index = session['phase'], session['q_index']
    if not _cas(cur, session, {'phase': 'finished', 'phase_started_ms': now, 'phase_ends_ms': now,
                               'finished_ms': now, 'end_reason': reason}):
        return False
    if prev_phase == 'question':
        _score_question(cur, session, prev_index)
    played = prev_index + 1 if prev_phase in ('question', 'reveal') else 0

    cur.execute(
        '''SELECT user_id, COUNT(*) AS answered, SUM(correct) AS correct, SUM(points) AS points
           FROM game_answers WHERE session_id = %s AND q_index < %s GROUP BY user_id''',
        (session['id'], played),
    )
    agg = {r['user_id']: r for r in cur.fetchall()}
    rows = []
    for p in session_members(players, session):
        a = agg.get(p['user_id']) or {}
        rows.append({'p': p, 'answered': int(a.get('answered') or 0),
                     'correct': int(a.get('correct') or 0), 'points': int(a.get('points') or 0)})

    multiplayer = sum(1 for r in rows if r['answered'] > 0) >= 2
    rows.sort(key=lambda r: -r['points'])
    rank, prev = 0, None
    for i, r in enumerate(rows):
        if r['points'] != prev:
            rank, prev = i + 1, r['points']
        r['rank'] = rank

    for r in rows:
        p = r['p']
        stayed = p['state'] == 'active'
        won = multiplayer and r['rank'] == 1 and r['points'] > 0 and stayed
        bonus = (BONUS_COMPLETE if played and stayed and r['answered'] * 2 >= played else 0) + (BONUS_WIN if won else 0)
        earned = r['points'] + bonus
        xp = 0
        if multiplayer and earned > 0 and r['answered'] > 0:
            xp = max(0, min(earned, DAILY_XP_CAP - _today_xp(cur, p['user_id'], now)))
        cur.execute(
            '''INSERT INTO game_results (session_id, room_id, user_id, game_type, subject, topic, difficulty,
                                         score, earned, xp, correct, wrong, total, accuracy, rank, players, won,
                                         duration_ms, created_ms)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (session_id, user_id) DO NOTHING''',
            (session['id'], room['id'], p['user_id'], session['game_type'], session['subject'], session['topic'],
             session['difficulty'], r['points'], earned, xp, r['correct'], r['answered'] - r['correct'],
             played, round(100 * r['correct'] / played) if played else 0, r['rank'], len(rows), int(won),
             now - int(session['started_ms']), now),
        )

    cur.execute("UPDATE game_rooms SET status = 'finished', version = version + 1, activity_ms = %s WHERE id = %s",
                (now, room['id']))
    cur.execute('UPDATE game_room_players SET ready = 0 WHERE room_id = %s AND user_id != %s',
                (room['id'], room['host_user_id']))
    room['status'] = 'finished'
    return True


# ───────────────────────── Mijozga holat ─────────────────────────

def scores(cur, session_id) -> dict:
    cur.execute('SELECT user_id, SUM(points) AS points FROM game_answers WHERE session_id = %s GROUP BY user_id',
                (session_id,))
    return {r['user_id']: int(r['points'] or 0) for r in cur.fetchall()}


def _question_answers(cur, session):
    cur.execute(
        '''SELECT user_id, answer, correct, partial, points, answered_ms FROM game_answers
           WHERE session_id = %s AND q_index = %s ORDER BY answered_ms, id''',
        (session['id'], session['q_index']),
    )
    return cur.fetchall()


def answered_users(cur, session) -> set:
    if session['phase'] not in ('question', 'reveal'):
        return set()
    return {a['user_id'] for a in _question_answers(cur, session)}


def session_payload(cur, session, players, me, now, names) -> dict:
    limit = time_limit_ms(session)
    data = {
        'id': session['id'],
        'phase': session['phase'],
        'q_index': session['q_index'],
        'total': session['total'],
        'mode': session['mode'],
        'time_limit_ms': limit,
        'phase_started_ms': int(session['phase_started_ms']),
        'phase_ends_ms': int(session['phase_ends_ms']),
    }
    if session['phase'] == 'question':
        data['deadline_ms'] = int(session['phase_started_ms']) + limit

    if session['phase'] in ('question', 'reveal'):
        q = questions_for(cur, session['id'])[session['q_index']]
        answers = _question_answers(cur, session)
        mine = next((a for a in answers if a['user_id'] == me['user_id']), None)
        data['question'] = questions.public(q)
        data['answered_count'] = len(answers)
        data['expected_count'] = max(1, len(_alive(players, now, OFFLINE_MS)))
        data['my_answer'] = json.loads(mine['answer']) if mine else None
        if session['phase'] == 'reveal':
            reveal = questions.reveal(q)
            first = next((a for a in answers if a['correct']), None) if session['mode'] == 'first' else None
            reveal.update({
                'answered': mine is not None,
                'my_correct': bool(mine and mine['correct']),
                'my_partial': int(mine['partial']) if mine else 0,
                'my_points': int(mine['points']) if mine else 0,
                'first_name': names.get(first['user_id']) if first else None,
                'gains': [{'name': names.get(a['user_id'], "O'yinchi"), 'points': int(a['points']),
                           'me': a['user_id'] == me['user_id']}
                          for a in sorted(answers, key=lambda a: -int(a['points'])) if int(a['points']) > 0][:5],
            })
            data['reveal'] = reveal

    if session['phase'] == 'finished':
        data['end_reason'] = session['end_reason']
        data['results'] = results_payload(cur, session, me['user_id'], names)
    return data


def results_payload(cur, session, user_id, names) -> dict:
    cur.execute(
        '''SELECT user_id, score, earned, xp, correct, wrong, total, accuracy, rank, won, duration_ms
           FROM game_results WHERE session_id = %s ORDER BY rank, score DESC, user_id''',
        (session['id'],),
    )
    rows = cur.fetchall()
    table = [{
        'rank': int(r['rank']), 'name': names.get(r['user_id'], "O'yinchi"), 'score': int(r['score']),
        'correct': int(r['correct']), 'accuracy': int(r['accuracy']), 'won': bool(r['won']),
        'me': r['user_id'] == user_id,
    } for r in rows]
    mine = next((r for r in rows if r['user_id'] == user_id), None)
    me = None
    if mine:
        total = int(mine['total'])
        me = {
            'rank': int(mine['rank']), 'score': int(mine['score']), 'earned': int(mine['earned']),
            'bonus': int(mine['earned']) - int(mine['score']), 'xp': int(mine['xp']),
            'chaqmoq': int(mine['xp']) // 10, 'correct': int(mine['correct']), 'wrong': int(mine['wrong']),
            'unanswered': max(0, total - int(mine['correct']) - int(mine['wrong'])), 'total': total,
            'accuracy': int(mine['accuracy']), 'won': bool(mine['won']), 'duration_ms': int(mine['duration_ms']),
            'multiplayer': sum(1 for r in rows if int(r['correct']) + int(r['wrong']) > 0) >= 2,
            'capped': int(mine['xp']) < int(mine['earned']),
        }
    return {
        'rows': table,
        'me': me,
        'players': len(rows),
        'learning': learning_summary(cur, session, user_id, int(mine['total']) if mine else 0),
    }


def learning_summary(cur, session, user_id, played) -> dict:
    """"Nimalarni o'rgandingiz?" — mavzular bo'yicha kuchli/zaif tomonlar va
    har bir savolning to'g'ri javobi bilan tushuntirishi."""
    qs = questions_for(cur, session['id'])[:played]
    cur.execute('SELECT q_index, answer, correct, partial FROM game_answers WHERE session_id = %s AND user_id = %s',
                (session['id'], user_id))
    by_q = {a['q_index']: a for a in cur.fetchall()}
    topics, review = {}, []
    correct_total = 0
    for i, q in enumerate(qs):
        a = by_q.get(i)
        ok = bool(a and a['correct'])
        correct_total += ok
        title = q.get('topic_title') or '—'
        t = topics.setdefault(title, {'title': title, 'correct': 0, 'total': 0, 'link': q.get('link')})
        t['total'] += 1
        t['correct'] += ok
        item = {'n': i + 1, 'kind': q['kind'], 'prompt': q['prompt'], 'correct': ok, 'answered': a is not None,
                'right_answer': questions.answer_text(q), 'explain': q.get('explain') or ''}
        if q['kind'] == 'choice' and a is not None:
            item['your_answer'] = q['options'][json.loads(a['answer'])]
        if q['kind'] == 'match':
            item['partial'] = int(a['partial']) if a else 0
            item['pairs'] = [[left, q['right'][q['answer'][k]]] for k, left in enumerate(q['left'])]
        review.append(item)

    strong = sorted((t for t in topics.values() if t['correct'] == t['total']),
                    key=lambda t: -t['total'])[:3]
    weak = sorted((t for t in topics.values() if t['correct'] * 2 < t['total']),
                  key=lambda t: (t['correct'] / t['total'], -t['total']))[:3]
    return {
        'summary': f"Siz {played} ta savoldan {correct_total} tasiga to'g'ri javob berdingiz." if played
        else "O'yin savollar boshlanishidan oldin tugadi.",
        'strong': strong,
        'weak': weak,
        'review': review,
    }
