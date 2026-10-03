# -*- coding: utf-8 -*-
"""
O'yin reytingi, profil statistikasi va chaqmoq bilan bog'lanish.

"Ball" — o'yin XP'si: har bir natijada hisobga o'tgan qismi game_results.xp
(faqat kamida 2 ishtirokchili o'yinlar, kunlik limit bilan) — o'yin darajasi va
o'yin reytingi shundan.

Chaqmoq (platformaning umumiy valyutasi) o'yinlardan: 24 soatda 3 ta chaqmoqli
o'yin, 1-o'rin +30, qolganlar +20 (games/chances.py) — game_results.chaqmoq.
Eski natijalarda (chaqmoq IS NULL) avvalgidek har GAME_XP_PER_CHAQMOQ ball = 1
chaqmoq — o'quvchilar oldin olgan chaqmoqni yo'qotmaydi.
"""

from datetime import timedelta

import boshqaruv
import curriculum as cur_mod
import premium
from games import catalog, clock, schema
from games.rooms import level_for_xp

GAME_XP_PER_CHAQMOQ = 10
PERIODS = ('day', 'week', 'month', 'all')
SCOPES = ('global', 'subject')


_CHAQMOQ_SQL = ('COALESCE(SUM(CASE WHEN chaqmoq IS NULL THEN xp ELSE 0 END), 0) AS old_xp, '
                'COALESCE(SUM(chaqmoq), 0) AS ch')


def _chaqmoq(row) -> int:
    return int(row['old_xp'] or 0) // GAME_XP_PER_CHAQMOQ + int(row['ch'] or 0)


def chaqmoq_by_user(cur) -> dict:
    """Umumiy chaqmoq reytingi uchun: user_id → o'yinlardan olingan chaqmoq."""
    if not schema.READY:
        return {}
    cur.execute(f'SELECT user_id, {_CHAQMOQ_SQL} FROM game_results WHERE user_id > 0 GROUP BY user_id')
    return {r['user_id']: _chaqmoq(r) for r in cur.fetchall()}


def chaqmoq_from_games(cur, user_id) -> int:
    if not schema.READY:
        return 0
    cur.execute(f'SELECT {_CHAQMOQ_SQL} FROM game_results WHERE user_id = %s', (user_id,))
    return _chaqmoq(cur.fetchone())


def leaderboard(cur, user_id, period='week', scope='global', subject=None, limit=20) -> dict:
    period = period if period in PERIODS else 'week'
    scope = scope if scope in SCOPES else 'global'
    now = clock.now_ms()
    where, params, join = ['r.created_ms >= %s', 'r.user_id > 0'], [clock.period_start_ms(period, now)], ''

    if scope == 'subject':
        if subject not in cur_mod.SUBJECT_CATALOG:
            subject = 'math'
        where.append('r.subject = %s')
        params.append(subject)

    cur.execute(
        f'''SELECT r.user_id, SUM(r.xp) AS xp, COUNT(*) AS games, SUM(r.won) AS wins,
                   SUM(r.correct) AS correct, SUM(r.total) AS total
            FROM game_results r {join}
            WHERE {' AND '.join(where)}
            GROUP BY r.user_id''',
        params,
    )
    rows = cur.fetchall()
    banned = boshqaruv.banned_ids(cur)       # natija olingandan keyin (shu cursor'da yangi so'rov); bloklanganlar ko'rinmaydi
    rows = [r for r in rows if int(r['xp'] or 0) > 0 and int(r['user_id']) not in banned]
    rows.sort(key=lambda r: (-int(r['xp'] or 0), -int(r['wins'] or 0), r['user_id']))

    wanted = {r['user_id'] for r in rows[:limit]} | {user_id}
    info = {}
    if rows:
        ids = list(wanted)
        marks = ', '.join(['%s'] * len(ids))
        cur.execute(f'SELECT id, name, photo_url FROM users WHERE id IN ({marks})', ids)
        info = {r['id']: r for r in cur.fetchall()}

    def entry(rank, r):
        meta = info.get(r['user_id']) or {}
        total = int(r['total'] or 0)
        return {
            'rank': rank, 'user_id': r['user_id'], 'name': meta.get('name') or "O'yinchi", 'photo_url': meta.get('photo_url'),
            'xp': int(r['xp'] or 0), 'games': int(r['games'] or 0), 'wins': int(r['wins'] or 0),
            'accuracy': round(100 * int(r['correct'] or 0) / total) if total else 0,
            'me': r['user_id'] == user_id,
        }

    top, me = [], None
    for rank, r in enumerate(rows, start=1):
        if rank <= limit:
            top.append(entry(rank, r))
        if r['user_id'] == user_id:
            me = entry(rank, r)
    premium.decorate(cur, top + ([me] if me else []))      # ramka va emoji — boshqa reytinglardagidek
    return {'top': top, 'me': me, 'total_players': len(rows), 'period': period, 'scope': scope,
            'subject': subject if scope == 'subject' else None,
            'tournament': tournament(cur, now) if period == 'week' else None}


def _streak(days: set, today) -> int:
    """Ketma-ket o'ynalgan kunlar (bugun hali o'ynalmagan bo'lsa — kechadan)."""
    cursor =today if today in days else today - timedelta(days=1)
    n = 0
    while cursor in days:
        n += 1
        cursor -= timedelta(days=1)
    return n


def my_stats(cur, user_id) -> dict:
    cur.execute(
        '''SELECT COUNT(*) AS games, COALESCE(SUM(won), 0) AS wins, COALESCE(SUM(xp), 0) AS xp,
                  COALESCE(SUM(correct), 0) AS correct, COALESCE(SUM(total), 0) AS total
           FROM game_results WHERE user_id = %s''',
        (user_id,),
    )
    t = cur.fetchone()
    games, total, xp = int(t['games'] or 0), int(t['total'] or 0), int(t['xp'] or 0)

    cur.execute(
        '''SELECT subject, COUNT(*) AS games, SUM(correct) AS correct, SUM(total) AS total
           FROM game_results WHERE user_id = %s GROUP BY subject''',
        (user_id,),
    )
    subjects = []
    for r in cur.fetchall():
        if r['subject'] not in cur_mod.SUBJECT_CATALOG:
            continue
        s_total = int(r['total'] or 0)
        info = catalog.subject_info(r['subject'])
        subjects.append({
            'key': r['subject'], 'name': info['name'], 'icon': info['icon'], 'color': info['color'],
            'games': int(r['games']), 'accuracy': round(100 * int(r['correct'] or 0) / s_total) if s_total else 0,
        })
    subjects.sort(key=lambda s: (-s['games'], -s['accuracy']))

    now = clock.now_ms()
    cur.execute('SELECT created_ms FROM game_results WHERE user_id = %s AND created_ms >= %s',
                (user_id, now - 400 * 24 * 3600 * 1000))
    days = {clock.tashkent_date(r['created_ms']) for r in cur.fetchall()}

    cur.execute(
        '''SELECT game_type, subject, score, rank, players, won, accuracy, xp, created_ms
           FROM game_results WHERE user_id = %s ORDER BY created_ms DESC LIMIT 5''',
        (user_id,),
    )
    recent = [{
        'game_name': catalog.GAMES.get(r['game_type'], {}).get('name', r['game_type']),
        'icon': catalog.GAMES.get(r['game_type'], {}).get('icon', 'brain'),
        'subject_name': catalog.subject_info(r['subject'])['name'] if r['subject'] in cur_mod.SUBJECT_CATALOG else '',
        'score': int(r['score']), 'rank': int(r['rank']), 'players': int(r['players']),
        'won': bool(r['won']), 'accuracy': int(r['accuracy']), 'xp': int(r['xp']), 'at_ms': int(r['created_ms']),
    } for r in cur.fetchall()]

    return {
        'games': games,
        'wins': int(t['wins'] or 0),
        'xp': xp,
        'chaqmoq': chaqmoq_from_games(cur, user_id),
        'level': level_for_xp(xp),
        'accuracy': round(100 * int(t['correct'] or 0) / total) if total else 0,
        'streak': _streak(days, clock.tashkent_date(now)),
        'favorite_subjects': [s['name'] for s in subjects[:2]],
        'subjects': subjects[:6],
        'recent': recent,
        'medals': medals(cur, user_id),
    }


# ───────────────────────── Haftalik turnir ─────────────────────────
#
# Hafta dushanba 00:00 (Toshkent) dan boshlanadi. Hafta tugagach eng ko'p
# ball to'plagan 3 kishi medal oladi (notify.py'dagi haftalik vazifa
# award_week'ni chaqiradi; takror chaqirilsa ham bir marta yoziladi).

WEEK_MS = 7 * 24 * 3600 * 1000


def medals(cur, user_id) -> dict:
    cur.execute('SELECT place, COUNT(*) AS n FROM game_awards WHERE user_id = %s GROUP BY place', (user_id,))
    got = {int(r['place']): int(r['n']) for r in cur.fetchall()}
    return {'gold': got.get(1, 0), 'silver': got.get(2, 0), 'bronze': got.get(3, 0)}


def week_top(cur, start_ms, end_ms, limit=3) -> list:
    cur.execute(
        '''SELECT user_id, SUM(xp) AS xp, SUM(won) AS wins FROM game_results
           WHERE created_ms >= %s AND created_ms < %s AND user_id > 0
           GROUP BY user_id''',
        (start_ms, end_ms),
    )
    rows = cur.fetchall()
    banned = boshqaruv.banned_ids(cur)       # natija olingandan keyin (shu cursor'da yangi so'rov); bloklanganlar ko'rinmaydi
    rows = [r for r in rows if int(r['xp'] or 0) > 0 and int(r['user_id']) not in banned]
    rows.sort(key=lambda r: (-int(r['xp']), -int(r['wins'] or 0), r['user_id']))
    return [{'user_id': r['user_id'], 'xp': int(r['xp'])} for r in rows[:limit]]


def award_week(cur, conn, week_start_ms) -> list:
    """O'tgan hafta top-3'iga medal yozadi. Yangi yozilgan g'oliblarni qaytaradi."""
    winners = []
    now = clock.now_ms()
    for place, w in enumerate(week_top(cur, week_start_ms, week_start_ms + WEEK_MS), start=1):
        cur.execute(
            '''INSERT INTO game_awards (week_start_ms, place, user_id, xp, created_ms) VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (week_start_ms, place) DO NOTHING''',
            (week_start_ms, place, w['user_id'], w['xp'], now),
        )
        if cur.rowcount == 1:
            winners.append(dict(w, place=place))
    conn.commit()
    return winners


def tournament(cur, now) -> dict:
    """Joriy hafta qachon tugashi va o'tgan hafta g'oliblari."""
    start = clock.period_start_ms('week', now)
    cur.execute(
        '''SELECT a.place, a.xp, u.name FROM game_awards a LEFT JOIN users u ON u.id = a.user_id
           WHERE a.week_start_ms = %s ORDER BY a.place''',
        (start - WEEK_MS,),
    )
    return {
        'ends_ms': start + WEEK_MS,
        'last_winners': [{'place': int(r['place']), 'xp': int(r['xp']), 'name': r['name'] or "O'yinchi"}
                         for r in cur.fetchall()],
    }


# ───────────────────────── Takrorlash (zaif mavzular) ─────────────────────────

WEAK_ACCURACY = 0.6


def weak_topics(cur, user_id, limit=5) -> list:
    """Zaif mavzular: o'yinlarda aniqlik 60% dan past yoki mavzu testidan
    o'tolmagan. Eng zaifi birinchi."""
    scores = {}
    if schema.READY:
        cur.execute('SELECT topic, correct, total FROM game_topic_stats WHERE user_id = %s AND total > 0', (user_id,))
        for r in cur.fetchall():
            accuracy = int(r['correct']) / int(r['total'])
            if accuracy < WEAK_ACCURACY:
                scores[r['topic']] = accuracy
    cur.execute(
        'SELECT topic_id, quiz_score FROM user_progress WHERE user_id = %s AND quiz_attempts > 0 AND quiz_passed = 0',
        (user_id,),
    )
    for r in cur.fetchall():
        accuracy = (int(r['quiz_score'] or 0)) / 100
        scores[r['topic_id']] = min(scores.get(r['topic_id'], 1.0), accuracy)
    ordered = sorted(scores.items(), key=lambda kv: kv[1])[:limit]
    return [{'topic_id': t, 'accuracy': round(a * 100)} for t, a in ordered]
