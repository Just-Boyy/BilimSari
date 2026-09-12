/* BilimSari frontend testi — jsdom orqali haqiqiy sahifalarni yuklaydi
   va ishlayotgan serverga murojaat qildiradi. */

const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const BASE = 'http://127.0.0.1:5055';
const DIR = 'C:/Users/ADMIN/Desktop/BilimSari/backend';

const o_tdi = [];
const yiqildi = [];

function check(nom, shart, tafsilot = '') {
  if (shart) { o_tdi.push(nom); console.log('  ✓ ' + nom); }
  else { yiqildi.push(nom + ' — ' + tafsilot); console.log('  ✗ ' + nom + '  → ' + tafsilot); }
}

function kut(ms) { return new Promise(r => setTimeout(r, ms)); }

/** Element paydo bo'lguncha kutadi (sobit sleep o'rniga — flake bo'lmasin). */
async function kutSelektor(w, selektor, ms = 5000) {
  const chek = Date.now() + ms;
  while (Date.now() < chek) {
    if (w.document.querySelector(selektor)) return true;
    await kut(50);
  }
  return false;
}

/** Sahifani jsdom da ochadi, skriptlarni ishlatadi, localStorage ni oldindan to'ldiradi. */
async function sahifaOch(fayl, saqlangan = {}, qidiruv = '') {
  let html = fs.readFileSync(path.join(DIR, fayl), 'utf8');
  // Telegram skriptini olib tashlaymiz (tashqi tarmoq kerak emas)
  html = html.replace(/<script src="https:\/\/telegram\.org[^"]*"><\/script>/g, '');

  const vc = new VirtualConsole();
  const xatolar = [];
  const EʼTIBORSIZ = /scrollTo|scrollIntoView|navigation to another Document|Could not parse CSS/i;
  vc.on('jsdomError', e => { if (!EʼTIBORSIZ.test(e.message)) xatolar.push(e.message); });
  vc.on('error', (...a) => { const m = a.join(' '); if (!EʼTIBORSIZ.test(m)) xatolar.push(m); });

  const dom = new JSDOM(html, {
    url: BASE + '/' + fayl + qidiruv,
    runScripts: 'dangerously',
    resources: 'usable',
    pretendToBeVisual: true,
    virtualConsole: vc,
  });

  const w = dom.window;
  w.scrollTo = () => {};
  w.HTMLElement.prototype.scrollIntoView = () => {};
  // fetch ni node ning fetch iga bog'laymiz (jsdom da yo'q)
  w.fetch = (url, opt) => fetch(url.startsWith('http') ? url : BASE + (url.startsWith('/') ? '' : '/') + url, opt);
  Object.keys(saqlangan).forEach(k => w.localStorage.setItem(k, saqlangan[k]));

  // Skriptlar DOMContentLoaded dan keyin ishlaydi — biroz kutamiz
  await kut(150);
  // api.js/ui.js tashqi fayl, resources:usable ularni yuklaydi
  return { dom, w, xatolar };
}

(async function () {
  // ── Tayyorgarlik: test foydalanuvchisi ─────────────────
  const email = 'ui' + Date.now() + '@bilimsari.uz';
  let r = await fetch(BASE + '/api/register', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'UI Test', email, password: 'parol123' }),
  }).then(x => x.json());

  const TOKEN = r.token;
  const SESSIYA = {
    bilimsari_token: TOKEN,
    bilimsari_user: JSON.stringify(r.user),
  };

  await fetch(BASE + '/api/study/grade', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + TOKEN },
    body: JSON.stringify({ grade: 1 }),
  });

  // ══ 1. Onboarding ══
  console.log('\n═══ ONBOARDING ═══');
  {
    const { w, xatolar } = await sahifaOch('onboarding.html', SESSIYA);
    await kutSelektor(w, '.sinf-tugma');
    const tugmalar = w.document.querySelectorAll('.sinf-tugma');
    check('Sinf tugmalari chizildi', tugmalar.length === 11, tugmalar.length + ' ta');
    check('1-sinf "tayyor" deb belgilangan',
      tugmalar[0] && tugmalar[0].classList.contains('tayyor'),
      tugmalar[0] ? tugmalar[0].className : 'yo\'q');
    check('1-sinfda mavzular soni ko\'rsatilgan',
      tugmalar[0] && /19 mavzu/.test(tugmalar[0].textContent),
      tugmalar[0] ? tugmalar[0].textContent : '');
    check('3-sinf "tayyorlanmoqda"',
      tugmalar[2] && /tayyorlanmoqda/.test(tugmalar[2].textContent),
      tugmalar[2] ? tugmalar[2].textContent : '');
    check('Davom tugmasi boshida o\'chiq',
      w.document.getElementById('sinfDavom').disabled, 'yoqilgan');
    check('JS xatosi yo\'q', xatolar.length === 0, xatolar.join(' | '));

    // Sinf tanlash
    tugmalar[0].click();
    await kut(60);
    check('Sinf tanlangach tugma yoqiladi',
      !w.document.getElementById('sinfDavom').disabled, 'hali o\'chiq');
  }

  // ══ 2. Dashboard ══
  console.log('\n═══ DASHBOARD ═══');
  {
    const { w, xatolar } = await sahifaOch('dashboard.html', SESSIYA);
    await kutSelektor(w, '.fan');
    const d = w.document;
    check('Salom matni chiqdi', /Salom, UI/.test(d.getElementById('salom').textContent),
      d.getElementById('salom').textContent);
    check('Sinf yorlig\'i ko\'rinadi',
      /1-sinf/.test(d.getElementById('sinfYorliq').textContent),
      d.getElementById('sinfYorliq').textContent);
    check('Bugungi dars kartasi bor',
      /Bugungi dars/.test(d.getElementById('bugun').textContent),
      d.getElementById('bugun').textContent.slice(0, 80));
    check('Birinchi mavzu — Sonlar',
      /Sonlar/.test(d.getElementById('bugun').textContent), '');
    // jsdom "?" bo'lgan atribut selektorini parse qila olmaydi — to'g'ridan-to'g'ri solishtiramiz
    const boshlaHavola = d.querySelector('#bugun a');
    check('"Darsni boshlash" havolasi to\'g\'ri',
      !!boshlaHavola && boshlaHavola.getAttribute('href') === 'topic.html?fan=math&mavzu=sonlar',
      boshlaHavola ? boshlaHavola.getAttribute('href') : 'yo\'q');
    check('4 ta fan kartasi', d.querySelectorAll('.fan').length === 4,
      d.querySelectorAll('.fan').length + ' ta');
    check('Statistika chizildi', d.querySelectorAll('.stat').length === 3, '');
    check('Pastki navigatsiya bor', d.querySelectorAll('.pastki-nav a').length === 4, '');
    check('JS xatosi yo\'q', xatolar.length === 0, xatolar.join(' | '));
  }

  // ══ 3. Mavzular ro'yxati ══
  console.log('\n═══ MAVZULAR YO\'LI ═══');
  {
    const { w, xatolar } = await sahifaOch('topics.html', SESSIYA, '?fan=math');
    await kutSelektor(w, '.mavzu');
    const d = w.document;
    const mavzular = d.querySelectorAll('.mavzu');
    check('6 ta mavzu chizildi', mavzular.length === 6, mavzular.length + ' ta');
    check('1-mavzu "joriy"', mavzular[0].classList.contains('joriy'), mavzular[0].className);
    check('1-mavzu bosiladigan havola', mavzular[0].tagName === 'A', mavzular[0].tagName);
    check('2-mavzu "qulflangan"', mavzular[1].classList.contains('qulflangan'),
      mavzular[1].className);
    check('Qulflangan mavzu havola emas', mavzular[1].tagName === 'DIV', mavzular[1].tagName);
    check('Holat yorliqlari o\'zbekcha',
      /Bugungi mavzu/.test(mavzular[0].textContent) && /Qulflangan/.test(mavzular[1].textContent),
      '');
    check('Fan nomi sarlavhada',
      /Matematika/.test(d.getElementById('fanNomi').textContent), '');
    check('JS xatosi yo\'q', xatolar.length === 0, xatolar.join(' | '));
  }

  // ══ 4. Mavzu sahifasi: dars → quiz → uy ══
  console.log('\n═══ MAVZU SAHIFASI ═══');
  {
    const { w, xatolar } = await sahifaOch('topic.html', SESSIYA, '?fan=math&mavzu=sonlar');
    await kutSelektor(w, '.bosqich');
    const d = w.document;

    check('3 ta bosqich tugmasi', d.querySelectorAll('.bosqich').length === 3, '');
    check('Dars paneli ochiq',
      d.getElementById('panelDars').classList.contains('faol'), '');
    check('Dars matni chizildi', d.querySelectorAll('#panelDars .blok').length >= 5,
      d.querySelectorAll('#panelDars .blok').length + ' blok');
    check('Eslatma bloki uslublangan',
      d.querySelectorAll('#panelDars .blok-eslatma').length > 0, '');
    check('Qadamlar bloki chizildi',
      d.querySelectorAll('#panelDars .blok-qadamlar li').length === 4, '');
    check('AI paneli mavjud', !!d.querySelector('.ai-qavs'), '');
    check('AI "qo\'shimcha" deb belgilangan',
      /Rasmiy dars yuqorida/.test(d.querySelector('.ai-qavs').textContent), '');
    check('3 ta AI rejimi', d.querySelectorAll('[data-ai]').length === 3, '');

    // Darsni o'qidim
    d.getElementById('darsTugadi').click();
    await kut(400);
    check('Dars o\'qilgach quizga o\'tdi',
      d.getElementById('panelQuiz').classList.contains('faol'), '');
    check('Dars bosqichi ✓ bilan belgilandi',
      d.querySelector('.bosqich[data-bosqich="dars"]').classList.contains('bajarildi'), '');

    // Quiz
    check('Savol ko\'rsatildi', !!d.querySelector('.savol-matn'), '');
    check('Progress chiziqlari 6 ta',
      d.querySelectorAll('.quiz-progress i').length === 6, '');
    check('Keyingi tugmasi boshida o\'chiq',
      d.getElementById('quizKeyingi').disabled, '');

    // 6 ta savolga to'g'ri javob: [1,1,1,true,'6',1]
    const javoblar = [1, 1, 1, 'true', '6', 1];
    for (let i = 0; i < 6; i++) {
      const j = javoblar[i];
      const matnMaydon = d.getElementById('quizMatn');
      if (matnMaydon) {
        matnMaydon.value = String(j);
        matnMaydon.dispatchEvent(new w.Event('input'));
      } else {
        const v = d.querySelector('.variant[data-javob="' + j + '"]');
        if (!v) { check('Variant topildi (savol ' + (i + 1) + ')', false, 'javob=' + j); break; }
        v.click();
      }
      await kut(60);
      d.getElementById('quizKeyingi').click();
      await kut(i === 5 ? 600 : 120);
    }

    check('Quiz natijasi ko\'rsatildi', !!d.querySelector('.natija'), '');
    check('100% natija', /100%/.test(d.querySelector('.halqa') ? d.querySelector('.halqa').textContent : ''),
      d.querySelector('.halqa') ? d.querySelector('.halqa').textContent : 'yo\'q');
    check('"Ajoyib natija" xabari',
      /Ajoyib natija/.test(d.getElementById('panelQuiz').textContent), '');

    // Uyga vazifa
    d.getElementById('uygaO-t').click();
    await kut(150);
    check('Uy vazifasi paneli ochildi',
      d.getElementById('panelUy').classList.contains('faol'), '');
    check('4 ta vazifa', d.querySelectorAll('#panelUy .vazifa').length === 4, '');
    check('Erkin javob belgisi bor', !!d.querySelector('.erkin-belgi'), '');

    const forma = d.getElementById('uyForma');
    forma.elements['h1'].value = '6';
    forma.elements['h2'].value = '3';
    forma.elements['h3'].value = '10';
    forma.elements['h4'].value = 'Derazalarni sanadim, 4 ta';
    forma.dispatchEvent(new w.Event('submit'));
    await kut(800);

    check('Yakunlash ekrani chiqdi',
      /Tabriklaymiz/.test(d.getElementById('tana').textContent),
      d.getElementById('tana').textContent.slice(0, 60));
    check('Taymer ko\'rsatildi', !!d.getElementById('yakunTaymer'), '');
    check('Taymer raqam formatida',
      /^\d{2}:\d{2}:\d{2}$/.test(d.getElementById('yakunTaymer').textContent),
      d.getElementById('yakunTaymer').textContent);
    check('Keyingi mavzu nomi ko\'rsatildi',
      /Qo'shish va ayirish/.test(d.getElementById('tana').textContent), '');
    check('JS xatosi yo\'q', xatolar.length === 0, xatolar.join(' | '));
  }

  // ══ 5. Kutish holati ══
  console.log('\n═══ KUTISH HOLATI ═══');
  {
    const { w, xatolar } = await sahifaOch('dashboard.html', SESSIYA);
    await kutSelektor(w, '.kutish-karta');
    const d = w.document;
    check('Dashboardda kutish kartasi',
      /Bugungi mavzuni yakunladingiz/.test(d.getElementById('bugun').textContent), '');
    check('Taymer ishlaydi',
      /^\d{2}:\d{2}:\d{2}$/.test((d.getElementById('taymer') || {}).textContent || ''),
      (d.getElementById('taymer') || {}).textContent);
    check('Toshkent vaqti ko\'rsatilgan',
      /Toshkent vaqti/.test(d.getElementById('bugun').textContent), '');
    check('JS xatosi yo\'q', xatolar.length === 0, xatolar.join(' | '));
  }
  {
    const { w } = await sahifaOch('topic.html', SESSIYA, '?fan=math&mavzu=qoshish-ayirish');
    await kutSelektor(w, '.kutish-karta');
    check('Qulflangan mavzu ochilmadi',
      /Bugungi mavzuni yakunladingiz/.test(w.document.getElementById('tana').textContent),
      w.document.getElementById('tana').textContent.slice(0, 60));
  }

  // ══ 6. Natijalar sahifasi ══
  console.log('\n═══ NATIJALAR ═══');
  {
    const { w, xatolar } = await sahifaOch('progress.html', SESSIYA);
    await kutSelektor(w, '.mavzu-qator', 8000);
    const d = w.document;
    check('Umumiy progress chizildi', /Umumiy progress/.test(d.getElementById('tana').textContent), '');
    check('Fanlar bo\'yicha bo\'lim bor',
      d.querySelectorAll('.fan-blok').length === 4,
      d.querySelectorAll('.fan-blok').length + ' ta');
    check('Mavzu qatorlari chizildi',
      d.querySelectorAll('.mavzu-qator').length >= 19,
      d.querySelectorAll('.mavzu-qator').length + ' ta');
    check('Quiz bali ko\'rsatildi', /100%/.test(d.getElementById('tana').textContent), '');
    check('JS xatosi yo\'q', xatolar.length === 0, xatolar.join(' | '));
  }

  // ══ 7. Bo'sh sinf holati ══
  console.log('\n═══ BO\'SH HOLAT ═══');
  {
    await fetch(BASE + '/api/study/grade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + TOKEN },
      body: JSON.stringify({ grade: 4 }),
    });
    const { w } = await sahifaOch('subjects.html', SESSIYA);
    await kutSelektor(w, '.holat-karta');
    const matn = w.document.getElementById('fanlar').textContent;
    check('Bo\'sh holat xabari o\'zbekcha', /tayyorlanmoqda/.test(matn), matn.slice(0, 80));
    check('Sinfni o\'zgartirish tugmasi bor',
      !!w.document.querySelector('a[href="onboarding.html"]'), '');
  }

  // ══ 8. Kirish sahifasi ══
  console.log('\n═══ KIRISH ═══');
  {
    const { w, xatolar } = await sahifaOch('login.html', {});
    await kut(200);
    const d = w.document;
    d.getElementById('email').value = email;
    d.getElementById('parol').value = 'notogri';
    d.getElementById('forma').dispatchEvent(new w.Event('submit'));
    await kut(600);
    check('Noto\'g\'ri parolda xato ko\'rsatiladi',
      /Parol/.test(d.getElementById('xato').textContent),
      d.getElementById('xato').textContent);

    d.getElementById('parol').value = 'parol123';
    d.getElementById('forma').dispatchEvent(new w.Event('submit'));
    await kut(600);
    check('To\'g\'ri parolda token saqlanadi',
      !!w.localStorage.getItem('bilimsari_token'), '');
    check('JS xatosi yo\'q', xatolar.length === 0, xatolar.join(' | '));
  }

  console.log('\n' + '═'.repeat(55));
  console.log('  O\'TDI: ' + o_tdi.length + '     YIQILDI: ' + yiqildi.length);
  console.log('═'.repeat(55));
  if (yiqildi.length) {
    console.log('\nYiqilganlar:');
    yiqildi.forEach(f => console.log('  • ' + f));
  }
  process.exit(yiqildi.length ? 1 : 0);
})();
