"""
BilimSari Backend — Flask + PostgreSQL
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import urllib.request

import ai_tutor
import study
import study_api
from auth_core import (
    SECRET,
    auth_required,
    create_token,
    hash_password,
    needs_rehash,
    token_from_request,
    verify_password,
)
from db import add_column_if_missing, get_connection

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.register_blueprint(study_api.bp)
app.register_blueprint(ai_tutor.bp)

# BOT_TOKEN faqat muhit o'zgaruvchisidan olinadi — kodda saqlanmaydi.
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://bilimsari-production.up.railway.app')


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT,
            telegram_id BIGINT UNIQUE,
            username TEXT,
            photo_url TEXT,
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
    ]:
        add_column_if_missing(cur, conn, 'users', column, ddl)

    # Yangi o'quv tizimi: subjects / topics / user_progress + curriculum sinxroni
    try:
        study.ensure_tables(cur, conn)
        written = study.sync_curriculum(cur, conn)
        if written:
            print(f'Curriculum sinxronlandi: {written} ta mavzu')
    except Exception as e:
        print(f'Study jadvallari xatosi: {e}')
        conn.rollback()

    # Eski AI-darslar tizimi (saqlanib qoldi, ixtiyoriy qo'shimcha sifatida)
    try:
        from lesson_ai import ensure_ai_tables
        ensure_ai_tables(cur, conn)
    except Exception as e:
        print(f'AI lessons table xato: {e}')
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


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if len(name) < 2:
        return jsonify({'ok': False, 'error': 'Ism kamida 2 ta belgidan iborat bo‘lsin'}), 400
    if '@' not in email:
        return jsonify({'ok': False, 'error': 'Email noto‘g‘ri'}), 400
    if len(password) < 6:
        return jsonify({'ok': False, 'error': 'Parol kamida 6 ta belgidan iborat bo‘lsin'}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute('SELECT id FROM users WHERE email = %s', (email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'ok': False, 'error': 'Bu email allaqachon ro‘yxatdan o‘tgan'}), 400

    pw_hash = hash_password(password)
    cur.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id',
        (name, email, pw_hash)
    )
    user_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()

    token = create_token(user_id)
    return jsonify({
        'ok': True,
        'token': token,
        'user': {'id': user_id, 'name': name, 'email': email}
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'ok': False, 'error': 'Email va parolni kiriting'}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT id, name, email, grade, password_hash FROM users WHERE email = %s',
        (email,)
    )
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        return jsonify({'ok': False, 'error': 'Bunday foydalanuvchi topilmadi'}), 401

    if not verify_password(password, user['password_hash']):
        cur.close()
        conn.close()
        return jsonify({'ok': False, 'error': 'Parol noto‘g‘ri'}), 401

    # Eski sha256 hash — kirish paytida yangi formatga ko'chiramiz
    if needs_rehash(user['password_hash']):
        cur.execute(
            'UPDATE users SET password_hash = %s WHERE id = %s',
            (hash_password(password), user['id'])
        )
        conn.commit()

    cur.close()
    conn.close()

    token = create_token(user['id'])
    return jsonify({
        'ok': True,
        'token': token,
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email'],
                 'grade': user.get('grade')}
    })


@app.route('/api/me', methods=['GET'])
@auth_required
def me():
    return jsonify({'ok': True, 'user': request.user})


@app.route('/api/logout', methods=['POST'])
@auth_required
def logout():
    token = token_from_request()
    conn = get_connection()
    cur = conn.cursor()
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
        cur.execute(
            'UPDATE users SET name = %s, username = %s, photo_url = COALESCE(%s, photo_url) WHERE id = %s',
            (name, username, photo, user_id)
        )
        conn.commit()
        # Javobda eng so‘nggi rasm
        photo = photo or row.get('photo_url')
    else:
        cur.execute(
            'INSERT INTO users (name, email, password_hash, telegram_id, username, photo_url) '
            'VALUES (%s, NULL, NULL, %s, %s, %s) RETURNING id',
            (name, tg_id, username, photo)
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


@app.route('/api/courses', methods=['GET'])
def api_courses():
    """Barcha fanlar (units + lessons bilan)"""
    try:
        from seed_courses import fetch_courses_tree, seed_courses
        conn = get_connection()
        cur = conn.cursor()
        seed_courses(cur, conn)  # bo‘sh bo‘lsa to‘ldiradi
        courses = fetch_courses_tree(cur)
        cur.close()
        conn.close()
        return jsonify({'ok': True, 'courses': courses})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e), 'courses': []}), 500


@app.route('/api/courses/<course_id>', methods=['GET'])
def api_course_one(course_id):
    try:
        from seed_courses import fetch_courses_tree, seed_courses
        conn = get_connection()
        cur = conn.cursor()
        seed_courses(cur, conn)
        courses = fetch_courses_tree(cur)
        cur.close()
        conn.close()
        course = next((c for c in courses if c['id'] == course_id), None)
        if not course:
            return jsonify({'ok': False, 'error': 'Fan topilmadi'}), 404
        return jsonify({'ok': True, 'course': course})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500



@app.route('/api/path/<course_id>', methods=['GET'])
def api_learning_path(course_id):
    """Tanlangan fan bo'yicha AI+DB darslar ro'yxati"""
    try:
        from lesson_ai import ensure_ai_tables, list_lessons, ensure_min_lessons, COURSE_META
        conn = get_connection()
        cur = conn.cursor()
        ensure_ai_tables(cur, conn)
        # kamida 1 dars
        err = ensure_min_lessons(cur, conn, course_id, minimum=1)
        lessons = list_lessons(cur, course_id)
        cur.close()
        conn.close()
        meta = COURSE_META.get(course_id, {'name': course_id})
        return jsonify({
            'ok': True,
            'course_id': course_id,
            'course_name': meta.get('name', course_id),
            'lessons': [
                {
                    'id': f'{course_id}-ai-{L["seq"]}',
                    'seq': L['seq'],
                    'title': L['title'],
                    'unit_title': L.get('unit_title') or '',
                    'type': 'lesson',
                }
                for L in lessons
            ],
            'error_gen': err,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e), 'lessons': []}), 500


@app.route('/api/lessons/next', methods=['POST'])
def api_lesson_next():
    """Keyingi darsni DB dan ol yoki AI bilan yaratib saqla"""
    body = request.get_json(silent=True) or {}
    course_id = (body.get('course_id') or '').strip()
    if not course_id:
        return jsonify({'ok': False, 'error': 'course_id kerak'}), 400
    try:
        from lesson_ai import get_or_create_next_lesson, ensure_ai_tables
        conn = get_connection()
        cur = conn.cursor()
        ensure_ai_tables(cur, conn)
        lesson, err = get_or_create_next_lesson(cur, conn, course_id)
        cur.close()
        conn.close()
        if err:
            return jsonify({'ok': False, 'error': err}), 502
        qs = lesson.get('questions')
        if isinstance(qs, str):
            import json as _json
            qs = _json.loads(qs)
        return jsonify({
            'ok': True,
            'lesson': {
                'id': f'{course_id}-ai-{lesson["seq"]}',
                'seq': lesson['seq'],
                'title': lesson['title'],
                'unit_title': lesson.get('unit_title') or '',
                'questions': qs,
            }
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/lessons/<course_id>/<int:seq>', methods=['GET'])
def api_lesson_get(course_id, seq):
    """Bitta dars + savollar (DB)"""
    try:
        from lesson_ai import get_lesson, ensure_ai_tables
        import json as _json
        conn = get_connection()
        cur = conn.cursor()
        ensure_ai_tables(cur, conn)
        lesson = get_lesson(cur, course_id, seq)
        cur.close()
        conn.close()
        if not lesson:
            return jsonify({'ok': False, 'error': 'Dars topilmadi'}), 404
        qs = lesson.get('questions')
        if isinstance(qs, str):
            qs = _json.loads(qs)
        return jsonify({
            'ok': True,
            'lesson': {
                'id': f'{course_id}-ai-{lesson["seq"]}',
                'seq': lesson['seq'],
                'title': lesson['title'],
                'unit_title': lesson.get('unit_title') or '',
                'questions': qs,
            }
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# ───────────────────────────── Frontend (static) ─────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Xizmat ko'rsatiladigan sahifalar. Yangi sahifa qo'shsangiz shu ro'yxatga yozing.
PAGES = {
    'index.html', 'login.html', 'register.html', 'onboarding.html',
    'dashboard.html', 'subjects.html', 'topics.html', 'topic.html',
    'progress.html', 'profile.html', 'leaderboard.html',
    # eski (AI-darslar) oqimi — ishlashda davom etadi
    'learn.html', 'lesson.html', 'courses.html', 'review.html',
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
    return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename)


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

def tg_api(method, payload):
    if not BOT_TOKEN:
        return None
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/{method}'
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f'Telegram API xato {method}: {e}')
        return None


def send_start_message(chat_id, first_name):
    name = first_name or 'do‘st'
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


def send_help_message(chat_id):
    tg_api('sendMessage', {
        'chat_id': chat_id,
        'text': (
            'Buyruqlar:\n'
            '/start — ilovani ochish\n'
            '/help — yordam\n\n'
            'O‘rganish uchun Boshlash tugmasini bosing.'
        ),
    })


def setup_telegram_bot():
    """Webhook + menu tugmasi — polling kerak emas, 24/7 Flask orqali."""
    if not BOT_TOKEN:
        print('BOT_TOKEN yo‘q — Telegram webhook o‘rnatilmadi')
        return
    webhook_url = WEBAPP_URL.rstrip('/') + '/telegram/webhook'
    r = tg_api('setWebhook', {
        'url': webhook_url,
        'allowed_updates': ['message'],
        'drop_pending_updates': False,
    })
    print('setWebhook:', r)
    tg_api('setMyCommands', {
        'commands': [
            {'command': 'start', 'description': 'Ilovani ochish'},
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
        send_start_message(chat_id, first_name)
    elif cmd == '/help':
        send_help_message(chat_id)
    elif text:
        send_start_message(chat_id, first_name)

    return jsonify({'ok': True})


# ───────────────────────────── Start ─────────────────────────────

try:
    init_db()
except Exception as e:
    print(f'DB init ogohlantirish: {e}')

try:
    setup_telegram_bot()
except Exception as e:
    print(f'Telegram webhook ogohlantirish: {e}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'BilimSari API → http://127.0.0.1:{port}')
    app.run(host='0.0.0.0', port=port, debug=True)
