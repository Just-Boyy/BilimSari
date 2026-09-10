"""
BilimSari Backend — Flask + SQLite
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Vercel va boshqa frontendlar uchun

DB_PATH = os.path.join(os.path.dirname(__file__), 'bilimsari.db')
SECRET = os.environ.get('SECRET_KEY', 'bilimsari-dev-secret-change-me')


# ───────────────────────────── Database ─────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256((password + SECRET).encode()).hexdigest()


def create_token(user_id: int) -> str:
    token = secrets.token_hex(32)
    expires = (datetime.utcnow() + timedelta(days=7)).isoformat()
    conn = get_db()
    conn.execute(
        'INSERT INTO tokens (token, user_id, expires_at) VALUES (?, ?, ?)',
        (token, user_id, expires)
    )
    conn.commit()
    conn.close()
    return token


def get_user_by_token(token: str):
    if not token:
        return None
    conn = get_db()
    row = conn.execute('''
        SELECT u.id, u.name, u.email
        FROM tokens t
        JOIN users u ON u.id = t.user_id
        WHERE t.token = ? AND t.expires_at > ?
    ''', (token, datetime.utcnow().isoformat())).fetchone()
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
    return jsonify({'ok': True, 'service': 'BilimSari API'})


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

    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'ok': False, 'error': 'Bu email allaqachon ro‘yxatdan o‘tgan'}), 400

    pw_hash = hash_password(password)
    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        'INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
        (name, email, pw_hash, now)
    )
    user_id = cur.lastrowid
    conn.commit()
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

    conn = get_db()
    user = conn.execute(
        'SELECT id, name, email, password_hash FROM users WHERE email = ?',
        (email,)
    ).fetchone()
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
    conn = get_db()
    conn.execute('DELETE FROM tokens WHERE token = ?', (token,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# ───────────────────────────── Start ─────────────────────────────

# Gunicorn va lokal ishga tushirishda ham DB tayyor bo‘lsin
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'BilimSari API ishga tushdi → http://127.0.0.1:{port}')
    app.run(host='0.0.0.0', port=port, debug=True)
