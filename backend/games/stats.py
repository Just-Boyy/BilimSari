# -*- coding: utf-8 -*-
"""
O'yin reytingi, profil statistikasi va chaqmoq bilan bog'lanish.

"Ball" — o'yin XP'si: har bir natijada hisobga o'tgan qismi game_results.xp
(faqat kamida 2 ishtirokchili o'yinlar, kunlik limit bilan). Platformaning
umumiy valyutasi chaqmoq: har GAME_XP_PER_CHAQMOQ ball = 1 chaqmoq, u
dashboard va umumiy reytingdagi chaqmoqqa qo'shiladi (study.compute_chaqmoq).
"""

from datetime import timedelta

import curriculum as cur_mod
from games import catalog, clock, schema
from games.rooms import level_for_xp

GAME_XP_PER_CHAQMOQ = 10
PERIODS = ('day', 'week', 'month', 'all')
SCOPES = ('global', 'subject', 'grade')


def xp_by_user(cur) -> dict:
    """Umumiy chaqmoq reytingi uchun: user_id → hisobga o'tgan ball."""
    if not schema.READY:
        return {}
    cur.execute('SELECT user_id, SUM(xp) AS xp FROM game_results GROUP BY user_id')
    return {r['user_id']: int(r['xp'] or 0) for r in cur.fetchall()}


def chaqmoq_from_games(cur, user_id) -> int:
    if not schema.READY:
        return 0
    cur.execute('SELECT COALESCE(SUM(xp), 0) AS xp FROM game_results WHERE user_id = %s', (user_id,))
    return int(cur.fetchone()['xp'] or 0) // GAME_XP_PER_CHAQMOQ


def leaderboard(cur, user_id, period='week', scope='global', subject=None, limit=20) -> dict:
    period = period if period in PERIODS else 'week'
    scope = scope if scope in SCOPES else 'global'
    now = clock.now_ms()
    where, params, join = ['r.created_ms >= %s'], [clock.period_start_ms(period, now)], ''

    if scope == 'subject':
        if subject not in cur_mod.SUBJECT_CATALOG:
            subject = 'math'
        where.append('r.subject = %s')
        params.append(subject)
    grade = None
    if scope == 'grade':
        cur.execute('SELECT grade FROM users WHERE id = %s', (user_id,))
        grade = (cur.fetchone() or {}).get('grade')
        if not grade:
            return {'top': [], 'me': None, 'total_players': 0, 'period': period, 'scope': scope,
                    'notice': "Sinfingiz ko'rsatilmagan — bu reyting hozircha bo'sh."}
        join = 'JOIN users u ON u.id = r.user_id'
        where.append('u.grade = %s')
        params.append(grade)

    cur.execute(
        f'''SELECT r.user_id, SUM(r.xp) AS xp, COUNT(*) AS games, SUM(r.won) AS wins,
                   SUM(r.correct) AS correct, SUM(r.total) AS total
            FROM game_results r {join}
            WHERE {' AND '.join(where)}
            GROUP BY r.user_id''',
        params,
    )
    rows = [r for r in cur.fetchall() if int(r['xp'] or 0) > 0]
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
            'rank': rank, 'name': meta.get('name') or "O'yinchi", 'photo_url': meta.get('photo_url'),
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
    return {'top': top, 'me': me, 'total_players': len(rows), 'period': period, 'scope': scope,
            'subject': subject if scope == 'subject' else None, 'grade': grade}


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
        'chaqmoq': xp // GAME_XP_PER_CHAQMOQ,
        'level': level_for_xp(xp),
        'accuracy': round(100 * int(t['correct'] or 0) / total) if total else 0,
        'streak': _streak(days, clock.tashkent_date(now)),
        'favorite_subjects': [s['name'] for s in subjects[:2]],
        'subjects': subjects[:6],
        'recent': recent,
    }
