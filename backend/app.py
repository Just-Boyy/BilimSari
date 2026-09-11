"""
BilimSari Backend — Flask + PostgreSQL
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

SECRET = os.environ.get('SECRET_KEY', 'bilimsari-dev-secret-change-me')


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
    bot_token = os.environ.get('BOT_TOKEN', '')

    if not bot_token:
        return jsonify({'ok': False, 'error': 'BOT_TOKEN sozlanmagan'}), 500

    tg_user = validate_init_data(init_data, bot_token)
    if not tg_user or not tg_user.get('telegram_id'):
        return jsonify({'ok': False, 'error': "Telegram ma'lumotlari yaroqsiz"}), 401

    tg_id = tg_user['telegram_id']
    name = (tg_user['first_name'] + ' ' + tg_user['last_name']).strip() or tg_user['username'] or f'User{tg_id}'
    username = tg_user.get('username') or None
    photo = tg_user.get('photo_url') or None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT id, name, email, telegram_id FROM users WHERE telegram_id = %s',
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

# ───────────────────────────── Start ─────────────────────────────

try:
    init_db()
except Exception as e:
    print(f'DB init ogohlantirish: {e}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'BilimSari API → http://127.0.0.1:{port}')
    app.run(host='0.0.0.0', port=port, debug=True)
