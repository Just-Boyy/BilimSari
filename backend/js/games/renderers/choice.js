/* Game Hub renderer: variantli savol (Quiz Battle, Quick Answer, Word Battle,
   Math Battle, Code Challenge). Klaviatura: 1–4 yoki A–D. */
(function () {
  'use strict';

  var G = window.Games;
  var LETTERS = 'ABCDEFGH';

  G.renderers.choice = {
    mount: function (box, q, opts) {
      box.innerHTML =
        '<div class="variantlar oy-variantlar" role="group" aria-label="Javob variantlari">' +
          q.options.map(function (o, i) {
            return '<button type="button" class="variant" data-i="' + i + '">' +
              '<span class="harf" aria-hidden="true">' + LETTERS[i] + '</span>' +
              '<span class="oy-variant-matn">' + G.rich(o) + '</span></button>';
          }).join('') +
        '</div>' +
        '<p class="izoh oy-klaviatura">Klaviatura: 1–' + q.options.length + ' yoki A–' + LETTERS[q.options.length - 1] + '</p>';

      var buttons = Array.prototype.slice.call(box.querySelectorAll('.variant'));
      var locked = false;

      function choose(i) {
        if (!locked && i >= 0 && i < buttons.length) opts.onAnswer(i);
      }

      buttons.forEach(function (b) {
        opts.scope.on(b, 'click', function () { choose(Number(b.dataset.i)); });
      });
      opts.scope.on(document, 'keydown', function (e) {
        if (locked || e.altKey || e.ctrlKey || e.metaKey) return;
        var tag = (document.activeElement || {}).tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
        var k = String(e.key || '').toUpperCase();
        var i = '12345678'.indexOf(k);
        if (i < 0) i = LETTERS.indexOf(k);
        if (i >= 0 && i < buttons.length && k.length === 1) {
          e.preventDefault();
          choose(i);
        }
      });

      var ctrl = {
        lock: function () {
          locked = true;
          buttons.forEach(function (b) { b.disabled = true; });
        },
        unlock: function () {
          locked = false;
          buttons.forEach(function (b) { b.disabled = false; b.removeAttribute('aria-pressed'); });
        },
        /** Yuborilgan javobni belgilaydi (to'g'ri-noto'g'riligi hali noma'lum). */
        mine: function (i) {
          buttons.forEach(function (b, j) { b.setAttribute('aria-pressed', String(j === i)); });
          ctrl.lock();
        },
        reveal: function (rv, mine) {
          ctrl.lock();
          buttons.forEach(function (b, j) {
            b.removeAttribute('aria-pressed');
            if (j === rv.answer) b.classList.add('to-g-ri');
            else if (j === mine) b.classList.add('xato');
          });
        },
      };
      if (opts.answered != null) ctrl.mine(opts.answered);
      return ctrl;
    },
  };
})();
