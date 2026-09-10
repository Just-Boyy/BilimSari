// BilimSari — oddiy auth (localStorage)
// Keyinchalik backend bilan almashtirish oson

const AUTH_KEY = 'bilimsari_users';
const SESSION_KEY = 'bilimsari_session';

function getUsers() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_KEY)) || [];
  } catch {
    return [];
  }
}

function saveUsers(users) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(users));
}

function getSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY));
  } catch {
    return null;
  }
}

function setSession(user) {
  localStorage.setItem(SESSION_KEY, JSON.stringify({
    email: user.email,
    name: user.name,
    loggedAt: Date.now()
  }));
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

function isLoggedIn() {
  return !!getSession();
}

function register(name, email, password) {
  email = email.trim().toLowerCase();
  name = name.trim();

  if (!name || name.length < 2) {
    return { ok: false, error: 'Ism kamida 2 ta belgidan iborat bo‘lsin' };
  }
  if (!email || !email.includes('@')) {
    return { ok: false, error: 'Email noto‘g‘ri' };
  }
  if (!password || password.length < 6) {
    return { ok: false, error: 'Parol kamida 6 ta belgidan iborat bo‘lsin' };
  }

  const users = getUsers();
  if (users.find(u => u.email === email)) {
    return { ok: false, error: 'Bu email allaqachon ro‘yxatdan o‘tgan' };
  }

  const user = { name, email, password, createdAt: Date.now() };
  users.push(user);
  saveUsers(users);
  setSession(user);

  return { ok: true, user };
}

function login(email, password) {
  email = email.trim().toLowerCase();

  if (!email || !password) {
    return { ok: false, error: 'Email va parolni kiriting' };
  }

  const users = getUsers();
  const user = users.find(u => u.email === email);

  if (!user) {
    return { ok: false, error: 'Bunday foydalanuvchi topilmadi' };
  }
  if (user.password !== password) {
    return { ok: false, error: 'Parol noto‘g‘ri' };
  }

  setSession(user);
  return { ok: true, user };
}

function logout() {
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
    window.location.href = 'dashboard.html';
  }
}
