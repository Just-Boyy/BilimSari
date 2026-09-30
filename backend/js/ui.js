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
    { yo_l: 'games.html', nishon: 'gamepad', matn: "O'yinlar" },
    { yo_l: 'shaxsiy.html', nishon: 'sparkle', matn: 'Shaxsiy' },
    { yo_l: 'leaderboard.html', nishon: 'trophy', matn: 'Reyting' },
  ];
  // Oxirgi band — "Menyu": bosilganda ro'yxat ochiladi
  var MENYU = [
    { yo_l: 'profile.html', nishon: 'user', matn: 'Profil' },
    { yo_l: 'settings.html', nishon: 'settings', matn: 'Sozlamalar' },
    { yo_l: 'shaxsiy.html', nishon: 'sparkle', matn: 'Shaxsiy darslar' },
    { yo_l: 'shop.html', nishon: 'shop', matn: "Do'kon" },
    { kanal: true, nishon: 'info', matn: 'Biz haqimizda' },
    { yo_l: 'hamkor.html', nishon: 'users', matn: 'Hamkorlik', hamkor: true },
  ];
  var MENYU_SAHIFALAR = ['profile.html', 'settings.html', 'hamkor.html', 'shop.html'];
  var MENYU_KESH = 'bilimsari_menyu';

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
    var menyuFaol = MENYU_SAHIFALAR.indexOf(joriy) >= 0;
    nav.innerHTML = NAV.map(function (n) {
      var faol = n.yo_l === joriy ? ' faol' : '';
      return '<a href="' + n.yo_l + '" class="' + faol.trim() + '"' +
        (faol ? ' aria-current="page"' : '') + '>' +
        '<span class="nishon">' + nishon(n.nishon) + '</span>' +
        '<span>' + n.matn + '</span></a>';
    }).join('') +
      '<button type="button" class="nav-menyu-tugma' + (menyuFaol ? ' faol' : '') + '" id="navMenyuTugma" ' +
        'aria-haspopup="true" aria-expanded="false" aria-controls="navMenyu">' +
        '<span class="nishon">' + nishon('menu') + '</span><span>Menyu</span></button>' +
      '<div class="nav-menyu" id="navMenyu" role="menu" hidden></div>';
    document.body.appendChild(nav);
    menyuUlash();
  }

  /** "Menyu" ro'yxati: Profil, Sozlamalar, Shaxsiy darslar, Biz haqimizda (kanal) va
   * hamkorlarga — Hamkorlik. Hamkorlik va kanal havolasi serverdan (/api/menu) keladi;
   * sahifa tez chizilishi uchun oxirgi javob localStorage'da saqlanadi. */
  function menyuUlash() {
    var tugma = document.getElementById('navMenyuTugma');
    var quti = document.getElementById('navMenyu');
    var holat = {};
    try { holat = JSON.parse(localStorage.getItem(MENYU_KESH) || '{}') || {}; } catch (e) { holat = {}; }

    var sahifa = location.pathname.split('/').pop() || 'dashboard.html';
    function chiz() {
      quti.innerHTML = MENYU.filter(function (m) { return !m.hamkor || holat.partner; }).map(function (m) {
        var ichi = '<span class="nishon">' + nishon(m.nishon) + '</span><span>' + m.matn + '</span>';
        if (m.kanal) {
          return '<button type="button" role="menuitem" data-kanal>' + ichi +
            '<span class="tashqi" aria-hidden="true">' + nishon('send') + '</span></button>';
        }
        var faol = m.yo_l === sahifa;
        return '<a role="menuitem" href="' + m.yo_l + '"' + (faol ? ' class="faol" aria-current="page"' : '') + '>' + ichi + '</a>';
      }).join('');
      var kanal = quti.querySelector('[data-kanal]');
      if (kanal) kanal.onclick = kanalniOch;
    }

    function kanalniOch() {
      yop();
      var url = holat.channel_url;
      if (!url) { xabar('Kanal havolasi tez orada qo\'shiladi.'); return; }
      var tg = window.Telegram && window.Telegram.WebApp;
      if (tg && tg.initData && tg.openTelegramLink && /^https:\/\/t\.me\//.test(url)) tg.openTelegramLink(url);
      else window.open(url, '_blank', 'noopener');
    }

    function och() {
      quti.hidden = false;
      // Odatda yuqoriga ochiladi (telefonda menyu pastda); tepada joy bo'lmasa — pastga
      quti.classList.remove('pastga');
      if (tugma.getBoundingClientRect().top < quti.offsetHeight + 16) quti.classList.add('pastga');
      tugma.setAttribute('aria-expanded', 'true');
      tugma.classList.add('ochiq');
      var birinchi = quti.querySelector('a, button');
      if (birinchi && document.activeElement === tugma && tugma.dataset.klaviatura) birinchi.focus();
    }
    function yop() {
      quti.hidden = true;
      tugma.setAttribute('aria-expanded', 'false');
      tugma.classList.remove('ochiq');
    }

    tugma.onclick = function (e) {
      e.stopPropagation();
      if (quti.hidden) och(); else yop();
    };
    tugma.onkeydown = function (e) { if (e.key === 'Enter' || e.key === ' ') tugma.dataset.klaviatura = '1'; };
    document.addEventListener('click', function (e) {
      if (!quti.hidden && !quti.contains(e.target)) yop();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !quti.hidden) { yop(); tugma.focus(); }
    });

    chiz();
    if (window.API && API.token && API.token()) {
      API.get('/api/menu').then(function (r) {
        if (!r || !r.ok) return;
        holat = { partner: !!r.partner, channel_url: r.channel_url || null };
        try { localStorage.setItem(MENYU_KESH, JSON.stringify(holat)); } catch (e) { /* */ }
        chiz();
      });
    }
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
  var RAMKALAR = { 'oltin-chaqmoq': 1, 'kok-chaqmoq': 1, 'yashil-chaqmoq': 1 };
  /** Avatar HTML'ini Premium ramkasi bilan o'raydi (ramka bo'lmasa — o'zgarishsiz). */
  function ramkali(avatarHtml, ramka, cls) {
    if (!ramka || !RAMKALAR[ramka]) return avatarHtml;
    return '<span class="ramkali ramka-ichida' + (cls ? ' ' + cls : '') + '">' + avatarHtml +
      '<span class="ramka r-' + ramka + '" aria-hidden="true"></span></span>';
  }

  /** "hozir", "5 daqiqa oldin", "3 soat oldin", "kecha", "4 kun oldin". */
  function oldin(ms) {
    if (!ms) return '';
    var s = Math.max(0, (Date.now() - ms) / 1000);
    if (s < 90) return 'hozirgina';
    if (s < 3600) return Math.round(s / 60) + ' daqiqa oldin';
    if (s < 86400) return Math.round(s / 3600) + ' soat oldin';
    if (s < 2 * 86400) return 'kecha';
    return Math.round(s / 86400) + ' kun oldin';
  }

  /** Do'st (yoki qidiruv natijasi) qatori: rasm+ramka, ism+emoji, holat; o'ngda — amallar. */
  function dostQator(c, amallar, izoh, havolasiz) {
    var av = c.photo_url
      ? '<img class="avatar" alt="" src="' + esc(c.photo_url) + '">'
      : '<span class="avatar" aria-hidden="true">' + esc(harfAvatar(c.name)) + '</span>';
    var holat = izoh != null ? izoh : (c.online ? 'onlayn' : (c.last_seen_ms ? oldin(c.last_seen_ms) : ''));
    return '<div class="dost-qator' + (c.online ? ' onlayn' : '') + '">' +
      (havolasiz ? '<span class="dost-kim">' : '<a class="dost-kim" href="' + profilYoli(c.id) + '">') +
        '<span class="dost-avatar">' + ramkali(av, c.premium && c.frame) + '</span>' +
        '<span class="dost-matn"><b><span>' + esc(c.name) + '</span>' + emoji(c.emoji) + '</b>' +
          (holat ? '<small>' + esc(holat) + '</small>' : '') + '</span>' +
      (havolasiz ? '</span>' : '</a>') + (amallar ? '<span class="dost-amal">' + amallar + '</span>' : '') + '</div>';
  }

  /** Boshqa o'quvchi profili sahifasi (o'ziniki — profile.html). */
  function profilYoli(uid, men) {
    return men ? 'profile.html' : 'foydalanuvchi.html?id=' + encodeURIComponent(uid);
  }
  /** Ro'yxat qatori uchun ochuvchi teg: foydalanuvchi ID bo'lsa — profilga havola, aks holda div. */
  function qatorTeg(cls, uid, men) {
    return uid
      ? '<a class="' + cls + '" href="' + profilYoli(uid, men) + '">'
      : '<div class="' + cls + '">';
  }
  function qatorYop(uid) { return uid ? '</a>' : '</div>'; }

  /** Sahifadan chiqmasdan kichik profil oynasi (o'yin xonasida — room tashlab ketilmasin).
   * Har qanday [data-profil="ID"] elementni bosganda ochiladi. */
  async function profilOyna(uid) {
    if (!uid || document.getElementById('profilOyna')) return;
    var oyna = document.createElement('div');
    oyna.id = 'profilOyna';
    oyna.className = 'yutuq-tabrik profil-oyna';
    oyna.innerHTML = '<div class="yutuq-tabrik-karta" role="dialog" aria-modal="true" aria-label="Profil">' + yuklanmoqda() + '</div>';
    document.body.appendChild(oyna);
    function yop() { oyna.remove(); document.removeEventListener('keydown', tugma); }
    function tugma(e) { if (e.key === 'Escape') yop(); }
    document.addEventListener('keydown', tugma);
    oyna.addEventListener('click', function (e) { if (e.target === oyna || e.target.closest('[data-yop]')) yop(); });
    var r = await API.get('/api/study/profile/' + encodeURIComponent(uid));
    var karta = oyna.querySelector('.yutuq-tabrik-karta');
    if (!r.ok) {
      karta.innerHTML = '<p class="izoh">' + esc(r.error || 'Xatolik') + '</p>' +
        '<button class="tugma" type="button" data-yop>Yopish</button>';
      return;
    }
    var p = r.profile, pr = p.premium || {};
    var av = p.photo_url
      ? '<img class="avatar" alt="" src="' + esc(p.photo_url) + '">'
      : '<span class="avatar" aria-hidden="true">' + esc(harfAvatar(p.name)) + '</span>';
    var nish = ((p.badges && p.badges.items) || []).slice().sort(function (a, b) { return b.unlocked_ms - a.unlocked_ms; }).slice(0, 7);
    var s = function (b, t) { return '<div><b>' + b + '</b>' + esc(t) + '</div>'; };
    karta.innerHTML =
      '<div class="po-bosh">' + ramkali(av, pr.active && pr.frame) +
        '<h2><span>' + esc(p.name) + '</span>' + emoji(pr.active && pr.emoji) + '</h2>' +
        (pr.active ? '<span class="premium-pill">' + nishon('crown') + '<span>Bilim Premium</span></span>' : '') +
      '</div>' +
      '<div class="po-stat">' + s(String(p.chaqmoq), 'Chaqmoq') + s(p.rank ? String(p.rank) : '—', "O'rin") +
        s(String(p.streak), 'Streak') + s(String(p.topics), 'Mavzu') + '</div>' +
      (nish.length ? '<div class="po-nishonlar">' + nish.map(function (a) {
        return '<span class="yutuq-belgi d-' + daraja(a.tier) + '" title="' + esc(a.title) + '">' + nishon(a.icon) + '</span>';
      }).join('') + '</div>' : '') +
      '<a class="tugma" href="' + profilYoli(p.id, p.me) + '">To\'liq profil</a>' +
      '<button class="matn-tugma" type="button" data-yop style="margin-top:8px">Yopish</button>';
  }
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-profil]');
    if (!t) return;
    var ichki = e.target.closest('button, a');            // qator ichidagi tugmalar (masalan, "chiqarish")
    if (ichki && ichki !== t && t.contains(ichki)) return;
    e.preventDefault();
    profilOyna(t.getAttribute('data-profil'));
  });

  var DARAJALAR = { bronza: 'Bronza', kumush: 'Kumush', oltin: 'Oltin', brilyant: 'Brilyant', premium: 'Premium' };
  /** Nishon darajasi (CSS klassi uchun xavfsiz): bronza | kumush | oltin | brilyant | premium. */
  function daraja(t) { return DARAJALAR[t] ? t : 'oltin'; }
  function darajaNomi(t) { return DARAJALAR[daraja(t)]; }

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
            '<span class="yutuq-belgi d-' + daraja(y.tier) + '">' + nishon(y.icon) + '</span>' +
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
    daraja: daraja,
    ramkali: ramkali,
    profilYoli: profilYoli,
    oldin: oldin,
    dostQator: dostQator,
    qatorTeg: qatorTeg,
    qatorYop: qatorYop,
    profilOyna: profilOyna,
    darajaNomi: darajaNomi,
    tasdiq: tasdiq,
    emoji: emoji,
  };
})();
