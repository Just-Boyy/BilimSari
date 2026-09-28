# -*- coding: utf-8 -*-
"""
Serverdagi jiddiy xatolar: egaga Telegram xabari va xatolar jurnali.

Root logger'ga ERROR darajasidagi handler qo'shiladi — logger.exception(...)
va Flask'ning "Exception on /api/..." xabarlari shu yerga tushadi. Xato
error_log jadvaliga yoziladi (admin panel → Tizim) va egaga (ADMIN_TELEGRAM_IDS)
bot orqali xabar yuboriladi. Bir xil xato (imzo — joy va xato turi) 30
daqiqada ko'pi bilan bir marta xabar qilinadi, soatiga jami 20 tadan oshmaydi.

Ishlov berish alohida fon oqimida: so'rov kutib qolmaydi, baza yoki Telegram
ishlamay qolsa ham asosiy kod buzilmaydi.
"""

import hashlib
import html
import logging
import queue
import threading
import time
import traceback

from db import get_connection

logger = logging.getLogger('bilimsari.alerts')

NOTIFY_EVERY_MS = 30 * 60 * 1000     # bir xil xato haqida qayta xabar — 30 daqiqadan keyin
MAX_PER_HOUR = 20                    # bitta worker'dan soatiga jami xabarlar
KEEP_DAYS = 30                       # jurnal shuncha kun saqlanadi
TRACE_LINES = 14

_queue = queue.Queue(maxsize=200)
_local = threading.local()
_sent = {}                           # imzo → oxirgi xabar vaqti (baza ishlamasa ham takrorlanmasin)
_hour = {'start': 0, 'n': 0}
_started = False


def _now_ms():
    return int(time.time() * 1000)


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS error_log (
            id SERIAL PRIMARY KEY,
            ms BIGINT NOT NULL,
            sig TEXT NOT NULL,
            source TEXT NOT NULL,
            message TEXT NOT NULL,
            trace TEXT,
            path TEXT,
            notified INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    cur.execute('CREATE INDEX IF NOT EXISTS idx_error_log_sig ON error_log (sig, ms)')
    conn.commit()


# ───────────────────────── Handler ─────────────────────────

class AlertHandler(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.ERROR)

    def emit(self, record):
        if getattr(_local, 'busy', False) or record.name.startswith('bilimsari.alerts'):
            return                                   # o'z xatolarimiz — aylanib qolmasin
        try:
            _queue.put_nowait(_describe(record))
        except Exception:  # noqa: BLE001  (navbat to'la — xato jurnalga tushmaydi, xolos)
            pass


def _request_path():
    try:
        from flask import has_request_context, request
        if has_request_context():
            return f'{request.method} {request.path}'
    except Exception:  # noqa: BLE001
        pass
    return None


def _describe(record) -> dict:
    message = record.getMessage()
    trace, where, kind = None, '', ''
    if record.exc_info and record.exc_info[1] is not None:
        etype, evalue, tb = record.exc_info
        kind = etype.__name__
        lines = traceback.format_exception(etype, evalue, tb)
        trace = ''.join(lines)
        frames = traceback.extract_tb(tb)
        if frames:
            last = frames[-1]
            where = f'{last.filename.replace(chr(92), "/").rsplit("/", 1)[-1]}:{last.lineno}'
        message = f'{message}\n{kind}: {evalue}'.strip()
    sig_src = f'{record.name}|{record.msg}|{kind}|{where}'
    return {
        'ms': int(record.created * 1000),
        'sig': hashlib.sha1(sig_src.encode('utf-8', 'replace')).hexdigest()[:16],
        'source': (f'{record.name} {where}').strip()[:120],
        'message': message[:2000],
        'trace': trace[-6000:] if trace else None,
        'path': _request_path(),
    }


# ───────────────────────── Fon ishchisi ─────────────────────────

def _allowed_by_rate(sig, now) -> bool:
    if now - _sent.get(sig, 0) < NOTIFY_EVERY_MS:
        return False
    if now - _hour['start'] > 3600 * 1000:
        _hour['start'], _hour['n'] = now, 0
    return _hour['n'] < MAX_PER_HOUR


def _alert_text(item) -> str:
    tail = ''
    if item['trace']:
        tail = '\n'.join(item['trace'].strip().splitlines()[-TRACE_LINES:])
    text = (f"⚠️ <b>Serverda xato</b>\n"
            f"<b>Joy:</b> {html.escape(item['source'])}\n")
    if item['path']:
        text += f"<b>So'rov:</b> {html.escape(item['path'])}\n"
    text += f"\n{html.escape(item['message'][:600])}"
    if tail:
        text += f"\n\n<pre>{html.escape(tail[-2200:])}</pre>"
    return text[:4000]


def _store(item) -> bool:
    """Jurnalga yozadi; shu xato haqida 30 daqiqada boshqa worker xabar
    qilmagan bo'lsa — True (xabar yuborish kerak)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT 1 FROM error_log WHERE sig = %s AND notified = 1 AND ms >= %s LIMIT 1',
                    (item['sig'], item['ms'] - NOTIFY_EVERY_MS))
        fresh = cur.fetchone() is None
        cur.execute('INSERT INTO error_log (ms, sig, source, message, trace, path, notified) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (item['ms'], item['sig'], item['source'], item['message'], item['trace'], item['path'],
                     int(fresh)))
        conn.commit()
        return fresh
    finally:
        cur.close()
        conn.close()


def _handle(item):
    import admin_auth
    import tgbot
    try:
        fresh = _store(item)
    except Exception:  # noqa: BLE001  (baza ishlamayapti — bu ham xabar qilinishi kerak)
        fresh = True
    now = _now_ms()
    if not fresh or not _allowed_by_rate(item['sig'], now):
        return
    _sent[item['sig']] = now
    _hour['n'] += 1
    for owner in sorted(admin_auth.ADMIN_TELEGRAM_IDS):
        tgbot.tg_api('sendMessage', {'chat_id': owner, 'text': _alert_text(item), 'parse_mode': 'HTML',
                                     'disable_web_page_preview': True})


def _worker():
    _local.busy = True               # shu oqimdagi log xabarlari qayta navbatga tushmaydi
    while True:
        item = _queue.get()
        try:
            _handle(item)
        except Exception:  # noqa: BLE001
            pass
        finally:
            _queue.task_done()


def install():
    """Root logger'ga handler qo'shadi va fon ishchisini ishga tushiradi (bir marta)."""
    global _started
    if _started:
        return
    _started = True
    logging.getLogger().addHandler(AlertHandler())
    threading.Thread(target=_worker, name='bilimsari-alerts', daemon=True).start()


def flush(timeout=5.0):
    """Testlar uchun: navbatdagi barcha xatolar ishlanguncha kutadi."""
    end = time.time() + timeout
    while _queue.unfinished_tasks and time.time() < end:
        time.sleep(0.02)


# ───────────────────────── Admin panel ─────────────────────────

def recent(cur, limit=30) -> list:
    cur.execute('SELECT id, ms, source, message, trace, path FROM error_log ORDER BY ms DESC, id DESC LIMIT %s',
                (limit,))
    return [dict(r, ms=int(r['ms'])) for r in cur.fetchall()]


def counts(cur, now_ms=None) -> dict:
    now_ms = now_ms or _now_ms()
    cur.execute('SELECT COUNT(*) AS n FROM error_log WHERE ms >= %s', (now_ms - 24 * 3600 * 1000,))
    day = int(cur.fetchone()['n'])
    cur.execute('SELECT COUNT(*) AS n FROM error_log WHERE ms >= %s', (now_ms - 7 * 24 * 3600 * 1000,))
    return {'day': day, 'week': int(cur.fetchone()['n'])}


def cleanup(cur, conn, now_ms=None):
    now_ms = now_ms or _now_ms()
    cur.execute('DELETE FROM error_log WHERE ms < %s', (now_ms - KEEP_DAYS * 24 * 3600 * 1000,))
    conn.commit()


def clear(cur, conn):
    cur.execute('DELETE FROM error_log')
    conn.commit()


def send_test() -> int:
    """Admin panel: "Sinov xabari" — egalarga Telegram orqali yuboradi."""
    import admin_auth
    import tgbot
    sent = 0
    for owner in sorted(admin_auth.ADMIN_TELEGRAM_IDS):
        res = tgbot.tg_api('sendMessage', {'chat_id': owner, 'parse_mode': 'HTML', 'text': (
            "✅ <b>Sinov xabari</b>\nServerda jiddiy xato chiqsa, shu yerga xuddi shunday xabar keladi.")})
        if res and res.get('ok'):
            sent += 1
    return sent
