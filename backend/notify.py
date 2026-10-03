# -*- coding: utf-8 -*-
"""
Telegram eslatmalari va ularni vaqtida yuboruvchi rejalashtiruvchi.

  * Kun savoli (09:00, Toshkent) — "Bugungi savol tayyor!".
  * Kunlik eslatma (o'quvchi Sozlamalarda tanlagan soatda, standart 19:00,
    Toshkent) — so'nggi 14 kunda faol bo'lgan, lekin bugun hali o'qimagan
    o'quvchilarga; streak bo'lsa, uni eslatadi.
  * "Keyingi mavzu ochildi" — biror fanda 24 soatlik kutish tugagan zahoti
    (kutish har fanga alohida, xabar ham fan nomi bilan).
  * O'yin taklifi — oldin birga o'ynagan odam yangi room ochsa.
  * Haftalik turnir — hafta tugagach top-3 ga medal va tabrik xabari.
  * To'lovlar — muddati o'tgan buyurtmalarni yopish, 30 daqiqadan beri
    tekshirilmagan chek haqida adminga eslatma, 21:00 da kunlik hisobot.
  * Zaxira nusxa — har kuni 03:00 da butun baza egaga Telegram'da fayl
    bo'lib yuboriladi (backup.py).

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

import alerts
import backup
import botchat
import broadcast
import curriculum as cur_mod
import daily
import dostlar
import marafon
import payments
import personal
import premium
import study
from db import TASHKENT_TZ, add_column_if_missing, as_utc, get_connection
from games import clock
from games import stats as game_stats
from tgbot import BOT_TOKEN, L, fan_ru, kun_ru, pick, send

logger = logging.getLogger('bilimsari.notify')

QUESTION_HOUR = 9           # "Bugungi savol tayyor!" vaqti (Toshkent)
QUESTION_LAST_HOUR = 12
DAILY_HOUR = 19             # kunlik eslatmaning standart vaqti (Toshkent)
REMIND_HOURS = range(7, 23)  # o'quvchi tanlashi mumkin bo'lgan soatlar: 07:00 … 22:00
REMIND_GRACE_H = 2          # server shu soatda ishlamagan bo'lsa — keyingi 2 soat ichida yuboriladi
ACTIVE_DAYS = 14            # shundan uzoq kirmaganlarni bezovta qilmaymiz
COOLDOWN_WINDOW_MIN = 30    # kutish shu oraliqda tugagan bo'lsa — xabar
INVITE_WINDOW_MS = 2 * 3600 * 1000   # bitta odamga 2 soatda ko'pi bilan 1 ta taklif
MAX_INVITES = 10
TICK_SECONDS = 60
PAY_SUMMARY_HOUR = 21        # adminga kunlik to'lov hisoboti (Toshkent)
JOB_KEEP_MS = 30 * 24 * 3600 * 1000   # job_runs qatorlari shuncha saqlanadi
FOOTER = L("\n\n<i>Eslatmalarni Profil → Sozlamalar bo'limida o'chirishingiz mumkin.</i>",
           "\n\n<i>Напоминания можно отключить в разделе Профиль → Настройки.</i>")


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
    # Kunlik eslatma soati (Toshkent), NULL — standart DAILY_HOUR
    add_column_if_missing(cur, conn, 'users', 'remind_hour', 'INTEGER')


def remind_hour(value):
    """Saqlangan soat yoki standart."""
    try:
        h = int(value)
    except (TypeError, ValueError):
        return DAILY_HOUR
    return h if h in REMIND_HOURS else DAILY_HOUR


def _utc(ms):
    """Epoch millisekund → naive UTC datetime (bazadagi TIMESTAMP bilan solishtirish uchun)."""
    return datetime.fromtimestamp(int(ms) / 1000, timezone.utc).replace(tzinfo=None)


_kun_ru = kun_ru
_fan_ru = fan_ru


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
    lang = 'ru' if user.get('lang') == 'ru' else 'uz'
    ok, error_code = send(user['telegram_id'], pick(text, lang) + pick(FOOTER, lang), pick(button, lang), path, lang=lang)
    if not ok and error_code == 403:
        cur.execute('UPDATE users SET notify = 0 WHERE id = %s', (user['id'],))
        conn.commit()
    time.sleep(0.05)   # Telegram cheklovi: sekundiga ~30 xabar
    return ok


def _recipients(cur, ids=None):
    sql = ('SELECT id, name, telegram_id, created_at, remind_hour, lang FROM users '
           'WHERE telegram_id IS NOT NULL AND notify = 1')
    params = []
    if ids is not None:
        if not ids:
            return []
        sql += f" AND id IN ({', '.join(['%s'] * len(ids))})"
        params = list(ids)
    cur.execute(sql, params)
    return cur.fetchall()


# ───────────────────────── Vazifalar ─────────────────────────

def daily_reminders(cur, conn, now_ms, hour=None) -> int:
    """hour berilsa — faqat eslatma soati shu soatga to'g'ri kelganlarga
    (REMIND_GRACE_H soatgacha kechikkanlar ham). Kuniga bir martadan ortiq emas."""
    today = clock.tashkent_date(now_ms)
    day_start = _utc(clock.period_start_ms('day', now_ms))
    now = _utc(now_ms)
    active_since = now - timedelta(days=ACTIVE_DAYS)
    cooldown = timedelta(hours=study.COOLDOWN_HOURS)

    cur.execute('SELECT user_id, MAX(started_at) AS s, MAX(completed_at) AS c FROM user_progress GROUP BY user_id')
    progress = {r['user_id']: (as_utc(r['s']), as_utc(r['c'])) for r in cur.fetchall()}
    cur.execute('SELECT user_id, MAX(created_ms) AS g FROM game_results WHERE user_id > 0 GROUP BY user_id')
    games = {r['user_id']: _utc(r['g']) for r in cur.fetchall()}
    # Kutish har fanga alohida: qaysi fanlar hozir kutishda va o'quvchida qaysi fanlar ochiq
    waiting = {}
    for (uid, subject), last in _subject_completions(cur).items():
        if now - last < cooldown:
            waiting.setdefault(uid, set()).add(subject)
    opened = {}
    cur.execute('SELECT id, chosen_subject_key FROM users WHERE chosen_subject_key IS NOT NULL')
    for r in cur.fetchall():
        opened.setdefault(r['id'], set()).add(r['chosen_subject_key'])
    cur.execute('SELECT user_id, subject_key FROM subject_purchases')
    for r in cur.fetchall():
        opened.setdefault(r['user_id'], set()).add(r['subject_key'])

    sent = 0
    for u in _recipients(cur):
        own = remind_hour(u.get('remind_hour'))
        if hour is not None and not hour - REMIND_GRACE_H <= own <= hour:
            continue                                  # boshqa soatni tanlagan
        started, completed = progress.get(u['id'], (None, None))
        played = games.get(u['id'])
        studied = [m for m in (started, completed, played) if m]
        moments = studied + [m for m in (as_utc(u['created_at']),) if m]
        if not moments or max(moments) < active_since:
            continue                                  # uzoq vaqt kirmagan
        if studied and max(studied) >= day_start:
            continue                                  # bugun o'qigan yoki o'ynagan
        mine = opened.get(u['id'], set())
        if mine and mine <= waiting.get(u['id'], set()):
            continue                                  # barcha fanlari kutishda — "ochildi" xabari keladi
        streak = study.compute_streak(cur, u['id'])
        ism = _first_name(u["name"])
        if own < 12:                                  # ertalabki eslatma boshqacha ohangda
            uz, ru = f'Xayrli tong, {ism}! Bugungi darsni boshlaymizmi?\n', f'Доброе утро, {ism}! Начнём сегодняшний урок?\n'
        else:
            uz, ru = f'{ism}, bugun hali dars qilmadingiz.\n', f'{ism}, сегодня вы ещё не занимались.\n'
        if streak:
            uz += f'Streak: <b>{streak} kun</b> — uzilib qolmasin!'
            ru += f'Серия: <b>{streak} {_kun_ru(streak)}</b> — не прерывайте её!'
        else:
            uz += 'Bitta mavzu atigi 10–15 daqiqa oladi — boshlaymizmi?'
            ru += 'Одна тема занимает всего 10–15 минут — начнём?'
        if _deliver(cur, conn, u, 'daily', today.isoformat(), L(uz, ru), L('Darsni boshlash', 'Начать урок'),
                    'dashboard.html'):
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
        ism = _first_name(u["name"])
        uz = (f'{ism}, <b>bugungi savol tayyor!</b>\n'
              f'Bugun — {html.escape(subject)}. To\'g\'ri va tez javob berib, kunlik reytingga chiqing.')
        ru = (f'{ism}, <b>вопрос дня готов!</b>\n'
              f'Сегодня — {html.escape(_fan_ru(subject))}. Отвечайте правильно и быстро — и попадите в рейтинг дня.')
        if streak:
            uz += f'\nKun savoli streak: <b>{streak} kun</b>.'
            ru += f'\nСерия вопроса дня: <b>{streak} {_kun_ru(streak)}</b>.'
        if _deliver(cur, conn, u, 'question', day, L(uz, ru), L('Savolni ochish', 'Открыть вопрос'), 'daily.html'):
            sent += 1
    return sent


def _subject_completions(cur) -> dict:
    """{(o'quvchi, fan): oxirgi tugallangan mavzu vaqti} — kutish har fanga alohida."""
    cur.execute(
        '''SELECT p.user_id, t.subject_key, MAX(p.completed_at) AS last FROM user_progress p
           JOIN topics t ON t.id = p.topic_id
           WHERE p.status = %s AND p.completed_at IS NOT NULL
           GROUP BY p.user_id, t.subject_key''',
        (study.STATUS_COMPLETED,),
    )
    return {(r['user_id'], r['subject_key']): as_utc(r['last']) for r in cur.fetchall() if r['last']}


def cooldown_ready(cur, conn, now_ms) -> int:
    """Biror fanda 24 soatlik kutish endigina tugagan o'quvchilarga — shu fan
    bo'yicha "keyingi mavzu ochildi" (har fan uchun alohida xabar)."""
    now = _utc(now_ms)
    hours = timedelta(hours=study.COOLDOWN_HOURS)
    lo, hi = now - hours - timedelta(minutes=COOLDOWN_WINDOW_MIN), now - hours
    due = {}
    for (uid, subject), last in _subject_completions(cur).items():
        if lo <= last <= hi:
            due.setdefault(uid, []).append((subject, last))
    sent = 0
    for u in _recipients(cur, list(due)):
        for subject, last in due[u['id']]:
            name = cur_mod.subject_meta(subject)['name']
            ism = _first_name(u["name"])
            text = L(f'{ism}, kutish tugadi — <b>{html.escape(name)}</b> fanida '
                     f'<b>keyingi mavzu ochildi!</b>\nDavom etamizmi?',
                     f'{ism}, ожидание закончилось — по предмету <b>{html.escape(_fan_ru(name))}</b> '
                     f'<b>открылась следующая тема!</b>\nПродолжим?')
            if _deliver(cur, conn, u, 'cooldown', f'{subject}:{last.isoformat()}', text, L('Davom etish', 'Продолжить'),
                        f'topics.html?fan={subject}'):
                sent += 1
    return sent


PREMIUM_SOON_DAYS = 3
PREMIUM_HOURS = range(9, 22)        # eslatmalar kunduzi yuboriladi


def premium_reminders(cur, conn, now_ms) -> int:
    """Premium tugashiga 3 kun qolganda va tugagan kuni — bir martadan (muddat bo'yicha)."""
    day = premium.DAY_MS
    cur.execute('''SELECT id, name, telegram_id, premium_until, lang FROM users
                   WHERE telegram_id IS NOT NULL AND notify = 1 AND premium_until IS NOT NULL
                     AND premium_until > %s AND premium_until <= %s''',
                (now_ms - 2 * day, now_ms + PREMIUM_SOON_DAYS * day))
    sent = 0
    for u in cur.fetchall():
        until = int(u['premium_until'])
        till = datetime.fromtimestamp(until / 1000, TASHKENT_TZ).strftime('%d.%m.%Y')
        ism = _first_name(u["name"])
        if until > now_ms:
            text = L(f'{ism}, <b>Bilim Premium</b> {till} kuni tugaydi. '
                     'Muddati tugagach, Premium sahifasidan yana 1 oyga olishingiz mumkin.',
                     f'{ism}, <b>Bilim Premium</b> заканчивается {till}. '
                     'После окончания срока его можно снова оформить на 1 месяц на странице Premium.')
            ok = _deliver(cur, conn, u, 'premium_soon', str(until), text, 'Premium', 'premium.html')
        else:
            text = L(f'{ism}, <b>Bilim Premium</b> muddati tugadi. AI tushuntirish va yangi '
                     "shaxsiy darslar yopildi — yaratgan darslaringiz o'zingizda qoladi. Qayta olasizmi?",
                     f'{ism}, срок <b>Bilim Premium</b> закончился. Объяснения ИИ и новые личные уроки '
                     'закрыты — созданные уроки остаются у вас. Оформите снова?')
            ok = _deliver(cur, conn, u, 'premium_end', str(until), text, L('Premium olish', 'Оформить Premium'),
                          'premium.html')
        sent += int(bool(ok))
    return sent


def weekly_awards(cur, conn, now_ms) -> list:
    """O'tgan hafta top-3'iga medal va tabrik xabari."""
    week_start = clock.period_start_ms('week', now_ms) - game_stats.WEEK_MS
    winners = game_stats.award_week(cur, conn, week_start)
    by_id = {w['user_id']: w for w in winners}
    for u in _recipients(cur, list(by_id)):
        w = by_id[u['id']]
        ism = _first_name(u["name"])
        text = L(f'Tabriklaymiz, {ism}! Haftalik o\'yin turnirida '
                 f'<b>{w["place"]}-o\'rin</b> ({w["xp"]} ball). Medal profilingizga qo\'shildi.',
                 f'Поздравляем, {ism}! В еженедельном игровом турнире у вас '
                 f'<b>{w["place"]}-е место</b> ({w["xp"]} очков). Медаль добавлена в профиль.')
        _deliver(cur, conn, u, 'award', str(week_start), text, L('Profilni ochish', 'Открыть профиль'), 'profile.html')
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
                host = _first_name(host_name)
                text = L(f'{host} yangi o\'yin ochdi: <b>{html.escape(game_name)} • '
                         f'{html.escape(subject_name)}</b>.\nRoom kodi: <b>{code}</b>. Qo\'shilasizmi?',
                         f'{host} открыл(а) новую игру: <b>{html.escape(game_name)} • '
                         f'{html.escape(_fan_ru(subject_name))}</b>.\nКод комнаты: <b>{code}</b>. Присоединитесь?')
                if _deliver(cur, conn, u, 'invite', str(now // INVITE_WINDOW_MS), text,
                            L("Qo'shilish", 'Присоединиться'), f'games.html?kod={code}'):
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
            broadcast.resume_stale(cur, conn, now_ms)      # worker o'lib qolgan tarqatishni davom ettirish
            botchat.cleanup_updates(cur, conn, now_ms)
            alerts.cleanup(cur, conn, now_ms)
            personal.housekeeping(cur, conn, now_ms)      # yarim qolgan shaxsiy dars yaratishlari
            dostlar.housekeeping(cur, conn, now_ms)       # eski chaqiruvlar va javob berilgan so'rovlar
            cur.execute('DELETE FROM job_runs WHERE ran_ms < %s', (now_ms - JOB_KEEP_MS,))
            conn.commit()
        local = datetime.fromtimestamp(now_ms / 1000, TASHKENT_TZ)
        if (QUESTION_HOUR <= local.hour < QUESTION_LAST_HOUR
                and _claim(cur, conn, 'question', local.date().isoformat())):
            logger.info('Kun savoli xabari: %d ta', question_ready(cur, conn, now_ms))
        # Kunlik eslatma har soatda — o'sha soatni tanlagan o'quvchilarga
        if (REMIND_HOURS.start <= local.hour
                and _claim(cur, conn, 'daily', f'{local.date().isoformat()}:{local.hour:02d}')):
            logger.info('Kunlik eslatma (%02d:00): %d ta', local.hour,
                        daily_reminders(cur, conn, now_ms, hour=local.hour))
        if PAY_SUMMARY_HOUR <= local.hour and _claim(cur, conn, 'pay_summary', local.date().isoformat()):
            summary = payments.daily_summary(cur, now_ms)
            for admin in payments.admin_ids() if summary else []:
                send(admin, summary, 'Admin panel', 'admin.html')
        if local.hour in PREMIUM_HOURS and _claim(cur, conn, 'premium', f'{local.date().isoformat()}:{local.hour:02d}'):
            premium_reminders(cur, conn, now_ms)
        # Kunlik zaxira nusxa (03:00 dan keyin, kuniga bir marta) — egaga Telegram'da fayl
        if backup.BACKUP_HOUR <= local.hour and _claim(cur, conn, 'backup', local.date().isoformat()):
            try:
                backup.run('auto', now_ms)
            except Exception:  # noqa: BLE001
                conn.rollback()
                logger.exception('Zaxira nusxa olinmadi')
        # Yutuqli marafon: boshlash, eslatmalar, yakunlash (ichida CAS — bir marta bajariladi)
        marafon.tick(cur, conn, now_ms)
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
            # Bitta xato (masalan, baza vaqtincha ulanmasa) oqimni o'ldirmasin — aks holda
            # eslatmalar va zaxira nusxa keyingi qayta ishga tushirishgacha to'xtab qoladi
            try:
                tick()
            except Exception:  # noqa: BLE001
                logger.exception('Rejalashtiruvchi: tick xatosi — keyingi daqiqada qayta uriniladi')
            time.sleep(TICK_SECONDS)

    threading.Thread(target=loop, name='bilimsari-scheduler', daemon=True).start()
