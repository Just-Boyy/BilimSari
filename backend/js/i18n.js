// BilimSari i18n — uz / ru / en
(function () {
  var LANG_KEY = 'bs_lang';

  var STR = {
    uz: {
      app_name: 'BilimSari',
      welcome_sub: 'O‘rganishni boshlash uchun davom eting',
      start: 'Boshlash',
      back: 'Orqaga',
      lang_title: 'Tilni tanlang',
      lang_sub: 'Ilova qaysi tilda ishlasin?',
      lang_uz: 'O‘zbek tili',
      lang_ru: 'Русский язык',
      lang_en: 'English',
      name_title: 'Ismingiz',
      name_sub: 'Telegramdagi ismingiz topildi. Shu bilan qolsinmi?',
      tg_name_label: 'Telegram ismi',
      keep_name: 'Ha, shu bilan',
      own_name: 'O‘zim kiritaman',
      name_manual_title: 'Ism kiriting',
      name_manual_sub: 'Qanday murojaat qilaylik?',
      ph_first: 'Ism',
      ph_last: 'Familiya (ixtiyoriy)',
      continue: 'Davom etish',
      fan_title: 'Fan tanlang',
      fan_sub: 'Qaysi fan bo‘yicha o‘qimoqchisiz? Faqat bitta fan.',
      loading: 'Yuklanmoqda...',
      fans_fail: 'Fanlar yuklanmadi. Qayta urinib ko‘ring.',
      retry: 'Qayta yuklash',
      learn: 'O‘rganish',
      courses: 'Kurslar',
      rating: 'Reyting',
      review: 'Takrorlash',
      profile: 'Profil',
      unit_default: 'Bo‘lim',
      check: 'TEKSHIRISH',
      next: 'DAVOM ETISH',
      correct: 'To‘g‘ri!',
      wrong: 'Noto‘g‘ri',
      correct_answer: 'To‘g‘ri javob:',
      lesson_done: 'Dars tugadi!',
      accuracy: 'Aniqlik',
      streak: 'Streak',
      hearts_empty_title: 'Yuraklaringiz tugadi',
      hearts_empty_text: 'Takrorlash orqali yurak tiklash mumkin yoki keyinroq qayting.',
      practice_heart: 'Takrorlash (+1 yurak)',
      exit: 'Chiqish',
      open_app: 'Appni ochish',
      download: 'Yuklab olish',
    },
    ru: {
      app_name: 'BilimSari',
      welcome_sub: 'Нажмите, чтобы начать обучение',
      start: 'Начать',
      back: 'Назад',
      lang_title: 'Выберите язык',
      lang_sub: 'На каком языке будет приложение?',
      lang_uz: 'O‘zbek tili',
      lang_ru: 'Русский язык',
      lang_en: 'English',
      name_title: 'Ваше имя',
      name_sub: 'Мы нашли имя из Telegram. Оставить его?',
      tg_name_label: 'Имя в Telegram',
      keep_name: 'Да, оставить',
      own_name: 'Ввести своё',
      name_manual_title: 'Введите имя',
      name_manual_sub: 'Как к вам обращаться?',
      ph_first: 'Имя',
      ph_last: 'Фамилия (необязательно)',
      continue: 'Продолжить',
      fan_title: 'Выберите предмет',
      fan_sub: 'По какому предмету хотите учиться? Только один.',
      loading: 'Загрузка...',
      fans_fail: 'Не удалось загрузить предметы. Попробуйте снова.',
      retry: 'Повторить',
      learn: 'Учёба',
      courses: 'Курсы',
      rating: 'Рейтинг',
      review: 'Повторение',
      profile: 'Профиль',
      unit_default: 'Раздел',
      check: 'ПРОВЕРИТЬ',
      next: 'ПРОДОЛЖИТЬ',
      correct: 'Верно!',
      wrong: 'Неверно',
      correct_answer: 'Правильный ответ:',
      lesson_done: 'Урок завершён!',
      accuracy: 'Точность',
      streak: 'Серия',
      hearts_empty_title: 'Сердца закончились',
      hearts_empty_text: 'Можно восстановить через повторение или зайти позже.',
      practice_heart: 'Повторение (+1 сердце)',
      exit: 'Выйти',
      open_app: 'Открыть приложение',
      download: 'Скачать',
    },
    en: {
      app_name: 'BilimSari',
      welcome_sub: 'Continue to start learning',
      start: 'Start',
      back: 'Back',
      lang_title: 'Choose language',
      lang_sub: 'Which language should the app use?',
      lang_uz: 'O‘zbek tili',
      lang_ru: 'Русский язык',
      lang_en: 'English',
      name_title: 'Your name',
      name_sub: 'We found your Telegram name. Keep it?',
      tg_name_label: 'Telegram name',
      keep_name: 'Yes, keep it',
      own_name: 'Enter my own',
      name_manual_title: 'Enter name',
      name_manual_sub: 'What should we call you?',
      ph_first: 'First name',
      ph_last: 'Last name (optional)',
      continue: 'Continue',
      fan_title: 'Choose a subject',
      fan_sub: 'Which subject do you want to study? Only one.',
      loading: 'Loading...',
      fans_fail: 'Could not load subjects. Please try again.',
      retry: 'Retry',
      learn: 'Learn',
      courses: 'Courses',
      rating: 'Leaderboard',
      review: 'Review',
      profile: 'Profile',
      unit_default: 'Unit',
      check: 'CHECK',
      next: 'CONTINUE',
      correct: 'Correct!',
      wrong: 'Wrong',
      correct_answer: 'Correct answer:',
      lesson_done: 'Lesson complete!',
      accuracy: 'Accuracy',
      streak: 'Streak',
      hearts_empty_title: 'Out of hearts',
      hearts_empty_text: 'Restore hearts via review or come back later.',
      practice_heart: 'Practice (+1 heart)',
      exit: 'Exit',
      open_app: 'Open app',
      download: 'Download',
    }
  };

  function getLang() {
    try {
      var l = localStorage.getItem(LANG_KEY);
      if (l && STR[l]) return l;
    } catch (e) {}
    return 'uz';
  }

  function setLang(code) {
    if (!STR[code]) code = 'uz';
    try { localStorage.setItem(LANG_KEY, code); } catch (e) {}
    document.documentElement.lang = code === 'uz' ? 'uz' : code;
    return code;
  }

  function t(key) {
    var lang = getLang();
    var pack = STR[lang] || STR.uz;
    return pack[key] != null ? pack[key] : (STR.uz[key] || key);
  }

  /** data-i18n="key" va data-i18n-placeholder="key" ni to‘ldiradi */
  function apply(root) {
    root = root || document;
    root.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      if (key) el.textContent = t(key);
    });
    root.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-placeholder');
      if (key) el.setAttribute('placeholder', t(key));
    });
    root.querySelectorAll('[data-i18n-html]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-html');
      if (key) el.innerHTML = t(key);
    });
  }

  window.BS_I18N = {
    STR: STR,
    getLang: getLang,
    setLang: setLang,
    t: t,
    apply: apply,
    LANG_KEY: LANG_KEY
  };
})();
