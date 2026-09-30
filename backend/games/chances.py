# -*- coding: utf-8 -*-
"""
Chaqmoqli o'yin imkoniyatlari.

O'ynash cheksiz, lekin chaqmoqni ketma-ket faqat 3 ta o'yin beradi: 1-o'rin +30,
qolgan o'rinlar +20. Imkoniyat odamlar bilan (kamida 2 kishi) o'ynalgan o'yin
BOSHLANGANDA ishlatiladi — o'yinchi keyin chiqib ketsa ham qaytmaydi (chaqmoq ham
olmaydi). Kompyuter bilan o'yin imkoniyatni ishlatmaydi va chaqmoq bermaydi.

3-imkoniyat ishlatilgan o'yin tugagach (yoki undan chiqilgach) 24 soatlik taymer
boshlanadi; u tugaganda yana 3 ta imkoniyat beriladi.

    game_chances       — har bir ishlatilgan imkoniyat (qaysi o'yin, qancha chaqmoq)
    game_chance_state  — o'quvchining joriy aylanasi: nechtasi ishlatilgan, qachon yangilanadi
"""

MAX = 3
WIN = 30                       # 1-o'rin
PLAY = 20                      # qolgan o'rinlar (o'yin oxirigacha qolganlar)
RESET_MS = 24 * 3600 * 1000
STALE_MS = 2 * 3600 * 1000     # 3-o'yin shuncha vaqtda tugamasa (osilib qolgan) — boshlangan vaqtidan sanaladi


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_chances (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            used_ms BIGINT NOT NULL,
            ended_ms BIGINT,
            chaqmoq INTEGER NOT NULL DEFAULT 0,
            UNIQUE (user_id, session_id)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_chance_state (
            user_id INTEGER PRIMARY KEY,
            used INTEGER NOT NULL DEFAULT 0,
            reset_at_ms BIGINT
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_chances_user ON game_chances (user_id, used_ms)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_chances_session ON game_chances (session_id)')
    conn.commit()


def _effective(cur, user_id, now):
    """(ishlatilgan, yangilanish vaqti, 3-o'yin hali davom etyaptimi) — taymer tugagan bo'lsa aylana nolga qaytadi."""
    cur.execute('SELECT used, reset_at_ms FROM game_chance_state WHERE user_id = %s', (user_id,))
    row = cur.fetchone()
    used = int(row['used']) if row else 0
    reset_at = int(row['reset_at_ms']) if row and row['reset_at_ms'] else None
    pending = False
    if used >= MAX and reset_at is None:
        # Taymer 3-o'yin tugagach boshlanadi: tugaganmi yoki osilib qolganmi — tekshiramiz
        cur.execute('SELECT used_ms, ended_ms FROM game_chances WHERE user_id = %s ORDER BY used_ms DESC, id DESC LIMIT 1',
                    (user_id,))
        last = cur.fetchone()
        if last and last['ended_ms']:
            reset_at = int(last['ended_ms']) + RESET_MS
        elif last and now - int(last['used_ms']) > STALE_MS:
            reset_at = int(last['used_ms']) + RESET_MS
        else:
            pending = True
    if reset_at is not None and now >= reset_at:
        used, reset_at = 0, None
    return used, reset_at, pending


def status(cur, user_id, now) -> dict:
    used, reset_at, pending = _effective(cur, user_id, now)
    used = min(used, MAX)
    return {'max': MAX, 'used': used, 'left': MAX - used, 'win': WIN, 'play': PLAY,
            'reset_at_ms': reset_at if used >= MAX else None, 'pending': pending}


def _save(cur, user_id, used, reset_at):
    cur.execute(
        '''INSERT INTO game_chance_state (user_id, used, reset_at_ms) VALUES (%s, %s, %s)
           ON CONFLICT (user_id) DO UPDATE SET used = EXCLUDED.used, reset_at_ms = EXCLUDED.reset_at_ms''',
        (user_id, used, reset_at),
    )


def consume(cur, user_id, session_id, now) -> bool:
    """O'yin boshlanganda: imkoniyat bo'lsa ishlatadi (True — bu o'yin chaqmoq beradi)."""
    used, reset_at, _ = _effective(cur, user_id, now)
    if used >= MAX:
        return False
    cur.execute('INSERT INTO game_chances (user_id, session_id, used_ms) VALUES (%s, %s, %s) '
                'ON CONFLICT (user_id, session_id) DO NOTHING', (user_id, session_id, now))
    if cur.rowcount != 1:
        return True                     # shu o'yin uchun allaqachon ishlatilgan
    _save(cur, user_id, used + 1, None)
    return True


def begin_session(cur, session_id, human_ids, now) -> dict:
    """O'yin boshlandi. Kamida 2 odam bo'lsa — har biriga imkoniyat ishlatiladi. {user_id: chaqmoq beradimi}."""
    humans = sorted({int(u) for u in human_ids if u and int(u) > 0})
    cur.execute('UPDATE game_sessions SET humans = %s WHERE id = %s', (len(humans), session_id))
    if len(humans) < 2:
        return {u: False for u in humans}
    return {u: consume(cur, u, session_id, now) for u in humans}


def close(cur, user_id, session_id, now, chaqmoq=0) -> bool:
    """O'yin shu o'quvchi uchun tugadi (natija yoki chiqib ketish). 3-imkoniyat bo'lsa — taymer boshlanadi."""
    cur.execute('UPDATE game_chances SET ended_ms = %s, chaqmoq = %s '
                'WHERE user_id = %s AND session_id = %s AND ended_ms IS NULL',
                (now, int(chaqmoq), user_id, session_id))
    if cur.rowcount != 1:
        return False
    cur.execute('SELECT used, reset_at_ms FROM game_chance_state WHERE user_id = %s', (user_id,))
    st = cur.fetchone()
    if st and int(st['used']) >= MAX and not st['reset_at_ms']:
        _save(cur, user_id, int(st['used']), now + RESET_MS)
    return True


def open_users(cur, session_id) -> set:
    cur.execute('SELECT user_id FROM game_chances WHERE session_id = %s AND ended_ms IS NULL', (session_id,))
    return {int(r['user_id']) for r in cur.fetchall()}


def close_all(cur, session_id, now):
    """O'yin tugadi — yopilmay qolgan imkoniyatlar (chaqmoqsiz) yopiladi."""
    for uid in open_users(cur, session_id):
        close(cur, uid, session_id, now, 0)


def for_session(cur, user_id, session_id):
    cur.execute('SELECT used_ms, ended_ms, chaqmoq FROM game_chances WHERE user_id = %s AND session_id = %s',
                (user_id, session_id))
    return cur.fetchone()


def game_info(cur, user_id, now, session=None, humans_now=None) -> dict:
    """Mijoz uchun: imkoniyatlar holati va BU o'yin chaqmoq beradimi.
    kind: 'yes' — beradi, 'no_chance' — imkoniyat tugagan, 'bot' — odamlar kam (kompyuter bilan)."""
    info = status(cur, user_id, now)
    if session and session.get('humans') is not None:
        if for_session(cur, user_id, session['id']):
            kind = 'yes'
        else:
            kind = 'bot' if int(session['humans']) < 2 else 'no_chance'
    else:
        kind = 'bot' if (humans_now or 0) < 2 else ('yes' if info['left'] > 0 else 'no_chance')
    return dict(info, kind=kind)
