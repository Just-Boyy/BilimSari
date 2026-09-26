# -*- coding: utf-8 -*-
"""
Game Hub jadvallari. Vaqtlar epoch millisekund (BIGINT), mantiqiy qiymatlar
INTEGER 0/1 — PostgreSQL va lokal SQLite'da bir xil ishlashi uchun.

    game_rooms         — room (kod, sozlamalar, holat, versiya)
    game_room_players  — roomdagi o'yinchilar (tayyor, chiqdi, chiqarildi)
    game_sessions      — bitta o'yin (savollar faqat serverda, faza, taymer)
    game_answers       — javoblar; (session, user, savol) noyob — ikki marta javob yo'q
    game_results       — yakuniy natijalar (statistika va reyting manbai)
    game_queue         — random raqib qidirish navbati
    game_presence      — "onlayn o'yinchilar" hisobi uchun oxirgi faollik
"""

READY = False


def ensure_tables(cur, conn):
    global READY
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_rooms (
            id SERIAL PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            host_user_id INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT,
            difficulty TEXT NOT NULL,
            question_count INTEGER NOT NULL,
            max_players INTEGER NOT NULL,
            is_public INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL DEFAULT 'create',
            status TEXT NOT NULL DEFAULT 'waiting',
            session_id INTEGER,
            version INTEGER NOT NULL DEFAULT 1,
            created_ms BIGINT NOT NULL,
            activity_ms BIGINT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_room_players (
            id SERIAL PRIMARY KEY,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 1,
            ready INTEGER NOT NULL DEFAULT 0,
            state TEXT NOT NULL DEFAULT 'active',
            joined_ms BIGINT NOT NULL,
            seen_ms BIGINT NOT NULL,
            left_ms BIGINT,
            UNIQUE (room_id, user_id)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_sessions (
            id SERIAL PRIMARY KEY,
            room_id INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT,
            difficulty TEXT NOT NULL,
            mode TEXT NOT NULL,
            total INTEGER NOT NULL,
            questions TEXT NOT NULL,
            phase TEXT NOT NULL,
            q_index INTEGER NOT NULL DEFAULT 0,
            phase_started_ms BIGINT NOT NULL,
            phase_ends_ms BIGINT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            started_ms BIGINT NOT NULL,
            finished_ms BIGINT,
            end_reason TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_answers (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            q_index INTEGER NOT NULL,
            answer TEXT NOT NULL,
            correct INTEGER NOT NULL DEFAULT 0,
            partial INTEGER NOT NULL DEFAULT 0,
            points INTEGER NOT NULL DEFAULT 0,
            answered_ms BIGINT NOT NULL,
            elapsed_ms INTEGER NOT NULL,
            UNIQUE (session_id, user_id, q_index)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_results (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT,
            difficulty TEXT NOT NULL,
            score INTEGER NOT NULL,
            earned INTEGER NOT NULL,
            xp INTEGER NOT NULL DEFAULT 0,
            correct INTEGER NOT NULL,
            wrong INTEGER NOT NULL,
            total INTEGER NOT NULL,
            accuracy INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            players INTEGER NOT NULL,
            won INTEGER NOT NULL DEFAULT 0,
            duration_ms BIGINT NOT NULL DEFAULT 0,
            created_ms BIGINT NOT NULL,
            UNIQUE (session_id, user_id)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_queue (
            user_id INTEGER PRIMARY KEY,
            game_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT,
            difficulty TEXT NOT NULL,
            question_count INTEGER NOT NULL,
            skill INTEGER NOT NULL DEFAULT 50,
            status TEXT NOT NULL DEFAULT 'waiting',
            room_code TEXT,
            created_ms BIGINT NOT NULL,
            seen_ms BIGINT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_presence (
            user_id INTEGER PRIMARY KEY,
            seen_ms BIGINT NOT NULL
        )
    ''')
    conn.commit()

    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_rooms_lobby ON game_rooms (status, is_public, activity_ms)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_players_user ON game_room_players (user_id, state)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_players_room ON game_room_players (room_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_sessions_room ON game_sessions (room_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_answers_q ON game_answers (session_id, q_index)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_results_user ON game_results (user_id, created_ms)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_results_time ON game_results (created_ms)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_queue_match ON game_queue (status, game_type, subject)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_game_presence_seen ON game_presence (seen_ms)')
    conn.commit()
    READY = True
