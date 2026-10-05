// Telegram Mini App yordamchi
(function () {
  function isTelegram() {
    return !!(window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData);
  }

  /** Telegram ichida ochilganmizmi — skript yuklanmagan bo'lsa ham (URL, iOS proksi, oldingi sahifa xotirasi). */
  function telegramBelgisi() {
    try {
      if (/tgWebApp(Data|Platform|Version)=/.test(location.hash || '')) return true;
      if (window.TelegramWebviewProxy) return true;
      if (/tgWebAppData/.test(sessionStorage.getItem('__telegram__initParams') || '')) return true;
    } catch (e) {}
    return false;
  }

  // telegram.org skripti kelmasa (iPhone'da birinchi ochilishda sekin/uzilgan internet) — o'zimizdagi nusxa
  var zaxiraYuklandi = false;
  function zaxiraYukla() {
    if (zaxiraYuklandi || (window.Telegram && window.Telegram.WebApp)) return;
    zaxiraYuklandi = true;
    var s = document.createElement('script');
    s.src = '/js/telegram-web-app.js';
    document.head.appendChild(s);
  }

  /** Telegram ma'lumoti (initData) tayyor bo'lguncha kutadi. Telegram belgisi bo'lmasa — qisqa kutish. */
  function tayyor(maxMs) {
    maxMs = maxMs || 8000;
    return new Promise(function (resolve) {
      if (isTelegram()) return resolve(true);
      if (!telegramBelgisi()) maxMs = Math.min(maxMs, 1500);
      var t0 = Date.now();
      (function tekshir() {
        if (isTelegram()) return resolve(true);
        var o_tdi = Date.now() - t0;
        if (o_tdi >= 300) zaxiraYukla();
        if (o_tdi >= maxMs) return resolve(false);
        setTimeout(tekshir, 100);
      })();
    });
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
      // O'quvchi Sozlamalarda o'z rasmini yuklagan bo'lsa — Telegram rasmi uni almashtirmaydi
      if (user.photo_url === photoUrl || String(user.photo_url || '').indexOf('/api/photo/') === 0) return;
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
      // Kirish — ilova ochilganda birinchi so'rov: uzilsa 2 marta qayta urinamiz (takroriy kirish zararsiz)
      const f = (window.API && API.ishonchliFetch) ? function (u, o) { return API.ishonchliFetch(u, o, 2); } : fetch;
      const res = await f('/api/telegram/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          initData: wa.initData,
          photo_url: tgUser && tgUser.photo_url ? tgUser.photo_url : null
        })
      });
      const data = await res.json();
      // Admin yangi o'quvchilar qabulini yopgan — tushunarli oyna
      if (data && data.code === 'registration_closed' && window.API && API.holatOyna) API.holatOyna(data);
      if (data.ok && data.token && data.user) {
        // Prefer server photo, else Telegram client photo
        if (!data.user.photo_url && !data.user.custom_photo && tgUser && tgUser.photo_url) {
          data.user.photo_url = tgUser.photo_url;
        }
        localStorage.setItem('bilimsari_token', data.token);
        localStorage.setItem('bilimsari_user', JSON.stringify(data.user));
        // Boshqa qurilmada tanlangan interfeys tili
        if (window.I18N && data.user.lang) I18N.moslash(data.user.lang);
      }
      return data;
    } catch (e) {
      return { ok: false, error: 'Telegram orqali kirib bo‘lmadi' };
    }
  }

  /** Sahifa yuklanganda: TG ichida bo‘lsa avtomatik login + rasm yangilash */
  async function autoAuthIfTelegram() {
    if (!(await tayyor())) return false;
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
    telegramBelgisi: telegramBelgisi,
    tayyor: tayyor,
    getWebApp: getWebApp,
    getTelegramUser: getTelegramUser,
    loginWithTelegram: loginWithTelegram,
    autoAuthIfTelegram: autoAuthIfTelegram,
  };
})();
