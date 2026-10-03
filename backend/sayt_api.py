# -*- coding: utf-8 -*-
"""Admin panel: qoidalar, matnlar, bot matnlari, dizayn, ma'lumotlar bazasi, ommaviy xabarlar (guruh va vaqt
bo'yicha), rejalashtirilgan ishlar va kun savoli rejasi. Ochiq: /api/site/config (o'quvchi sahifalari uchun)."""

import json
from datetime import timedelta

from flask import Blueprint, Response, jsonify, request

import admin_audit
import alerts
import baza
import botchat
import broadcast
import curriculum as cur_mod
import daily
import dostlar
import mavzu_qosh
import notify
import payments
import personal
import qoidalar
import sayt
import tgbot
from admin_auth import admin_required
from db import TASHKENT_TZ, get_connection
from games import clock

bp = Blueprint('sayt_admin', __name__, url_prefix='/api/admin')
public_bp = Blueprint('sayt_public', __name__, url_prefix='/api/site')


def _conn():
    conn = get_connection()
    return conn, conn.cursor()


def _close(conn, cur):
    try:
        cur.close()
        conn.close()
    except Exception:  # noqa: BLE001
        pass


def _body():
    return request.get_json(silent=True) or {}


def _ip():
    fwd = request.headers.get('X-Forwarded-For', '')
    return fwd.split(',')[0].strip() if fwd else (request.remote_addr or 'unknown')


def _err(message, status=400):
    return jsonify({'ok': False, 'error': message}), status


# ───────────────────────── Ochiq: o'quvchi sahifalari uchun ─────────────────────────

@public_bp.route('/live', methods=['GET'])
def site_live():
    """Jonli yangilanish: ochiq sahifa ~8 s da so'raydi; versiya o'zgarsa — o'sha qismni qayta yuklaydi.
    Kirgan o'quvchi bloklangan yoki ilova to'xtatilgan bo'lsa — 403/423 (sahifada darhol oyna chiqadi)."""
    from auth_core import get_user_by_token, token_from_request   # noqa: PLC0415
    import boshqaruv   # noqa: PLC0415
    conn, cur = _conn()
    try:
        user = get_user_by_token(token_from_request())
        if user:
            blocked = boshqaruv.check_request(user, 'GET', request.path)
            if blocked:
                return jsonify(blocked[0]), blocked[1]
        v = {'site': sayt.config(cur)['v'], 'control': boshqaruv.version(), 'content': sayt.content_version(cur)}
        if user:
            v['me'] = sayt.me_version(cur, user['id'])
        resp = jsonify({'ok': True, 'v': v})
    finally:
        _close(conn, cur)
    resp.headers['Cache-Control'] = 'no-store'
    return resp


@public_bp.route('/config', methods=['GET'])
def site_config():
    conn, cur = _conn()
    try:
        resp = jsonify(sayt.config(cur))
    finally:
        _close(conn, cur)
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


# ───────────────────────── Qoidalar ─────────────────────────

@bp.route('/rules', methods=['GET'])
@admin_required
def rules():
    qoidalar.refresh(force=True)
    return jsonify({'ok': True, 'rules': qoidalar.listing()})


@bp.route('/rules', methods=['POST'])
@admin_required
def rules_save():
    changes = _body().get('values') or {}
    conn, cur = _conn()
    try:
        before = qoidalar.values()
        after = qoidalar.save(cur, conn, changes)
    except qoidalar.RuleError as exc:
        return _err(exc.message)
    finally:
        _close(conn, cur)
    diff = ' '.join(f'{k}={before[k]}→{after[k]}' for k in after if before[k] != after[k])
    admin_audit.log('rules_save', detail=diff[:500], ip=_ip())
    return jsonify({'ok': True, 'rules': qoidalar.listing()})


# ───────────────────────── Matnlar ─────────────────────────

def _bot_defaults():
    import app as main   # noqa: PLC0415 — app bu modulni import qiladi
    return {
        'start': {'uz': main.START_TEXT['uz'], 'ru': main.START_TEXT['ru']},
        'help': {'uz': main.HELP_TEXT['uz'], 'ru': main.HELP_TEXT['ru']},
        'description': {'uz': main.BOT_DESCRIPTION, 'ru': main.BOT_DESCRIPTION_RU},
        'short_description': {'uz': main.BOT_SHORT_DESCRIPTION, 'ru': main.BOT_SHORT_DESCRIPTION_RU},
    }


def _texts_payload(cur):
    custom = sayt.bot_texts(cur)
    defaults = _bot_defaults()
    bots = [{'key': k, 'label': v[0], 'hint': v[1], 'limit': v[2], 'html': v[3], 'default': defaults[k],
             'custom': custom.get(k)} for k, v in sayt.BOT_TEXTS.items()]
    auto = qoidalar.auto_texts()
    return {'ok': True, 'texts': sorted(sayt.ui_texts(cur), key=lambda x: -int(x.get('ms') or 0)),
            'bot': bots, 'auto': [{'orig': k, 'uz': v, 'ru': auto['ru'].get(k)} for k, v in auto['uz'].items()]}


@bp.route('/texts', methods=['GET'])
@admin_required
def texts():
    conn, cur = _conn()
    try:
        return jsonify(_texts_payload(cur))
    finally:
        _close(conn, cur)


@bp.route('/texts/search', methods=['GET'])
@admin_required
def texts_search():
    return jsonify({'ok': True, 'items': sayt.search_catalog(request.args.get('q', ''))})


@bp.route('/texts', methods=['POST'])
@admin_required
def texts_save():
    b = _body()
    conn, cur = _conn()
    try:
        if b.get('delete'):
            sayt.delete_ui_text(cur, conn, b.get('orig'))
            admin_audit.log('text_delete', detail=str(b.get('orig'))[:200], ip=_ip())
        else:
            sayt.save_ui_text(cur, conn, b.get('orig'), b.get('uz'), b.get('ru'))
            admin_audit.log('text_save', detail=f"{str(b.get('orig'))[:120]} → {str(b.get('uz') or b.get('ru'))[:120]}",
                            ip=_ip())
        return jsonify(_texts_payload(cur))
    except sayt.SiteError as exc:
        return _err(exc.message)
    finally:
        _close(conn, cur)


@bp.route('/bot-texts', methods=['POST'])
@admin_required
def bot_texts_save():
    b = _body()
    key = b.get('key')
    conn, cur = _conn()
    try:
        sayt.save_bot_text(cur, conn, key, b.get('uz'), b.get('ru'))
        sayt._bot_cache['t'] = 0.0
        admin_audit.log('bot_text', detail=str(key), ip=_ip())
        if key in ('description', 'short_description'):
            from app import setup_telegram_bot   # noqa: PLC0415
            setup_telegram_bot(force=True)          # Telegram'dagi bot tavsifi darhol yangilansin
        return jsonify(_texts_payload(cur))
    except sayt.SiteError as exc:
        return _err(exc.message)
    finally:
        _close(conn, cur)


# ───────────────────────── Dizayn ─────────────────────────

def _design_payload(cur):
    th = sayt.theme(cur)
    hidden = set(sayt.hidden_blocks(cur))
    return {'ok': True,
            'colors': [{'key': k, 'label': v[0], 'default': v[2], 'value': th.get(k, v[2])} for k, v in sayt.THEME.items()],
            'blocks': [{'key': k, 'group': v[0], 'label': v[1], 'hidden': k in hidden} for k, v in sayt.BLOCKS.items()]}


@bp.route('/design', methods=['GET'])
@admin_required
def design():
    conn, cur = _conn()
    try:
        return jsonify(_design_payload(cur))
    finally:
        _close(conn, cur)


@bp.route('/design', methods=['POST'])
@admin_required
def design_save():
    b = _body()
    conn, cur = _conn()
    try:
        if 'colors' in b:
            sayt.save_theme(cur, conn, b.get('colors'))
            admin_audit.log('design_colors', detail=json.dumps(b.get('colors'))[:300], ip=_ip())
        if 'hide' in b:
            sayt.save_hidden(cur, conn, b.get('hide'))
            admin_audit.log('design_blocks', detail=','.join(b.get('hide') or [])[:300], ip=_ip())
        return jsonify(_design_payload(cur))
    except sayt.SiteError as exc:
        return _err(exc.message)
    finally:
        _close(conn, cur)


# ───────────────────────── Ma'lumotlar bazasi ─────────────────────────

def _key_arg():
    try:
        key = json.loads(request.args.get('key') or '{}')
    except (TypeError, ValueError):
        key = None
    return key if isinstance(key, dict) else {}


@bp.route('/db/tables', methods=['GET'])
@admin_required
def db_tables():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'tables': baza.tables(cur)})
    finally:
        _close(conn, cur)


@bp.route('/db/rows', methods=['GET'])
@admin_required
def db_rows():
    a = request.args
    conn, cur = _conn()
    try:
        data = baza.rows(cur, a.get('table'), a.get('q'), a.get('col'), int(a.get('page') or 1), a.get('order'),
                         a.get('desc', '1') == '1')
        return jsonify(dict(data, ok=True))
    except baza.DbError as exc:
        return _err(exc.message, exc.http_status)
    except ValueError:
        return _err("So'rov noto'g'ri.")
    finally:
        _close(conn, cur)


@bp.route('/db/row', methods=['GET'])
@admin_required
def db_row():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'row': baza.get_row(cur, request.args.get('table'), _key_arg()),
                        'columns': baza.columns(cur, request.args.get('table'))})
    except baza.DbError as exc:
        return _err(exc.message, exc.http_status)
    finally:
        _close(conn, cur)


@bp.route('/db/update', methods=['POST'])
@admin_required
def db_update():
    b = _body()
    conn, cur = _conn()
    try:
        before, after = baza.update_row(cur, conn, b.get('table'), b.get('key') or {}, b.get('changes') or {})
        detail = f"{b.get('table')} {json.dumps(b.get('key'), ensure_ascii=False)} " + '; '.join(
            f'{k}: {baza.short(before[k], 60)} → {baza.short(after[k], 60)}' for k in after)
        admin_audit.log('db_update', detail=detail[:900], ip=_ip())
        return jsonify({'ok': True, 'row': baza.get_row(cur, b.get('table'), b.get('key') or {})})
    except baza.DbError as exc:
        return _err(exc.message, exc.http_status)
    except Exception as exc:  # noqa: BLE001 — bazaning o'z cheklovi (UNIQUE, FOREIGN KEY ...)
        conn.rollback()
        return _err('Baza qabul qilmadi: ' + str(exc).split('\n')[0][:300])
    finally:
        _close(conn, cur)


@bp.route('/db/delete', methods=['POST'])
@admin_required
def db_delete():
    b = _body()
    conn, cur = _conn()
    try:
        old = baza.delete_row(cur, conn, b.get('table'), b.get('key') or {})
        admin_audit.log('db_delete', detail=f"{b.get('table')} {baza.short(old, 700)}", ip=_ip())
        return jsonify({'ok': True})
    except baza.DbError as exc:
        return _err(exc.message, exc.http_status)
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        return _err('Baza qabul qilmadi: ' + str(exc).split('\n')[0][:300])
    finally:
        _close(conn, cur)


@bp.route('/db/export', methods=['GET'])
@admin_required
def db_export():
    table = request.args.get('table')
    conn, cur = _conn()
    try:
        data = baza.export_csv(cur, table)
    except baza.DbError as exc:
        return _err(exc.message, exc.http_status)
    finally:
        _close(conn, cur)
    admin_audit.log('db_export', detail=str(table), ip=_ip())
    return Response(data, mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="{table}.csv"'})


# ───────────────────────── Ommaviy xabarlar ─────────────────────────

def _broadcasts_payload(cur):
    now = clock.now_ms()
    return {'ok': True, 'items': broadcast.recent(cur),
            'segments': [{'key': k, 'label': v[0], 'count': broadcast.count(cur, k, now=now)}
                         for k, v in broadcast.SEGMENTS.items()]}


@bp.route('/broadcasts', methods=['GET'])
@admin_required
def broadcasts():
    conn, cur = _conn()
    try:
        return jsonify(_broadcasts_payload(cur))
    finally:
        _close(conn, cur)


@bp.route('/broadcasts', methods=['POST'])
@admin_required
def broadcasts_create():
    if not tgbot.BOT_TOKEN:
        return _err("BOT_TOKEN sozlanmagan — bot ulanmagan", 503)
    b = _body()
    button = str(b.get('button_text') or '').strip()[:40] or None
    path = str(b.get('button_path') or '').strip()[:120]
    if button and (not path or '://' in path or path.startswith('/')):
        return _err("Tugma uchun ilova sahifasini tanlang.")
    start_ms = None
    if b.get('start_at'):
        try:
            from datetime import datetime   # noqa: PLC0415
            local = datetime.fromisoformat(str(b['start_at'])).replace(tzinfo=TASHKENT_TZ)
            start_ms = int(local.timestamp() * 1000)
        except (TypeError, ValueError):
            return _err("Vaqt noto'g'ri.")
        if start_ms < clock.now_ms() - 60 * 1000:
            return _err('Vaqt o\'tib ketgan — kelajakdagi vaqtni tanlang.')
    conn, cur = _conn()
    try:
        info = broadcast.start(cur, conn, b.get('text'), html=bool(b.get('html')), button=button, path=path,
                               queue=True, text_ru=b.get('text_ru'), button_ru=str(b.get('button_ru') or '').strip()[:40] or None,
                               segment=b.get('segment') or 'all', start_ms=start_ms)
        admin_audit.log('broadcast', detail=f"id={info['id']} total={info['total']} segment={b.get('segment') or 'all'} "
                                            f"start={b.get('start_at') or 'hozir'} text={str(b.get('text'))[:100]!r}", ip=_ip())
        return jsonify(_broadcasts_payload(cur))
    except broadcast.BroadcastError as exc:
        return _err(exc.message, exc.http_status)
    finally:
        _close(conn, cur)


@bp.route('/broadcasts/<int:bid>/cancel', methods=['POST'])
@admin_required
def broadcasts_cancel(bid):
    conn, cur = _conn()
    try:
        if not broadcast.cancel(cur, conn, bid):
            return _err("Bu xabarni bekor qilib bo'lmaydi (allaqachon yuborilgan yoki yuborilmoqda).")
        admin_audit.log('broadcast_cancel', detail=f'id={bid}', ip=_ip())
        return jsonify(_broadcasts_payload(cur))
    finally:
        _close(conn, cur)


# ───────────────────────── Rejalashtirilgan ishlar ─────────────────────────

def _run_cleanup(cur, conn, now):
    payments.housekeeping(cur, conn, now)
    botchat.cleanup_updates(cur, conn, now)
    alerts.cleanup(cur, conn, now)
    personal.housekeeping(cur, conn, now)
    dostlar.housekeeping(cur, conn, now)
    return 'bajarildi'


JOBS = {
    'question': ('«Kun savoli tayyor» xabari', 'Har kuni ertalab. Bugun olmaganlarga yuboriladi (takror yubormaydi).',
                 lambda cur, conn, now: f"{notify.question_ready(cur, conn, now)} ta yuborildi"),
    'daily': ('Kunlik eslatma — hozir hammaga', "Odatda har kim o'zi tanlagan soatda oladi. Bu tugma bugun hali olmagan "
                                                "barcha faol o'quvchilarga hozir yuboradi.",
              lambda cur, conn, now: f"{notify.daily_reminders(cur, conn, now)} ta yuborildi"),
    'cooldown': ('«Yangi mavzu ochildi» xabarlari', 'Har 5 daqiqada.',
                 lambda cur, conn, now: f"{notify.cooldown_ready(cur, conn, now)} ta yuborildi"),
    'premium': ('Premium tugash eslatmalari', 'Kunduzi har soatda.',
                lambda cur, conn, now: f"{notify.premium_reminders(cur, conn, now) or 0} ta yuborildi"),
    'cleanup': ('Tozalash', "Eskirgan buyurtmalar, chaqiruvlar, bot yangilanishlari va xatolar jurnali.", _run_cleanup),
    'broadcasts': ('Rejalashtirilgan xabarlarni tekshirish', 'Har daqiqada.',
                   lambda cur, conn, now: f"{len(broadcast.start_due(cur, conn, now))} ta boshlandi"),
}
INFO_ONLY = {'weekly': "Haftalik turnir g'oliblari", 'backup': 'Kunlik zaxira nusxa', 'pay_summary': "Kunlik to'lov hisoboti",
             'bot_setup': 'Bot sozlamasi (webhook, buyruqlar)', 'marafon': 'Marafon'}


@bp.route('/jobs', methods=['GET'])
@admin_required
def jobs():
    conn, cur = _conn()
    try:
        cur.execute('SELECT job, MAX(ran_ms) AS last, COUNT(*) AS n FROM job_runs GROUP BY job')
        last = {r['job']: (int(r['last']), int(r['n'])) for r in cur.fetchall()}
    finally:
        _close(conn, cur)
    items = [{'key': k, 'label': v[0], 'hint': v[1], 'runnable': True,
              'last_ms': last.get('daily' if k == 'daily' else k, (None, 0))[0]} for k, v in JOBS.items()]
    items += [{'key': k, 'label': v, 'hint': '', 'runnable': False, 'last_ms': last.get(k, (None, 0))[0]}
              for k, v in INFO_ONLY.items()]
    return jsonify({'ok': True, 'jobs': items})


@bp.route('/jobs/<key>/run', methods=['POST'])
@admin_required
def jobs_run(key):
    if key not in JOBS:
        return _err("Bu ishni qo'lda bajarib bo'lmaydi.", 404)
    conn, cur = _conn()
    try:
        result = JOBS[key][2](cur, conn, clock.now_ms())
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        return _err('Xato: ' + str(exc)[:200], 500)
    finally:
        _close(conn, cur)
    admin_audit.log('job_run', detail=f'{key}: {result}', ip=_ip())
    return jsonify({'ok': True, 'result': result})


# ───────────────────────── Yangi mavzular (admin qo'shgan) ─────────────────────────

@bp.route('/subjects/<key>/admin-topics', methods=['GET'])
@admin_required
def admin_topics(key):
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'items': mavzu_qosh.listing(cur, key)})
    finally:
        _close(conn, cur)


@bp.route('/subjects/<key>/admin-topics', methods=['POST'])
@admin_required
def admin_topics_create(key):
    b = _body()
    conn, cur = _conn()
    try:
        item = mavzu_qosh.create(cur, conn, key, b.get('title'), 'manual' if b.get('mode') == 'manual' else 'ai', b.get('note'))
        admin_audit.log('topic_add', detail=f"{key}: {item['title']} ({b.get('mode') or 'ai'})", ip=_ip())
        return jsonify({'ok': True, 'item': item, 'items': mavzu_qosh.listing(cur, key)})
    except mavzu_qosh.TopicError as exc:
        return _err(exc.message, exc.http_status)
    finally:
        _close(conn, cur)


@bp.route('/admin-topics/<tid>/retry', methods=['POST'])
@admin_required
def admin_topics_retry(tid):
    conn, cur = _conn()
    try:
        item = mavzu_qosh.retry(cur, conn, tid)
        return jsonify({'ok': True, 'item': item, 'items': mavzu_qosh.listing(cur, item['subject_key'])})
    except mavzu_qosh.TopicError as exc:
        return _err(exc.message, exc.http_status)
    finally:
        _close(conn, cur)


@bp.route('/admin-topics/<tid>', methods=['DELETE'])
@admin_required
def admin_topics_delete(tid):
    conn, cur = _conn()
    try:
        item = mavzu_qosh.get(cur, tid)
        mavzu_qosh.delete(cur, conn, tid)
        admin_audit.log('topic_delete', detail=f"{tid}: {(item or {}).get('title')}", ip=_ip())
        return jsonify({'ok': True, 'items': mavzu_qosh.listing(cur, (item or {}).get('subject_key'))})
    except mavzu_qosh.TopicError as exc:
        return _err(exc.message, exc.http_status)
    finally:
        _close(conn, cur)


# ───────────────────────── Kun savoli rejasi ─────────────────────────

def _question_view(cur, topic_id, q_index):
    cur.execute('SELECT id, title, subject_key, quiz FROM topics WHERE id = %s', (topic_id,))
    t = cur.fetchone()
    if not t:
        return None
    quiz = daily._quiz(t['quiz'])
    q = quiz[q_index] if 0 <= q_index < len(quiz) else {}
    return {'topic_id': t['id'], 'topic_title': t['title'], 'subject': cur_mod.subject_meta(t['subject_key'])['name'],
            'q_index': q_index, 'question': q.get('q') or '—', 'type': q.get('type', 'mc'),
            'options': q.get('options') or (["To'g'ri", "Noto'g'ri"] if q.get('type') == 'tf' else []),
            'answer': q.get('answer')}


def _daily_plan(cur, now):
    today = clock.tashkent_date(now)
    out = []
    for i in range(7):
        day = (today + timedelta(days=i)).isoformat()
        cur.execute('SELECT topic_id, q_index, admin FROM daily_questions WHERE day = %s', (day,))
        row = cur.fetchone()
        if row:
            topic_id, q_index, admin = row['topic_id'], int(row['q_index']), bool(row.get('admin'))
        else:
            try:
                topic_id, q_index = daily._pick(cur, day)
            except Exception:  # noqa: BLE001
                out.append({'day': day, 'question': None})
                continue
            admin = False
        cur.execute('SELECT COUNT(*) AS n FROM daily_answers WHERE day = %s', (day,))
        answers = int(cur.fetchone()['n'])
        out.append(dict(_question_view(cur, topic_id, q_index) or {}, day=day, admin=admin, answers=answers))
    return out


@bp.route('/daily-plan', methods=['GET'])
@admin_required
def daily_plan():
    conn, cur = _conn()
    try:
        return jsonify({'ok': True, 'days': _daily_plan(cur, clock.now_ms())})
    finally:
        _close(conn, cur)


@bp.route('/daily-plan/questions', methods=['GET'])
@admin_required
def daily_questions():
    conn, cur = _conn()
    try:
        cur.execute('SELECT quiz FROM topics WHERE id = %s', (request.args.get('topic_id'),))
        t = cur.fetchone()
        if not t:
            return _err('Mavzu topilmadi.', 404)
        quiz = daily._quiz(t['quiz'])
        items = [{'q_index': i, 'question': q.get('q'), 'type': q.get('type', 'mc')} for i, q in enumerate(quiz)
                 if isinstance(q, dict) and q.get('q') and q.get('type', 'mc') in ('mc', 'tf')]
        return jsonify({'ok': True, 'items': items})
    finally:
        _close(conn, cur)


@bp.route('/daily-plan', methods=['POST'])
@admin_required
def daily_plan_set():
    b = _body()
    day = str(b.get('day') or '')
    conn, cur = _conn()
    try:
        now = clock.now_ms()
        today = clock.tashkent_date(now).isoformat()
        if not day or day < today or len(day) != 10:
            return _err("Kun noto'g'ri (bugun yoki keyingi kunlar).")
        cur.execute('SELECT COUNT(*) AS n FROM daily_answers WHERE day = %s', (day,))
        if int(cur.fetchone()['n']):
            return _err("Bu kungi savolga o'quvchilar javob bera boshlagan — endi almashtirib bo'lmaydi.")
        cur.execute('DELETE FROM daily_questions WHERE day = %s', (day,))
        if b.get('reset'):
            audit = ('daily_reset', day)
        else:
            try:
                q_index = int(b.get('q_index'))
            except (TypeError, ValueError):
                return _err("Savol tanlanmadi.")
            view = _question_view(cur, b.get('topic_id'), q_index)
            if not view or view['question'] == '—' or view['type'] not in ('mc', 'tf'):
                conn.rollback()
                return _err("Bu savolni kun savoli qilib bo'lmaydi (faqat variantli yoki to'g'ri/noto'g'ri savol).")
            cur.execute('INSERT INTO daily_questions (day, topic_id, q_index, created_ms, admin) VALUES (%s, %s, %s, %s, 1)',
                        (day, b.get('topic_id'), q_index, now))
            audit = ('daily_set', f"{day}: {b.get('topic_id')} #{q_index}")
        conn.commit()
        admin_audit.log(audit[0], detail=audit[1], ip=_ip())      # commitdan keyin (alohida ulanishda yoziladi)
        return jsonify({'ok': True, 'days': _daily_plan(cur, now)})
    finally:
        _close(conn, cur)
