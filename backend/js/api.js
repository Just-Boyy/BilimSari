/* BilimSari — API klienti va sessiya.
   Barcha so'rovlar shu yerdan o'tadi, token avtomatik qo'shiladi. */
(function () {
  var TOKEN_KEY = 'bilimsari_token';
  var USER_KEY = 'bilimsari_user';

  function saqlash(kalit, qiymat) {
    try { localStorage.setItem(kalit, qiymat); } catch (e) {}
  }
  function o_qish(kalit) {
    try { return localStorage.getItem(kalit); } catch (e) { return null; }
  }
  function o_chirish(kalit) {
    try { localStorage.removeItem(kalit); } catch (e) {}
  }

  function token() { return o_qish(TOKEN_KEY); }

  function user() {
    try { return JSON.parse(o_qish(USER_KEY) || 'null'); } catch (e) { return null; }
  }

  function sessiyaOchish(t, u) {
    saqlash(TOKEN_KEY, t);
    saqlash(USER_KEY, JSON.stringify(u || {}));
  }

  function sessiyaYopish() {
    o_chirish(TOKEN_KEY);
    o_chirish(USER_KEY);
  }

  function userYangilash(yangi) {
    var joriy = user() || {};
    Object.keys(yangi || {}).forEach(function (k) { joriy[k] = yangi[k]; });
    saqlash(USER_KEY, JSON.stringify(joriy));
    return joriy;
  }

  /** Asosiy so'rov funksiyasi. Xatoda {ok:false, error} qaytaradi, tashlamaydi. */
  async function so_rov(yo_l, sozlama) {
    sozlama = sozlama || {};
    var bosh = { 'Content-Type': 'application/json' };
    var t = token();
    if (t) bosh['Authorization'] = 'Bearer ' + t;

    var javob;
    try {
      javob = await fetch(yo_l, {
        method: sozlama.method || 'GET',
        headers: bosh,
        body: sozlama.body ? JSON.stringify(sozlama.body) : undefined,
      });
    } catch (e) {
      return { ok: false, error: 'Internet aloqasi yo\'q. Ulanishni tekshiring.', code: 'network' };
    }

    var data = {};
    try { data = await javob.json(); } catch (e) {}

    if (javob.status === 401) {
      sessiyaYopish();
      if (!/\/(login|register|index)\.html$|\/$/.test(location.pathname)) {
        location.href = 'login.html?qaytish=' + encodeURIComponent(location.pathname + location.search);
        return { ok: false, error: 'Sessiya tugadi', code: 'unauthorized' };
      }
    }

    if (typeof data.ok === 'undefined') data.ok = javob.ok;
    data.status = javob.status;
    if (!data.ok && !data.error) data.error = 'Xatolik yuz berdi (' + javob.status + ')';
    return data;
  }

  var API = {
    token: token,
    user: user,
    sessiyaOchish: sessiyaOchish,
    sessiyaYopish: sessiyaYopish,
    userYangilash: userYangilash,
    kirganmi: function () { return !!token(); },

    get: function (yo_l) { return so_rov(yo_l); },
    post: function (yo_l, tana) { return so_rov(yo_l, { method: 'POST', body: tana }); },

    // — Auth —
    kirish: function (email, parol) {
      return so_rov('/api/login', { method: 'POST', body: { email: email, password: parol } });
    },
    ro_yxat: function (ism, email, parol) {
      return so_rov('/api/register', { method: 'POST', body: { name: ism, email: email, password: parol } });
    },
    chiqish: async function () {
      await so_rov('/api/logout', { method: 'POST' });
      sessiyaYopish();
    },
    men: function () { return so_rov('/api/me'); },

    // — O'qish —
    sinflar: function () { return so_rov('/api/study/grades'); },
    sinfTanlash: function (sinf) {
      return so_rov('/api/study/grade', { method: 'POST', body: { grade: sinf } });
    },
    dashboard: function () { return so_rov('/api/study/dashboard'); },
    fanlar: function (sinf) {
      return so_rov('/api/study/subjects' + (sinf ? '?grade=' + sinf : ''));
    },
    mavzular: function (fan, sinf) {
      return so_rov('/api/study/topics/' + encodeURIComponent(fan) + (sinf ? '?grade=' + sinf : ''));
    },
    mavzu: function (fan, slug, sinf) {
      return so_rov('/api/study/topic/' + encodeURIComponent(fan) + '/' + encodeURIComponent(slug)
        + (sinf ? '?grade=' + sinf : ''));
    },
    darsO_qildi: function (fan, slug) {
      return so_rov('/api/study/lesson-read', { method: 'POST', body: { subject_key: fan, slug: slug } });
    },
    quizYuborish: function (fan, slug, javoblar) {
      return so_rov('/api/study/quiz', {
        method: 'POST', body: { subject_key: fan, slug: slug, answers: javoblar },
      });
    },
    uyIshiYuborish: function (fan, slug, javoblar) {
      return so_rov('/api/study/homework', {
        method: 'POST', body: { subject_key: fan, slug: slug, answers: javoblar },
      });
    },
    kutish: function () { return so_rov('/api/study/cooldown'); },

    // — AI —
    aiHolat: function () { return so_rov('/api/ai/status'); },
    aiTushuntir: function (fan, slug, rejim) {
      return so_rov('/api/ai/explain', {
        method: 'POST', body: { subject_key: fan, slug: slug, mode: rejim || 'simple' },
      });
    },
    aiSavol: function (matn, fan, slug) {
      return so_rov('/api/ai/tutor', {
        method: 'POST', body: { message: matn, subject_key: fan, slug: slug },
      });
    },
  };

  window.API = API;
})();
