# -*- coding: utf-8 -*-
"""
Telegram eslatmalari va ularni vaqtida yuboruvchi rejalashtiruvchi.

  * Kun savoli (09:00, Toshkent) — "Bugungi savol tayyor!".
  * Kunlik eslatma (19:00, Toshkent) — so'nggi 14 kunda faol bo'lgan, lekin
    bugun hali o'qimagan o'quvchilarga; streak bo'lsa, uni eslatadi.
  * "Keyingi mavzu ochildi" — 24 soatlik kutish tugagan zahoti.
  * O'yin taklifi — oldin birga o'ynagan odam yangi room ochsa.
  * Haftalik turnir — hafta tugagach top-3 ga medal va tabrik xabari.
  * To'lovlar — muddati o'tgan buyurtmalarni yopish, 30 daqiqadan beri
    tekshirilmagan chek haqida adminga eslatma, 21:00 da kunlik hisobot.

Alohida fon xizmati (cron) yo'q: har bir gunicorn worker'da bitta fon oqimi
daqiqada bir marta tick() ni chaqiradi. Vazifa job_runs jadvalidagi noyob
(job, slot) kaliti orqali "egallanadi" — worker'lar nechta bo'lsa ham har bir
vazifa bir marta bajariladi. Har bir xabar notify_log'ga yoziladi va qayta
yuborilmaydi. O'quvchi eslatmalarni profilda o'chira oladi; botni bloklagan
(403) foydalanuvchiga eslatmalar avtomatik o'chiriladi.
"""

import html
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone

import daily
import payments
import study
from db import TASHKENT_TZ, add_column_if_missing, as_utc, get_connection
from games import clock
from games import stats as game_stats
from tgbot import BOT_TOKEN, send

logger = logging.getLogger('bilimsari.notify')

QUESTION_HOUR = 9           # "Bugungi savol tayyor!" vaqti (Toshkent)
QUESTION_LAST_HOUR = 12
DAILY_HOUR = 19             # kunlik eslatma vaqti (Toshkent)
DAILY_LAST_HOUR = 22        # server kech ishga tushsa — o'sha kuni kechasi yubormaydi
ACTIVE_DAYS = 14            # shundan uzoq kirmaganlarni bezovta qilmaymiz
COOLDOWN_WINDOW_MIN = 30    # kutish shu oraliqda tugagan bo'lsa — xabar
INVITE_WINDOW_MS = 2 * 3600 * 1000   # bitta odamga 2 soatda ko'pi bilan 1 ta taklif
MAX_INVITES = 10
TICK_SECONDS = 60
PAY_SUMMARY_HOUR = 21        # adminga kunlik to'lov hisoboti (Toshkent)
FOOTER = "\n\n<i>Eslatmalarni Profil → Sozlamalar bo'limida o'chirishingiz mumkin.</i>"


def ensure_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notify_log (
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            ref TEXT NOT NULL,
            sent_ms BIGINT NOT NULL,
            PRIMARY KEY (user_id, kind, ref)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS job_runs (
            job TEXT NOT NULL,
            slot TEXT NOT NULL,
            ran_ms BIGINT NOT NULL,
            PRIMARY KEY (job, slot)
        )
    ''')
    conn.commit()
    add_column_if_missing(cur, conn, 'users', 'notify', 'INTEGER NOT NULL DEFAULT 1')


def _utc(ms):
    """Epoch millisekund → naive UTC datetime (bazadagi TIMESTAMP bilan solishtirish uchun)."""
    return datetime.fromtimestamp(int(ms) / 1000, timezone.utc).replace(tzinfo=None)


def _first_name(name):
    parts = str(name or '').split()
    return html.escape(parts[0] if parts else 'do‘st')


def _claim(cur, conn, job, slot) -> bool:
    """Vazifani shu slot uchun egallaydi — muvaffaqiyatli bo'lsa, faqat shu worker bajaradi."""
    cur.execute('INSERT INTO job_runs (job, slot, ran_ms) VALUES (%s, %s, %s) ON CONFLICT (job, slot) DO NOTHING',
                (job, slot, clock.now_ms()))
    claimed = cur.rowcount == 1
    conn.commit()
    return claimed


def _deliver(cur, conn, user, kind, ref, text, button, path) -> bool:
    """Xabarni bir marta yuboradi (notify_log). Bot bloklangan bo'lsa (403) —
    shu foydalanuvchiga eslatmalar o'chiriladi."""
    cur.execute('INSERT INTO notify_log (user_id, kind, ref, sent_ms) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING',
                (user['id'], kind, ref, clock.now_ms()))
    fresh = cur.rowcount == 1
    conn.commit()
    if not fresh:
        return False
    ok, error_code = send(user['telegram_id'], text + FOOTER, button, path)
    if not ok and error_code == 403:
        cur.execute('UPDATE users SET notify = 0 WHERE id = %s', (user['id'],))
        conn.commit()
    time.sleep(0.05)   # Telegram cheklovi: sekundiga ~30 xabar
    return ok


def _recipients(cur, ids=None):
    sql = 'SELECT id, name, telegram_id, created_at FROM users WHERE telegram_id IS NOT NULL AND notify = 1'
    params = []
    if ids is not None:
        if not ids:
            return []
        sql += f" AND id IN ({', '.join(['%s'] * len(ids))})"
        params = list(ids)
    cur.execute(sql, params)
    return cur.fetchall()


# ───────────────────────── Vazifalar ─────────────────────────

def daily_reminders(cur, conn, now_ms) -> int:
    today = clock.tashkent_date(now_ms)
    day_start = _utc(clock.period_start_ms('day', now_ms))
    now = _utc(now_ms)
    active_since = now - timedelta(days=ACTIVE_DAYS)
    cooldown = timedelta(hours=study.COOLDOWN_HOURS)

    cur.execute('SELECT user_id, MAX(started_at) AS s, MAX(completed_at) AS c FROM user_progress GROUP BY user_id')
    progress = {r['user_id']: (as_utc(r['s']), as_utc(r['c'])) for r in cur.fetchall()}
    cur.execute('SELECT user_id, MAX(created_ms) AS g FROM game_results WHERE user_id > 0 GROUP BY user_id')
    games = {r['user_id']: _utc(r['g']) for r in cur.fetchall()}

    sent = 0
    for u in _recipients(cur):
        started, completed = progress.get(u['id'], (None, None))
        played = games.get(u['id'])
        studied = [m for m in (started, completed, played) if m]
        moments = studied + [m for m in (as_utc(u['created_at']),) if m]
        if not moments or max(moments) < active_since:
            continue                                  # uzoq vaqt kirmagan
        if studied and max(studied) >= day_start:
            continue                                  # bugun o'qigan yoki o'ynagan
        if completed and now - completed < cooldown:
            continue                                  # kutishda — "ochildi" xabari keladi
        streak = study.compute_streak(cur, u['id'])
        text = f'{_first_name(u["name"])}, bugun hali dars qilmadingiz.\n'
        text += (f'Streak: <b>{streak} kun</b> — uzilib qolmasin!' if streak
                 else 'Bitta mavzu atigi 10–15 daqiqa oladi — boshlaymizmi?')
        if _deliver(cur, conn, u, 'daily', today.isoformat(), text, 'Darsni boshlash', 'dashboard.html'):
            sent += 1
    return sent


def question_ready(cur, conn, now_ms) -> int:
    """Ertalab "Bugungi savol tayyor!" — so'nggi 14 kunda faol bo'lgan, bugungi
    savolni hali ochmagan o'quvchilarga."""
    day = daily.today(now_ms)
    since_ms = now_ms - ACTIVE_DAYS * 24 * 3600 * 1000
    since = _utc(since_ms)
    cur.execute('SELECT DISTINCT user_id FROM user_progress WHERE started_at >= %s OR completed_at >= %s',
                (since, since))
    active = {r['user_id'] for r in cur.fetchall()}
    cur.execute('SELECT DISTINCT user_id FROM game_results WHERE user_id > 0 AND created_ms >= %s', (since_ms,))
    active |= {r['user_id'] for r in cur.fetchall()}
    cur.execute('SELECT DISTINCT user_id FROM daily_answers WHERE opened_ms >= %s', (since_ms,))
    active |= {r['user_id'] for r in cur.fetchall()}
    cur.execute('SELECT user_id FROM daily_answers WHERE day = %s', (day,))
    opened = {r['user_id'] for r in cur.fetchall()}

    subject = daily.subject_of_day(cur, conn, now_ms)
    sent = 0
    for u in _recipients(cur):
        created = as_utc(u['created_at'])
        if u['id'] in opened or not (u['id'] in active or (created and created >= since)):
            continue
        streak = daily.streak(cur, u['id'], now_ms)
        text = (f'{_first_name(u["name"])}, <b>bugungi savol tayyor!</b>\n'
                f'Bugun — {html.escape(subject)}. To\'g\'ri va tez javob berib, kunlik reytingga chiqing.')
        if streak:
            text += f'\nKun savoli streak: <b>{streak} kun</b>.'
        if _deliver(cur, conn, u, 'question', day, text, 'Savolni ochish', 'daily.html'):
            sent += 1
    return sent


def cooldown_ready(cur, conn, now_ms) -> int:
    """24 soatlik kutish endigina tugagan o'quvchilarga "keyingi mavzu ochildi"."""
    now = _utc(now_ms)
    hours = timedelta(hours=study.COOLDOWN_HOURS)
    lo, hi = now - hours - timedelta(minutes=COOLDOWN_WINDOW_MIN), now - hours
    cur.execute(
        'SELECT user_id, MAX(completed_at) AS last FROM user_progress WHERE status = %s AND completed_at IS NOT NULL '
        'GROUP BY user_id',
        (study.STATUS_COMPLETED,),
    )
    due = {r['user_id']: as_utc(r['last']) for r in cur.fetchall() if lo <= as_utc(r['last']) <= hi}
    sent = 0
    for u in _recipients(cur, list(due)):
        text = f'{_first_name(u["name"])}, kutish tugadi — <b>keyingi mavzu ochildi!</b>\nDavom etamizmi?'
        if _deliver(cur, conn, u, 'cooldown', due[u['id']].isoformat(), text, 'Davom etish', 'dashboard.html'):
            sent += 1
    return sent


def weekly_awards(cur, conn, now_ms) -> list:
    """O'tgan hafta top-3'iga medal va tabrik xabari."""
    week_start = clock.period_start_ms('week', now_ms) - game_stats.WEEK_MS
    winners = game_stats.award_week(cur, conn, week_start)
    by_id = {w['user_id']: w for w in winners}
    for u in _recipients(cur, list(by_id)):
        w = by_id[u['id']]
        text = (f'Tabriklaymiz, {_first_name(u["name"])}! Haftalik o\'yin turnirida '
                f'<b>{w["place"]}-o\'rin</b> ({w["xp"]} ball). Medal profilingizga qo\'shildi.')
        _deliver(cur, conn, u, 'award', str(week_start), text, 'Profilni ochish', 'profile.html')
    return winners


def invite_co_players(host_id, host_name, code, game_name, subject_name):
    """Yangi room ochilganda — so'nggi 30 kunda shu host bilan birga o'ynagan,
    hozir ilovada bo'lmagan o'yinchilarga taklif. Fonda yuboriladi (so'rov
    kutib qolmaydi)."""
    if not BOT_TOKEN:
        return

    def run():
        conn = get_connection()
        cur = conn.cursor()
        try:
            now = clock.now_ms()
            cur.execute(
                '''SELECT DISTINCT r2.user_id FROM game_results r1
                   JOIN game_results r2 ON r2.session_id = r1.session_id
                   WHERE r1.user_id = %s AND r2.user_id != %s AND r2.user_id > 0 AND r1.created_ms >= %s''',
                (host_id, host_id, now - 30 * 24 * 3600 * 1000),
            )
            ids = [r['user_id'] for r in cur.fetchall()][:50]
            cur.execute('SELECT user_id FROM game_presence WHERE seen_ms >= %s', (now - 2 * 60 * 1000,))
            online = {r['user_id'] for r in cur.fetchall()}
            sent = 0
            for u in _recipients(cur, [i for i in ids if i not in online]):
                if sent >= MAX_INVITES:
                    break
                text = (f'{_first_name(host_name)} yangi o\'yin ochdi: <b>{html.escape(game_name)} • '
                        f'{html.escape(subject_name)}</b>.\nRoom kodi: <b>{code}</b>. Qo\'shilasizmi?')
                if _deliver(cur, conn, u, 'invite', str(now // INVITE_WINDOW_MS), text,
                            "Qo'shilish", f'games.html?kod={code}'):
                    sent += 1
        except Exception:  # noqa: BLE001
            logger.exception("O'yin taklifi yuborilmadi")
        finally:
            cur.close()
            conn.close()

    threading.Thread(target=run, name='bilimsari-invite', daemon=True).start()


# ───────────────────────── Rejalashtiruvchi ─────────────────────────

def tick(now_ms=None):
    now_ms = now_ms or clock.now_ms()
    conn = get_connection()
    cur = conn.cursor()
    try:
        if _claim(cur, conn, 'cooldown', str(now_ms // (5 * 60 * 1000))):
            cooldown_ready(cur, conn, now_ms)
            payments.housekeeping(cur, conn, now_ms)
        local = datetime.fromtimestamp(now_ms / 1000, TASHKENT_TZ)
        if (QUESTION_HOUR <= local.hour < QUESTION_LAST_HOUR
                and _claim(cur, conn, 'question', local.date().isoformat())):
            logger.info('Kun savoli xabari: %d ta', question_ready(cur, conn, now_ms))
        if DAILY_HOUR <= local.hour < DAILY_LAST_HOUR and _claim(cur, conn, 'daily', local.date().isoformat()):
            logger.info('Kunlik eslatma: %d ta', daily_reminders(cur, conn, now_ms))
        if (PAY_SUMMARY_HOUR <= local.hour < DAILY_LAST_HOUR + 1
                and _claim(cur, conn, 'pay_summary', local.date().isoformat())):
            summary = payments.daily_summary(cur, now_ms)
            for admin in payments.admin_ids() if summary else []:
                send(admin, summary, 'Admin panel', 'admin.html')
        week_start = clock.period_start_ms('week', now_ms) - game_stats.WEEK_MS
        if _claim(cur, conn, 'weekly', str(week_start)):
            logger.info('Haftalik turnir g\'oliblari: %s', weekly_awards(cur, conn, now_ms))
    except Exception:  # noqa: BLE001
        conn.rollback()
        logger.exception('Rejalashtiruvchi xatosi')
    finally:
        cur.close()
        conn.close()


_started = False


def start():
    """Fon oqimini ishga tushiradi (har bir worker'da bir marta). Lokal
    testlarda BOT_TOKEN bo'lmaydi yoki SCHEDULER_ENABLED=0 — ishga tushmaydi."""
    global _started
    if _started or not BOT_TOKEN or os.environ.get('SCHEDULER_ENABLED', '1') != '1':
        return
    _started = True

    def loop():
        time.sleep(15)
        while True:
            tick()
            time.sleep(TICK_SECONDS)

    threading.Thread(target=loop, name='bilimsari-scheduler', daemon=True).start()
