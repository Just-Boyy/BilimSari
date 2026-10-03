# -*- coding: utf-8 -*-
"""Admin panel → «Boshqaruv»: bot/ilova tanaffusi, funksiya kalitlari, e'lon, bot holati va
o'quvchi ustidan amallar (bloklash, ism, bonus chaqmoq, imkoniyatlar, kutish, seanslar)."""

from datetime import timedelta

from flask import Blueprint, jsonify, request

import admin_audit
import boshqaruv
import study
import tgbot
from admin_auth import admin_required
from db import as_utc, get_connection, utc_now
from games import chances, clock

bp = Blueprint('boshqaruv_admin', __name__, url_prefix='/api/admin')


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


def _fail(exc):
    return jsonify({'ok': False, 'error': exc.message}), exc.http_status


def _bot_info():
    """Webhook holati (Telegram'dan). Token yo'q yoki Telegram javob bermasa — None."""
    res = tgbot.tg_api('getWebhookInfo', {}) or {}
    w = res.get('result') if res.get('ok') else None
    if not w:
        return None
    return {'username': tgbot.BOT_USERNAME, 'url': w.get('url') or '', 'pending': int(w.get('pending_update_count') or 0),
            'last_error': w.get('last_error_message') or '',
            'last_error_ms': int(w['last_error_date']) * 1000 if w.get('last_error_date') else None}


def _overview(cur, with_bot=False):
    now = clock.now_ms()
    st = boshqaruv.state(fresh=True)
    pause = {}
    for kind in boshqaruv.TARGETS:
        p = st['pause'].get(kind)
        pause[kind] = dict(p, active=boshqaruv.pause_info(kind, now, st) is not None) if p else None
    out = {
        'ok': True, 'now': now, 'pause': pause,
        'features': [{'key': k, 'label': label, 'on': boshqaruv.feature_on(k, st)} for k, label in boshqaruv.FEATURES.items()],
        'announcement': st.get('announcement'),
        'banned': boshqaruv.banned_list(cur, now),
    }
    if with_bot:
        out['bot'] = _bot_info()
    return out


@bp.route('/control', methods=['GET'])
@admin_required
def overview():
    conn, cur = _conn()
    try:
        return jsonify(_overview(cur, with_bot=request.args.get('bot') == '1'))
    finally:
        _close(conn, cur)


@bp.route('/control/<action>', methods=['POST'])
@admin_required
def control_action(action):
    body = _body()
    conn, cur = _conn()
    try:
        if action == 'pause':
            targets = body.get('targets') or []
            boshqaruv.set_pause(cur, conn, targets, body.get('minutes'), body.get('message'))
            admin_audit.log('control_pause', detail=f"targets={','.join(targets)} minutes={body.get('minutes') or 0}", ip=_ip())
        elif action == 'resume':
            targets = [t for t in (body.get('targets') or boshqaruv.TARGETS) if t in boshqaruv.TARGETS]
            boshqaruv.resume(cur, conn, targets)
            admin_audit.log('control_resume', detail='targets=' + ','.join(targets), ip=_ip())
        elif action == 'features':
            changes = body.get('features') or {}
            boshqaruv.set_features(cur, conn, changes)
            admin_audit.log('control_features', detail=' '.join(f'{k}={"on" if v else "off"}' for k, v in changes.items()),
                            ip=_ip())
        elif action == 'announcement':
            boshqaruv.set_announcement(cur, conn, body.get('text'), body.get('text_ru'), body.get('kind'), body.get('minutes'))
            admin_audit.log('announcement_set', detail=str(body.get('text') or '')[:80], ip=_ip())
        elif action == 'announcement-clear':
            boshqaruv.clear_announcement(cur, conn)
            admin_audit.log('announcement_clear', ip=_ip())
        elif action == 'webhook':
            from app import setup_telegram_bot   # noqa: PLC0415 — app bu modulni import qiladi
            setup_telegram_bot(force=True)
            admin_audit.log('bot_webhook', ip=_ip())
            return jsonify(_overview(cur, with_bot=True))
        else:
            return jsonify({'ok': False, 'error': "Noma'lum amal"}), 404
        return jsonify(_overview(cur))
    except boshqaruv.ControlError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)


# ───────────────────────── O'quvchi ustidan amallar ─────────────────────────

def _user(cur, uid):
    cur.execute('''SELECT id, name, telegram_id, lang, premium_until, last_seen_ms, banned_until, ban_reason
                   FROM users WHERE id = %s''', (uid,))
    return cur.fetchone()


def _user_control(cur, u):
    now = clock.now_ms()
    cur.execute('SELECT COUNT(*) AS n FROM tokens WHERE user_id = %s AND expires_at > %s', (u['id'], utc_now()))
    sessions = int(cur.fetchone()['n'])
    parts = study.chaqmoq_parts(cur, u['id'])
    return {
        'ok': True, 'user_id': u['id'], 'name': u['name'],
        'ban': boshqaruv.ban_info(u, now),
        'chaqmoq': sum(parts.values()), 'parts': parts,
        'bonus': boshqaruv.bonus_list(cur, u['id']),
        'chances': chances.status(cur, u['id'], now),
        'cooldown': study.cooldown_state(cur, u['id']),
        'premium_until': int(u['premium_until']) if u['premium_until'] and int(u['premium_until']) > now else None,
        'last_seen_ms': int(u['last_seen_ms']) if u['last_seen_ms'] else None,
        'lang': u['lang'] or 'uz', 'sessions': sessions,
    }


def _notify(u, text):
    """O'quvchiga bot orqali xabar (Telegram'i bo'lsa). Yuborilmasa ham amal bajarilgan."""
    if u and u['telegram_id']:
        try:
            tgbot.send(u['telegram_id'], text, lang='ru' if u['lang'] == 'ru' else 'uz')
        except Exception:  # noqa: BLE001
            pass


@bp.route('/users/<int:uid>/control', methods=['GET'])
@admin_required
def user_control(uid):
    conn, cur = _conn()
    try:
        u = _user(cur, uid)
        if not u:
            return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi'}), 404
        return jsonify(_user_control(cur, u))
    finally:
        _close(conn, cur)


@bp.route('/users/<int:uid>/<action>', methods=['POST'])
@admin_required
def user_action(uid, action):
    body = _body()
    conn, cur = _conn()
    try:
        u = _user(cur, uid)
        if not u:
            return jsonify({'ok': False, 'error': 'Foydalanuvchi topilmadi'}), 404
        if action == 'ban':
            info = boshqaruv.ban(cur, conn, uid, body.get('minutes'), body.get('reason'))
            cur.execute('DELETE FROM tokens WHERE user_id = %s', (uid,))       # ochiq seanslar ham yopiladi
            conn.commit()
            if body.get('notify', True):
                _notify(u, tgbot.L(boshqaruv.banned_text(info, 'uz'), boshqaruv.banned_text(info, 'ru')))
            admin_audit.log('user_ban', detail=f"user_id={uid} minutes={body.get('minutes') or 0} "
                                               f"reason={str(body.get('reason') or '')[:60]}", ip=_ip())
        elif action == 'unban':
            boshqaruv.unban(cur, conn, uid)
            if body.get('notify', True):
                _notify(u, tgbot.L('✅ Akkauntingiz blokdan chiqarildi. BilimSari\'dan yana foydalanishingiz mumkin.',
                                   '✅ Ваш аккаунт разблокирован. Вы снова можете пользоваться BilimSari.'))
            admin_audit.log('user_unban', detail=f'user_id={uid}', ip=_ip())
        elif action == 'rename':
            name = ' '.join(str(body.get('name') or '').split())[:60]
            if len(name) < 2:
                return jsonify({'ok': False, 'error': "Ism kamida 2 ta harf bo'lsin."}), 400
            # custom_name — Telegram orqali qayta kirganda ism Telegram'dagisi bilan almashtirilmaydi
            cur.execute('UPDATE users SET name = %s, custom_name = 1 WHERE id = %s', (name, uid))
            conn.commit()
            admin_audit.log('user_rename', detail=f'user_id={uid} {u["name"]} -> {name}', ip=_ip())
        elif action == 'bonus':
            amount = boshqaruv.add_bonus(cur, conn, uid, body.get('amount'), body.get('note'))
            if body.get('notify', True) and amount > 0:
                note = str(body.get('note') or '').strip()[:200]
                _notify(u, tgbot.L(f"🎁 Admin sizga <b>+{amount}</b> chaqmoq berdi!" + (f"\n{note}" if note else ''),
                                   f"🎁 Админ начислил вам <b>+{amount}</b> молний!" + (f"\n{note}" if note else '')))
            admin_audit.log('user_bonus', detail=f'user_id={uid} amount={amount} note={str(body.get("note") or "")[:60]}',
                            ip=_ip())
        elif action == 'reset-chances':
            chances._save(cur, uid, 0, None)
            conn.commit()
            admin_audit.log('user_reset_chances', detail=f'user_id={uid}', ip=_ip())
        elif action == 'reset-cooldown':
            # Oxirgi 24 soatda tugatilgan mavzular vaqti kutish muddatiga orqaga suriladi — keyingi mavzu darhol ochiladi
            hours = study.COOLDOWN_HOURS
            cutoff = utc_now() - timedelta(hours=hours)
            cur.execute('SELECT topic_id, completed_at FROM user_progress WHERE user_id = %s AND status = %s '
                        'AND completed_at IS NOT NULL', (uid, study.STATUS_COMPLETED))
            moved = 0
            for r in cur.fetchall():
                at = as_utc(r['completed_at'])
                if at and at > cutoff:
                    cur.execute('UPDATE user_progress SET completed_at = %s WHERE user_id = %s AND topic_id = %s',
                                (at - timedelta(hours=hours), uid, r['topic_id']))
                    moved += 1
            conn.commit()
            admin_audit.log('user_reset_cooldown', detail=f'user_id={uid} topics={moved}', ip=_ip())
        elif action == 'logout':
            cur.execute('DELETE FROM tokens WHERE user_id = %s', (uid,))
            conn.commit()
            admin_audit.log('user_logout', detail=f'user_id={uid}', ip=_ip())
        else:
            return jsonify({'ok': False, 'error': "Noma'lum amal"}), 404
        return jsonify(_user_control(cur, _user(cur, uid)))
    except boshqaruv.ControlError as exc:
        return _fail(exc)
    finally:
        _close(conn, cur)
