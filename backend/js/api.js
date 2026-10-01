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
    // Kontent tili: ruscha interfeysda darslar, testlar va o'yin savollari ham ruscha keladi
    if (window.I18N && I18N.til) bosh['X-Lang'] = I18N.til;

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
      if (!/\/(telegram-kerak|index)\.html$|\/$/.test(location.pathname)) {
        location.href = 'telegram-kerak.html';
        return { ok: false, error: 'Sessiya tugadi', code: 'unauthorized' };
      }
    }

    if (typeof data.ok === 'undefined') data.ok = javob.ok;
    data.status = javob.status;
    if (!data.ok && !data.error) data.error = 'Xatolik yuz berdi (' + javob.status + ')';
    if (data.error && window.I18N) data.error = I18N.t(data.error);   // ruscha interfeysda — xato ham ruscha
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
    del: function (yo_l) { return so_rov(yo_l, { method: 'DELETE' }); },

    // — Auth —
    /** Ism bilan tezkor hisob — email/parol so'ralmaydi. */
    mehmon: function (ism) {
      return so_rov('/api/guest', { method: 'POST', body: { name: ism } });
    },
    chiqish: async function () {
      await so_rov('/api/logout', { method: 'POST' });
      sessiyaYopish();
    },
    men: function () { return so_rov('/api/me'); },
    /** Interfeys tili ('uz' | 'ru') — serverda saqlanadi, boshqa qurilmada ham shu til ochiladi. */
    tilSaqla: function (til) { return so_rov('/api/profile/lang', { method: 'POST', body: { lang: til } }); },

    // — O'qish —
    sinflar: function () { return so_rov('/api/study/grades'); },
    sinfTanlash: function (sinf) {
      return so_rov('/api/study/grade', { method: 'POST', body: { grade: sinf } });
    },
    dashboard: function () { return so_rov('/api/study/dashboard'); },
    fanlar: function () {
      return so_rov('/api/study/subjects');
    },
    mavzular: function (fan) {
      return so_rov('/api/study/topics/' + encodeURIComponent(fan));
    },
    fanTanla: function (fan) {
      return so_rov('/api/study/subjects/' + encodeURIComponent(fan) + '/choose', { method: 'POST' });
    },
    // — To'lov (bot orqali, admin tasdiqlaydi) —
    do_kon: function () { return so_rov('/api/pay/shop'); },
    narxHisobla: function (fanlar, promo) {
      return so_rov('/api/pay/quote', { method: 'POST', body: { keys: fanlar, promo: promo || null } });
    },
    buyurtmaBer: function (fanlar, promo) {
      return so_rov('/api/pay/orders', { method: 'POST', body: { keys: fanlar, promo: promo || null } });
    },
    buyurtmaBekor: function (id) { return so_rov('/api/pay/orders/' + id + '/cancel', { method: 'POST' }); },
    tolovlarim: function () { return so_rov('/api/pay/orders'); },

    // — Bilim Premium —
    premium: function () { return so_rov('/api/premium'); },
    premiumBuyurtma: function (promo) { return so_rov('/api/premium/order', { method: 'POST', body: { promo: promo || null } }); },
    ramkaTanla: function (kalit) { return so_rov('/api/premium/frame', { method: 'POST', body: { frame: kalit } }); },
    emojiTanla: function (kalit) { return so_rov('/api/premium/emoji', { method: 'POST', body: { emoji: kalit || null } }); },

    // — Hamkorlik (promo-kod egasi) —
    hamkor: function () { return so_rov('/api/partner'); },

    // — Do'stlar —
    marafon: function () { return so_rov('/api/marathon'); },
    marafonBanner: function () { return so_rov('/api/marathon/banner'); },
    marafonTarix: function (id) { return so_rov('/api/marathon/history/' + Number(id)); },
    marafonQatnash: function (id) { return so_rov('/api/marathon/join', { method: 'POST', body: { id: id, agree: true } }); },
    dostlar: function () { return so_rov('/api/friends'); },
    dostChaqiruvlar: function () { return so_rov('/api/friends/invites'); },
    dostQidir: function (q) { return so_rov('/api/friends/search?q=' + encodeURIComponent(q)); },
    dostSorov: function (uid) { return so_rov('/api/friends/request', { method: 'POST', body: { user_id: uid } }); },
    dostJavob: function (id, qabul) { return so_rov('/api/friends/respond', { method: 'POST', body: { request_id: id, accept: !!qabul } }); },
    dostBekor: function (id) { return so_rov('/api/friends/cancel', { method: 'POST', body: { request_id: id } }); },
    dostOchir: function (uid) { return so_rov('/api/friends/remove', { method: 'POST', body: { user_id: uid } }); },
    dostChaqir: function (uid, kod) { return so_rov('/api/friends/invite', { method: 'POST', body: { user_id: uid, code: kod } }); },
    dostReyting: function () { return so_rov('/api/friends/leaderboard'); },
    dostLenta: function () { return so_rov('/api/friends/feed'); },
    shikoyat: function (uid, sabab, izoh) {
      return so_rov('/api/friends/report', { method: 'POST', body: { user_id: uid, reason: sabab, note: izoh || null } });
    },

    // — Shaxsiy darslar —
    shaxsiy: function () { return so_rov('/api/personal'); },
    shaxsiyVariant: function (fan, matn) {
      return so_rov('/api/personal/suggest', { method: 'POST', body: { subject_key: fan, text: matn } });
    },
    shaxsiyYarat: function (fan, nom) {
      return so_rov('/api/personal/generate', { method: 'POST', body: { subject_key: fan, title: nom } });
    },
    shaxsiyKorildi: function (idlar) { return so_rov('/api/personal/seen', { method: 'POST', body: { ids: idlar } }); },
    shaxsiyDars: function (id) { return so_rov('/api/personal/' + id); },
    shaxsiyOqildi: function (id) { return so_rov('/api/personal/' + id + '/read', { method: 'POST' }); },
    shaxsiyQuiz: function (id, javoblar) {
      return so_rov('/api/personal/' + id + '/quiz', { method: 'POST', body: { answers: javoblar } });
    },
    shaxsiyUy: function (id, javoblar) {
      return so_rov('/api/personal/' + id + '/homework', { method: 'POST', body: { answers: javoblar } });
    },
    mavzu: function (fan, slug, sinf) {
      return so_rov('/api/study/topic/' + encodeURIComponent(fan) + '/' + encodeURIComponent(slug)
        + '?grade=' + encodeURIComponent(sinf));
    },
    darsO_qildi: function (fan, slug, sinf) {
      return so_rov('/api/study/lesson-read', {
        method: 'POST', body: { subject_key: fan, slug: slug, grade: sinf },
      });
    },
    quizYuborish: function (fan, slug, javoblar, sinf) {
      return so_rov('/api/study/quiz', {
        method: 'POST', body: { subject_key: fan, slug: slug, answers: javoblar, grade: sinf },
      });
    },
    uyIshiYuborish: function (fan, slug, javoblar, sinf) {
      return so_rov('/api/study/homework', {
        method: 'POST', body: { subject_key: fan, slug: slug, answers: javoblar, grade: sinf },
      });
    },
    reyting: function () { return so_rov('/api/study/leaderboard'); },

    // — Kun savoli va yutuqlar —
    kunSavoli: function (ko_rish) { return so_rov('/api/study/daily' + (ko_rish ? '?peek=1' : '')); },
    kunJavob: function (javob) {
      return so_rov('/api/study/daily/answer', { method: 'POST', body: { answer: javob } });
    },
    yutuqlar: function () { return so_rov('/api/study/achievements'); },
    nishonTanla: function (kalitlar) {
      return so_rov('/api/study/achievements/pin', { method: 'POST', body: { keys: kalitlar } });
    },
    rasmYukla: function (dataUrl) {
      return so_rov('/api/profile/photo', { method: 'POST', body: { image: dataUrl } });
    },
    rasmOchir: function () { return so_rov('/api/profile/photo/remove', { method: 'POST' }); },

    o_yinSavollari: function (soni, rejim) {
      return so_rov('/api/study/game/questions?count=' + (soni || 10) + (rejim ? '&mode=' + encodeURIComponent(rejim) : ''));
    },
    o_yinTekshir: function (topicId, qIndex, javob) {
      return so_rov('/api/study/game/check', {
        method: 'POST', body: { topic_id: topicId, q_index: qIndex, answer: javob },
      });
    },
    ismYangilash: function (ism) {
      return so_rov('/api/profile/name', { method: 'POST', body: { name: ism } });
    },
    ismTasdiqla: function () {
      return so_rov('/api/profile/onboarded', { method: 'POST' });
    },
    kutish: function () { return so_rov('/api/study/cooldown'); },

    // — AI —
    aiHolat: function () { return so_rov('/api/ai/status'); },
    aiTushuntir: function (fan, slug, rejim, sinf) {
      return so_rov('/api/ai/explain', {
        method: 'POST', body: { subject_key: fan, slug: slug, mode: rejim, grade: sinf, lang: window.I18N ? I18N.til : 'uz' },
      });
    },
    aiShaxsiy: function (id, rejim) {
      return so_rov('/api/ai/explain', {
        method: 'POST', body: { personal_id: id, mode: rejim, lang: window.I18N ? I18N.til : 'uz' },
      });
    },
    aiSavol: function (matn, fan, slug, sinf) {
      return so_rov('/api/ai/tutor', {
        method: 'POST', body: { message: matn, subject_key: fan, slug: slug, grade: sinf, lang: window.I18N ? I18N.til : 'uz' },
      });
    },
  };

  window.API = API;
})();
