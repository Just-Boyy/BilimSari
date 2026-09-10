// BilimSari Auth — Backend API bilan ishlaydi

const API_URL = '/api';
const TOKEN_KEY = 'bilimsari_token';
const USER_KEY = 'bilimsari_user';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getSession() {
  try {
    const user = JSON.parse(localStorage.getItem(USER_KEY));
    const token = getToken();
    if (user && token) return { ...user, token };
    return null;
  } catch {
    return null;
  }
}

function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function isLoggedIn() {
  return !!getToken();
}

async function register(name, email, password) {
  try {
    const res = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    });
    const data = await res.json();
    if (data.ok) {
      setSession(data.token, data.user);
    }
    return data;
  } catch (err) {
    return { ok: false, error: 'Serverga ulanib bo‘lmadi. Backend ishlayaptimi?' };
  }
}

async function login(email, password) {
  try {
    const res = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.ok) {
      setSession(data.token, data.user);
    }
    return data;
  } catch (err) {
    return { ok: false, error: 'Serverga ulanib bo‘lmadi. Backend ishlayaptimi?' };
  }
}

async function logout() {
  const token = getToken();
  if (token) {
    try {
      await fetch(`${API_URL}/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (_) {}
  }
  clearSession();
  window.location.href = 'login.html';
}

function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = 'login.html';
  }
}

function redirectIfLoggedIn() {
  if (isLoggedIn()) {
    window.location.href = 'learn.html';
  }
}
