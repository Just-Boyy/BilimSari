/* BilimSari Game Hub — umumiy yadro.

   Tarkibi: API, polling transporti, server soati bilan sinxronlash, ekranlar
   (hash router), tozalash (taymer/listener/poll), modal, dangasa yuklash.

   Real-time: hozircha Poller qisqa so'rovlar bilan ishlaydi. Keyinchalik
   WebSocket/SSE ga o'tishda faqat Poller o'rnini bosuvchi transport
   yoziladi (start/stop/now/onData interfeysi saqlanadi) — ekranlar va
   o'yin mantig'i o'zgarmaydi. */
(function () {
  'use strict';

  var G = window.Games = window.Games || {};
  G.V = '3';                       // dangasa yuklanadigan fayllar keshini yangilash uchun
  G.renderers = G.renderers || {};

  function enc(s) { return encodeURIComponent(s == null ? '' : s); }
  function roomUrl(code) { return '/api/games/rooms/' + enc(code); }

  // ── API ───────────────────────────────────────────────
  G.api = {
    catalog: function () { return API.get('/api/games/catalog'); },
    topics: function (game, subject) {
      return API.get('/api/games/topics?game=' + enc(game) + '&subject=' + enc(subject));
    },
    lobby: function () { return API.get('/api/games/lobby'); },
    create: function (s) { return API.post('/api/games/rooms', s); },
    join: function (code) { return API.post('/api/games/rooms/join', { code: code }); },
    state: function (code, since) {
      return API.get(roomUrl(code) + (since ? '?since=' + enc(since) : ''));
    },
    ready: function (code, v) { return API.post(roomUrl(code) + '/ready', { ready: v }); },
    settings: function (code, s) { return API.post(roomUrl(code) + '/settings', s); },
    kick: function (code, pid) { return API.post(roomUrl(code) + '/kick', { pid: pid }); },
    start: function (code) { return API.post(roomUrl(code) + '/start', {}); },
    rematch: function (code) { return API.post(roomUrl(code) + '/rematch', {}); },
    answer: function (code, q, a) { return API.post(roomUrl(code) + '/answer', { q: q, answer: a }); },
    leave: function (code) { return API.post(roomUrl(code) + '/leave', {}); },
    mmStart: function (s) { return API.post('/api/games/matchmaking', s); },
    mmPoll: function () { return API.get('/api/games/matchmaking'); },
    mmCancel: function () { return API.del('/api/games/matchmaking'); },
    leaderboard: function (p) {
      return API.get('/api/games/leaderboard?period=' + enc(p.period) + '&scope=' + enc(p.scope) +
        (p.subject ? '&subject=' + enc(p.subject) : ''));
    },
    me: function () { return API.get('/api/games/me'); },
  };

  // Katalog bir marta yuklanadi va ekranlar orasida qayta ishlatiladi
  var catalogPromise = null;
  G.catalog = function () {
    if (!catalogPromise) {
      catalogPromise = G.api.catalog().then(function (res) {
        if (!res.ok) catalogPromise = null;
        return res;
      });
    }
    return catalogPromise;
  };
  G.gameByKey = function (cat, key) {
    return (cat.games || []).filter(function (g) { return g.key === key; })[0] || null;
  };

  // ── Server soati ──────────────────────────────────────
  // Taymerlar server vaqtiga tayanadi: qurilma soati noto'g'ri bo'lsa ham
  // hamma o'yinchida bir xil hisoblanadi.
  var offset = null;
  G.clock = {
    sync: function (serverNow, sentAt, receivedAt) {
      if (!serverNow) return;
      var sample = serverNow - (sentAt + receivedAt) / 2;
      offset = offset === null ? sample : offset * 0.7 + sample * 0.3;
    },
    now: function () { return Date.now() + (offset || 0); },
  };

  // ── Tozalash doirasi (Scope) ──────────────────────────
  // Har bir ekran o'z taymer, listener va poll'larini shu yerga yozadi;
  // ekran almashganda hammasi bir yo'la to'xtatiladi — xotira oqmaydi.
  function Scope() { this.fns = []; this.dead = false; }
  Scope.prototype.add = function (fn) { this.fns.push(fn); return fn; };
  Scope.prototype.timeout = function (fn, ms) {
    var id = setTimeout(fn, ms);
    this.add(function () { clearTimeout(id); });
    return id;
  };
  Scope.prototype.interval = function (fn, ms) {
    var id = setInterval(fn, ms);
    this.add(function () { clearInterval(id); });
    return id;
  };
  Scope.prototype.on = function (el, ev, fn, opt) {
    el.addEventListener(ev, fn, opt);
    this.add(function () { el.removeEventListener(ev, fn, opt); });
  };
  Scope.prototype.dispose = function () {
    this.dead = true;
    var fns = this.fns;
    this.fns = [];
    fns.forEach(function (fn) { try { fn(); } catch (e) { /* tozalashda xato e'tiborsiz */ } });
  };
  G.Scope = Scope;

  // ── Polling transporti ────────────────────────────────
  /* opts: fetch() → Promise<res>, onData(res), onError(res),
           interval() → ms, hiddenFactor (yashirin tabda sekinlashish) */
  function Poller(opts) {
    this.opts = opts;
    this.timer = null;
    this.stopped = true;
    this.failures = 0;
    this.busy = false;
  }
  Poller.prototype.start = function () {
    this.stopped = false;
    this.now();
  };
  Poller.prototype.stop = function () {
    this.stopped = true;
    clearTimeout(this.timer);
  };
  Poller.prototype.schedule = function (ms) {
    var self = this;
    clearTimeout(this.timer);
    if (!this.stopped) this.timer = setTimeout(function () { self.tick(); }, ms);
  };
  Poller.prototype.now = function () { this.schedule(0); };
  Poller.prototype.tick = function () {
    var self = this;
    var o = this.opts;
    if (this.stopped || this.busy) return;
    this.busy = true;
    o.fetch().then(function (res) {
      self.busy = false;
      if (self.stopped) return;
      if (res && res.code === 'network') {
        self.failures++;
        if (o.onError) o.onError(res);
        self.schedule(Math.min(8000, 1000 * Math.pow(2, self.failures - 1)));
        return;
      }
      self.failures = 0;
      var keepGoing = o.onData(res);
      if (keepGoing === false) { self.stop(); return; }
      var ms = o.interval();
      if (document.hidden) ms *= (o.hiddenFactor || 3);
      self.schedule(ms);
    }, function () {
      self.busy = false;
      self.failures++;
      self.schedule(4000);
    });
  };
  G.Poller = Poller;

  // ── Ekranlar (hash router) ────────────────────────────
  var routes = {};
  var current = { scope: null, name: null };
  G.el = function () { return document.getElementById('ekran'); };
  G.route = function (name, fn) { routes[name] = fn; };

  G.parse = function () {
    var h = (location.hash || '').replace(/^#/, '');
    var parts = h.split('/');
    return { name: parts[0] || 'lobby', arg: decodeURIComponent(parts[1] || '') };
  };

  G.go = function (hash, replace) {
    var target = '#' + hash;
    if (location.hash === target) { G.render(); return; }
    if (replace) {
      history.replaceState(null, '', target);
      G.render();
    } else {
      location.hash = target;
    }
  };

  G.render = function () {
    var r = G.parse();
    var fn = routes[r.name] || routes.lobby;
    if (current.scope) current.scope.dispose();
    G.banner(null);
    G.closeModal();
    var scope = new Scope();
    current = { scope: scope, name: r.name };
    window.scrollTo(0, 0);
    try {
      fn(r.arg, scope);
    } catch (e) {
      G.el().innerHTML = UI.xatoHolat("Sahifani ko'rsatib bo'lmadi.", function () { G.render(); });
    }
  };

  window.addEventListener('hashchange', function () { G.render(); });

  // ── Sarlavha qatori ───────────────────────────────────
  G.header = function (o) {
    var h1 = document.getElementById('sarlavha');
    h1.innerHTML = UI.esc(o.title) + (o.sub ? '<small>' + UI.esc(o.sub) + '</small>' : '');
    document.title = o.title + ' — BilimSari';
    var back = document.getElementById('orqagaTugma');
    back.onclick = function () {
      if (typeof o.back === 'function') o.back();
      else location.href = o.back || 'dashboard.html';
    };
    document.getElementById('ustkiOng').innerHTML = o.right || '';
  };

  /** Yangi ekranda o'qish tartibini boshiga qaytaradi (ekran o'quvchilar uchun). */
  G.focusMain = function () {
    var t = G.el().querySelector('[data-fokus]') || G.el().querySelector('h2');
    if (t) {
      if (!t.hasAttribute('tabindex')) t.setAttribute('tabindex', '-1');
      try { t.focus({ preventScroll: true }); } catch (e) { t.focus(); }
    }
  };

  // ── Ogohlantirish lentasi (aloqa uzilishi va h.k.) ────
  G.banner = function (text, tur) {
    var el = document.getElementById('oyLenta');
    if (!el) return;
    if (!text) { el.hidden = true; el.innerHTML = ''; return; }
    el.className = 'oy-lenta' + (tur ? ' ' + tur : '');
    el.innerHTML = UI.nishon(tur === 'xato' ? 'alert' : 'wifiOff') + '<span>' + UI.esc(text) + '</span>';
    el.hidden = false;
  };

  // ── Modal ─────────────────────────────────────────────
  var modalState = null;
  G.closeModal = function () {
    if (!modalState) return;
    var m = modalState;
    modalState = null;
    m.layer.remove();
    document.removeEventListener('keydown', m.onKey);
    if (m.onClose) m.onClose();
    if (m.returnFocus && m.returnFocus.focus) m.returnFocus.focus();
  };
  G.modal = function (html, opts) {
    opts = opts || {};
    G.closeModal();
    var layer = document.createElement('div');
    layer.className = 'oy-modal-fon';
    layer.innerHTML = '<div class="oy-modal" role="dialog" aria-modal="true" aria-labelledby="oyModalSarlavha">' +
      '<button class="oy-modal-yop" type="button" aria-label="Yopish">' + UI.nishon('x') + '</button>' +
      html + '</div>';
    document.body.appendChild(layer);
    var onKey = function (e) {
      if (e.key === 'Escape') { G.closeModal(); return; }
      if (e.key !== 'Tab') return;
      // Fokus modal ichida qoladi
      var f = layer.querySelectorAll('button, [href], input, select, textarea');
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    modalState = { layer: layer, onKey: onKey, onClose: opts.onClose, returnFocus: document.activeElement };
    document.addEventListener('keydown', onKey);
    layer.addEventListener('click', function (e) { if (e.target === layer) G.closeModal(); });
    layer.querySelector('.oy-modal-yop').onclick = G.closeModal;
    var auto = layer.querySelector('[data-avto-fokus]') || layer.querySelector('.oy-modal-yop');
    setTimeout(function () { if (auto) auto.focus(); }, 30);
    return layer.querySelector('.oy-modal');
  };

  // ── Segmentli tanlov (radiogroup) ─────────────────────
  G.segment = function (name, label, items, value) {
    return '<div class="oy-segment" role="radiogroup" aria-label="' + UI.esc(label) + '" data-segment="' + name + '">' +
      items.map(function (it) {
        var on = String(it.value) === String(value);
        return '<button type="button" role="radio" aria-checked="' + on + '" tabindex="' + (on ? '0' : '-1') + '"' +
          ' data-value="' + UI.esc(it.value) + '">' + UI.esc(it.label) + '</button>';
      }).join('') + '</div>';
  };
  /** Segment tugmalariga bosish va strelkalar bilan boshqarish. */
  G.bindSegment = function (root, scope, onChange) {
    root.querySelectorAll('[data-segment]').forEach(function (seg) {
      var buttons = Array.prototype.slice.call(seg.querySelectorAll('[role="radio"]'));
      function select(btn, focus) {
        buttons.forEach(function (b) {
          var on = b === btn;
          b.setAttribute('aria-checked', on);
          b.tabIndex = on ? 0 : -1;
        });
        if (focus) btn.focus();
        onChange(seg.dataset.segment, btn.dataset.value);
      }
      buttons.forEach(function (b, i) {
        scope.on(b, 'click', function () { select(b, false); });
        scope.on(b, 'keydown', function (e) {
          var d = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : (e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0);
          if (!d) return;
          e.preventDefault();
          select(buttons[(i + d + buttons.length) % buttons.length], true);
        });
      });
    });
  };

  // ── Dangasa yuklash (code splitting) ──────────────────
  var loaded = {};
  G.load = function (src) {
    if (!loaded[src]) {
      loaded[src] = new Promise(function (resolve, reject) {
        var s = document.createElement('script');
        s.src = src + '?v=' + G.V;
        s.async = true;
        s.onload = resolve;
        s.onerror = function () { delete loaded[src]; reject(new Error('yuklanmadi: ' + src)); };
        document.head.appendChild(s);
      });
    }
    return loaded[src];
  };

  // ── Yordamchilar ──────────────────────────────────────
  G.initial = function (name) { return UI.harfAvatar(name); };
  G.mmss = function (ms) {
    var s = Math.max(0, Math.ceil(ms / 1000));
    return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
  };
  /** `kod` qismlarini <code> ga aylantiradi (matn avval xavfsiz escape qilinadi). */
  G.rich = function (text) {
    return UI.esc(text).replace(/`([^`]+)`/g, '<code>$1</code>');
  };
  G.copy = function (text) {
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      ta.remove();
      return ok;
    }
    var done = function (ok) { UI.xabar(ok ? 'Nusxalandi' : "Nusxalab bo'lmadi — qo'lda belgilang", ok ? 'muvaffaqiyat' : 'xato'); };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(fallback()); });
    } else {
      done(fallback());
    }
  };
  G.remember = function (key, value) {
    try {
      if (value === undefined) return JSON.parse(localStorage.getItem('oy_' + key) || 'null');
      localStorage.setItem('oy_' + key, JSON.stringify(value));
    } catch (e) { /* xotira yopiq bo'lsa — standart sozlamalar */ }
    return null;
  };
  G.difficultyName = { oson: 'Oson', orta: "O'rta", qiyin: 'Qiyin' };

  /** Tasdiqlash oynasi — Telegram ichida uning o'z dialogi, aks holda brauzerniki. */
  G.confirm = function (text) {
    var tg = window.Telegram && window.Telegram.WebApp;
    if (tg && tg.initData && tg.showConfirm && tg.isVersionAtLeast && tg.isVersionAtLeast('6.2')) {
      return new Promise(function (resolve) {
        try { tg.showConfirm(text, function (ok) { resolve(!!ok); }); } catch (e) { resolve(window.confirm(text)); }
      });
    }
    return Promise.resolve(window.confirm(text));
  };
})();
