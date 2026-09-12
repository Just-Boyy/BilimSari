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
    { yo_l: 'dashboard.html', nishon: '🏠', matn: 'Bosh sahifa' },
    { yo_l: 'subjects.html', nishon: '📚', matn: 'Fanlarim' },
    { yo_l: 'progress.html', nishon: '📈', matn: 'Natijalar' },
    { yo_l: 'profile.html', nishon: '👤', matn: 'Profil' },
  ];

  function navChiz(faolYo_l) {
    var joriy = faolYo_l || location.pathname.split('/').pop() || 'dashboard.html';
    var nav = document.createElement('nav');
    nav.className = 'pastki-nav';
    nav.setAttribute('aria-label', 'Asosiy menyu');
    nav.innerHTML = NAV.map(function (n) {
      var faol = n.yo_l === joriy ? ' faol' : '';
      return '<a href="' + n.yo_l + '" class="' + faol.trim() + '"' +
        (faol ? ' aria-current="page"' : '') + '>' +
        '<span class="nishon" aria-hidden="true">' + n.nishon + '</span>' +
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
      '<span class="belgi" aria-hidden="true">' + (sozlama.belgi || '📭') + '</span>' +
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
      '<span class="belgi" aria-hidden="true">⚠️</span>' +
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
      var sarlavha = b.title ? '<h3>' + esc(b.title) + '</h3>' : '';
      switch (b.type) {
        case 'example':
          return '<div class="blok blok-misol">' + sarlavha +
            '<p>' + matnHtml(b.body) + '</p></div>';
        case 'note':
          return '<div class="blok blok-eslatma">' + sarlavha +
            '<p>' + matnHtml(b.body) + '</p></div>';
        case 'life':
          return '<div class="blok blok-hayot">' + sarlavha +
            '<p>' + matnHtml(b.body) + '</p></div>';
        case 'formula':
          return '<div class="blok blok-formula">' + esc(b.body) + '</div>';
        case 'steps':
          return '<div class="blok blok-qadamlar">' + sarlavha + '<ol>' +
            (b.items || []).map(function (i) {
              return '<li>' + matnHtml(i) + '</li>';
            }).join('') + '</ol></div>';
        case 'table':
          return '<div class="blok"><div class="jadval-o-rov"><table>' +
            '<thead><tr>' + (b.head || []).map(function (h) {
              return '<th>' + esc(h) + '</th>';
            }).join('') + '</tr></thead><tbody>' +
            (b.rows || []).map(function (r) {
              return '<tr>' + r.map(function (c) { return '<td>' + esc(c) + '</td>'; }).join('') + '</tr>';
            }).join('') + '</tbody></table></div></div>';
        default:
          return '<div class="blok">' + sarlavha + '<p>' + matnHtml(b.body) + '</p></div>';
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

    location.href = 'login.html?qaytish=' +
      encodeURIComponent(location.pathname.split('/').pop() + location.search);
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
    darsHtml: darsHtml,
    sessiyaKerak: sessiyaKerak,
    sinfKerak: sinfKerak,
    bosh: bosh,
    harfAvatar: harfAvatar,
  };
})();
