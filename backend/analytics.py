# -*- coding: utf-8 -*-
"""
Admin panel uchun batafsil statistika: kunlik faol o'quvchilar, ertasi kuni
qaytganlar ulushi, mashhur fanlar, do'kon konversiyasi va faol soatlar.

"Faol" — shu kuni ilovani ochgan (activity_days) yoki mavzu boshlagan/
tugatgan, o'yin o'ynagan, kun savolini ochgan yoki buyurtma bergan o'quvchi.
activity_days ilova ochilishini ham qayd etadi (har o'quvchi uchun kuniga
bitta qator); u joriy qilinishidan oldingi kunlar qolgan jadvallardan
tiklanadi, shuning uchun tarix ham bo'sh emas.
"""

import logging
from datetime import datetime, timedelta, timezone

import curriculum as cur_mod
from db import TASHKENT_TZ, as_utc, get_connection, to_tashkent
from games import clock

logger = logging.getLogger('bilimsari.analytics')

APP, SHOP = 'app', 'shop'
PERIODS = (7, 30, 90)
_seen = {'day': None, 'keys': set()}   # shu worker bugun yozgan (o'quvchi, tur) — bazaga qayta bormaslik uchun


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS activity_days (
            user_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            kind TEXT NOT NULL,
            PRIMARY KEY (user_id, day, kind)
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_activity_days_day ON activity_days (day, kind)')
    conn.commit()


def touch(user_id, kind=APP, now_ms=None):
    """O'quvchi bugun ilovani (yoki do'konni) ochganini qayd etadi — kuniga bir marta."""
    day = clock.tashkent_date(now_ms or clock.now_ms()).isoformat()
    if _seen['day'] != day:
        _seen['day'], _seen['keys'] = day, set()
    key = (int(user_id), kind)
    if key in _seen['keys']:
        return
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO activity_days (user_id, day, kind) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                    (key[0], day, kind))
        conn.commit()
        _seen['keys'].add(key)
    except Exception:  # noqa: BLE001  (statistika asosiy so'rovni buzmasin)
        conn.rollback()
        logger.warning('activity_days yozilmadi', exc_info=True)
    finally:
        cur.close()
        conn.close()


# ───────────────────────── Hisobot ─────────────────────────

def _local(dt_or_ms):
    if dt_or_ms is None:
        return None
    if isinstance(dt_or_ms, (int, float)):
        return datetime.fromtimestamp(int(dt_or_ms) / 1000, TASHKENT_TZ)
    return to_tashkent(as_utc(dt_or_ms))


def _pct(part, whole):
    return round(100 * part / whole) if whole else None


def report(cur, days=30, now_ms=None) -> dict:
    now_ms = now_ms or clock.now_ms()
    days = days if days in PERIODS else 30
    today = clock.tashkent_date(now_ms)
    # Retention uchun oynadan 7 kun oldingi ro'yxatdan o'tganlar ham kerak
    first = today - timedelta(days=days - 1)
    span_start = first - timedelta(days=7)
    since_local = datetime(span_start.year, span_start.month, span_start.day, tzinfo=TASHKENT_TZ)
    since_ms = int(since_local.timestamp() * 1000)
    since_utc = since_local.astimezone(timezone.utc).replace(tzinfo=None)   # bazadagi TIMESTAMP — naive UTC

    active = {}                    # kun → {o'quvchilar}
    hours = [0] * 24               # faol soatlar (voqealar soni)

    def mark(uid, when, count_hour=True):
        loc = _local(when)
        if not loc or not uid:
            return
        d = loc.date()
        if d < span_start or d > today:
            return
        active.setdefault(d, set()).add(int(uid))
        if count_hour and d >= first:
            hours[loc.hour] += 1

    cur.execute('SELECT user_id, day FROM activity_days WHERE kind = %s AND day >= %s', (APP, span_start.isoformat()))
    for r in cur.fetchall():
        try:
            d = datetime.strptime(r['day'], '%Y-%m-%d').date()
        except (TypeError, ValueError):
            continue
        active.setdefault(d, set()).add(int(r['user_id']))

    cur.execute('''SELECT p.user_id, p.started_at, p.completed_at, t.subject_key FROM user_progress p
                   LEFT JOIN topics t ON t.id = p.topic_id
                   WHERE p.started_at >= %s OR p.completed_at >= %s''', (since_utc, since_utc))
    subj_learners, subj_done = {}, {}
    for r in cur.fetchall():
        mark(r['user_id'], r['started_at'])
        mark(r['user_id'], r['completed_at'])
        key = r['subject_key']
        if not key:
            continue
        for when in (r['started_at'], r['completed_at']):
            loc = _local(when)
            if loc and loc.date() >= first:
                subj_learners.setdefault(key, set()).add(int(r['user_id']))
        loc = _local(r['completed_at'])
        if loc and loc.date() >= first:
            subj_done[key] = subj_done.get(key, 0) + 1

    cur.execute('SELECT user_id, subject, created_ms FROM game_results WHERE user_id > 0 AND created_ms >= %s',
                (since_ms,))
    subj_games = {}
    for r in cur.fetchall():
        mark(r['user_id'], int(r['created_ms']))
        if _local(int(r['created_ms'])).date() >= first:
            subj_games[r['subject']] = subj_games.get(r['subject'], 0) + 1

    cur.execute('SELECT user_id, opened_ms FROM daily_answers WHERE opened_ms >= %s', (since_ms,))
    for r in cur.fetchall():
        mark(r['user_id'], int(r['opened_ms']))

    cur.execute('SELECT user_id, created_ms, status FROM pay_orders WHERE created_ms >= %s', (since_ms,))
    orders = cur.fetchall()
    for r in orders:
        mark(r['user_id'], int(r['created_ms']), count_hour=False)

    # Ro'yxatdan o'tganlar (retention kogortalari)
    cur.execute('SELECT id, created_at FROM users WHERE created_at >= %s', (since_utc,))
    signups = {}
    for r in cur.fetchall():
        loc = _local(r['created_at'])
        if loc:
            signups.setdefault(loc.date(), set()).add(int(r['id']))
            active.setdefault(loc.date(), set()).add(int(r['id']))

    window = [first + timedelta(days=i) for i in range(days)]
    dau = [{'date': d.isoformat(), 'n': len(active.get(d, ()))} for d in window]

    def unique(n_days):
        out = set()
        for i in range(n_days):
            out |= active.get(today - timedelta(days=i), set())
        return out

    # Ertasi kuni / 7 kun ichida qaytganlar (kogorta — oynadagi ro'yxatdan o'tish kuni)
    d1_base = d1_back = d7_base = d7_back = 0
    cohorts = []
    for d in window:
        users = signups.get(d, set())
        if not users:
            continue
        nxt = d + timedelta(days=1)
        back1 = len(users & active.get(nxt, set())) if nxt <= today else None
        week = set()
        for i in range(1, 8):
            week |= active.get(d + timedelta(days=i), set())
        back7 = len(users & week) if d + timedelta(days=7) <= today else None
        if back1 is not None:
            d1_base += len(users)
            d1_back += back1
        if back7 is not None:
            d7_base += len(users)
            d7_back += back7
        cohorts.append({'date': d.isoformat(), 'signups': len(users), 'd1': back1, 'd7': back7})

    # Mashhur fanlar
    subjects = []
    for key, meta in cur_mod.SUBJECT_CATALOG.items():
        learners = len(subj_learners.get(key, ()))
        done = subj_done.get(key, 0)
        games = subj_games.get(key, 0)
        if learners or done or games:
            subjects.append({'key': key, 'name': meta['name'], 'color': meta.get('color'),
                             'learners': learners, 'completed': done, 'games': games})
    subjects.sort(key=lambda s: (-s['learners'], -s['completed'], -s['games']))

    # Do'kon konversiyasi: do'konni ochgan → buyurtma bergan → to'lagan
    first_iso = first.isoformat()
    cur.execute('SELECT DISTINCT user_id FROM activity_days WHERE kind = %s AND day >= %s', (SHOP, first_iso))
    visitors = {int(r['user_id']) for r in cur.fetchall()}
    ordered, paid = set(), set()
    for r in orders:
        if _local(int(r['created_ms'])).date() < first:
            continue
        uid = int(r['user_id'])
        ordered.add(uid)
        if r['status'] == 'approved':
            paid.add(uid)
    visitors |= ordered                 # buyurtma berganlar do'konni ham ochgan
    cur.execute('SELECT MIN(day) AS d FROM activity_days WHERE kind = %s', (SHOP,))
    shop_since = (cur.fetchone() or {}).get('d')

    return {
        'days': days,
        'today': today.isoformat(),
        'dau': dau,
        'dau_today': len(active.get(today, ())),
        'wau': len(unique(7)),
        'mau': len(unique(30)) if days >= 30 else None,
        'period_active': len(unique(days)),
        'avg_dau': round(sum(p['n'] for p in dau) / len(dau), 1) if dau else 0,
        'retention': {'d1': _pct(d1_back, d1_base), 'd1_base': d1_base,
                      'd7': _pct(d7_back, d7_base), 'd7_base': d7_base},
        'cohorts': cohorts[-14:],
        'subjects': subjects,
        'funnel': {'visitors': len(visitors), 'ordered': len(ordered), 'paid': len(paid),
                   'conversion': _pct(len(paid), len(visitors)), 'shop_tracked_since': shop_since},
        'hours': hours,
    }
