# -*- coding: utf-8 -*-
"""
Boshqa o'quvchining ochiq profili — reyting, kun savoli va o'yinlarda ismini bosganda ochiladi.

Faqat ilovada allaqachon ochiq ko'rinadigan narsalar beriladi (ism, rasm, chaqmoq, reytingdagi
o'rin, nishonlar, o'yin natijalari). Telegram username/ID, email, to'lovlar va Premium muddati
berilmaydi.
"""

import achievements
import dostlar
import premium
import study
from games import clock
from games import stats as game_stats


def _badges(cur, user_id) -> dict:
    """Olingan nishonlar (faqat o'qish — boshqaning nishonlari bu yerda "ochilmaydi")."""
    cur.execute('SELECT key, unlocked_ms FROM user_achievements WHERE user_id = %s', (user_id,))
    have = {r['key']: int(r['unlocked_ms']) for r in cur.fetchall()}
    items = [{'key': key, 'title': title, 'desc': desc, 'icon': icon,
              'tier': achievements.TIERS.get(key, 'oltin'), 'unlocked_ms': have[key]}
             for key, title, desc, icon, _metric, _goal in achievements.ACHIEVEMENTS if key in have]
    pinned = [k for k in achievements._pinned(cur, user_id) if k in have]
    return {'items': items, 'unlocked': len(items), 'total': len(achievements.ACHIEVEMENTS), 'pinned': pinned}


def public(cur, user_id, now=None, viewer_id=None):
    """Ochiq profil yoki None (bunday o'quvchi yo'q)."""
    now = now or clock.now_ms()
    cur.execute('SELECT id, name, photo_url FROM users WHERE id = %s', (user_id,))
    u = cur.fetchone()
    if not u:
        return None
    board = study.leaderboard(cur, user_id, limit=0)
    me = board.get('me') or {}
    st = premium.status(cur, user_id, now)
    cur.execute('SELECT COUNT(*) AS n FROM user_progress WHERE user_id = %s AND status = %s',
                (user_id, study.STATUS_COMPLETED))
    topics = int(cur.fetchone()['n'] or 0)
    g = game_stats.my_stats(cur, user_id)
    return {
        'id': int(u['id']),
        'name': u['name'] or "O'quvchi",
        'photo_url': u['photo_url'],
        'premium': {'active': st['active'], 'emoji': st['emoji'], 'frame': st['frame']},
        'chaqmoq': int(me.get('chaqmoq') or 0),
        'rank': me.get('rank'),
        'total_players': board.get('total_players', 0),
        'streak': study.compute_streak(cur, user_id),
        'topics': topics,
        'games': {k: g.get(k) for k in ('games', 'wins', 'accuracy', 'xp', 'level', 'medals')},
        'badges': _badges(cur, user_id),
        'friends_count': dostlar.count(cur, user_id),
        'friend': dostlar.relation(cur, viewer_id, user_id) if viewer_id else None,
    }
