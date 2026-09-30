# -*- coding: utf-8 -*-
"""
Chaqmoq jurnali — har bir chaqmoq QACHON va NIMA UCHUN olingani.

Umumiy chaqmoq (dashboard, reyting) avvalgidek manbalardan hisoblanadi (darslar,
o'yinlar, kun savoli). Jurnal esa vaqtga bog'liq hisoblar uchun: yutuqli marafon
faqat marafon davomida olingan chaqmoqni sanaydi. Yozuv chaqmoq berilgan joyda
qo'shiladi:

    source   ref (noyob — bir chaqmoq ikki marta yozilmaydi)
    dars     dars:<topic_id>:quiz | dars:<topic_id>:uy
    shaxsiy  shaxsiy:<pid>:quiz   | shaxsiy:<pid>:uy
    oyin     oyin:<session_id>
    kun      kun:<sana>

premium — olingan paytda o'quvchida Premium faolmidi ("faqat Premium" marafon uchun).
"""

import logging

import premium
from games import clock

logger = logging.getLogger('bilimsari.jurnal')

SOURCES = ('dars', 'shaxsiy', 'oyin', 'kun')


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS chaqmoq_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            source TEXT NOT NULL,
            ref TEXT NOT NULL,
            premium INTEGER NOT NULL DEFAULT 0,
            created_ms BIGINT NOT NULL,
            UNIQUE (user_id, ref)
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_chaqmoq_log_time ON chaqmoq_log (created_ms)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_chaqmoq_log_user ON chaqmoq_log (user_id, created_ms)')
    conn.commit()


def add(cur, user_id, amount, source, ref, now=None) -> bool:
    """Yozuv qo'shadi (commit — chaqiruvchida). Bir ref ikki marta yozilmaydi."""
    amount = int(amount or 0)
    if amount <= 0 or not user_id or int(user_id) <= 0:
        return False
    now = now or clock.now_ms()
    active = premium.status(cur, int(user_id), now)['active']
    cur.execute('INSERT INTO chaqmoq_log (user_id, amount, source, ref, premium, created_ms) '
                'VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (user_id, ref) DO NOTHING',
                (int(user_id), amount, source, str(ref), int(bool(active)), now))
    return cur.rowcount == 1


def record(cur, conn, user_id, amount, source, ref, now=None) -> bool:
    """Asosiy amal saqlangandan KEYIN chaqiriladi: jurnal xatosi darsni yoki javobni buzmaydi."""
    try:
        ok = add(cur, user_id, amount, source, ref, now)
        conn.commit()
        return ok
    except Exception:  # noqa: BLE001
        conn.rollback()
        logger.warning('Chaqmoq jurnaliga yozilmadi (%s %s)', source, ref, exc_info=True)
        return False


def cleanup_user(cur, user_id):
    cur.execute('DELETE FROM chaqmoq_log WHERE user_id = %s', (user_id,))
