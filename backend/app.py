"""
BilimSari Backend — Flask + PostgreSQL
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib
import secrets
import os
import json
import urllib.request
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

SECRET = os.environ.get('SECRET_KEY', 'bilimsari-dev-secret-change-me')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8994766252:AAG_wqhRFHJNx447MmyqWAYsbzGD88kReVE')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://bilimsari-production.up.railway.app')



# ───────────────────────────── Database ─────────────────────────────

def get_connection():
    """PostgreSQL ulanishi (Railway DATABASE_URL orqali)"""
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        raise RuntimeError(
            'DATABASE_URL topilmadi. Railway’da PostgreSQL qo‘shing '
            'yoki lokalda DATABASE_URL o‘rnating.'
        )

    # Railway ba’zan postgres:// beradi, psycopg2 postgresql:// kutadi
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    return conn


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
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_id BIGINT UNIQUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_url TEXT",
    ]:
        try:
            cur.execute(stmt)
            conn.commit()
        except Exception:
            conn.rollback()

    # Fanlar (courses) jadvallari + seed
    try:
        from seed_courses import seed_courses
        seed_courses(cur, conn)
    except Exception as e:
        print(f'Course seed xato: {e}')
        conn.rollback()

    conn.commit()
    cur.close()
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256((password + SECRET).encode()).hexdigest()


def create_token(user_id: int) -> str:
    token = secrets.token_hex(32)
    expires = datetime.utcnow() + timedelta(days=7)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO tokens (token, user_id, expires_at) VALUES (%s, %s, %s)',
        (token, user_id, expires)
    )
    conn.commit()
    cur.close()
    conn.close()
    return token


def get_user_by_token(token: str):
    if not token:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT u.id, u.name, u.email
        FROM tokens t
        JOIN users u ON u.id = t.user_id
        WHERE t.token = %s AND t.expires_at > NOW()
    ''', (token,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '').strip() if auth.startswith('Bearer ') else None
        user = get_user_by_token(token)
        if not user:
            return jsonify({'ok': False, 'error': 'Avtorizatsiya talab qilinadi'}), 401
        request.user = user
        return f(*args, **kwargs)
    return decorated


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
        'SELECT id, name, email, password_hash FROM users WHERE email = %s',
        (email,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({'ok': False, 'error': 'Bunday foydalanuvchi topilmadi'}), 401

    if user['password_hash'] != hash_password(password):
        return jsonify({'ok': False, 'error': 'Parol noto‘g‘ri'}), 401

    token = create_token(user['id'])
    return jsonify({
        'ok': True,
        'token': token,
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}
    })


@app.route('/api/me', methods=['GET'])
@auth_required
def me():
    return jsonify({'ok': True, 'user': request.user})


@app.route('/api/logout', methods=['POST'])
@auth_required
def logout():
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '').strip()
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
        'SELECT id, name, email, telegram_id, photo_url FROM users WHERE telegram_id = %s',
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


# ───────────────────────────── Frontend (static) ─────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/index.html')
def index_page():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/login.html')
def login_page():
    return send_from_directory(BASE_DIR, 'login.html')


@app.route('/register.html')
def register_page():
    return send_from_directory(BASE_DIR, 'register.html')


@app.route('/dashboard.html')
def dashboard_page():
    return send_from_directory(BASE_DIR, 'dashboard.html')


@app.route('/learn.html')
def learn_page():
    return send_from_directory(BASE_DIR, 'learn.html')


@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename)




@app.route('/lesson.html')
def lesson_page():
    return send_from_directory(BASE_DIR, 'lesson.html')



@app.route('/courses.html')
def courses_page():
    return send_from_directory(BASE_DIR, 'courses.html')



@app.route('/profile.html')
def profile_page():
    return send_from_directory(BASE_DIR, 'profile.html')



@app.route('/leaderboard.html')
def leaderboard_page():
    return send_from_directory(BASE_DIR, 'leaderboard.html')



@app.route('/review.html')
def review_page():
    return send_from_directory(BASE_DIR, 'review.html')

@app.route('/js/<path:filename>')
def js_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'js'), filename)


@app.route('/manifest.json')
def manifest():
    return send_from_directory(BASE_DIR, 'manifest.json')


@app.route('/sw.js')
def service_worker():
    response = send_from_directory(BASE_DIR, 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response



# ───────────────────────────── AI Tutor ─────────────────────────────

XAI_API_KEY = os.environ.get('XAI_API_KEY') or os.environ.get('GROK_API_KEY') or ''
XAI_BASE = os.environ.get('XAI_API_BASE', 'https://api.x.ai/v1')
XAI_MODEL = os.environ.get('XAI_MODEL', 'grok-3-mini')

def ai_system_prompt(lang: str) -> str:
    if lang == 'ru':
        return (
            'Ты дружелюбный репетитор BilimSari для школьников. '
            'Отвечай кратко, понятно, на русском. Помогай с предметами: '
            'математика, языки, биология и др. Не давай вредных советов. '
            'Если вопрос не об учёбе — вежливо верни к теме обучения.'
        )
    if lang == 'en':
        return (
            'You are a friendly BilimSari tutor for students. '
            'Answer briefly and clearly in English. Help with school subjects. '
            'Stay educational and safe. If off-topic, gently return to learning.'
        )
    return (
        'Sen BilimSari platformasidagi do‘stona o‘qituvchi yordamchisan. '
        'O‘quvchilarga qisqa, tushunarli, o‘zbek tilida javob ber. '
        'Maktab fanlari: matematika, tillar, biologiya va boshqalar. '
        'Zararli maslahat berma. Mavzudan tashqari bo‘lsa, o‘qishga qaytar.'
    )


@app.route('/api/ai/tutor', methods=['POST'])
def ai_tutor():
    """AI o'qituvchi — savol / tushuntirish"""
    import requests as http_requests

    body = request.get_json(silent=True) or {}
    message = (body.get('message') or '').strip()
    lang = (body.get('lang') or 'uz')[:5]
    context = (body.get('context') or '').strip()  # savol, javob, fan

    if not message:
        return jsonify({'ok': False, 'error': 'Xabar bo‘sh'}), 400
    if len(message) > 2000:
        return jsonify({'ok': False, 'error': 'Xabar juda uzun'}), 400

    if not XAI_API_KEY:
        return jsonify({
            "ok": False,
            "error": "AI ulanmagan. Railway Variables ga XAI_API_KEY qoshin.",
            "reply": None,
        }), 503

    user_content = message
    if context:
        user_content = f'Mavzu/kontekst:\n{context}\n\nO‘quvchi:\n{message}'

    try:
        r = http_requests.post(
            f'{XAI_BASE.rstrip("/")}/chat/completions',
            headers={
                'Authorization': f'Bearer {XAI_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': XAI_MODEL,
                'messages': [
                    {'role': 'system', 'content': ai_system_prompt(lang)},
                    {'role': 'user', 'content': user_content},
                ],
                'temperature': 0.6,
                'max_tokens': 600,
            },
            timeout=45,
        )
        if r.status_code != 200:
            detail = ''
            try:
                err_json = r.json()
                detail = err_json.get('error') or err_json.get('message') or str(err_json)
                if isinstance(detail, dict):
                    detail = detail.get('message') or str(detail)
            except Exception:
                detail = (r.text or '')[:300]
            return jsonify({
                'ok': False,
                'error': f'AI xato {r.status_code}: {detail}',
                'reply': None,
            }), 502
        data = r.json()
        reply = (
            data.get('choices', [{}])[0]
            .get('message', {})
            .get('content', '')
            .strip()
        )
        if not reply:
            return jsonify({'ok': False, 'error': 'Bosh javob', 'reply': None}), 502
        return jsonify({'ok': True, 'reply': reply})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e), 'reply': None}), 500


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
