# -*- coding: utf-8 -*-
"""Admin panelda qilingan harakatlar tarixi (bitta umumiy admin parol bilan
ishlaganda ham, keyin "kim nima qildi" savoliga javob topish uchun)."""

from db import as_utc, get_connection, iso_utc, utc_now


def ensure_table(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            id SERIAL PRIMARY KEY,
            action TEXT NOT NULL,
            detail TEXT,
            ip TEXT,
            ts TIMESTAMP NOT NULL
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_admin_audit_ts ON admin_audit_log (ts DESC)')
    conn.commit()


def log(action: str, detail: str = '', ip: str = ''):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO admin_audit_log (action, detail, ip, ts) VALUES (%s, %s, %s, %s)',
            (action, detail, ip, utc_now()),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def recent(limit: int = 100):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'SELECT action, detail, ip, ts FROM admin_audit_log ORDER BY ts DESC LIMIT %s',
            (limit,),
        )
        return [{
            'action': r['action'],
            'detail': r['detail'],
            'ip': r['ip'],
            'ts': iso_utc(as_utc(r['ts'])),
        } for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()
