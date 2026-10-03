# -*- coding: utf-8 -*-
"""
Ma'lumotlar bazasi (admin panel → «Baza»): dasturchi bazada qila oladigan ishlar — kodsiz.

  * Istalgan jadvalni ko'rish, ustun bo'yicha qidirish va saralash, CSV yuklab olish.
  * Qatorni tahrirlash va o'chirish (birlamchi kalit bo'yicha).

Xavfsizlik: sessiya tokenlari va admin sozlamalari jadvallari, parol xeshlari ko'rsatilmaydi; jadval tuzilmasini
o'zgartirib bo'lmaydi (faqat qatorlar); birlamchi kalitni o'zgartirib bo'lmaydi; jadval va ustun nomlari faqat
bazaning haqiqiy ro'yxatidan qabul qilinadi (SQL injection yo'q). Har bir o'zgarish audit jurnaliga yoziladi.
"""

import csv
import io
import json
from datetime import date, datetime
from decimal import Decimal

from db import is_postgres

HIDDEN_TABLES = {'tokens', 'admin_settings'}
HIDDEN_COLUMNS = {'password_hash'}
LIST_CELL = 300            # ro'yxatda uzun qiymat shuncha belgigacha qisqartiriladi
PER_PAGE = 50


class DbError(Exception):
    def __init__(self, message, http_status=400):
        super().__init__(message)
        self.message = message
        self.http_status = http_status


def _q(name) -> str:
    return '"' + name.replace('"', '""') + '"'


def tables(cur) -> list:
    if is_postgres():
        cur.execute("SELECT tablename AS name FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    names = [r['name'] for r in cur.fetchall() if r['name'] not in HIDDEN_TABLES]
    out = []
    for n in names:
        cur.execute(f'SELECT COUNT(*) AS n FROM {_q(n)}')
        out.append({'name': n, 'rows': int(cur.fetchone()['n'])})
    return out


def _table(cur, name) -> str:
    if name in HIDDEN_TABLES or name not in {t['name'] for t in _table_names(cur)}:
        raise DbError('Bunday jadval yo\'q.', 404)
    return name


def _table_names(cur):
    if is_postgres():
        cur.execute("SELECT tablename AS name FROM pg_tables WHERE schemaname = 'public'")
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
    return cur.fetchall()


def columns(cur, table) -> list:
    """[{name, type, pk, nullable}] — maxfiy ustunlarsiz."""
    table = _table(cur, table)
    if is_postgres():
        cur.execute('''SELECT column_name AS name, data_type AS type, is_nullable AS nl FROM information_schema.columns
                       WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position''', (table,))
        cols = [{'name': r['name'], 'type': r['type'], 'nullable': r['nl'] == 'YES'} for r in cur.fetchall()]
        cur.execute('''SELECT kcu.column_name AS name FROM information_schema.table_constraints tc
                       JOIN information_schema.key_column_usage kcu
                         ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                       WHERE tc.table_schema = 'public' AND tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY' ''',
                    (table,))
        pk = {r['name'] for r in cur.fetchall()}
    else:
        cur.execute(f'PRAGMA table_info({_q(table)})')
        info = cur.fetchall()
        cols = [{'name': r['name'], 'type': (r['type'] or 'text').lower(), 'nullable': not r['notnull']} for r in info]
        pk = {r['name'] for r in info if r['pk']}
    for c in cols:
        c['pk'] = c['name'] in pk
    return [c for c in cols if c['name'] not in HIDDEN_COLUMNS]


def _show(v, limit=None):
    if isinstance(v, (datetime, date)):
        return v.isoformat(sep=' ') if isinstance(v, datetime) else v.isoformat()
    if isinstance(v, Decimal):
        return int(v) if v == int(v) else float(v)
    if isinstance(v, (bytes, bytearray, memoryview)):
        return '[fayl: ' + str(len(bytes(v))) + ' bayt]'
    if isinstance(v, (dict, list)):
        v = json.dumps(v, ensure_ascii=False)
    if isinstance(v, str) and limit and len(v) > limit:
        return v[:limit] + '…'
    return v


def rows(cur, table, q='', col='', page=1, order='', desc=True, per=PER_PAGE) -> dict:
    cols = columns(cur, table)
    names = [c['name'] for c in cols]
    where, params = '', []
    q = str(q or '').strip()
    if q:
        targets = [col] if col in names else names[:15]
        if not targets:
            raise DbError("Ustun noto'g'ri.")
        cast = 'TEXT'
        op = 'ILIKE' if is_postgres() else 'LIKE'
        where = 'WHERE ' + ' OR '.join(f'CAST({_q(c)} AS {cast}) {op} %s' for c in targets)
        params = ['%' + q + '%'] * len(targets)
    pk = [c['name'] for c in cols if c['pk']]
    order_col = order if order in names else (pk[0] if len(pk) == 1 else names[0])
    page = max(1, int(page or 1))
    cur.execute(f'SELECT COUNT(*) AS n FROM {_q(table)} {where}', params)
    total = int(cur.fetchone()['n'])
    sel = ', '.join(_q(n) for n in names)
    cur.execute(f'SELECT {sel} FROM {_q(table)} {where} ORDER BY {_q(order_col)} {"DESC" if desc else "ASC"} '
                f'LIMIT %s OFFSET %s', params + [per, (page - 1) * per])
    data = [{n: _show(r[n], LIST_CELL) for n in names} for r in cur.fetchall()]
    return {'table': table, 'columns': cols, 'rows': data, 'total': total, 'page': page, 'per': per,
            'order': order_col, 'desc': bool(desc), 'editable': bool(pk)}


def _pk_where(cols, key) -> tuple:
    pk = [c['name'] for c in cols if c['pk']]
    if not pk:
        raise DbError("Bu jadvalda birlamchi kalit yo'q — qatorlarni faqat ko'rish mumkin.")
    if not isinstance(key, dict) or any(k not in key for k in pk):
        raise DbError("Qator kaliti noto'g'ri.")
    return ' AND '.join(f'{_q(k)} = %s' for k in pk), [key[k] for k in pk]


def get_row(cur, table, key) -> dict:
    cols = columns(cur, table)
    where, params = _pk_where(cols, key)
    cur.execute(f'SELECT {", ".join(_q(c["name"]) for c in cols)} FROM {_q(table)} WHERE {where}', params)
    r = cur.fetchone()
    if not r:
        raise DbError('Qator topilmadi.', 404)
    return {c['name']: _show(r[c['name']]) for c in cols}


def _convert(col, value):
    """Formadan kelgan matnni ustun turiga aylantiradi. None — NULL."""
    if value is None:
        if not col['nullable']:
            raise DbError(f"«{col['name']}» bo'sh bo'lishi mumkin emas.")
        return None
    t = (col['type'] or '').lower()
    s = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    try:
        if 'int' in t or t in ('serial', 'bigserial'):
            return int(str(s).strip())
        if any(x in t for x in ('real', 'double', 'numeric', 'decimal', 'float')):
            return float(str(s).strip())
        if 'bool' in t:
            low = str(s).strip().lower()
            if low not in ('true', 'false', '1', '0', 'ha', "yo'q", 't', 'f'):
                raise ValueError
            return low in ('true', '1', 'ha', 't')
        if 'json' in t:
            json.loads(s)
            return s
    except (TypeError, ValueError):
        raise DbError(f"«{col['name']}» uchun qiymat noto'g'ri ({col['type']}).")
    if 'bytea' in t or 'blob' in t:
        raise DbError(f"«{col['name']}» — fayl ustunini bu yerda o'zgartirib bo'lmaydi.")
    return s


def update_row(cur, conn, table, key, changes) -> tuple:
    """(eski, yangi) — faqat o'zgargan ustunlar."""
    cols = columns(cur, table)
    by_name = {c['name']: c for c in cols}
    if not isinstance(changes, dict) or not changes:
        raise DbError("O'zgarish yo'q.")
    old = get_row(cur, table, key)
    sets, params, before, after = [], [], {}, {}
    for name, value in changes.items():
        col = by_name.get(name)
        if not col:
            raise DbError(f"Bunday ustun yo'q: {name}")
        if col['pk']:
            raise DbError("Birlamchi kalitni o'zgartirib bo'lmaydi.")
        v = _convert(col, value)
        sets.append(f'{_q(name)} = %s')
        params.append(v)
        before[name], after[name] = old.get(name), v
    where, wparams = _pk_where(cols, key)
    cur.execute(f'UPDATE {_q(table)} SET {", ".join(sets)} WHERE {where}', params + wparams)
    if cur.rowcount != 1:
        conn.rollback()
        raise DbError('Qator topilmadi.', 404)
    conn.commit()
    return before, after


def delete_row(cur, conn, table, key) -> dict:
    cols = columns(cur, table)
    old = get_row(cur, table, key)
    where, params = _pk_where(cols, key)
    cur.execute(f'DELETE FROM {_q(table)} WHERE {where}', params)
    if cur.rowcount != 1:
        conn.rollback()
        raise DbError('Qator topilmadi.', 404)
    conn.commit()
    return old


def export_csv(cur, table) -> str:
    cols = columns(cur, table)
    names = [c['name'] for c in cols]
    cur.execute(f'SELECT {", ".join(_q(n) for n in names)} FROM {_q(table)}')
    buf = io.StringIO()
    buf.write('﻿')                      # Excel o'zbek/rus harflarini to'g'ri ochsin
    w = csv.writer(buf)
    w.writerow(names)
    for r in cur.fetchall():
        w.writerow([_show(r[n]) for n in names])
    return buf.getvalue()


def short(v, limit=120) -> str:
    """Audit jurnali uchun qisqa ko'rinish."""
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
    return s if len(s) <= limit else s[:limit] + '…'

