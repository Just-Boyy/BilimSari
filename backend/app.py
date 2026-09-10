"""
BilimSari Backend — Flask + PostgreSQL
"""

from flask import Flask, request, jsonify
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
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
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


# ───────────────────────────── Start ─────────────────────────────

try:
    init_db()
except Exception as e:
    print(f'DB init ogohlantirish: {e}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'BilimSari API → http://127.0.0.1:{port}')
    app.run(host='0.0.0.0', port=port, debug=True)
