/* BilimSari Game Hub — lobby, o'yin sozlamalari, random raqib qidirish,
   kod orqali qo'shilish va o'yin reytingi. Room ekrani (room.js) va o'yin
   renderlari kerak bo'lgandagina dangasa yuklanadi. */
(function () {
  'use strict';

  var G = window.Games;
  var esc = UI.esc;
  var ic = UI.nishon;

  function subjectsLabel(game) {
    var s = game.subjects || [];
    if (s.length === 1) return s[0].name;
    if (s.length === 2) return s[0].name + ', ' + s[1].name;
    return s.length + ' ta fan';
  }

  function tabs(active) {
    return '<div class="oy-tablar" role="tablist" aria-label="Game Hub bo\'limlari">' +
      '<a role="tab" href="#lobby" aria-selected="' + (active === 'lobby') + '">' + ic('gamepad') + "<span>O'yinlar</span></a>" +
      '<a role="tab" href="#reyting" aria-selected="' + (active === 'reyting') + '">' + ic('trophy') + '<span>Reyting</span></a>' +
      '</div>';
  }

  function skeletonCards(n) {
    var out = '';
    for (var i = 0; i < n; i++) out += '<div class="skelet oy-karta-skelet"></div>';
    return out;
  }

  // ───────────────────────── Lobby ─────────────────────────

  function gameCard(g) {
    return '<article class="oy-karta">' +
      '<div class="oy-karta-bosh">' +
        '<span class="oy-belgi">' + ic(g.icon) + '</span>' +
        '<div class="oy-karta-matn"><h3>' + esc(g.name) + '</h3><p>' + esc(g.tagline) + '</p></div>' +
      '</div>' +
      '<p class="oy-meta">' + esc(subjectsLabel(g)) + ' • ' + g.default_count + ' savol • 2–16 o\'yinchi • ~' + g.minutes + ' daqiqa</p>' +
      '<div class="oy-karta-past">' +
        '<span class="oy-chip">Oson · O\'rta · Qiyin</span>' +
        '<button class="tugma tugma-mayda" type="button" data-oyin="' + esc(g.key) + '" aria-label="' + esc(g.name) + ' — o\'ynash">' +
          ic('play') + "<span>O'ynash</span></button>" +
      '</div>' +
    '</article>';
  }

  function roomRow(r) {
    return '<div class="oy-room-qator">' +
      '<span class="oy-belgi kichik">' + ic(r.icon) + '</span>' +
      '<div class="oy-room-matn"><b>' + esc(r.game_name) + '</b>' +
        '<small>' + esc(r.subject_name) + ' • ' + esc(r.difficulty_name) + ' • host: ' + esc(r.host) + '</small></div>' +
      '<span class="oy-pill" aria-label="' + r.players + ' / ' + r.max_players + ' o\'yinchi">' + ic('users') + r.players + '/' + r.max_players + '</span>' +
      '<button class="tugma tugma-mayda" type="button" data-kod="' + esc(r.code) + '">Qo\'shilish</button>' +
    '</div>';
  }

  G.route('lobby', function (arg, scope) {
    G.header({ title: "O'yinlar", sub: 'Bilim + raqobat + zavq', back: 'dashboard.html' });
    var el = G.el();
    el.innerHTML =
      tabs('lobby') +
      '<section class="oy-hero">' +
        '<div><h2 data-fokus>O\'yin tanlang</h2><p>Do\'stlaringiz bilan bilim bellashing</p></div>' +
        '<div class="oy-jonli" aria-live="polite">' +
          '<span class="oy-pill"><i class="oy-nuqta" aria-hidden="true"></i><b id="onlaynSon">…</b>&nbsp;onlayn</span>' +
          '<span class="oy-pill"><b id="roomSon">…</b>&nbsp;faol room</span>' +
        '</div>' +
      '</section>' +
      '<div id="meningRoom"></div>' +
      '<div class="oy-amallar">' +
        '<button class="tugma tugma-ikkilamchi tugma-mayda" type="button" id="qoshilishTugma">' + ic('logIn') + "<span>Roomga qo'shilish</span></button>" +
        '<a class="tugma tugma-ikkilamchi tugma-mayda" href="game.html">' + ic('target') + '<span>Yakka mashq</span></a>' +
      '</div>' +
      '<div class="oy-setka" id="oyinlar">' + skeletonCards(4) + '</div>' +
      '<section class="bo-lim">' +
        '<div class="bo-lim-bosh"><h2>Faol roomlar</h2><span class="izoh">Ochiq roomlarga qo\'shiling</span></div>' +
        '<div id="roomlar"><div class="skelet" style="height:64px;margin-bottom:8px"></div><div class="skelet" style="height:64px"></div></div>' +
      '</section>';
    G.focusMain();

    scope.on(document.getElementById('qoshilishTugma'), 'click', function () { openJoin(); });

    G.catalog().then(function (res) {
      if (scope.dead) return;
      var box = document.getElementById('oyinlar');
      if (!res.ok) { box.innerHTML = UI.xatoHolat(res.error, function () { G.render(); }); return; }
      box.innerHTML = res.games.map(gameCard).join('');
      box.querySelectorAll('[data-oyin]').forEach(function (b) {
        scope.on(b, 'click', function () { G.go('setup/' + b.dataset.oyin); });
      });
    });

    var poller = new G.Poller({
      fetch: G.api.lobby,
      interval: function () { return 10000; },
      hiddenFactor: 6,
      onError: function () { G.banner("Internet aloqasi uzildi. Qayta ulanmoqda..."); },
      onData: function (res) {
        if (!res.ok) return;
        G.banner(null);
        document.getElementById('onlaynSon').textContent = res.online;
        document.getElementById('roomSon').textContent = res.rooms.length;
        var mine = document.getElementById('meningRoom');
        mine.innerHTML = res.my_room
          ? '<a class="oy-mening-room" href="#room/' + esc(res.my_room.code) + '">' + ic('play') +
            '<span>Sizning faol roomingiz: <b>' + esc(res.my_room.code) + '</b></span><span class="oy-oq">Qaytish ›</span></a>'
          : '';
        var box = document.getElementById('roomlar');
        if (!res.rooms.length) {
          box.innerHTML = '<div class="oy-bosh">' + ic('users') +
            '<div><b>Hozircha faol room yo\'q</b><p>Do\'stingiz bilan yangi room yarating yoki random raqib toping.</p></div></div>';
          return;
        }
        box.innerHTML = res.rooms.map(roomRow).join('');
        box.querySelectorAll('[data-kod]').forEach(function (b) {
          scope.on(b, 'click', function () { joinCode(b.dataset.kod, b); });
        });
      },
    });
    poller.start();
    scope.add(function () { poller.stop(); });
    scope.on(document, 'visibilitychange', function () { if (!document.hidden) poller.now(); });
  });

  // ───────────────────────── Kod orqali qo'shilish ─────────────────────────

  function joinCode(code, btn, errEl) {
    if (btn) btn.disabled = true;
    return G.api.join(code).then(function (res) {
      if (btn) btn.disabled = false;
      if (res.ok) {
        G.closeModal();
        G.go('room/' + res.code);
        return;
      }
      if (errEl) errEl.textContent = res.error;
      else UI.xabar(res.error, 'xato');
    });
  }

  function openJoin() {
    var m = G.modal(
      '<h2 id="oyModalSarlavha">Roomga qo\'shilish</h2>' +
      '<p class="izoh">Do\'stingiz yuborgan 6 belgili kodni kiriting.</p>' +
      '<form id="kodForma" class="oy-kod-forma" novalidate>' +
        '<label for="kodMaydon" class="oy-sr">Room kodi</label>' +
        '<input id="kodMaydon" class="kiritish oy-kod-kiritish" data-avto-fokus inputmode="text" autocomplete="off"' +
          ' autocapitalize="characters" spellcheck="false" maxlength="7" placeholder="AB7K92" aria-describedby="kodXato">' +
        '<p class="oy-xato" id="kodXato" role="alert"></p>' +
        '<button class="tugma" type="submit" id="kodYubor">' + ic('logIn') + "<span>Qo'shilish</span></button>" +
      '</form>'
    );
    var input = m.querySelector('#kodMaydon');
    var err = m.querySelector('#kodXato');
    input.addEventListener('input', function () {
      var v = input.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
      if (input.value !== v) input.value = v;
      err.textContent = '';
    });
    m.querySelector('#kodForma').addEventListener('submit', function (e) {
      e.preventDefault();
      var code = input.value.trim();
      if (code.length !== 6) { err.textContent = "Kod 6 ta harf va raqamdan iborat bo'ladi."; input.focus(); return; }
      joinCode(code, m.querySelector('#kodYubor'), err);
    });
  }
  G.openJoin = openJoin;

  // ─────── Sozlamalar formasi (setup ekrani va room sozlamalari uchun umumiy) ───────

  G.settingsForm = function (game, s) {
    var subject;
    if (game.subjects.length === 1) {
      subject = '<p class="oy-maydon-qiymat">' + ic(game.subjects[0].icon) + esc(game.subjects[0].name) + '</p>';
    } else if (game.subjects.length <= 4) {
      subject = G.segment('subject', 'Fan', game.subjects.map(function (x) { return { value: x.key, label: x.name }; }), s.subject);
    } else {
      subject = '<select class="kiritish" id="fanTanlov" aria-label="Fan">' + game.subjects.map(function (x) {
        return '<option value="' + esc(x.key) + '"' + (x.key === s.subject ? ' selected' : '') + '>' + esc(x.name) + '</option>';
      }).join('') + '</select>';
    }
    return '<div class="oy-maydon"><span class="oy-yorliq">Fan</span>' + subject + '</div>' +
      '<div class="oy-maydon"><label class="oy-yorliq" for="mavzuTanlov">Mavzu</label>' +
        '<select class="kiritish" id="mavzuTanlov"><option value="">Barcha mavzular (aralash)</option></select></div>' +
      '<div class="oy-maydon"><span class="oy-yorliq">Qiyinlik</span>' +
        G.segment('difficulty', 'Qiyinlik', [
          { value: 'oson', label: 'Oson' }, { value: 'orta', label: "O'rta" }, { value: 'qiyin', label: 'Qiyin' }], s.difficulty) + '</div>' +
      '<div class="oy-maydon"><span class="oy-yorliq">' + (game.renderer === 'match' ? 'Raundlar soni' : 'Savollar soni') + '</span>' +
        G.segment('count', 'Savollar soni', game.counts.map(function (n) { return { value: n, label: n }; }), s.count) + '</div>' +
      '<div class="oy-maydon"><span class="oy-yorliq">O\'yinchilar (room uchun)</span>' +
        G.segment('max_players', "O'yinchilar soni", [2, 4, 8, 16].map(function (n) { return { value: n, label: n }; }), s.max_players) + '</div>' +
      '<label class="oy-almashtirgich"><input type="checkbox" id="ochiqRoom"' + (s.public ? ' checked' : '') + '>' +
        '<span><b>Hammaga ochiq room</b><small>Lobbydagi “Faol roomlar” ro\'yxatida ko\'rinadi</small></span></label>' +
      '<p class="izoh" id="davomiylik"></p>';
  };

  G.bindSettingsForm = function (root, game, s, scope, onChange) {
    var topicSel = root.querySelector('#mavzuTanlov');

    function changed() {
      var mins = Math.max(1, Math.round((s.count * (game.time_limit * 0.6 + 4) + 5) / 60));
      root.querySelector('#davomiylik').textContent = 'Taxminan ' + mins + ' daqiqa • ' + s.count + ' ' +
        (game.renderer === 'match' ? 'raund' : 'savol');
      if (onChange) onChange();
    }

    function loadTopics() {
      topicSel.disabled = true;
      var generated = game.generated_topics && game.generated_topics[s.subject];
      var p = generated ? Promise.resolve({ ok: true, topics: generated }) : G.api.topics(game.key, s.subject);
      p.then(function (res) {
        if (scope.dead) return;
        topicSel.disabled = false;
        var topics = (res.ok && res.topics) || [];
        var option = function (t) { return '<option value="' + esc(t.key) + '">' + esc(t.title) + '</option>'; };
        var html = '<option value="">Barcha mavzular (aralash)</option>';
        if (topics.length && topics[0].difficulty) {
          ['oson', 'orta', 'qiyin'].forEach(function (d) {
            var group = topics.filter(function (t) { return t.difficulty === d; });
            if (group.length) html += '<optgroup label="' + G.difficultyName[d] + '">' + group.map(option).join('') + '</optgroup>';
          });
        } else {
          html += topics.map(option).join('');
        }
        topicSel.innerHTML = html;
        var has = topics.some(function (t) { return t.key === s.topic; });
        topicSel.value = has ? s.topic : '';
        if (!has) s.topic = '';
      });
    }

    G.bindSegment(root, scope, function (name, value) {
      if (name === 'subject') { s.subject = value; s.topic = ''; loadTopics(); }
      else if (name === 'count' || name === 'max_players') s[name] = Number(value);
      else s[name] = value;
      changed();
    });
    var fanSel = root.querySelector('#fanTanlov');
    if (fanSel) scope.on(fanSel, 'change', function () { s.subject = fanSel.value; s.topic = ''; loadTopics(); changed(); });
    scope.on(topicSel, 'change', function () { s.topic = topicSel.value; changed(); });
    scope.on(root.querySelector('#ochiqRoom'), 'change', function (e) { s.public = e.target.checked; changed(); });
    changed();
    loadTopics();
  };

  G.settingsPayload = function (s, extra) {
    var p = { game: s.game, subject: s.subject, topic: s.topic || null, difficulty: s.difficulty,
      count: s.count, max_players: s.max_players, public: s.public };
    Object.keys(extra || {}).forEach(function (k) { p[k] = extra[k]; });
    return p;
  };

  // ───────────────────────── O'yin sozlamalari ─────────────────────────

  G.route('setup', function (key, scope) {
    G.header({ title: "O'yin sozlamalari", back: function () { G.go('lobby'); } });
    var el = G.el();
    el.innerHTML = '<div class="skelet" style="height:120px;margin-bottom:12px"></div><div class="skelet" style="height:320px"></div>';

    G.catalog().then(function (cat) {
      if (scope.dead) return;
      if (!cat.ok) { el.innerHTML = UI.xatoHolat(cat.error, function () { G.render(); }); return; }
      var game = G.gameByKey(cat, key);
      if (!game) { G.go('lobby', true); return; }
      G.header({ title: game.name, sub: "O'yin sozlamalari", back: function () { G.go('lobby'); } });

      var saved = G.remember('sozlama_' + game.key) || {};
      var s = {
        game: game.key,
        subject: game.subjects.some(function (x) { return x.key === saved.subject; }) ? saved.subject : game.subjects[0].key,
        topic: saved.topic || '',
        difficulty: saved.difficulty || 'orta',
        count: game.counts.indexOf(saved.count) >= 0 ? saved.count : game.default_count,
        max_players: [2, 4, 8, 16].indexOf(saved.max_players) >= 0 ? saved.max_players : 4,
        public: saved.public !== false,
      };

      el.innerHTML =
        '<section class="karta oy-sozlama-bosh">' +
          '<span class="oy-belgi katta">' + ic(game.icon) + '</span>' +
          '<div><h2 data-fokus>' + esc(game.name) + '</h2><p>' + esc(game.rules) + '</p></div>' +
        '</section>' +
        '<form class="oy-forma" id="sozlamaForma" novalidate>' + G.settingsForm(game, s) + '</form>' +
        '<div class="oy-tanlov">' +
          '<button class="tugma" type="button" id="randomTugma">' + ic('shuffle') + '<span>Random raqib</span></button>' +
          '<button class="tugma tugma-ikkilamchi" type="button" id="yaratTugma">' + ic('plus') + '<span>Room yaratish</span></button>' +
          '<button class="tugma tugma-ikkilamchi" type="button" id="dostTugma">' + ic('users') + "<span>Do'st bilan o'ynash</span></button>" +
        '</div>' +
        '<p class="oy-xato" id="sozlamaXato" role="alert"></p>';
      G.focusMain();

      var errEl = document.getElementById('sozlamaXato');
      G.bindSettingsForm(document.getElementById('sozlamaForma'), game, s, scope, function () {
        G.remember('sozlama_' + game.key, s);
      });

      function payload(extra) { return G.settingsPayload(s, extra); }

      function busy(on) {
        ['randomTugma', 'yaratTugma', 'dostTugma'].forEach(function (id) { document.getElementById(id).disabled = on; });
      }

      function create(isFriend) {
        errEl.textContent = '';
        busy(true);
        G.api.create(payload(isFriend ? { public: false } : {})).then(function (res) {
          if (scope.dead) return;
          busy(false);
          if (!res.ok) { errEl.textContent = res.error; return; }
          if (isFriend) G.flash = { invite: true };
          G.go('room/' + res.code);
        });
      }

      scope.on(document.getElementById('yaratTugma'), 'click', function () { create(false); });
      scope.on(document.getElementById('dostTugma'), 'click', function () { create(true); });
      scope.on(document.getElementById('randomTugma'), 'click', function () {
        errEl.textContent = '';
        busy(true);
        G.api.mmStart(payload()).then(function (res) {
          if (scope.dead) return;
          busy(false);
          if (!res.ok) { errEl.textContent = res.error; return; }
          G.search = { game: game, settings: payload(), first: res };
          G.go('izlash');
        });
      });
    });
  });

  // ───────────────────────── Random raqib qidirish ─────────────────────────

  G.route('izlash', function (arg, scope) {
    var ctx = G.search;
    if (!ctx) { G.go('lobby', true); return; }
    var game = ctx.game;
    var matched = false;

    function cancelAndGo(hash) {
      matched = true; // dispose'da qayta bekor qilinmasin
      G.api.mmCancel().then(function (res) {
        if (res.ok && res.result === 'matched') { G.go('room/' + res.code, true); return; }
        G.go(hash);
      });
    }

    G.header({ title: 'Raqib qidirish', sub: game.name, back: function () { cancelAndGo('setup/' + game.key); } });
    var subjectName = (game.subjects.filter(function (x) { return x.key === ctx.settings.subject; })[0] || {}).name || '';
    var el = G.el();
    el.innerHTML =
      '<section class="oy-izlash" role="status" aria-live="polite">' +
        '<div class="oy-radar" aria-hidden="true"><span></span><span></span><i>' + ic('search') + '</i></div>' +
        '<h2 data-fokus id="izlashSarlavha">Raqib qidirilmoqda...</h2>' +
        '<p class="izoh">' + esc(game.name) + ' • ' + esc(subjectName) + ' • ' + esc(G.difficultyName[ctx.settings.difficulty] || '') + '</p>' +
        '<p class="oy-vaqt" id="izlashVaqt">0:00</p>' +
        '<p class="izoh" id="izlashHolat">Sizga mos raqib qidiryapmiz</p>' +
        '<button class="tugma tugma-ikkilamchi tugma-avto" type="button" id="bekorTugma">Bekor qilish</button>' +
      '</section>';
    G.focusMain();

    var started = Date.now();
    scope.interval(function () {
      var s = Math.floor((Date.now() - started) / 1000);
      document.getElementById('izlashVaqt').textContent = Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
    }, 1000);

    scope.on(document.getElementById('bekorTugma'), 'click', function () { cancelAndGo('setup/' + game.key); });

    function onMatched(code) {
      matched = true;
      document.getElementById('izlashSarlavha').textContent = 'Raqib topildi!';
      document.getElementById('izlashHolat').textContent = "O'yin boshlanmoqda...";
      el.querySelector('.oy-izlash').classList.add('topildi');
      scope.timeout(function () { G.go('room/' + code, true); }, 700);
    }

    function showTimeout() {
      matched = true;
      el.innerHTML = UI.holat({
        belgi: 'users',
        sarlavha: 'Hozircha mos raqib topilmadi',
        matn: "Hozir onlayn o'yinchilar kam. Room yaratib do'stingizni taklif qiling yoki birozdan so'ng qayta urinib ko'ring.",
      }) +
      '<div class="tugmalar" style="margin-top:12px">' +
        '<button class="tugma" type="button" id="qaytaIzla">' + ic('refresh') + '<span>Qayta qidirish</span></button>' +
        '<button class="tugma tugma-ikkilamchi" type="button" id="roomYarat">' + ic('plus') + '<span>Room yaratish</span></button>' +
      '</div>';
      document.getElementById('qaytaIzla').onclick = function () {
        G.api.mmStart(ctx.settings).then(function (res) {
          if (!res.ok) { UI.xabar(res.error, 'xato'); return; }
          G.render();
        });
      };
      document.getElementById('roomYarat').onclick = function () {
        G.api.create(ctx.settings).then(function (res) {
          if (!res.ok) { UI.xabar(res.error, 'xato'); return; }
          G.flash = { invite: true };
          G.go('room/' + res.code, true);
        });
      };
    }

    function handle(res) {
      if (!res.ok) { document.getElementById('izlashHolat').textContent = res.error; return true; }
      if (res.result === 'matched') { onMatched(res.code); return false; }
      if (res.result === 'timeout') { showTimeout(); return false; }
      if (res.result === 'idle' || res.result === 'cancelled') { G.go('setup/' + game.key, true); return false; }
      if (res.relaxed) {
        document.getElementById('izlashHolat').textContent = 'Qidiruv kengaytirildi: boshqa qiyinlik va mavzular ham';
      }
      return true;
    }

    var poller = new G.Poller({
      fetch: G.api.mmPoll,
      interval: function () { return 1500; },
      hiddenFactor: 2,
      onError: function () { G.banner('Internet aloqasi uzildi. Qayta ulanmoqda...'); },
      onData: function (res) { G.banner(null); return handle(res); },
    });
    if (ctx.first && handle(ctx.first) === false) return;
    ctx.first = null;
    poller.start();
    scope.add(function () {
      poller.stop();
      // Brauzerning "orqaga" tugmasi bilan chiqilsa ham qidiruv bekor bo'ladi
      if (!matched) G.api.mmCancel();
    });
  });

  // ───────────────────────── O'yin reytingi ─────────────────────────

  var MEDAL = { 1: 'medal-1', 2: 'medal-2', 3: 'medal-3' };

  function lbRow(u) {
    var place = u.rank <= 3
      ? '<span class="o-rin ' + MEDAL[u.rank] + '" aria-label="' + u.rank + '-o\'rin">' + ic('medal') + '</span>'
      : '<span class="o-rin">' + u.rank + '</span>';
    var avatar = u.photo_url
      ? '<img class="avatar" alt="" src="' + esc(u.photo_url) + '">'
      : '<div class="avatar" aria-hidden="true">' + esc(G.initial(u.name)) + '</div>';
    return '<div class="reyting-qator' + (u.me ? ' men' : '') + '">' + place + avatar +
      '<span class="ism">' + esc(u.name) + (u.me ? ' (siz)' : '') +
        '<small>' + u.games + " o'yin • " + u.wins + " g'alaba • " + u.accuracy + '%</small></span>' +
      '<span class="oy-ball">' + u.xp + '<small>ball</small></span></div>';
  }

  G.route('reyting', function (arg, scope) {
    G.header({ title: "O'yinlar", sub: 'Reyting', back: 'dashboard.html' });
    var saved = G.remember('reyting') || {};
    var f = { period: saved.period || 'week', scope: saved.scope || 'global', subject: saved.subject || 'math' };
    var el = G.el();
    el.innerHTML =
      tabs('reyting') +
      '<h2 class="oy-sr" data-fokus>O\'yin reytingi</h2>' +
      G.segment('period', 'Davr', [
        { value: 'day', label: 'Bugun' }, { value: 'week', label: 'Hafta' },
        { value: 'month', label: 'Oy' }, { value: 'all', label: 'Umumiy' }], f.period) +
      '<div class="oy-filtr">' +
        '<select class="kiritish" id="doiraTanlov" aria-label="Reyting doirasi">' +
          '<option value="global">Global</option><option value="subject">Fan bo\'yicha</option><option value="grade">Sinfim bo\'yicha</option>' +
        '</select>' +
        '<select class="kiritish" id="fanTanlov" aria-label="Fan" hidden></select>' +
      '</div>' +
      '<p class="izoh" style="margin:10px 0">O\'yinlarda hisobga o\'tgan ball bo\'yicha. Har 10 ball — 1 chaqmoq.</p>' +
      '<div id="reytingRoyxat"></div><div id="reytingMen"></div>';
    G.focusMain();

    var doira = document.getElementById('doiraTanlov');
    var fanSel = document.getElementById('fanTanlov');
    doira.value = f.scope;

    G.catalog().then(function (cat) {
      if (scope.dead || !cat.ok) return;
      var seen = {};
      var subjects = [];
      cat.games.forEach(function (g) {
        g.subjects.forEach(function (s) { if (!seen[s.key]) { seen[s.key] = 1; subjects.push(s); } });
      });
      fanSel.innerHTML = subjects.map(function (s) {
        return '<option value="' + esc(s.key) + '">' + esc(s.name) + '</option>';
      }).join('');
      fanSel.value = f.subject;
    });

    var seq = 0;
    function load() {
      G.remember('reyting', f);
      fanSel.hidden = f.scope !== 'subject';
      var box = document.getElementById('reytingRoyxat');
      var meBox = document.getElementById('reytingMen');
      box.innerHTML = '<div class="skelet" style="height:60px;margin-bottom:8px"></div>' +
        '<div class="skelet" style="height:60px;margin-bottom:8px"></div><div class="skelet" style="height:60px"></div>';
      meBox.innerHTML = '';
      var mySeq = ++seq;
      G.api.leaderboard(f).then(function (res) {
        if (scope.dead || mySeq !== seq) return;   // eskirgan javob yangisini bosib ketmasin
        if (!res.ok) { box.innerHTML = UI.xatoHolat(res.error, load); return; }
        if (!res.top.length) {
          box.innerHTML = UI.holat({
            belgi: 'trophy',
            sarlavha: res.notice ? 'Sinf ko\'rsatilmagan' : 'Hali natija yo\'q',
            matn: res.notice || "Bu davrda hali hech kim o'ynamagan. Birinchi bo'ling — o'yin tanlang!",
          });
          return;
        }
        box.innerHTML = res.top.map(lbRow).join('');
        if (res.me && !res.top.some(function (u) { return u.me; })) {
          meBox.innerHTML = '<div class="mening-o-rnim">' + lbRow(res.me) + '</div>';
        }
      });
    }

    G.bindSegment(el, scope, function (name, value) { f[name] = value; load(); });
    scope.on(doira, 'change', function () { f.scope = doira.value; load(); });
    scope.on(fanSel, 'change', function () { f.subject = fanSel.value; load(); });
    load();
  });

  // ───────────────────────── Room (dangasa yuklanadi) ─────────────────────────

  G.route('room', function (code, scope) {
    G.header({ title: 'Room', sub: code, back: function () { G.go('lobby'); } });
    G.el().innerHTML = UI.yuklanmoqda('Room tayyorlanmoqda...');
    G.load('js/games/room.js').then(function () {
      if (!scope.dead) G.roomScreen(code, scope);
    }, function () {
      if (!scope.dead) G.el().innerHTML = UI.xatoHolat("O'yin fayllari yuklanmadi. Internetni tekshiring.", function () { G.render(); });
    });
  });
})();
