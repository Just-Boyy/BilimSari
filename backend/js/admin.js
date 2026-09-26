/* BilimSari — admin panel klienti. Talabalar tokenidan butunlay alohida. */
(function () {
  var TOKEN_KEY = 'bilimsari_admin_token';

  function token() { try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; } }
  function saqlash(t) { try { localStorage.setItem(TOKEN_KEY, t); } catch (e) {} }
  function tozalash() { try { localStorage.removeItem(TOKEN_KEY); } catch (e) {} }

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
      return { ok: false, error: 'Internet aloqasi yo\'q.', code: 'network' };
    }

    var data = {};
    try { data = await javob.json(); } catch (e) {}

    if (javob.status === 401) tozalash();
    if (typeof data.ok === 'undefined') data.ok = javob.ok;
    data.status = javob.status;
    if (!data.ok && !data.error) data.error = 'Xatolik yuz berdi (' + javob.status + ')';
    return data;
  }

  /** Autentifikatsiyalangan faylni yuklab olish — token URL'da emas,
   * Authorization sarlavhasida yuboriladi. */
  async function faylYukla(yo_l, nomi) {
    var t = token();
    var javob;
    try {
      javob = await fetch(yo_l, { headers: t ? { 'Authorization': 'Bearer ' + t } : {} });
    } catch (e) {
      return { ok: false, error: 'Internet aloqasi yo\'q.' };
    }
    if (!javob.ok) return { ok: false, error: 'Yuklab bo\'lmadi (' + javob.status + ')' };

    var blob = await javob.blob();
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = nomi;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    return { ok: true };
  }

  var AdminAPI = {
    kirganmi: function () { return !!token(); },
    chiqish: function () { tozalash(); },

    kirish: function (parol) {
      return so_rov('/api/admin/login', { method: 'POST', body: { password: parol } })
        .then(function (res) {
          if (res.ok && res.token) saqlash(res.token);
          return res;
        });
    },

    /** Telegram Mini App ichida parolsiz kirish (faqat admin Telegram ID'lari uchun). */
    telegramKirish: function (initData) {
      return so_rov('/api/admin/telegram-login', { method: 'POST', body: { initData: initData } })
        .then(function (res) {
          if (res.ok && res.token) saqlash(res.token);
          return res;
        });
    },

    stats: function () { return so_rov('/api/admin/stats'); },

    foydalanuvchilar: function (opts) {
      opts = opts || {};
      var params = new URLSearchParams();
      if (opts.q) params.set('q', opts.q);
      if (opts.grade) params.set('grade', opts.grade);
      if (opts.purchasedOnly) params.set('purchased_only', '1');
      params.set('page', opts.page || 1);
      return so_rov('/api/admin/users?' + params.toString());
    },
    foydalanuvchi: function (id) { return so_rov('/api/admin/users/' + id); },
    foydalanuvchiMavzulari: function (id, subjectKey) {
      return so_rov('/api/admin/users/' + id + '/topics/' + subjectKey);
    },
    sinfYangilash: function (id, grade) {
      return so_rov('/api/admin/users/' + id + '/grade', { method: 'POST', body: { grade: grade } });
    },
    fanOchish: function (id, subjectKey) {
      return so_rov('/api/admin/users/' + id + '/unlock', { method: 'POST', body: { subject_key: subjectKey } });
    },
    fanYopish: function (id, subjectKey) {
      return so_rov('/api/admin/users/' + id + '/unlock/' + subjectKey, { method: 'DELETE' });
    },
    foydalanuvchiO_chirish: function (id) {
      return so_rov('/api/admin/users/' + id, { method: 'DELETE' });
    },
    foydalanuvchilarCsvYukla: function () {
      return faylYukla('/api/admin/users/export.csv', 'foydalanuvchilar.csv');
    },

    fanlar: function () { return so_rov('/api/admin/subjects'); },
    fanMavzulari: function (subjectKey) { return so_rov('/api/admin/subjects/' + subjectKey + '/topics'); },

    tolovlar: function (page) { return so_rov('/api/admin/purchases?page=' + (page || 1)); },
    tolovlarCsvYukla: function () {
      return faylYukla('/api/admin/purchases/export.csv', 'tolovlar.csv');
    },

    faoliyat: function (limit) { return so_rov('/api/admin/activity?limit=' + (limit || 50)); },

    xabarYuborish: function (matn) {
      return so_rov('/api/admin/broadcast', { method: 'POST', body: { message: matn } });
    },

    auditJurnali: function (limit) { return so_rov('/api/admin/audit?limit=' + (limit || 100)); },

    barchaSeanslarniTugat: function () {
      return so_rov('/api/admin/revoke-sessions', { method: 'POST' });
    },
  };

  window.AdminAPI = AdminAPI;
})();
