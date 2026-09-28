/* BilimSari — umumiy UI yordamchilari:
   navigatsiya, xabarlar, holatlar, dars matnini chizish, taymer. */
(function () {

  function esc(matn) {
    return String(matn == null ? '' : matn)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /** **qalin** va qator ko'chirishni HTML ga aylantiradi. */
  function matnHtml(matn) {
    return esc(matn)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
  }

  // ── Xabar ────────────────────────────────────────────────
  var xabarTimer = null;
  function xabar(matn, tur) {
    var el = document.getElementById('bsXabar');
    if (!el) {
      el = document.createElement('div');
      el.id = 'bsXabar';
      el.className = 'xabar';
      el.setAttribute('role', 'status');
      el.setAttribute('aria-live', 'polite');
      document.body.appendChild(el);
    }
    el.textContent = matn;
    el.className = 'xabar ko-rinsin' + (tur ? ' ' + tur : '');
    clearTimeout(xabarTimer);
    xabarTimer = setTimeout(function () {
      el.className = 'xabar' + (tur ? ' ' + tur : '');
    }, 3600);
  }

  // ── Navigatsiya ──────────────────────────────────────────
  var NAV = [
    { yo_l: 'dashboard.html', nishon: 'home', matn: 'Bosh sahifa' },
    { yo_l: 'shop.html', nishon: 'shop', matn: "Do'kon" },
    { yo_l: 'games.html', nishon: 'gamepad', matn: "O'yinlar" },
    { yo_l: 'shaxsiy.html', nishon: 'sparkle', matn: 'Shaxsiy' },
    { yo_l: 'leaderboard.html', nishon: 'trophy', matn: 'Reyting' },
    { yo_l: 'profile.html', nishon: 'user', matn: 'Profil' },
  ];

  /** Ikonka HTML si. icons.js yuklanmagan bo'lsa bo'sh qaytaradi. */
  function nishon(nom, cls, size) {
    return (window.BSIcons ? BSIcons.icon(nom, cls, size) : '');
  }

  /** n ta shakl (sanash mashqlari uchun). */
  function shakllar(nom, n, cls) {
    return (window.BSIcons ? BSIcons.shapes(nom, n, cls) : '');
  }

  /** Fan belgisi: rasm berilgan bo'lsa shuni, aks holda SVG ikonkani ko'rsatadi.
   * O'lcham CSS'da .belgi img qoidalari orqali (svg bilan bir xil joyda) beriladi. */
  function fanBelgi(rasm, ikon) {
    if (rasm) {
      return '<img src="' + esc(rasm) + '" alt="">';
    }
    return nishon(ikon);
  }

  function navChiz(faolYo_l) {
    var joriy = faolYo_l || location.pathname.split('/').pop() || 'dashboard.html';
    var nav = document.createElement('nav');
    nav.className = 'pastki-nav';
    nav.setAttribute('aria-label', 'Asosiy menyu');
    nav.innerHTML = NAV.map(function (n) {
      var faol = n.yo_l === joriy ? ' faol' : '';
      return '<a href="' + n.yo_l + '" class="' + faol.trim() + '"' +
        (faol ? ' aria-current="page"' : '') + '>' +
        '<span class="nishon">' + nishon(n.nishon) + '</span>' +
        '<span>' + n.matn + '</span></a>';
    }).join('');
    document.body.appendChild(nav);
  }

  // ── Holatlar ─────────────────────────────────────────────
  function yuklanmoqda(matn) {
    return '<div class="yuklanmoqda"><span class="aylana" aria-hidden="true"></span>' +
      '<span>' + esc(matn || 'Yuklanmoqda...') + '</span></div>';
  }

  function holat(sozlama) {
    var t = sozlama.tugma
      ? '<a class="tugma" href="' + esc(sozlama.tugmaYo_l || '#') + '">' + esc(sozlama.tugma) + '</a>'
      : '';
    return '<div class="holat-karta">' +
      '<span class="belgi">' + nishon(sozlama.belgi || 'inbox') + '</span>' +
      '<h3>' + esc(sozlama.sarlavha) + '</h3>' +
      '<p>' + esc(sozlama.matn || '') + '</p>' + t + '</div>';
  }

  function xatoHolat(matn, qaytaFn) {
    var id = 'qayta' + Math.random().toString(36).slice(2, 7);
    setTimeout(function () {
      var b = document.getElementById(id);
      if (b && qaytaFn) b.onclick = qaytaFn;
    }, 0);
    return '<div class="holat-karta">' +
      '<span class="belgi">' + nishon('alert') + '</span>' +
      '<h3>Ma\'lumot yuklanmadi</h3>' +
      '<p>' + esc(matn || 'Qayta urinib ko\'ring.') + '</p>' +
      '<button class="tugma tugma-avto" id="' + id + '">Qayta urinish</button></div>';
  }

  // ── Vaqt ─────────────────────────────────────────────────
  function vaqtMatn(soniya) {
    soniya = Math.max(0, Math.floor(soniya));
    var s = Math.floor(soniya / 3600);
    var d = Math.floor((soniya % 3600) / 60);
    var son = soniya % 60;
    if (s > 0) return s + ' soat ' + d + ' daqiqa';
    if (d > 0) return d + ' daqiqa ' + son + ' soniya';
    return son + ' soniya';
  }

  function vaqtRaqam(soniya) {
    soniya = Math.max(0, Math.floor(soniya));
    var s = String(Math.floor(soniya / 3600)).padStart(2, '0');
    var d = String(Math.floor((soniya % 3600) / 60)).padStart(2, '0');
    var son = String(soniya % 60).padStart(2, '0');
    return s + ':' + d + ':' + son;
  }

  /** Har soniyada yangilanadigan taymer. Tugaganda tugadi() chaqiriladi. */
  function taymer(el, soniya, tugadi) {
    var qolgan = soniya;
    function yangila() {
      if (qolgan <= 0) {
        clearInterval(id);
        if (tugadi) tugadi();
        return;
      }
      el.innerHTML = vaqtRaqam(qolgan);
      qolgan--;
    }
    yangila();
    var id = setInterval(yangila, 1000);
    return function to_xtat() { clearInterval(id); };
  }

  // ── Dars matnini chizish ─────────────────────────────────
  function darsHtml(bloklar) {
    if (!bloklar || !bloklar.length) {
      return '<p class="izoh">Bu mavzu uchun dars matni tayyorlanmoqda.</p>';
    }
    return bloklar.map(function (b) {
      var bosh = b.icon
        ? '<span class="blok-nishon">' + nishon(b.icon) + '</span>'
        : '';
      var sarlavha = b.title
        ? '<h3>' + bosh + '<span>' + esc(b.title) + '</span></h3>'
        : '';
      switch (b.type) {
        case 'count':
          return '<div translate="no" class="blok blok-sanash">' + sarlavha +
            (b.groups || []).map(function (g) {
              return '<div class="sanash-qator">' +
                shakllar(g.shape, g.n) +
                '<span class="sanash-yozuv">' + esc(g.label || '') + '</span></div>';
            }).join('') + '</div>';
        case 'example':
          return '<div translate="no" class="blok blok-misol">' + sarlavha +
            '<p>' + matnHtml(b.body) + '</p></div>';
        case 'note':
          return '<div translate="no" class="blok blok-eslatma">' + sarlavha +
            '<p>' + matnHtml(b.body) + '</p></div>';
        case 'life':
          return '<div translate="no" class="blok blok-hayot">' + sarlavha +
            '<p>' + matnHtml(b.body) + '</p></div>';
        case 'formula':
          return '<div translate="no" class="blok blok-formula">' + esc(b.body) + '</div>';
        case 'steps':
          return '<div translate="no" class="blok blok-qadamlar">' + sarlavha + '<ol>' +
            (b.items || []).map(function (i) {
              return '<li>' + matnHtml(i) + '</li>';
            }).join('') + '</ol></div>';
        case 'table':
          return '<div translate="no" class="blok"><div class="jadval-o-rov"><table>' +
            '<thead><tr>' + (b.head || []).map(function (h) {
              return '<th>' + esc(h) + '</th>';
            }).join('') + '</tr></thead><tbody>' +
            (b.rows || []).map(function (r) {
              return '<tr>' + r.map(function (c) { return '<td>' + esc(c) + '</td>'; }).join('') + '</tr>';
            }).join('') + '</tbody></table></div></div>';
        default:
          return '<div translate="no" class="blok">' + sarlavha + '<p>' + matnHtml(b.body) + '</p></div>';
      }
    }).join('');
  }

  // ── Sessiyani talab qilish ───────────────────────────────
  async function sessiyaKerak() {
    if (window.API && API.kirganmi()) return true;

    // Telegram Mini App ichida bo'lsak — avtomatik kirish
    if (window.BilimSariTG && typeof BilimSariTG.autoAuthIfTelegram === 'function') {
      try {
        var ok = await BilimSariTG.autoAuthIfTelegram();
        if (ok && API.kirganmi()) return true;
      } catch (e) {}
    }

    location.href = 'telegram-kerak.html';
    return false;
  }

  /** Sinf tanlanmagan bo'lsa onboardingga yuboradi. */
  function sinfKerak(javob) {
    if (javob && javob.code === 'no_grade') {
      location.href = 'onboarding.html';
      return true;
    }
    return false;
  }

  function bosh(nomi) {
    var u = (window.API && API.user()) || {};
    var ism = nomi || u.name || 'o\'quvchi';
    return String(ism).trim().split(/\s+/)[0];
  }

  function harfAvatar(ism) {
    var s = String(ism || '?').trim();
    return s ? s[0].toUpperCase() : '?';
  }

  // ── Yopiq fan kartasi: narx yoki to'lov holati ───────────
  var TOLOV_HOLATI = {
    awaiting_receipt: 'Chek kutilmoqda',
    pending: 'Tekshirilmoqda',
    rejected: "To'lov rad etildi",
  };
  /** 12000 → "12 000 so'm" (bot xabarlari bilan bir xil; brauzer tiliga bog'liq emas). */
  function pul(n) {
    return String(Math.round(Number(n) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + " so'm";
  }
  function qulfHolat(f) {
    return TOLOV_HOLATI[f.pay_status] || pul(f.price);
  }

  /** Ha/yo'q so'rovi. Telegram ichida — Telegram'ning o'z oynasi (brauzer confirm()
   * ba'zi Telegram ilovalarida ko'rinmaydi va jimgina "yo'q" qaytaradi). */
  function tasdiq(savol) {
    return new Promise(function (resolve) {
      var tg = window.Telegram && window.Telegram.WebApp;
      if (tg && tg.initData && tg.showConfirm && tg.isVersionAtLeast && tg.isVersionAtLeast('6.2')) {
        try { tg.showConfirm(String(savol).slice(0, 250), function (ha) { resolve(!!ha); }); return; } catch (e) { /* brauzer oynasi */ }
      }
      resolve(window.confirm(savol));
    });
  }

  /** Premium o'quvchi tanlagan emoji (ism yonida). Kalit bo'lmasa — bo'sh. */
  function emoji(kalit) {
    return kalit
      ? '<img class="nik-emoji" src="assets/emoji/' + esc(kalit) + '.png" alt="" aria-hidden="true" loading="lazy">'
      : '';
  }

  /** Telegram ichida bot chatini ochadi (Mini App'dan), brauzerda — yangi oynada. */
  function botniOch(bot, start) {
    var url = 'https://t.me/' + (bot || 'bilimsaribot') + (start ? '?start=' + encodeURIComponent(start) : '');
    var tg = window.Telegram && window.Telegram.WebApp;
    if (tg && tg.initData && tg.openTelegramLink) tg.openTelegramLink(url);
    else window.open(url, '_blank', 'noopener');
  }

  // ── Yangi yutuq (nishon) tabrigi ─────────────────────────
  // Server har bir yangi nishonni bir marta qaytaradi (new_achievements).
  function yutuqTabrik(yangilar) {
    if (!yangilar || !yangilar.length || document.getElementById('yutuqTabrik')) return;
    var oyna = document.createElement('div');
    oyna.id = 'yutuqTabrik';
    oyna.className = 'yutuq-tabrik';
    oyna.innerHTML =
      '<div class="yutuq-tabrik-karta" role="dialog" aria-modal="true" aria-labelledby="yutuqTabrikSarlavha">' +
        '<p class="yutuq-tabrik-ust">' + nishon('party') + '<span>Tabriklaymiz!</span></p>' +
        '<h2 id="yutuqTabrikSarlavha">' + (yangilar.length > 1 ? 'Yangi nishonlar' : 'Yangi nishon') + '</h2>' +
        yangilar.map(function (y) {
          return '<div class="yutuq-tabrik-qator">' +
            '<span class="yutuq-belgi">' + nishon(y.icon) + '</span>' +
            '<span><b>' + esc(y.title) + '</b><small>' + esc(y.desc) + '</small></span></div>';
        }).join('') +
        '<button class="tugma" type="button">Zo\'r!</button>' +
        '<a class="izoh" href="profile.html#yutuqlar">Barcha nishonlar</a>' +
      '</div>';
    function yop() {
      oyna.remove();
      document.removeEventListener('keydown', tugmaBilan);
    }
    function tugmaBilan(e) { if (e.key === 'Escape') yop(); }
    oyna.querySelector('button').onclick = yop;
    oyna.onclick = function (e) { if (e.target === oyna) yop(); };
    document.addEventListener('keydown', tugmaBilan);
    document.body.appendChild(oyna);
    oyna.querySelector('button').focus();
    try { Telegram.WebApp.HapticFeedback.notificationOccurred('success'); } catch (e) { /* brauzerda yo'q */ }
  }

  window.UI = {
    esc: esc,
    matnHtml: matnHtml,
    xabar: xabar,
    navChiz: navChiz,
    yuklanmoqda: yuklanmoqda,
    holat: holat,
    xatoHolat: xatoHolat,
    vaqtMatn: vaqtMatn,
    vaqtRaqam: vaqtRaqam,
    taymer: taymer,
    nishon: nishon,
    shakllar: shakllar,
    fanBelgi: fanBelgi,
    darsHtml: darsHtml,
    sessiyaKerak: sessiyaKerak,
    sinfKerak: sinfKerak,
    bosh: bosh,
    harfAvatar: harfAvatar,
    yutuqTabrik: yutuqTabrik,
    qulfHolat: qulfHolat,
    pul: pul,
    botniOch: botniOch,
    tasdiq: tasdiq,
    emoji: emoji,
  };
})();
