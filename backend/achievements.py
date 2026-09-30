# -*- coding: utf-8 -*-
"""
Yutuqlar (nishonlar) — o'qish, o'yin va kun savolidagi natijalar uchun.

Ta'riflar shu faylda. Shart bajarilganda user_achievements'ga yoziladi va
keyin shart buzilsa ham (masalan, streak uzilsa) nishon saqlanib qoladi.
seen_ms — tabriklash xabari ko'rsatilganmi (bir marta ko'rsatiladi).
Nishonlar faqat bezak: chaqmoqqa ta'sir qilmaydi.
"""

import json

import daily
import study
from db import add_column_if_missing
from games import clock
from games.errors import GameError

MAX_PINNED = 6   # avatar atrofida ko'rinadigan nishonlar soni

# (kalit, nomi, tavsifi, ikonka, metrika, chegara) — tartib profildagi tartib
ACHIEVEMENTS = [
    ('mavzu_1', 'Birinchi qadam', 'Birinchi mavzuni tugatdingiz', 'bookOpen', 'topics', 1),
    ('mavzu_10', 'Bilim izlovchi', '10 ta mavzu tugatildi', 'book', 'topics', 10),
    ('mavzu_50', '50 ta mavzu', '50 ta mavzu tugatildi', 'graduation', 'topics', 50),
    ('mavzu_100', 'Bilimdon', '100 ta mavzu tugatildi', 'gem', 'topics', 100),
    ('streak_3', '3 kunlik streak', '3 kun ketma-ket dars', 'flame', 'streak', 3),
    ('streak_7', '7 kunlik streak', '7 kun ketma-ket dars', 'flame', 'streak', 7),
    ('streak_30', '30 kunlik streak', '30 kun ketma-ket dars', 'zap', 'streak', 30),
    ('oyin_1', "Birinchi o'yin", "Birinchi o'yinni o'ynadingiz", 'gamepad', 'games', 1),
    ('galaba_1', "Birinchi g'alaba", "O'yinda 1-o'rinni oldingiz", 'trophy', 'wins', 1),
    ('galaba_10', "10 ta g'alaba", "O'yinlarda 10 marta g'olib bo'ldingiz", 'crown', 'wins', 10),
    ('bot_qiyin', 'Kompyuter ustasi', 'Qiyin darajadagi kompyuterni yutdingiz', 'bot', 'hard_bot', 1),
    ('turnir_3', 'Turnir sovrindori', "Haftalik turnirda top-3 ga kirdingiz", 'medal', 'podium', 1),
    ('turnir_1', "Turnir g'olibi", "Haftalik turnirda 1-o'rin", 'award', 'champion', 1),
    ('kun_1', 'Kun savoli', 'Birinchi kun savoliga javob berdingiz', 'sparkle', 'daily', 1),
    ('kun_7', 'Har kuni savol', '7 kun ketma-ket kun savoliga javob', 'target', 'daily_streak', 7),
    ('chaqmoq_500', '500 chaqmoq', "Jami 500 chaqmoq to'pladingiz", 'chaqmoq', 'chaqmoq', 500),
    ('premium', 'Bilim Premium', "Bilim Premium a'zolari uchun maxsus nishon", 'crown', 'premium', 1),
    ('marafon_sovrin', 'Marafon sovrindori', "Yutuqli marafonda sovrinli o'ringa kirdingiz", 'medal', 'marathon_prize', 1),
    ('marafon_1', "Marafon g'olibi", "Yutuqli marafonda 1-o'rinni oldingiz", 'trophy', 'marathon_champion', 1),
]

# Daraja — nishonni olish qanchalik qiyin bo'lsa, shunchalik yuqori:
# bronza → kumush → oltin → brilyant. Premium nishoni — alohida, yaltiroq "premium" darajasi.
TIERS = {
    'mavzu_1': 'bronza', 'oyin_1': 'bronza', 'kun_1': 'bronza', 'streak_3': 'bronza',
    'mavzu_10': 'kumush', 'streak_7': 'kumush', 'galaba_1': 'kumush', 'kun_7': 'kumush', 'chaqmoq_500': 'kumush',
    'mavzu_50': 'oltin', 'galaba_10': 'oltin', 'bot_qiyin': 'oltin', 'turnir_3': 'oltin',
    'mavzu_100': 'brilyant', 'streak_30': 'brilyant', 'turnir_1': 'brilyant',
    'marafon_sovrin': 'oltin', 'marafon_1': 'brilyant',
    'premium': 'premium',
}


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            unlocked_ms BIGINT NOT NULL,
            seen_ms BIGINT,
            PRIMARY KEY (user_id, key)
        )
    ''')
    conn.commit()
    # Avatar atrofida ko'rsatish uchun o'quvchi tanlagan nishonlar (JSON ro'yxat);
    # bo'sh bo'lsa — eng so'nggi olinganlari avtomatik ko'rsatiladi
    add_column_if_missing(cur, conn, 'users', 'pinned_badges', 'TEXT')


def _pinned(cur, user_id) -> list:
    cur.execute('SELECT pinned_badges FROM users WHERE id = %s', (user_id,))
    row = cur.fetchone()
    try:
        keys = json.loads((row or {}).get('pinned_badges') or '[]')
    except (TypeError, ValueError):
        return []
    return [k for k in keys if isinstance(k, str)] if isinstance(keys, list) else []


def pin(cur, conn, user_id, keys) -> list:
    """Avatar atrofidagi nishonlarni saqlaydi (faqat olinganlari, ko'pi bilan 6 ta).
    Bo'sh ro'yxat — avtomatik rejimga qaytish."""
    if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
        raise GameError('bad_request', "Nishonlar ro'yxati noto'g'ri.")
    keys = list(dict.fromkeys(keys))
    if len(keys) > MAX_PINNED:
        raise GameError('too_many', f"Ko'pi bilan {MAX_PINNED} ta nishon tanlash mumkin.")
    cur.execute('SELECT key FROM user_achievements WHERE user_id = %s', (user_id,))
    have = {r['key'] for r in cur.fetchall()}
    if any(k not in have for k in keys):
        raise GameError('not_unlocked', "Faqat olingan nishonlarni tanlash mumkin.")
    cur.execute('UPDATE users SET pinned_badges = %s WHERE id = %s', (json.dumps(keys) if keys else None, user_id))
    conn.commit()
    return keys


def _metrics(cur, user_id, now_ms) -> dict:
    cur.execute('SELECT COUNT(*) AS n FROM user_progress WHERE user_id = %s AND status = %s',
                (user_id, study.STATUS_COMPLETED))
    topics = int(cur.fetchone()['n'] or 0)
    cur.execute(
        '''SELECT COUNT(*) AS n, COALESCE(SUM(won), 0) AS w,
                  COALESCE(SUM(CASE WHEN won = 1 AND bot_level >= 5 THEN 1 ELSE 0 END), 0) AS hb
           FROM game_results WHERE user_id = %s''',
        (user_id,),
    )
    g = cur.fetchone()
    cur.execute('SELECT MIN(place) AS best FROM game_awards WHERE user_id = %s', (user_id,))
    best = cur.fetchone()['best']
    cur.execute('SELECT COUNT(*) AS n FROM daily_answers WHERE user_id = %s AND answered_ms IS NOT NULL',
                (user_id,))
    answered = int(cur.fetchone()['n'] or 0)
    # Premium: hozir faol yoki qachondir olingan (karta yoki admin orqali)
    cur.execute('SELECT premium_until FROM users WHERE id = %s', (user_id,))
    until = (cur.fetchone() or {}).get('premium_until')
    had_premium = bool(until and int(until) > now_ms)
    if not had_premium:
        cur.execute("SELECT 1 FROM premium_log WHERE user_id = %s AND source != 'revoke' LIMIT 1", (user_id,))
        had_premium = cur.fetchone() is not None
    try:
        cur.execute('SELECT MIN(place) AS best FROM marathon_winners WHERE user_id = %s', (user_id,))
        marathon_best = cur.fetchone()['best']
    except Exception:  # noqa: BLE001  (jadval hali yo'q)
        marathon_best = None
    return {
        'marathon_prize': 1 if marathon_best is not None else 0,
        'marathon_champion': 1 if marathon_best == 1 else 0,
        'topics': topics,
        'streak': study.compute_streak(cur, user_id),
        'games': int(g['n'] or 0),
        'wins': int(g['w'] or 0),
        'hard_bot': int(g['hb'] or 0),
        'podium': 1 if best is not None else 0,
        'champion': 1 if best == 1 else 0,
        'daily': answered,
        'daily_streak': daily.streak(cur, user_id, now_ms),
        'chaqmoq': study.compute_chaqmoq(cur, user_id),
        'premium': 1 if had_premium else 0,
    }


def evaluate(cur, conn, user_id, now_ms=None, mark_seen=True) -> dict:
    """Shartlarni tekshiradi, yangilarini ochadi. Qaytaradi: hamma nishonlar
    (ochilgan/yopiq, jarayon) va hali tabriklanmagan yangi nishonlar."""
    now_ms = now_ms or clock.now_ms()
    metrics = _metrics(cur, user_id, now_ms)
    cur.execute('SELECT key, unlocked_ms, seen_ms FROM user_achievements WHERE user_id = %s', (user_id,))
    have = {r['key']: r for r in cur.fetchall()}

    fresh = [a[0] for a in ACHIEVEMENTS if a[0] not in have and metrics[a[4]] >= a[5]]
    for key in fresh:
        cur.execute('INSERT INTO user_achievements (user_id, key, unlocked_ms) VALUES (%s, %s, %s) '
                    'ON CONFLICT (user_id, key) DO NOTHING', (user_id, key, now_ms))
        have[key] = {'key': key, 'unlocked_ms': now_ms, 'seen_ms': None}

    items, new = [], []
    for key, title, desc, icon, metric, goal in ACHIEVEMENTS:
        row = have.get(key)
        item = {
            'key': key, 'title': title, 'desc': desc, 'icon': icon, 'tier': TIERS.get(key, 'oltin'),
            'unlocked': row is not None, 'unlocked_ms': int(row['unlocked_ms']) if row else None,
            'progress': min(metrics[metric], goal), 'goal': goal,
        }
        items.append(item)
        if row is not None and row['seen_ms'] is None:
            new.append(item)
    if new and mark_seen:
        marks = ', '.join(['%s'] * len(new))
        cur.execute(f'UPDATE user_achievements SET seen_ms = %s WHERE user_id = %s AND key IN ({marks}) '
                    'AND seen_ms IS NULL', [now_ms, user_id] + [n['key'] for n in new])
    conn.commit()
    pinned = [k for k in _pinned(cur, user_id) if k in have]
    return {'items': items, 'new': new, 'unlocked': sum(1 for i in items if i['unlocked']), 'total': len(items),
            'pinned': pinned, 'max_pinned': MAX_PINNED}
