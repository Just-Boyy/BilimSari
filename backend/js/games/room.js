/* BilimSari Game Hub — room ekrani: kutish zali, countdown, o'yin, natijalar.

   Holat to'liq serverda (ball, taymer, to'g'ri javob). Bu fayl uni ko'rsatadi
   va javob yuboradi. Faqat roomga kirilganda yuklanadi (hub.js → G.load).
   Ekran almashganda poll, taymer va listenerlar scope orqali to'xtatiladi. */
(function () {
  'use strict';

  var G = window.Games;
  var esc = UI.esc;
  var ic = UI.nishon;

  var TERMINAL_TITLES = {
    room_not_found: 'Room topilmadi',
    room_expired: 'Roomning muddati tugagan',
    room_closed: 'Room yopilgan',
    kicked: 'Siz roomdan chiqarildingiz',
    not_member: 'Siz bu roomda emassiz',
    room_full: "Room to'liq",
    room_started: "O'yin allaqachon boshlangan",
    invalid_code: "Room kodi noto'g'ri",
  };

  function chip(icon, text) {
    return '<span class="oy-chip">' + (icon ? ic(icon) : '') + '<span>' + esc(text) + '</span></span>';
  }

  function spelled(code) { return code.split('').join(' '); }

  function topicHref(l) {
    return 'topic.html?fan=' + encodeURIComponent(l.fan) + '&mavzu=' + encodeURIComponent(l.mavzu) +
      '&sinf=' + encodeURIComponent(l.sinf);
  }

  function celebrate() {
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var layer = document.createElement('div');
    layer.className = 'konfetti-qavat';
    layer.setAttribute('aria-hidden', 'true');
    var colors = ['#58A700', '#89e219', '#eab308', '#1CB0F6', '#FF4B4B'];
    for (var i = 0; i < 36; i++) {
      var k = document.createElement('i');
      k.className = 'konfetti';
      k.style.left = Math.random() * 100 + '%';
      k.style.background = colors[i % colors.length];
      k.style.animationDuration = (1.6 + Math.random() * 1.4) + 's';
      k.style.animationDelay = (Math.random() * 0.4) + 's';
      layer.appendChild(k);
    }
    document.body.appendChild(layer);
    setTimeout(function () { layer.remove(); }, 3600);
  }

  G.roomScreen = function (code, scope) {
    code = String(code || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    var el = G.el();
    var S = null;            // oxirgi to'liq holat
    var etag = null;
    var view = null;         // chizilgan ko'rinish kaliti (keraksiz qayta chizishning oldini oladi)
    var vs = null;           // joriy ko'rinishning o'z scope'i
    var ctrl = null;         // savol renderer boshqaruvchisi
    var revealed = null;
    var sending = false;
    var triedJoin = false;
    var cache = {};          // bo'limlar HTML'i — o'zgarmagan bo'lsa qayta yozilmaydi (fokus saqlanadi)

    scope.add(function () { if (vs) vs.dispose(); });

    function setHeader() {
      G.header({ title: S ? S.game.name : 'Room', sub: 'Room ' + code, back: leave });
    }
    setHeader();

    function viewScope() {
      if (vs) vs.dispose();
      vs = new G.Scope();
      cache = {};
      return vs;
    }

    function put(id, html) {
      var node = document.getElementById(id);
      if (!node || cache[id] === html) return false;
      node.innerHTML = html;
      cache[id] = html;
      return true;
    }

    // ── Server bilan aloqa ──────────────────────────────
    function fetchState() {
      var t0 = Date.now();
      return G.api.state(code, etag).then(function (res) {
        if (res.ok && res.state) G.clock.sync(res.state.now, t0, Date.now());
        return res;
      });
    }

    var poller = new G.Poller({
      fetch: fetchState,
      hiddenFactor: 3,
      interval: function () {
        if (!S || S.status === 'waiting') return 1500;
        if (S.status === 'finished') return 3000;
        var ph = S.session && S.session.phase;
        return ph === 'question' ? 800 : 700;
      },
      onError: function () { G.banner('Internet aloqasi uzildi. Qayta ulanmoqda...'); },
      onData: function (res) {
        if (!res.ok) return handleError(res);
        G.banner(null);
        if (!res.state.same) apply(res.state);
        else notices();
        return view !== 'terminal';
      },
    });
    scope.add(function () { poller.stop(); });
    scope.on(document, 'visibilitychange', function () { if (!document.hidden) poller.now(); });
    poller.start();

    function handleError(res) {
      if (res.code === 'not_member' && !triedJoin) {
        // Havola yoki "faol room" orqali kelgan — avtomatik qo'shilamiz
        triedJoin = true;
        G.api.join(code).then(function (j) {
          if (scope.dead) return;
          if (j.ok) { apply(j.state); poller.start(); } else terminal(j);
        });
        return false;
      }
      if (TERMINAL_TITLES[res.code]) { terminal(res); return false; }
      G.banner(res.error || "Server bilan aloqa muammosi. Qayta urinilmoqda...", 'xato');
      return true;
    }

    function terminal(res) {
      poller.stop();
      if (vs) vs.dispose();
      view = 'terminal';
      G.header({ title: 'Room', sub: code, back: function () { G.go('lobby'); } });
      el.innerHTML = UI.holat({
        belgi: res.code === 'kicked' ? 'x' : 'alert',
        sarlavha: TERMINAL_TITLES[res.code] || 'Xatolik yuz berdi',
        matn: res.error || '',
      }) + '<div class="tugmalar" style="margin-top:12px"><a class="tugma" href="#lobby">' + ic('gamepad') +
        "<span>O'yinlar markaziga qaytish</span></a></div>";
      G.focusMain();
    }

    function leave() {
      if (!S || view === 'terminal') { G.go('lobby'); return; }
      var msg = null;
      if (S.status === 'playing') {
        msg = "O'yinni tark etasizmi? Hozirgi natijangiz saqlanadi, lekin bonuslar berilmaydi.";
      } else if (S.status === 'waiting') {
        msg = 'Roomdan chiqasizmi?';
      }
      (msg ? G.confirm(msg) : Promise.resolve(true)).then(function (ok) {
        if (!ok) return;
        poller.stop();
        G.api.leave(code).then(function () { G.go('lobby'); });
      });
    }

    // ── Holatni qo'llash ────────────────────────────────
    function apply(st) {
      if (!st || st.same || scope.dead) return;
      S = st;
      etag = st.etag;
      setHeader();
      if (st.status === 'expired' || st.status === 'cancelled') {
        terminal({ code: st.status === 'expired' ? 'room_expired' : 'room_closed',
          error: st.status === 'expired' ? 'Room uzoq vaqt harakatsiz qoldi. Yangi room yarating.' : "Hamma o'yinchilar roomdan chiqib ketdi." });
        return;
      }
      var sess = st.session;
      var key = 'wait';
      if (st.status === 'waiting') key = 'lobby';
      else if (st.status === 'finished' && sess) key = 'res:' + sess.id;
      else if (sess && sess.phase === 'countdown') key = 'cd:' + sess.id;
      else if (sess && (sess.phase === 'question' || sess.phase === 'reveal')) key = 'q:' + sess.id + ':' + sess.q_index;

      if (key !== view) {
        view = key;
        if (key === 'lobby') drawLobby();
        else if (key.indexOf('cd:') === 0) drawCountdown();
        else if (key.indexOf('q:') === 0) drawQuestion();
        else if (key.indexOf('res:') === 0) drawResults();
        else el.innerHTML = UI.yuklanmoqda("O'yin tayyorlanmoqda...");
      }
      if (view === 'lobby') updateLobby();
      else if (view.indexOf('q:') === 0) updateQuestion();
      else if (view.indexOf('res:') === 0) put('natijaPanel', resultsPanel()) && bindResultsPanel();
      notices();
    }

    function notices() {
      if (!S || S.status !== 'playing') return;
      var gone = S.players.filter(function (p) { return !p.me && !p.online; });
      if (gone.length) {
        G.banner((gone.length === 1 ? gone[0].name : gone.length + " ta o'yinchi") +
          ' aloqasi uzildi — qaytishini kutyapmiz...');
      }
    }

    function ensureRenderer() {
      var name = S.game.renderer;
      if (G.renderers[name]) return Promise.resolve(G.renderers[name]);
      return G.load('js/games/renderers/' + name + '.js').then(function () { return G.renderers[name]; });
    }

    // ── Kutish zali ─────────────────────────────────────
    function drawLobby() {
      var v = viewScope();
      el.innerHTML =
        '<section class="oy-kod-karta">' +
          '<span class="oy-kod-yorliq">Room kodi</span>' +
          '<div class="oy-kod" aria-label="Room kodi: ' + esc(spelled(code)) + '">' + esc(code) + '</div>' +
          '<div class="oy-kod-tugmalar">' +
            '<button class="tugma tugma-mayda tugma-ikkilamchi" type="button" id="kodNusxa">' + ic('copy') + '<span>Nusxalash</span></button>' +
            '<button class="tugma tugma-mayda" type="button" id="taklifTugma">' + ic('share') + '<span>Taklif qilish</span></button>' +
          '</div>' +
        '</section>' +
        '<section class="karta oy-info" id="roomInfo"></section>' +
        '<section class="bo-lim">' +
          '<div class="bo-lim-bosh"><h2 data-fokus>O\'yinchilar</h2><span class="izoh" id="oyinchiSon"></span></div>' +
          '<ul class="oy-oyinchilar" id="oyinchilar" aria-live="polite"></ul>' +
        '</section>' +
        '<div class="oy-panel" id="lobbyPanel"></div>';
      v.on(document.getElementById('kodNusxa'), 'click', function () { G.copy(code); });
      v.on(document.getElementById('taklifTugma'), 'click', openInvite);
      G.focusMain();
      if (G.flash && G.flash.invite) {
        G.flash = null;
        setTimeout(openInvite, 250);
      }
      ensureRenderer().catch(function () { /* o'yin boshlanganda qayta urinamiz */ });
    }

    function playerRow(p) {
      return '<li class="oy-oyinchi' + (p.me ? ' men' : '') + (p.online ? '' : ' oflayn') + '">' +
        '<span class="avatar" aria-hidden="true">' + esc(G.initial(p.name)) + '</span>' +
        '<span class="oy-oyinchi-matn"><b>' + esc(p.name) + (p.me ? ' (siz)' : '') + '</b>' +
          '<small>Daraja ' + p.level + (p.online ? '' : ' • oflayn') + '</small></span>' +
        (p.host ? '<span class="oy-toj" title="Host">' + ic('crown') + '<span class="oy-sr">Host</span></span>' : '') +
        '<span class="oy-tayyor ' + (p.ready ? 'ha' : 'yoq') + '">' + (p.ready ? ic('check') + 'Tayyor' : 'Kutilmoqda') + '</span>' +
        (S.me.host && !p.me ? '<button class="oy-chiqar" type="button" data-pid="' + p.pid + '" aria-label="' +
          esc(p.name) + 'ni roomdan chiqarish">' + ic('x') + '</button>' : '') +
      '</li>';
    }

    function emptySlots() {
      var free = S.settings.max_players - S.players.length;
      if (free <= 0) return '';
      var out = '';
      for (var i = 0; i < Math.min(free, 2); i++) {
        out += '<li class="oy-oyinchi bosh"><span class="avatar" aria-hidden="true">+</span>' +
          '<span class="oy-oyinchi-matn"><b>Bo\'sh joy</b><small>Do\'stingizni taklif qiling</small></span></li>';
      }
      if (free > 2) out += '<li class="oy-joy-qoldi">yana ' + (free - 2) + ' ta bo\'sh joy</li>';
      return out;
    }

    function lobbyPanel() {
      if (S.me.host) {
        return '<button class="tugma" type="button" id="startTugma"' + (S.can_start ? '' : ' disabled') + '>' +
            ic('play') + "<span>O'yinni boshlash</span></button>" +
          '<p class="izoh oy-panel-izoh">' + esc(S.can_start ? "Hamma tayyor — boshlashingiz mumkin!" : S.start_hint) + '</p>' +
          '<button class="tugma tugma-ikkilamchi tugma-mayda" type="button" id="sozlashTugma">' + ic('settings') +
            '<span>Sozlamalar</span></button>';
      }
      return '<button class="tugma' + (S.me.ready ? ' tugma-ikkilamchi' : '') + '" type="button" id="tayyorTugma" aria-pressed="' +
          S.me.ready + '">' + ic(S.me.ready ? 'checkCircle' : 'check') + '<span>' +
          (S.me.ready ? 'Tayyorsiz — bekor qilish' : 'Tayyorman') + '</span></button>' +
        '<p class="izoh oy-panel-izoh">' + (S.me.ready ? "Host o'yinni boshlashini kuting" : "Tayyor bo'lsangiz, tugmani bosing") + '</p>';
    }

    function updateLobby() {
      var s = S.settings;
      put('roomInfo',
        '<div class="oy-info-bosh"><span class="oy-belgi">' + ic(S.game.icon) + '</span>' +
          '<div><b>' + esc(S.game.name) + '</b><small>' + esc(S.game.rules) + '</small></div></div>' +
        '<div class="oy-chiplar">' +
          chip(s.subject_icon, s.subject_name) + (s.topic_title ? chip('bookOpen', s.topic_title) : '') +
          chip('target', s.difficulty_name) +
          chip('inbox', s.question_count + (S.game.renderer === 'match' ? ' raund' : ' savol')) +
          chip('clock', '~' + s.minutes + ' daqiqa') +
          chip(s.is_public ? 'users' : 'lock', s.is_public ? 'Ochiq room' : 'Yopiq room') +
        '</div>');
      var count = document.getElementById('oyinchiSon');
      if (count) count.textContent = S.players.length + ' / ' + s.max_players;
      if (put('oyinchilar', S.players.map(playerRow).join('') + emptySlots())) {
        document.querySelectorAll('#oyinchilar [data-pid]').forEach(function (b) {
          vs.on(b, 'click', function () { kick(Number(b.dataset.pid), b.getAttribute('aria-label')); });
        });
      }
      if (put('lobbyPanel', lobbyPanel())) bindLobbyPanel();
    }

    function act(promise, btn) {
      if (btn) btn.disabled = true;
      return promise.then(function (res) {
        if (btn && !scope.dead) btn.disabled = false;
        if (!res.ok) { UI.xabar(res.error, 'xato'); poller.now(); return res; }
        apply(res.state);
        return res;
      });
    }

    function bindLobbyPanel() {
      var start = document.getElementById('startTugma');
      if (start) vs.on(start, 'click', function () { act(G.api.start(code), start); });
      var settings = document.getElementById('sozlashTugma');
      if (settings) vs.on(settings, 'click', openSettings);
      var ready = document.getElementById('tayyorTugma');
      if (ready) vs.on(ready, 'click', function () { act(G.api.ready(code, !S.me.ready), ready); });
    }

    function kick(pid, label) {
      G.confirm((label || "O'yinchini chiqarish") + '?').then(function (ok) {
        if (ok) act(G.api.kick(code, pid));
      });
    }

    function openSettings() {
      G.catalog().then(function (cat) {
        var game = cat.ok && G.gameByKey(cat, S.game.type);
        if (!game || scope.dead) return;
        var s = {
          game: game.key, subject: S.settings.subject, topic: S.settings.topic || '',
          difficulty: S.settings.difficulty, count: S.settings.question_count,
          max_players: S.settings.max_players, public: S.settings.is_public,
        };
        var ms = new G.Scope();
        var m = G.modal(
          '<h2 id="oyModalSarlavha">Room sozlamalari</h2>' +
          '<form class="oy-forma" id="roomSozlama" novalidate>' + G.settingsForm(game, s) + '</form>' +
          '<p class="oy-xato" id="roomSozlamaXato" role="alert"></p>' +
          '<button class="tugma" type="button" id="sozlamaSaqla" data-avto-fokus>Saqlash</button>',
          { onClose: function () { ms.dispose(); } });
        G.bindSettingsForm(m.querySelector('#roomSozlama'), game, s, ms);
        var save = m.querySelector('#sozlamaSaqla');
        ms.on(save, 'click', function () {
          save.disabled = true;
          G.api.settings(code, G.settingsPayload(s)).then(function (res) {
            save.disabled = false;
            if (!res.ok) { m.querySelector('#roomSozlamaXato').textContent = res.error; return; }
            G.closeModal();
            apply(res.state);
            UI.xabar('Sozlamalar saqlandi', 'muvaffaqiyat');
          });
        });
      });
    }

    function openInvite() {
      if (scope.dead || !S) return;
      G.catalog().then(function (cat) {
        var bot = (cat && cat.bot) || 'bilimsaribot';
        var link = 'https://t.me/' + bot + '?start=room_' + code;
        var text = "BilimSari'da " + S.game.name + " o'yiniga taklif qilaman! Room kodi: " + code;
        var m = G.modal(
          '<h2 id="oyModalSarlavha">Do\'stlarni taklif qilish</h2>' +
          '<p class="izoh">Do\'stingiz havolani ochsa, shu roomga kiradi. Yoki O\'yinlar bo\'limida ' +
            '“Roomga qo\'shilish” tugmasini bosib, kodni kiritadi.</p>' +
          '<div class="oy-kod katta" aria-label="Room kodi: ' + esc(spelled(code)) + '">' + esc(code) + '</div>' +
          '<div class="oy-taklif-tugmalar">' +
            '<button class="tugma" type="button" id="tgYubor" data-avto-fokus>' + ic('send') + '<span>Telegram orqali yuborish</span></button>' +
            '<button class="tugma tugma-ikkilamchi" type="button" id="havolaNusxa">' + ic('copy') + '<span>Havolani nusxalash</span></button>' +
            '<button class="tugma tugma-ikkilamchi" type="button" id="kodNusxa2">' + ic('copy') + '<span>Kodni nusxalash</span></button>' +
          '</div>');
        m.querySelector('#tgYubor').onclick = function () {
          var tg = window.Telegram && window.Telegram.WebApp;
          var url = 'https://t.me/share/url?url=' + encodeURIComponent(link) + '&text=' + encodeURIComponent(text);
          if (tg && tg.initData && tg.openTelegramLink) tg.openTelegramLink(url);
          else if (navigator.share) navigator.share({ title: 'BilimSari', text: text, url: link }).catch(function () {});
          else window.open(url, '_blank', 'noopener');
        };
        m.querySelector('#havolaNusxa').onclick = function () { G.copy(text + '\n' + link); };
        m.querySelector('#kodNusxa2').onclick = function () { G.copy(code); };
      });
    }

    // ── 3, 2, 1, GO! ────────────────────────────────────
    function drawCountdown() {
      var v = viewScope();
      var sess = S.session;
      el.innerHTML =
        '<section class="oy-countdown">' +
          '<p class="oy-countdown-matn">' + (S.source === 'random' ? 'Raqib topildi!' : "O'yin boshlanmoqda") + '</p>' +
          '<div class="oy-countdown-son" id="cdSon" aria-hidden="true"></div>' +
          '<p class="izoh">' + esc(S.game.name) + ' • ' + esc(S.settings.subject_name) + ' • ' + sess.total +
            (S.game.renderer === 'match' ? ' raund' : ' savol') + '</p>' +
          '<ul class="oy-countdown-oyinchilar">' + S.players.map(function (p) {
            return '<li><span class="avatar" aria-hidden="true">' + esc(G.initial(p.name)) + '</span>' + esc(p.name) + '</li>';
          }).join('') + '</ul>' +
          '<p class="oy-sr" aria-live="assertive" id="cdSr"></p>' +
        '</section>';
      ensureRenderer().catch(function () {});
      var last = null;
      function tick() {
        var left = S.session.phase_ends_ms - G.clock.now();
        var n = Math.ceil(left / 1000);
        var txt = n > 3 ? '' : (n >= 1 ? String(n) : 'GO!');
        if (txt === last) return;
        last = txt;
        var node = document.getElementById('cdSon');
        if (!node) return;
        node.textContent = txt;
        node.classList.remove('pop');
        void node.offsetWidth;   // animatsiyani qayta boshlash
        node.classList.add('pop');
        document.getElementById('cdSr').textContent = txt === 'GO!' ? 'Boshladik!' : txt;
      }
      tick();
      v.interval(tick, 100);
    }

    // ── Savol ───────────────────────────────────────────
    function scoreboard() {
      var ps = S.players.slice().sort(function (a, b) { return b.score - a.score; });
      var me = ps.filter(function (p) { return p.me; })[0];
      var rival = ps.filter(function (p) { return !p.me; })[0];
      var cell = function (label, score, rank, cls) {
        return '<div class="oy-hisob-el' + (cls ? ' ' + cls : '') + '"><span>' + esc(label) + '</span><b>' + score +
          '</b><small>' + rank + '-o\'rin</small></div>';
      };
      return (me ? cell('Siz', me.score, ps.indexOf(me) + 1, 'men') : '') +
        (rival ? cell(rival.name, rival.score, ps.indexOf(rival) + 1) : '') +
        (ps.length > 2 ? '<div class="oy-hisob-el"><span>O\'yinchilar</span><b>' + ps.length + '</b><small>jami</small></div>' : '');
    }

    function drawQuestion() {
      var v = viewScope();
      var sess = S.session;
      var q = sess.question;
      ctrl = null;
      revealed = null;
      sending = false;
      el.innerHTML =
        '<div class="oy-oyin-tepa">' +
          '<span class="oy-savol-son">' + (S.game.renderer === 'match' ? 'Raund ' : 'Savol ') +
            '<b>' + (sess.q_index + 1) + '</b> / ' + sess.total + '</span>' +
          '<span class="oy-taymer" id="taymer" role="timer" aria-label="Qolgan vaqt">' + G.mmss(sess.time_limit_ms) + '</span>' +
        '</div>' +
        '<div class="oy-taymer-chiziq" aria-hidden="true"><i id="taymerChiziq"></i></div>' +
        '<div class="oy-hisob" id="hisob"></div>' +
        '<article class="karta oy-savol">' +
          (q.topic_title ? '<span class="oy-chip">' + esc(q.topic_title) + '</span>' : '') +
          '<p class="savol-matn" data-fokus>' + G.rich(q.prompt) + '</p>' +
          '<div id="javobJoy">' + UI.yuklanmoqda('') + '</div>' +
        '</article>' +
        '<p class="oy-holat" id="holatMatn" aria-live="polite"></p>' +
        '<div id="revealJoy"></div>' +
        '<p class="oy-sr" aria-live="assertive" id="eshittirish"></p>';
      document.getElementById('eshittirish').textContent =
        (S.game.renderer === 'match' ? 'Raund ' : 'Savol ') + (sess.q_index + 1) + ', jami ' + sess.total + '.';
      G.focusMain();

      ensureRenderer().then(function (r) {
        if (v.dead) return;
        ctrl = r.mount(document.getElementById('javobJoy'), q, {
          scope: v, answered: S.session.my_answer, onAnswer: sendAnswer,
        });
        updateQuestion();
      }, function () {
        if (!v.dead) document.getElementById('javobJoy').innerHTML = UI.xatoHolat("O'yin fayli yuklanmadi.", function () { G.render(); });
      });
      tickTimer();
      v.interval(tickTimer, 250);
    }

    function tickTimer() {
      var sess = S && S.session;
      var t = document.getElementById('taymer');
      var bar = document.getElementById('taymerChiziq');
      if (!sess || !t || !bar) return;
      if (sess.phase === 'question') {
        var left = sess.deadline_ms - G.clock.now();
        t.textContent = G.mmss(left);
        bar.style.width = Math.max(0, Math.min(100, left / sess.time_limit_ms * 100)) + '%';
        var urgent = left <= 5000;
        t.classList.toggle('shoshil', urgent);
        bar.classList.toggle('shoshil', urgent);
      } else {
        t.textContent = '00:00';
        bar.style.width = '0%';
        var next = document.getElementById('keyingiMatn');
        if (next && sess.phase === 'reveal') {
          var secs = Math.max(0, Math.ceil((sess.phase_ends_ms - G.clock.now()) / 1000));
          next.textContent = (sess.q_index + 1 < sess.total ? 'Keyingi savol' : 'Natijalar') + ' ' + secs + ' soniyadan so\'ng';
        }
      }
    }

    function setStatus(text) {
      var n = document.getElementById('holatMatn');
      if (n) n.textContent = text;
    }

    function updateQuestion() {
      var sess = S.session;
      if (!sess) return;
      put('hisob', scoreboard());
      if (sess.phase === 'question') {
        if (sess.my_answer != null) {
          if (ctrl) ctrl.mine(sess.my_answer);
          setStatus('Javobingiz qabul qilindi. Boshqalar kutilmoqda (' + sess.answered_count + '/' + sess.expected_count + ')');
        } else if (!sending) {
          setStatus(sess.answered_count ? sess.answered_count + " ta o'yinchi javob berdi" : '');
        }
      } else if (sess.phase === 'reveal' && revealed !== view && ctrl) {
        revealed = view;
        showReveal();
      }
    }

    function sendAnswer(answer) {
      var sess = S && S.session;
      if (sending || !sess || sess.phase !== 'question' || sess.my_answer != null) return;
      sending = true;
      if (ctrl) ctrl.mine(answer);
      setStatus('Yuborilmoqda...');
      G.api.answer(code, sess.q_index, answer).then(function (res) {
        sending = false;
        if (scope.dead) return;
        if (res.ok) { apply(res.state); return; }
        if (res.code === 'already_answered') { poller.now(); return; }
        if (res.code === 'too_late') { setStatus('Vaqt tugadi — javob qabul qilinmadi.'); poller.now(); return; }
        if (ctrl) ctrl.unlock();
        setStatus(res.error || "Javob yuborilmadi. Qayta urinib ko'ring.");
      });
    }

    function showReveal() {
      var sess = S.session;
      var rv = sess.reveal;
      var q = sess.question;
      if (!rv) return;
      ctrl.reveal(rv, sess.my_answer);
      setStatus('');
      var html = '';
      var sr;
      if (q.kind === 'match') {
        var total = q.left.length;
        var ok = rv.my_correct;
        html += '<div class="oy-natija-quti ' + (ok ? 'togri' : 'xato') + '">' + ic(ok ? 'check' : 'x') +
          '<b>' + (rv.answered ? (ok ? "Hammasi to'g'ri!" : rv.my_partial + '/' + total + " juftlik to'g'ri") : 'Javob berilmadi') +
          '</b>' + (rv.my_points ? '<span class="oy-ball-plus">+' + rv.my_points + '</span>' : '') + '</div>';
        var tips = (rv.pairs_explain || []).map(function (t, i) {
          return t ? '<li><b>' + G.rich(q.left[i]) + '</b> → ' + G.rich(q.right[rv.answer[i]]) + '<br><small>' + esc(t) + '</small></li>' : '';
        }).join('');
        if (tips) html += '<ul class="tushuntirish oy-juftlar">' + tips + '</ul>';
        sr = ok ? "Hammasi to'g'ri!" : rv.my_partial + ' ta juftlik to\'g\'ri.';
      } else {
        var right = q.options[rv.answer];
        if (rv.my_correct) {
          html += '<div class="oy-natija-quti togri">' + ic('check') + "<b>To'g'ri!</b>" +
            (rv.my_points ? '<span class="oy-ball-plus">+' + rv.my_points + '</span>' : '<span class="izoh">sekinroq bo\'ldi</span>') + '</div>';
          if (rv.explain) html += '<div class="tushuntirish">' + esc(rv.explain) + '</div>';
          sr = "To'g'ri javob!";
        } else {
          html += '<div class="oy-natija-quti xato">' + ic('x') + '<b>' + (rv.answered ? "Noto'g'ri" : 'Javob berilmadi') + '</b></div>' +
            '<div class="tushuntirish xato"><b>To\'g\'ri javob: ' + G.rich(right) + '</b>' + esc(rv.explain || '') + '</div>';
          sr = "To'g'ri javob: " + right;
        }
      }
      if (S.game.mode === 'first') {
        html += '<p class="izoh oy-birinchi">' + (rv.first_name
          ? ic('zap') + 'Birinchi to\'g\'ri javob: <b>' + esc(rv.first_name) + '</b>'
          : "Hech kim to'g'ri javob bermadi") + '</p>';
      }
      if (rv.gains && rv.gains.length) {
        html += '<ul class="oy-yutuqlar" aria-label="Shu savolda ball olganlar">' + rv.gains.map(function (g) {
          return '<li' + (g.me ? ' class="men"' : '') + '><span>' + esc(g.name) + (g.me ? ' (siz)' : '') + '</span><b>+' + g.points + '</b></li>';
        }).join('') + '</ul>';
      }
      html += '<p class="izoh oy-keyingi" id="keyingiMatn"></p>';
      document.getElementById('revealJoy').innerHTML = html;
      document.getElementById('eshittirish').textContent = sr;
      tickTimer();
    }

    // ── Natijalar ───────────────────────────────────────
    function stat(value, label) {
      return '<div class="stat"><b>' + esc(value) + '</b><span>' + esc(label) + '</span></div>';
    }

    function xpNote(me) {
      if (!me.multiplayer) return "Chaqmoq kamida 2 o'yinchi qatnashgan o'yinlarda beriladi.";
      var text = "Hisobga o'tdi: +" + me.xp + ' ball' + (me.bonus ? ' (bonus +' + me.bonus + ')' : '');
      if (me.capped) text += " — bugungi o'yin limiti to'ldi";
      return text + '. Har 10 ball = 1 chaqmoq.';
    }

    function reviewItem(it) {
      var mark = '<span class="oy-belgi-kichik ' + (it.correct ? 'togri' : 'xato') + '">' + ic(it.correct ? 'check' : 'x') + '</span>';
      var body;
      if (it.kind === 'match') {
        body = '<p>' + it.n + '-raund — ' + (it.partial || 0) + '/' + it.pairs.length + ' juftlik to\'g\'ri</p>' +
          '<ul class="oy-juftlar">' + it.pairs.map(function (p) {
            return '<li>' + G.rich(p[0]) + ' → <b>' + G.rich(p[1]) + '</b></li>';
          }).join('') + '</ul>';
      } else {
        body = '<p>' + G.rich(it.prompt) + '</p>' +
          (!it.answered ? '<p class="izoh">Javob berilmagan</p>'
            : (!it.correct ? '<p class="izoh">Sizning javobingiz: ' + G.rich(it.your_answer) + '</p>' : '')) +
          '<p><b>To\'g\'ri javob: ' + G.rich(it.right_answer) + '</b></p>' +
          (it.explain ? '<p class="izoh">' + esc(it.explain) + '</p>' : '');
      }
      return '<li class="oy-korib-el">' + mark + '<div>' + body + '</div></li>';
    }

    function learning(L) {
      var strong = (L.strong || []).map(function (t) {
        return '<li>' + ic('check') + '<span>' + esc(t.title) + ' <small>' + t.correct + '/' + t.total + '</small></span></li>';
      }).join('');
      var weak = (L.weak || []).map(function (t) {
        return '<li>' + ic('target') + '<span>' + esc(t.title) + ' <small>' + t.correct + '/' + t.total + '</small></span>' +
          (t.link ? '<a class="oy-dars-havola" href="' + esc(topicHref(t.link)) + '">Darsni ochish ›</a>' : '') + '</li>';
      }).join('');
      var review = (L.review || []).map(reviewItem).join('');
      return '<section class="karta oy-organdim">' +
        '<h3>' + ic('sparkle') + "<span>Nimalarni o'rgandingiz?</span></h3>" +
        '<p>' + esc(L.summary || '') + '</p>' +
        (strong ? '<div class="oy-mavzular yaxshi"><b>Kuchli mavzularingiz</b><ul>' + strong + '</ul></div>' : '') +
        (weak ? '<div class="oy-mavzular zaif"><b>Ko\'proq mashq qilish kerak</b><ul>' + weak + '</ul></div>' : '') +
        (review ? '<details class="oy-korib"><summary>Savollarni ko\'rib chiqish</summary><ol>' + review + '</ol></details>' : '') +
      '</section>';
    }

    function resultsPanel() {
      return (S.me.host
        ? '<button class="tugma" type="button" id="yanaTugma">' + ic('refresh') + "<span>Yana o'ynash</span></button>"
        : '<p class="izoh oy-panel-izoh">Host yangi o\'yin boshlasa, shu yerda qolasiz.</p>') +
        '<button class="tugma tugma-ikkilamchi" type="button" id="markazTugma">' + ic('gamepad') + "<span>O'yinlar markazi</span></button>";
    }

    function bindResultsPanel() {
      var again = document.getElementById('yanaTugma');
      if (again) vs.on(again, 'click', function () { act(G.api.rematch(code), again); });
      var hub = document.getElementById('markazTugma');
      if (hub) vs.on(hub, 'click', function () {
        poller.stop();
        G.api.leave(code).then(function () { G.go('lobby'); });
      });
    }

    function drawResults() {
      viewScope();
      var sess = S.session;
      var r = sess.results || {};
      var me = r.me;
      var rows = (r.rows || []).map(function (x) {
        return '<li class="reyting-qator' + (x.me ? ' men' : '') + '">' +
          '<span class="o-rin' + (x.rank <= 3 ? ' medal-' + x.rank : '') + '" aria-label="' + x.rank + '-o\'rin">' +
            (x.rank <= 3 ? ic('medal') : x.rank) + '</span>' +
          '<span class="avatar" aria-hidden="true">' + esc(G.initial(x.name)) + '</span>' +
          '<span class="ism">' + esc(x.name) + (x.me ? ' (siz)' : '') +
            '<small>' + x.correct + " to'g'ri • " + x.accuracy + '%</small></span>' +
          '<span class="oy-ball">' + x.score + '<small>ball</small></span></li>';
      }).join('');
      var title = !me ? "O'yin natijasi" : (me.won ? "G'alaba! Siz 1-o'rindasiz" : me.rank + "-o'rin");
      var mins = me ? Math.floor(me.duration_ms / 60000) : 0;
      var secs = me ? Math.round(me.duration_ms / 1000) % 60 : 0;
      el.innerHTML =
        '<section class="oy-natija-bosh">' +
          '<span class="oy-belgi katta' + (me && me.won ? ' oltin' : '') + '">' + ic('trophy') + '</span>' +
          '<h2 data-fokus>' + esc(title) + '</h2>' +
          '<p class="izoh">' + esc(S.game.name) + ' • ' + esc(S.settings.subject_name) +
            (S.settings.topic_title ? ' • ' + esc(S.settings.topic_title) : '') + '</p>' +
          (sess.end_reason === 'players_left'
            ? '<p class="oy-ogoh">' + ic('alert') + "<span>Raqiblar chiqib ketgani uchun o'yin muddatidan oldin yakunlandi.</span></p>" : '') +
        '</section>' +
        '<ol class="oy-podium" aria-label="Natijalar jadvali">' + rows + '</ol>' +
        (me
          ? '<div class="stat-setka oy-natija-stat">' +
              stat(me.correct, "To'g'ri") + stat(me.wrong, "Noto'g'ri") + stat(me.accuracy + '%', 'Aniqlik') +
              stat(mins + ':' + String(secs).padStart(2, '0'), 'Vaqt') + stat(me.score, 'Ball') + stat('+' + me.chaqmoq, 'Chaqmoq') +
            '</div><p class="izoh oy-xp-izoh">' + esc(xpNote(me)) + '</p>' + learning(r.learning || {})
          : '<p class="oy-ogoh">' + ic('users') + "<span>Siz bu o'yinda qatnashmadingiz. Host yangi o'yin boshlashini kuting.</span></p>") +
        '<div class="oy-panel" id="natijaPanel"></div>';
      G.focusMain();
      if (me && me.won) celebrate();
    }
  };
})();
