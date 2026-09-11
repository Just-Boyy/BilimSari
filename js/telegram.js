// Telegram Mini App yordamchi
(function () {
  function isTelegram() {
    return !!(window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData);
  }

  function getWebApp() {
    return window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  }

  async function loginWithTelegram() {
    const wa = getWebApp();
    if (!wa || !wa.initData) {
      return { ok: false, error: 'Telegram Mini App emas' };
    }
    try {
      wa.ready();
      wa.expand();
      const res = await fetch('/api/telegram/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: wa.initData })
      });
      const data = await res.json();
      if (data.ok && data.token && data.user) {
        localStorage.setItem('bilimsari_token', data.token);
        localStorage.setItem('bilimsari_user', JSON.stringify(data.user));
      }
      return data;
    } catch (e) {
      return { ok: false, error: 'Telegram orqali kirib bo‘lmadi' };
    }
  }

  /** Sahifa yuklanganda: TG ichida bo‘lsa avtomatik login */
  async function autoAuthIfTelegram() {
    if (!isTelegram()) return false;
    const existing = localStorage.getItem('bilimsari_token');
    if (existing) {
      const wa = getWebApp();
      if (wa) { wa.ready(); wa.expand(); }
      return true;
    }
    const result = await loginWithTelegram();
    return !!(result && result.ok);
  }

  window.BilimSariTG = {
    isTelegram,
    getWebApp,
    loginWithTelegram,
    autoAuthIfTelegram,
  };
})();
