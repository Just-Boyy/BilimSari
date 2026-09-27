"""
BilimSari Backend — Flask + PostgreSQL
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_compress import Compress
import hashlib
import html
import logging
import os

import achievements
import admin_api
import admin_audit
import admin_auth
import ai_tutor
import daily
import notify
import photos
import rate_limit
import study
import study_api
from auth_core import SECRET, auth_required, create_token, token_from_request
from db import add_column_if_missing, get_connection
from games import api as games_api
from games import rooms as game_rooms
from games import schema as game_schema
from tgbot import BOT_TOKEN, BOT_USERNAME, WEBAPP_URL, tg_api

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)
logger = logging.getLogger('bilimsari')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024   # eng katta so'rov — profil rasmi (~0.4 MB)
CORS(app, resources={r"/api/*": {"origins": "*"}})
Compress(app)  # JSON/HTML/CSS/JS javoblarini siqadi — mobil tarmoqda tezroq yuklanadi
app.register_blueprint(study_api.bp)
app.register_blueprint(ai_tutor.bp)
app.register_blueprint(admin_api.bp)
app.register_blueprint(games_api.bp)


@app.after_request
def _security_headers(response):
    # Telegram Web mini apps yuklanadi iframe orqali — shuning uchun
    # X-Frame-Options/frame-ancestors qo'shilmagan, aks holda ochilmay qolardi.
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# BOT_TOKEN va WEBAPP_URL — tgbot.py'da (muhit o'zgaruvchilaridan) o'qiladi.

# Webhook'ga faqat Telegram o'zi yuborayotganini tekshirish uchun maxfiy token.
# SECRET_KEY'dan hosil qilinadi — barcha worker'larda bir xil bo'lishi shart
# (tasodifiy generatsiya qilinsa, har bir gunicorn worker boshqa qiymat olib,
# webhook so'rovlari qaysi workerga tushishiga qarab tasodifiy rad etilib qolardi).
WEBHOOK_SECRET = hashlib.sha256(f'{SECRET}|telegram-webhook'.encode()).hexdigest()


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Bir martalik: eski (FastAPI) sxemasi bilan to'qnashmasligi uchun,
    # RESET_DB=1 bo'lsa jadvallar noldan qayta yaratiladi. Ishlatgandan
    # so'ng RESET_DB muhit o'zgaruvchisini o'chirib qo'yish kerak.
    if os.environ.get('RESET_DB') == '1':
        cur.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')
        conn.commit()
        logger.warning('RESET_DB=1: schema tozalandi')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT,
            telegram_id BIGINT UNIQUE,
            username TEXT,
            photo_url TEXT,
            onboarded BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at TIMESTAMP NOT NULL
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_tokens_user_id ON tokens (user_id)')
    conn.commit()
    for stmt in [
        "ALTER TABLE users ALTER COLUMN email DROP NOT NULL",
        "ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL",
    ]:
        try:
            cur.execute(stmt)
            conn.commit()
        except Exception:
            conn.rollback()

    for column, ddl in [
        ('telegram_id', 'BIGINT'),
        ('username', 'TEXT'),
        ('photo_url', 'TEXT'),
        ('onboarded', 'BOOLEAN NOT NULL DEFAULT FALSE'),
        # O'quvchi ismini/rasmini o'zi o'zgartirgan bo'lsa (1) — Telegram orqali
        # kirish ularni qayta yozmaydi. Telegram rasmi alohida saqlanadi.
        ('custom_name', 'INTEGER NOT NULL DEFAULT 0'),
        ('custom_photo', 'INTEGER NOT NULL DEFAULT 0'),
        ('tg_photo_url', 'TEXT'),
    ]:
        add_column_if_missing(cur, conn, 'users', column, ddl)

    # Yangi o'quv tizimi: subjects / topics / user_progress + curriculum sinxroni
    try:
        study.ensure_tables(cur, conn)
        written = study.sync_curriculum(cur, conn)
        if written:
            logger.info('Curriculum sinxronlandi: %d ta mavzu', written)
        else:
            logger.info('Curriculum o‘zgarmagan — sinxronlash o‘tkazib yuborildi')
    except Exception:
        logger.exception('Study jadvallari xatosi')
        conn.rollback()

    # Umumiy tezlik cheklovi (AI, admin login, mehmon hisob), admin audit
    # jurnali va admin token bekor qilish jadvali
    try:
        rate_limit.ensure_table(cur, conn)
        admin_audit.ensure_table(cur, conn)
        admin_auth.ensure_table(cur, conn)
        ai_tutor.ensure_cache_table(cur, conn)
    except Exception:
        logger.exception('rate_limit/admin_audit/admin_auth/ai_tutor jadvallari xatosi')
        conn.rollback()

    # Game Hub (multiplayer o'yinlar) jadvallari
    try:
        game_schema.ensure_tables(cur, conn)
    except Exception:
        logger.exception("O'yin jadvallari xatosi")
        conn.rollback()

    # Kun savoli, yutuqlar (nishonlar) va profil rasmlari
    try:
        daily.ensure_tables(cur, conn)
        achievements.ensure_tables(cur, conn)
        photos.ensure_tables(cur, conn)
    except Exception:
        logger.exception('Kun savoli/yutuqlar jadvallari xatosi')
        conn.rollback()

    # Telegram eslatmalari (jurnal, rejalashtiruvchi, users.notify)
    try:
        notify.ensure_tables(cur, conn)
    except Exception:
        logger.exception('Eslatma jadvallari xatosi')
        conn.rollback()

    conn.commit()
    cur.close()
    conn.close()


# ───────────────────────────── Routes ─────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    try:
        conn = get_connection()
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False
    return jsonify({'ok': True, 'service': 'BilimSari API', 'db': db_ok})


def _client_ip():
    fwd = request.headers.get('X-Forwarded-For', '')
    if fwd:
        return fwd.split(',')[0].strip()
    return request.remote_addr or 'unknown'


@app.route('/api/guest', methods=['POST'])
def guest():
    """
    Ism bilan tezkor hisob — email va parol so'ralmaydi.

    Eski ilovadagi «Boshlash» oqimi shunday edi. Farqi: endi token haqiqiy
    va progress serverda saqlanadi. Bunday hisobga boshqa qurilmadan kirib
    bo'lmaydi (email/parol yo'q) — Telegram orqali kirganlar bundan mustasno.
    """
    if not rate_limit.hit(f'guest:{_client_ip()}', 8, 3600):
        return jsonify({
            'ok': False,
            'error': "Juda ko'p urinish. Birozdan so'ng qayta urinib ko'ring.",
            'code': 'rate_limit',
        }), 429

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()[:80]

    if len(name) < 2:
        return jsonify({'ok': False, 'error': 'Ismingizni yozing (kamida 2 ta harf)'}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO users (name, email, password_hash, onboarded) VALUES (%s, NULL, NULL, TRUE) RETURNING id',
        (name,)
    )
    user_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()

    token = create_token(user_id)
    return jsonify({
        'ok': True,
        'token': token,
        'user': {'id': user_id, 'name': name, 'email': None, 'grade': None},
    }), 201


@app.route('/api/me', methods=['GET'])
@auth_required
def me():
    user = dict(request.user)
    # Faqat profilda "Admin panel" qatorini ko'rsatish uchun — haqiqiy kirish
    # /api/admin/telegram-login'da imzolangan initData orqali tekshiriladi.
    user['is_admin'] = admin_auth.is_admin_telegram(user.get('telegram_id'))
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT notify, custom_photo FROM users WHERE id = %s', (user['id'],))
        row = cur.fetchone() or {}
        user['notify'] = bool(row.get('notify', 1))
        user['custom_photo'] = bool(row.get('custom_photo'))
    except Exception:
        conn.rollback()
        user['notify'] = True
    finally:
        cur.close()
        conn.close()
    return jsonify({'ok': True, 'user': user, 'bot': BOT_USERNAME})


@app.route('/api/profile/notify', methods=['POST'])
@auth_required
def update_notify():
    """Telegram eslatmalarini yoqish/o'chirish (profil → Sozlamalar)."""
    on = bool((request.get_json(silent=True) or {}).get('on'))
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('UPDATE users SET notify = %s WHERE id = %s', (int(on), request.user['id']))
        conn.commit()
        return jsonify({'ok': True, 'notify': on})
    finally:
        cur.close()
        conn.close()


NAME_MAX = 40


@app.route('/api/profile/name', methods=['POST'])
@auth_required
def update_name():
    """Ismni o'zgartirish (onboarding'da "O'zim kiritaman" va Sozlamalar).
    Shundan keyin Telegram orqali kirish ismni qayta yozmaydi."""
    body = request.get_json(silent=True) or {}
    name = ' '.join(str(body.get('name') or '').split())
    if len(name) < 2:
        return jsonify({'ok': False, 'error': "Ismingizni to'liq yozing.", 'code': 'bad_name'}), 400
    if len(name) > NAME_MAX:
        return jsonify({'ok': False, 'error': f"Ism {NAME_MAX} ta belgidan oshmasin.", 'code': 'bad_name'}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute('UPDATE users SET name = %s, onboarded = TRUE, custom_name = 1 WHERE id = %s',
                (name, request.user['id']))
    conn.commit()
    cur.close()
    conn.close()

    updated = dict(request.user)
    updated['name'] = name
    updated['onboarded'] = True
    return jsonify({'ok': True, 'user': updated})


@app.route('/api/profile/onboarded', methods=['POST'])
@auth_required
def mark_onboarded():
    """Onboarding: Telegram ismi tasdiqlanganda (o'zgartirmasdan) chaqiriladi."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('UPDATE users SET onboarded = TRUE WHERE id = %s', (request.user['id'],))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'ok': True})


@app.route('/api/profile/photo', methods=['POST'])
@auth_required
def upload_photo():
    """Sozlamalar: o'quvchi o'z rasmini yuklaydi (brauzer oldindan kichraytiradi)."""
    if not rate_limit.hit(f'photo:{request.user["id"]}', 20, 3600):
        return jsonify({'ok': False, 'error': "Juda ko'p urinish. Birozdan keyin qayta urinib ko'ring."}), 429
    body = request.get_json(silent=True) or {}
    conn = get_connection()
    cur = conn.cursor()
    try:
        url = photos.save(cur, conn, request.user['id'], body.get('image'))
        return jsonify({'ok': True, 'photo_url': url})
    except photos.PhotoError as exc:
        return jsonify({'ok': False, 'error': str(exc), 'code': 'bad_photo'}), 400
    finally:
        cur.close()
        conn.close()


@app.route('/api/profile/photo/remove', methods=['POST'])
@auth_required
def remove_photo():
    conn = get_connection()
    cur = conn.cursor()
    try:
        return jsonify({'ok': True, 'photo_url': photos.remove(cur, conn, request.user['id'])})
    finally:
        cur.close()
        conn.close()


@app.route('/api/photo/<int:user_id>', methods=['GET'])
def user_photo(user_id):
    """O'quvchi yuklagan rasm. URL'da ?v=<vaqt> bor — rasm almashsa URL ham
    o'zgaradi, shuning uchun uzoq keshlash xavfsiz."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        found = photos.load(cur, user_id)
    finally:
        cur.close()
        conn.close()
    if not found:
        return jsonify({'ok': False, 'error': 'Rasm topilmadi'}), 404
    mime, data = found
    resp = app.response_class(data, mimetype=mime)
    resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resp


@app.route('/api/logout', methods=['POST'])
@auth_required
def logout():
    conn = get_connection()
    cur = conn.cursor()
    token = token_from_request()
    cur.execute('DELETE FROM tokens WHERE token = %s', (token,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'ok': True})


@app.route('/api/telegram/auth', methods=['POST'])
def telegram_auth():
    """Telegram Mini App orqali kirish / ro'yxat"""
    from telegram_auth import validate_init_data

    data = request.get_json(silent=True) or {}
    init_data = data.get('initData') or ''
    bot_token = BOT_TOKEN

    if not bot_token:
        return jsonify({'ok': False, 'error': 'BOT_TOKEN sozlanmagan'}), 500

    tg_user = validate_init_data(init_data, bot_token)
    if not tg_user or not tg_user.get('telegram_id'):
        return jsonify({'ok': False, 'error': "Telegram ma'lumotlari yaroqsiz"}), 401

    tg_id = tg_user['telegram_id']
    name = (tg_user['first_name'] + ' ' + tg_user['last_name']).strip() or tg_user['username'] or f'User{tg_id}'
    username = tg_user.get('username') or None
    # initData ichida yoki client yuborgan photo_url
    photo = tg_user.get('photo_url') or data.get('photo_url') or None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT id, name, email, grade, telegram_id, photo_url FROM users WHERE telegram_id = %s',
        (tg_id,)
    )
    row = cur.fetchone()

    if row:
        user_id = row['id']
        # O'quvchi Sozlamalarda o'zgartirgan ism/rasm Telegram'dagisi bilan qayta yozilmaydi
        cur.execute(
            '''UPDATE users SET name = CASE WHEN custom_name = 1 THEN name ELSE %s END,
                                username = %s,
                                tg_photo_url = COALESCE(%s, tg_photo_url),
                                photo_url = CASE WHEN custom_photo = 1 THEN photo_url ELSE COALESCE(%s, photo_url) END
               WHERE id = %s''',
            (name, username, photo, photo, user_id)
        )
        cur.execute('SELECT name, photo_url FROM users WHERE id = %s', (user_id,))
        saved = cur.fetchone()
        conn.commit()
        name, photo = saved['name'], saved['photo_url']
    else:
        cur.execute(
            'INSERT INTO users (name, email, password_hash, telegram_id, username, photo_url, tg_photo_url) '
            'VALUES (%s, NULL, NULL, %s, %s, %s, %s) RETURNING id',
            (name, tg_id, username, photo, photo)
        )
        user_id = cur.fetchone()['id']
        conn.commit()

    cur.close()
    conn.close()

    token = create_token(user_id)
    return jsonify({
        'ok': True,
        'token': token,
        'user': {
            'id': user_id,
            'name': name,
            'email': None,
            'telegram_id': tg_id,
            'username': username,
            'photo_url': photo,
            'grade': (row or {}).get('grade'),
        }
    })


# ───────────────────────────── Frontend (static) ─────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Xizmat ko'rsatiladigan sahifalar. Yangi sahifa qo'shsangiz shu ro'yxatga yozing.
PAGES = {
    'index.html', 'telegram-kerak.html', 'onboarding.html',
    'dashboard.html', 'subjects.html', 'topics.html', 'topic.html',
    'profile.html', 'leaderboard.html', 'game.html', 'games.html', 'daily.html', 'settings.html',
    'admin.html',
}


@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/<page>')
def serve_page(page):
    if page in PAGES:
        return send_from_directory(BASE_DIR, page)
    return jsonify({'ok': False, 'error': 'Sahifa topilmadi'}), 404


@app.route('/assets/<path:filename>')
def assets(filename):
    # Rasm/logo fayllari deyarli hech qachon o'sha nom bilan o'zgarmaydi —
    # brauzer bir kun davomida qayta so'ramasdan keshdan foydalansin.
    return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename, max_age=86400)


@app.route('/js/<path:filename>')
def js_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'js'), filename)


@app.route('/css/<path:filename>')
def css_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'css'), filename)


@app.route('/manifest.json')
def manifest():
    return send_from_directory(BASE_DIR, 'manifest.json')


@app.route('/sw.js')
def service_worker():
    response = send_from_directory(BASE_DIR, 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response


# AI yordamchi endi ai_tutor.py blueprintida (/api/ai/*)


# ───────────────────────────── Telegram bot (webhook) ─────────────────────────────

def send_start_message(chat_id, first_name):
    # parse_mode=HTML — ismdagi <, & kabi belgilar xabarni buzmasligi uchun escape
    name = html.escape(first_name or 'do‘st')
    tg_api('sendMessage', {
        'chat_id': chat_id,
        'text': (
            f'Salom, {name}!\n\n'
            f'<b>BilimSari</b> — bilim olish platformasi.\n'
            f'Kurslar, testlar, XP va streak — hammasi Telegram ichida.\n\n'
            f'Pastdagi tugma orqali ilovani oching.'
        ),
        'parse_mode': 'HTML',
        'reply_markup': {
            'inline_keyboard': [[
                {
                    'text': 'Boshlash',
                    'web_app': {'url': WEBAPP_URL},
                }
            ]]
        },
    })


def send_room_invite(chat_id, first_name, code):
    """Do'st yuborgan taklif havolasi orqali kelganda — roomga to'g'ridan-to'g'ri kirish."""
    name = html.escape(first_name or 'do‘st')
    tg_api('sendMessage', {
        'chat_id': chat_id,
        'text': (
            f'Salom, {name}!\n\n'
            f'Sizni <b>BilimSari</b>da bilim bellashuviga taklif qilishdi.\n'
            f'Room kodi: <b>{code}</b>\n\n'
            f'Pastdagi tugma orqali roomga qo‘shiling.'
        ),
        'parse_mode': 'HTML',
        'reply_markup': {
            'inline_keyboard': [[
                {
                    'text': 'Roomga qo‘shilish',
                    'web_app': {'url': f"{WEBAPP_URL.rstrip('/')}/games.html?kod={code}"},
                }
            ]]
        },
    })


def send_daily_invite(chat_id, first_name):
    """Kun savoli havolasi (t.me/<bot>?start=kun) yoki /kun buyrug'i."""
    name = html.escape(first_name or 'do‘st')
    tg_api('sendMessage', {
        'chat_id': chat_id,
        'text': (
            f'Salom, {name}!\n\n'
            f'<b>Kun savoli</b> — bugun hamma uchun bitta savol. '
            f'To‘g‘ri va tez javob bering, kunlik reytingga chiqing!'
        ),
        'parse_mode': 'HTML',
        'reply_markup': {
            'inline_keyboard': [[
                {
                    'text': 'Savolni ochish',
                    'web_app': {'url': f"{WEBAPP_URL.rstrip('/')}/daily.html"},
                }
            ]]
        },
    })


def send_help_message(chat_id):
    tg_api('sendMessage', {
        'chat_id': chat_id,
        'text': (
            'Buyruqlar:\n'
            '/start — ilovani ochish\n'
            '/kun — kun savoli\n'
            '/help — yordam\n\n'
            'O‘rganish uchun Boshlash tugmasini bosing.'
        ),
    })


def setup_telegram_bot():
    """Webhook + menu tugmasi — polling kerak emas, 24/7 Flask orqali."""
    if not BOT_TOKEN:
        logger.warning('BOT_TOKEN yo‘q — Telegram webhook o‘rnatilmadi')
        return
    webhook_url = WEBAPP_URL.rstrip('/') + '/telegram/webhook'
    r = tg_api('setWebhook', {
        'url': webhook_url,
        'allowed_updates': ['message'],
        'drop_pending_updates': False,
        'secret_token': WEBHOOK_SECRET,
    })
    logger.info('setWebhook: %s', r)
    tg_api('setMyCommands', {
        'commands': [
            {'command': 'start', 'description': 'Ilovani ochish'},
            {'command': 'kun', 'description': 'Kun savoli'},
            {'command': 'help', 'description': 'Yordam'},
        ]
    })
    tg_api('setChatMenuButton', {
        'menu_button': {
            'type': 'web_app',
            'text': 'BilimSari',
            'web_app': {'url': WEBAPP_URL},
        }
    })


@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != WEBHOOK_SECRET:
        return jsonify({'ok': False}), 403

    data = request.get_json(silent=True) or {}
    message = data.get('message') or {}
    text = (message.get('text') or '').strip()
    chat = message.get('chat') or {}
    chat_id = chat.get('id')
    if not chat_id:
        return jsonify({'ok': True})

    first_name = (message.get('from') or {}).get('first_name') or chat.get('first_name') or ''
    cmd = text.split()[0].split('@')[0] if text else ''

    if cmd in ('/start', '/boshlash'):
        # Taklif havolasi: t.me/<bot>?start=room_AB7K92 → o'sha roomga kirish tugmasi
        payload = text.split()[1] if len(text.split()) > 1 else ''
        room_code = game_rooms.normalize_code(payload[5:]) if payload.lower().startswith('room_') else ''
        if game_rooms.CODE_RE.match(room_code):
            send_room_invite(chat_id, first_name, room_code)
        elif payload.lower() == 'kun':
            send_daily_invite(chat_id, first_name)
        else:
            send_start_message(chat_id, first_name)
    elif cmd == '/kun':
        send_daily_invite(chat_id, first_name)
    elif cmd == '/help':
        send_help_message(chat_id)
    elif text:
        send_start_message(chat_id, first_name)

    return jsonify({'ok': True})


# ───────────────────────────── Start ─────────────────────────────

try:
    init_db()
except Exception:
    logger.exception('DB init ogohlantirish')

try:
    setup_telegram_bot()
except Exception:
    logger.exception('Telegram webhook ogohlantirish')

# Eslatmalar rejalashtiruvchisi (har worker'da fon oqimi; vazifalar bazada egallanadi)
notify.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Debug rejimi endi ATAYLAB yoqilmasa o'chiq — yoqilgan holda Werkzeug
    # HTTP orqali interaktiv Python konsolini ochadi (PIN bilan himoyalangan
    # bo'lsa ham, bu productionda hech qachon yoqilmasligi kerak bo'lgan
    # katta xavf). Ilgari `debug=True` qattiq yozilgan edi va FLASK_DEBUG
    # muhit o'zgaruvchisi hech qanday ta'sir qilmasdi.
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    logger.info('BilimSari API → http://127.0.0.1:%d (debug=%s)', port, debug)
    app.run(host='0.0.0.0', port=port, debug=debug)
