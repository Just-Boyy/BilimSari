/* Game Hub renderer: Memory / Match — chapdagi savollarni o'ngdagi javoblar
   bilan juftlash. Juftliklar faqat rang bilan emas, raqam belgisi bilan ham
   ko'rsatiladi (rangni ajrata olmaydiganlar uchun). */
(function () {
  'use strict';

  var G = window.Games;

  G.renderers.match = {
    mount: function (box, q, opts) {
      var n = q.left.length;
      var pairs = [];                 // pairs[chap] = o'ng indeks yoki null
      for (var k = 0; k < n; k++) pairs.push(null);
      var selected = 0;               // tanlangan chap element
      var locked = false;

      box.innerHTML =
        '<p class="izoh oy-match-yordam">Avval chapdagi savolni, keyin unga mos javobni bosing. ' +
          'Juftlikni bekor qilish uchun uni qayta bosing.</p>' +
        '<div class="oy-match">' +
          '<ol class="oy-match-ustun" aria-label="Savollar">' + q.left.map(function (t, i) {
            return '<li><button type="button" class="oy-match-el" data-l="' + i + '">' +
              '<span class="oy-match-raqam" aria-hidden="true">' + (i + 1) + '</span>' +
              '<span class="oy-match-matn">' + G.rich(t) + '</span></button></li>';
          }).join('') + '</ol>' +
          '<ul class="oy-match-ustun javoblar" aria-label="Javoblar">' + q.right.map(function (t, j) {
            return '<li><button type="button" class="oy-match-el javob" data-r="' + j + '">' +
              '<span class="oy-match-raqam" aria-hidden="true"></span>' +
              '<span class="oy-match-matn">' + G.rich(t) + '</span></button></li>';
          }).join('') + '</ul>' +
        '</div>' +
        '<button type="button" class="tugma" id="matchYubor" disabled>Tekshirish</button>';

      var lefts = Array.prototype.slice.call(box.querySelectorAll('[data-l]'));
      var rights = Array.prototype.slice.call(box.querySelectorAll('[data-r]'));
      var submit = box.querySelector('#matchYubor');

      function plain(el) { return el.querySelector('.oy-match-matn').textContent; }

      function paint() {
        lefts.forEach(function (b, i) {
          b.classList.toggle('tanlangan', !locked && selected === i);
          b.classList.toggle('juftlangan', pairs[i] !== null);
          b.setAttribute('aria-pressed', String(!locked && selected === i));
          b.setAttribute('aria-label', (i + 1) + '-savol: ' + plain(b) +
            (pairs[i] !== null ? '. Juftlandi: ' + plain(rights[pairs[i]]) : '. Hali juftlanmagan'));
        });
        rights.forEach(function (b, j) {
          var li = pairs.indexOf(j);
          b.classList.toggle('juftlangan', li >= 0);
          b.querySelector('.oy-match-raqam').textContent = li >= 0 ? String(li + 1) : '';
          b.setAttribute('aria-label', plain(b) + (li >= 0 ? '. ' + (li + 1) + '-savolga juftlangan' : ''));
          b.disabled = locked;
        });
        lefts.forEach(function (b) { b.disabled = locked; });
        submit.disabled = locked || pairs.indexOf(null) >= 0;
      }

      lefts.forEach(function (b, i) {
        opts.scope.on(b, 'click', function () {
          if (locked) return;
          if (selected === i && pairs[i] !== null) pairs[i] = null;   // ikkinchi bosish — juftlikni bekor qiladi
          selected = i;
          paint();
        });
      });
      rights.forEach(function (b, j) {
        opts.scope.on(b, 'click', function () {
          if (locked) return;
          var owner = pairs.indexOf(j);
          if (owner >= 0) pairs[owner] = null;
          if (selected === null) { paint(); return; }
          pairs[selected] = j;
          var next = pairs.indexOf(null);
          selected = next >= 0 ? next : null;
          paint();
          if (next < 0) submit.focus();
        });
      });
      opts.scope.on(submit, 'click', function () {
        if (!locked && pairs.indexOf(null) < 0) opts.onAnswer(pairs.slice());
      });

      var ctrl = {
        lock: function () { locked = true; paint(); },
        unlock: function () { locked = false; paint(); },
        mine: function (perm) {
          if (Array.isArray(perm)) pairs = perm.slice();
          ctrl.lock();
          submit.textContent = 'Yuborildi';
        },
        reveal: function (rv, mine) {
          ctrl.lock();
          submit.hidden = true;
          lefts.forEach(function (b, i) {
            var right = mine && mine[i] === rv.answer[i];
            b.classList.add(right ? 'togri' : 'xato');
            b.classList.remove('juftlangan');
          });
          // To'g'ri juftliklarni raqamlar bilan ko'rsatamiz
          rights.forEach(function (b, j) {
            var li = rv.answer.indexOf(j);
            b.querySelector('.oy-match-raqam').textContent = String(li + 1);
            b.classList.remove('juftlangan');
            b.classList.add('ochiq');
          });
        },
      };
      if (opts.answered != null) ctrl.mine(opts.answered);
      else paint();
      return ctrl;
    },
  };
})();
