// Telegram Mini App yordamchi
(function () {
  function isTelegram() {
    return !!(window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData);
  }

  function getWebApp() {
    return window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  }

  /** Telegramdan user (ism, rasm va hokazo) */
  function getTelegramUser() {
    const wa = getWebApp();
    if (!wa) return null;
    try {
      const u = (wa.initDataUnsafe && wa.initDataUnsafe.user) || null;
      if (!u) return null;
      return {
        id: u.id,
        first_name: u.first_name || '',
        last_name: u.last_name || '',
        username: u.username || '',
        language_code: u.language_code || '',
        photo_url: u.photo_url || null,
      };
    } catch (e) {
      return null;
    }
  }

  function mergePhotoIntoStoredUser(photoUrl) {
    if (!photoUrl) return;
    try {
      const raw = localStorage.getItem('bilimsari_user');
      const user = raw ? JSON.parse(raw) : {};
      if (user.photo_url === photoUrl) return;
      user.photo_url = photoUrl;
      localStorage.setItem('bilimsari_user', JSON.stringify(user));
    } catch (e) {}
  }

  async function loginWithTelegram() {
    const wa = getWebApp();
    if (!wa || !wa.initData) {
      return { ok: false, error: 'Telegram Mini App emas' };
    }
    try {
      wa.ready();
      wa.expand();
      const tgUser = getTelegramUser();
      const res = await fetch('/api/telegram/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          initData: wa.initData,
          photo_url: tgUser && tgUser.photo_url ? tgUser.photo_url : null
        })
      });
      const data = await res.json();
      if (data.ok && data.token && data.user) {
        // Prefer server photo, else Telegram client photo
        if (!data.user.photo_url && tgUser && tgUser.photo_url) {
          data.user.photo_url = tgUser.photo_url;
        }
        localStorage.setItem('bilimsari_token', data.token);
        localStorage.setItem('bilimsari_user', JSON.stringify(data.user));
      }
      return data;
    } catch (e) {
      return { ok: false, error: 'Telegram orqali kirib bo‘lmadi' };
    }
  }

  /** Sahifa yuklanganda: TG ichida bo‘lsa avtomatik login + rasm yangilash */
  async function autoAuthIfTelegram() {
    if (!isTelegram()) return false;
    const wa = getWebApp();
    if (wa) {
      try { wa.ready(); wa.expand(); } catch (e) {}
    }
    const tgUser = getTelegramUser();
    if (tgUser && tgUser.photo_url) {
      mergePhotoIntoStoredUser(tgUser.photo_url);
    }

    const existing = localStorage.getItem('bilimsari_token');
    if (existing) {
      // Token bor — lekin rasm/ism yangilanishi uchun authni yangilab qo‘yamiz
      try {
        const data = await loginWithTelegram();
        return !!(data && data.ok);
      } catch (e) {
        return true;
      }
    }
    const result = await loginWithTelegram();
    return !!(result && result.ok);
  }

  window.BilimSariTG = {
    isTelegram: isTelegram,
    getWebApp: getWebApp,
    getTelegramUser: getTelegramUser,
    loginWithTelegram: loginWithTelegram,
    autoAuthIfTelegram: autoAuthIfTelegram,
  };
})();
