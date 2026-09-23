# -*- coding: utf-8 -*-
"""
Baza orqali umumiy tezlik cheklovi.

Oldin har bir cheklov (AI, admin login) jarayon ichidagi oddiy dict'da
saqlanardi — gunicorn bir necha worker bilan ishlaganda har birida alohida
hisoblagich bo'lib, real chegara worker soniga ko'paytirilib ketardi.
Bu yerda hisob bazada (worker'lar orasida umumiy) saqlanadi.
"""

from datetime import timedelta

from db import get_connection, utc_now


def ensure_table(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS rate_hits (
            id SERIAL PRIMARY KEY,
            bucket TEXT NOT NULL,
            ts TIMESTAMP NOT NULL
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_rate_hits_bucket_ts ON rate_hits (bucket, ts)')
    conn.commit()


def _cleanup(cur, conn, bucket, window_seconds):
    cutoff = utc_now() - timedelta(seconds=window_seconds)
    cur.execute('DELETE FROM rate_hits WHERE bucket = %s AND ts < %s', (bucket, cutoff))
    conn.commit()


def hit(bucket: str, limit: int, window_seconds: int) -> bool:
    """Bitta so'rovni hisoblaydi. True — ruxsat, False — chegaradan oshgan."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        _cleanup(cur, conn, bucket, window_seconds)
        cur.execute('SELECT COUNT(*) AS n FROM rate_hits WHERE bucket = %s', (bucket,))
        if cur.fetchone()['n'] >= limit:
            return False
        cur.execute('INSERT INTO rate_hits (bucket, ts) VALUES (%s, %s)', (bucket, utc_now()))
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()


def is_blocked(bucket: str, limit: int, window_seconds: int) -> bool:
    """So'rovni hisoblamasdan, faqat hozirgi holatni tekshiradi."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        _cleanup(cur, conn, bucket, window_seconds)
        cur.execute('SELECT COUNT(*) AS n FROM rate_hits WHERE bucket = %s', (bucket,))
        return cur.fetchone()['n'] >= limit
    finally:
        cur.close()
        conn.close()


def record(bucket: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO rate_hits (bucket, ts) VALUES (%s, %s)', (bucket, utc_now()))
        conn.commit()
    finally:
        cur.close()
        conn.close()
