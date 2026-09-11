// BilimSari Auth — Telegram / onboarding asosiy, email ixtiyoriy

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

function isTelegramEnv() {
  try {
    return !!(window.Telegram && Telegram.WebApp && Telegram.WebApp.initData);
  } catch {
    return false;
  }
}

/** Onboarding ismi yoki Telegram orqali sessiya */
async function ensureSession() {
  if (isLoggedIn()) return true;

  // 1) Telegram Mini App
  if (window.BilimSariTG && typeof BilimSariTG.autoAuthIfTelegram === 'function') {
    try {
      const ok = await BilimSariTG.autoAuthIfTelegram();
      if (ok && isLoggedIn()) return true;
    } catch (_) {}
  }

  // 2) Onboardingda kiritilgan ism (login so‘ralmaydi)
  let name = localStorage.getItem('bs_display_name') || '';
  try {
    const ob = JSON.parse(localStorage.getItem('bs_onboarding_v1') || 'null');
    if (ob && ob.name) name = ob.name;
  } catch (_) {}

  // Telegram ismi (initDataUnsafe)
  if (!name && isTelegramEnv()) {
    try {
      const u = Telegram.WebApp.initDataUnsafe && Telegram.WebApp.initDataUnsafe.user;
      if (u) {
        name = ((u.first_name || '') + ' ' + (u.last_name || '')).trim() || u.username || '';
      }
    } catch (_) {}
  }

  if (name) {
    setSession('local_' + Date.now(), {
      id: 0,
      name: name,
      guest: true,
      source: isTelegramEnv() ? 'telegram' : 'onboarding'
    });
    return true;
  }

  return false;
}

async function register(name, email, password) {
  try {
    const res = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    });
    const data = await res.json();
    if (data.ok) setSession(data.token, data.user);
    return data;
  } catch (err) {
    return { ok: false, error: 'Serverga ulanib bo‘lmadi.' };
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
    if (data.ok) setSession(data.token, data.user);
    return data;
  } catch (err) {
    return { ok: false, error: 'Serverga ulanib bo‘lmadi.' };
  }
}

async function logout() {
  const token = getToken();
  if (token && !String(token).startsWith('local_')) {
    try {
      await fetch(`${API_URL}/logout`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (_) {}
  }
  clearSession();
  localStorage.removeItem('bs_onboarding_v1');
  window.location.href = 'index.html';
}

/** Login sahifasiga yubormaydi — TG/onboarding yetarli */
function requireAuth() {
  if (isLoggedIn()) return;

  // Sinxron holat: sessiya yo‘q
  if (isTelegramEnv()) {
    // Async auth ishlaydi; login.html ga YO‘NALTIRILMAYDI
    window.location.replace('index.html');
    return;
  }

  // Brauzerda ham onboarding bor bo‘lsa — index
  try {
    const ob = JSON.parse(localStorage.getItem('bs_onboarding_v1') || 'null');
    if (ob && ob.done) {
      window.location.replace('index.html');
      return;
    }
  } catch (_) {}

  window.location.replace('index.html');
}

function redirectIfLoggedIn() {
  if (isLoggedIn()) {
    const course = localStorage.getItem('bs_current_course');
    window.location.href = course ? ('learn.html?course=' + encodeURIComponent(course)) : 'index.html';
  }
}
