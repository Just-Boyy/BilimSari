const COURSES = [
  {
    id: 'english',
    icon: 'lang',
    name: 'Ingliz tili',
    desc: 'So‘zlar, gaplar va muloqot',
    color: '#FF4B4B',
    units: [{
      id: 'en-u1',
      title: '1-bo‘lim: Asoslar',
      desc: 'Salomlashish va oddiy gaplar',
      lessons: [
        { id: 'en-l1', title: 'Salomlashish', icon: 'star', type: 'lesson' },
        { id: 'en-l2', title: 'Oila', icon: 'star', type: 'lesson' },
        { id: 'en-l3', title: 'Mashq', icon: 'dumbbell', type: 'practice' },
        { id: 'en-l4', title: 'Raqamlar', icon: 'star', type: 'lesson' },
        { id: 'en-l5', title: 'Ranglar', icon: 'star', type: 'lesson' },
        { id: 'en-l6', title: 'Test', icon: 'trophy', type: 'review' },
      ],
    }],
  },
  {
    id: 'uzbek',
    icon: 'book',
    name: 'Ona tili',
    desc: 'Imlo, so‘z va gap tuzilishi',
    color: '#58A700',
    units: [{
      id: 'uz-u1',
      title: '1-bo‘lim: Asoslar',
      desc: 'To‘g‘ri yozuv va ifoda',
      lessons: [
        { id: 'uz-l1', title: 'Unli va undosh', icon: 'star', type: 'lesson' },
        { id: 'uz-l2', title: 'So‘z turkumlari', icon: 'star', type: 'lesson' },
        { id: 'uz-l3', title: 'Mashq', icon: 'dumbbell', type: 'practice' },
        { id: 'uz-l4', title: 'Gap bo‘laklari', icon: 'star', type: 'lesson' },
        { id: 'uz-l5', title: 'Test', icon: 'trophy', type: 'review' },
      ],
    }],
  },
  {
    id: 'russian',
    icon: 'lang',
    name: 'Rus tili',
    desc: 'Lug‘at va oddiy muloqot',
    color: '#1CB0F6',
    units: [{
      id: 'ru-u1',
      title: '1-bo‘lim: Asoslar',
      desc: 'Salom va tanishuv',
      lessons: [
        { id: 'ru-l1', title: 'Приветствие', icon: 'star', type: 'lesson' },
        { id: 'ru-l2', title: 'Семья', icon: 'star', type: 'lesson' },
        { id: 'ru-l3', title: 'Mashq', icon: 'dumbbell', type: 'practice' },
        { id: 'ru-l4', title: 'Числа', icon: 'star', type: 'lesson' },
        { id: 'ru-l5', title: 'Test', icon: 'trophy', type: 'review' },
      ],
    }],
  },
  {
    id: 'geography',
    icon: 'globe',
    name: 'Geografiya',
    desc: 'Dunyo va O‘zbekiston',
    color: '#0EA5E9',
    units: [{
      id: 'geo-u1',
      title: '1-bo‘lim: Asoslar',
      desc: 'Xarita va qit’alar',
      lessons: [
        { id: 'geo-l1', title: 'Qit’alar', icon: 'star', type: 'lesson' },
        { id: 'geo-l2', title: 'Okeanlar', icon: 'star', type: 'lesson' },
        { id: 'geo-l3', title: 'Mashq', icon: 'dumbbell', type: 'practice' },
        { id: 'geo-l4', title: 'O‘zbekiston', icon: 'star', type: 'lesson' },
        { id: 'geo-l5', title: 'Test', icon: 'trophy', type: 'review' },
      ],
    }],
  },
  {
    id: 'math',
    icon: 'calc',
    name: 'Matematika',
    desc: 'Arifmetika va mantiq',
    color: '#7C3AED',
    units: [{
      id: 'math-u1',
      title: '1-bo‘lim: Sonlar',
      desc: 'Qo‘shish, ayirish, ko‘paytirish',
      lessons: [
        { id: 'm-l1', title: 'Qo‘shish', icon: 'star', type: 'lesson' },
        { id: 'm-l2', title: 'Ayirish', icon: 'star', type: 'lesson' },
        { id: 'm-l3', title: 'Mashq', icon: 'dumbbell', type: 'practice' },
        { id: 'm-l4', title: 'Ko‘paytirish', icon: 'star', type: 'lesson' },
        { id: 'm-l5', title: 'Bo‘lish', icon: 'star', type: 'lesson' },
        { id: 'm-l6', title: 'Test', icon: 'trophy', type: 'review' },
      ],
    }],
  },
  {
    id: 'geometry',
    icon: 'shapes',
    name: 'Geometriya',
    desc: 'Shakllar va o‘lchovlar',
    color: '#F59E0B',
    units: [{
      id: 'geom-u1',
      title: '1-bo‘lim: Shakllar',
      desc: 'Nuqta, chiziq, burchak',
      lessons: [
        { id: 'ge-l1', title: 'Nuqta va chiziq', icon: 'star', type: 'lesson' },
        { id: 'ge-l2', title: 'Burchaklar', icon: 'star', type: 'lesson' },
        { id: 'ge-l3', title: 'Mashq', icon: 'dumbbell', type: 'practice' },
        { id: 'ge-l4', title: 'Uchburchak', icon: 'star', type: 'lesson' },
        { id: 'ge-l5', title: 'Test', icon: 'trophy', type: 'review' },
      ],
    }],
  },
  {
    id: 'law',
    icon: 'scale',
    name: 'Huquq',
    desc: 'Huquq asoslari va burchlar',
    color: '#64748B',
    units: [{
      id: 'law-u1',
      title: '1-bo‘lim: Asoslar',
      desc: 'Konstitutsiya va huquq',
      lessons: [
        { id: 'law-l1', title: 'Huquq nima?', icon: 'star', type: 'lesson' },
        { id: 'law-l2', title: 'Huquq va burch', icon: 'star', type: 'lesson' },
        { id: 'law-l3', title: 'Mashq', icon: 'dumbbell', type: 'practice' },
        { id: 'law-l4', title: 'Bolalar huquqlari', icon: 'star', type: 'lesson' },
        { id: 'law-l5', title: 'Test', icon: 'trophy', type: 'review' },
      ],
    }],
  },
  {
    id: 'biology',
    icon: 'leaf',
    name: 'Biologiya',
    desc: 'Tirik tabiat asoslari',
    color: '#22C55E',
    units: [{
      id: 'bio-u1',
      title: '1-bo‘lim: Asoslar',
      desc: 'Hujayra va organizmlar',
      lessons: [
        { id: 'bio-l1', title: 'Tirik mavjudotlar', icon: 'star', type: 'lesson' },
        { id: 'bio-l2', title: 'Hujayra', icon: 'star', type: 'lesson' },
        { id: 'bio-l3', title: 'Mashq', icon: 'dumbbell', type: 'practice' },
        { id: 'bio-l4', title: 'O‘simliklar', icon: 'star', type: 'lesson' },
        { id: 'bio-l5', title: 'Test', icon: 'trophy', type: 'review' },
      ],
    }],
  },
  {
    id: 'literature',
    icon: 'book',
    name: 'Adabiyot',
    desc: 'Asarlar va yozuvchilar',
    color: '#EC4899',
    units: [{
      id: 'lit-u1',
      title: '1-bo‘lim: Asoslar',
      desc: 'Janrlar va she’r',
      lessons: [
        { id: 'lit-l1', title: 'Adabiyot nima?', icon: 'star', type: 'lesson' },
        { id: 'lit-l2', title: 'She’r va nasr', icon: 'star', type: 'lesson' },
        { id: 'lit-l3', title: 'Mashq', icon: 'dumbbell', type: 'practice' },
        { id: 'lit-l4', title: 'O‘zbek adiblari', icon: 'star', type: 'lesson' },
        { id: 'lit-l5', title: 'Test', icon: 'trophy', type: 'review' },
      ],
    }],
  },
];

const QUESTIONS = {
  'fe-l1': [
    { type: 'mc', q: 'HTML nimani anglatadi?', options: ['HyperText Markup Language', 'High Text Machine Language', 'Hyper Tool Markup Language', 'Home Tool Markup Language'], answer: 0 },
    { type: 'tf', q: 'HTML dasturlash tili hisoblanadi.', answer: false },
    { type: 'mc', q: 'HTML asosan nima uchun ishlatiladi?', options: ['Veb sahifa tuzilishi', 'Ma’lumotlar bazasi', 'Operatsion tizim', 'Grafika chizish'], answer: 0 },
    { type: 'fill', q: 'HTML hujjati odatda ___ kengaytmali faylda saqlanadi.', answer: 'html' },
    { type: 'mc', q: 'Brauzer HTML ni nima qiladi?', options: ['Ko‘rsatadi (render)', 'O‘chiradi', 'Shifrlaydi', 'Yubormaydi'], answer: 0 },
  ],
  'fe-l2': [
    { type: 'mc', q: 'Qaysi teg sarlavha uchun?', options: ['<h1>', '<p>', '<div>', '<span>'], answer: 0 },
    { type: 'mc', q: 'Paragraf tegi qaysi?', options: ['<p>', '<para>', '<text>', '<pr>'], answer: 0 },
    { type: 'tf', q: 'Barcha HTML teglari yopilishi shart.', answer: false },
    { type: 'match', pairs: [['<h1>', 'Sarlavha'], ['<p>', 'Paragraf'], ['<a>', 'Havola'], ['<img>', 'Rasm']] },
    { type: 'mc', q: 'Izoh qanday yoziladi?', options: ['<!-- izoh -->', '// izoh', '# izoh', '/* izoh */'], answer: 0 },
  ],
  'fe-l3': [
    { type: 'mc', q: '<html> tegining vazifasi?', options: ['Hujjat ildizi', 'Sarlavha', 'Stil', 'Skript'], answer: 0 },
    { type: 'mc', q: '<body> ichida nima bo‘ladi?', options: ['Ko‘rinadigan kontent', 'Faqat CSS', 'Faqat meta', 'Hech narsa'], answer: 0 },
    { type: 'tf', q: '<head> sahifada ko‘rinadi.', answer: false },
    { type: 'fill', q: 'Eng katta sarlavha tegi: <___>', answer: 'h1' },
    { type: 'mc', q: 'Ro‘yxat tegi?', options: ['<ul>', '<list>', '<ol-list>', '<items>'], answer: 0 },
  ],
  'fe-l4': [
    { type: 'mc', q: 'h1 dan h6 gacha nechta daraja?', options: ['6', '5', '4', '3'], answer: 0 },
    { type: 'tf', q: 'Bir sahifada bir nechta h1 bo‘lishi mumkin.', answer: true },
    { type: 'mc', q: 'Eng kichik sarlavha?', options: ['<h6>', '<h1>', '<h3>', '<h0>'], answer: 0 },
    { type: 'fill', q: 'Asosiy sarlavha odatda <___> bilan yoziladi.', answer: 'h1' },
    { type: 'mc', q: 'Sarlavhalar nima uchun muhim?', options: ['SEO va tuzilma', 'Faqat rang', 'Faqat rasm', 'Hech narsa'], answer: 0 },
  ],
  'fe-l5': [
    { type: 'mc', q: 'Havola tegi?', options: ['<a>', '<link>', '<href>', '<url>'], answer: 0 },
    { type: 'mc', q: 'href atributi nima qiladi?', options: ['Manzilni ko‘rsatadi', 'Rang beradi', 'Rasm qo‘yadi', 'Yashiradi'], answer: 0 },
    { type: 'tf', q: 'target="_blank" yangi tabda ochadi.', answer: true },
    { type: 'fill', q: 'Havola: <a ___="https://...">', answer: 'href' },
    { type: 'mc', q: 'Email havolasi qanday boshlanadi?', options: ['mailto:', 'email:', 'mail:', 'send:'], answer: 0 },
  ],
  'fe-l6': [
    { type: 'mc', q: 'HTML to‘liq nomi?', options: ['HyperText Markup Language', 'HyperText Markdown Language', 'HighText Markup Language', 'Hyper Transfer Markup Language'], answer: 0 },
    { type: 'mc', q: 'Qaysi teg rasm uchun?', options: ['<img>', '<image>', '<pic>', '<src>'], answer: 0 },
    { type: 'tf', q: 'HTML semantik teglarga ega.', answer: true },
    { type: 'match', pairs: [['<header>', 'Yuqori qism'], ['<footer>', 'Pastki qism'], ['<nav>', 'Navigatsiya'], ['<main>', 'Asosiy kontent']] },
    { type: 'mc', q: 'Doctype nima uchun?', options: ['HTML versiyasini bildiradi', 'CSS ulaydi', 'JS ishga tushiradi', 'Rasm yuklaydi'], answer: 0 },
  ],
  'fe-l7': [
    { type: 'mc', q: 'CSS nimani anglatadi?', options: ['Cascading Style Sheets', 'Computer Style Sheets', 'Creative Style System', 'Colorful Style Sheets'], answer: 0 },
    { type: 'tf', q: 'CSS sahifa tuzilishini belgilaydi.', answer: false },
    { type: 'mc', q: 'Inline stil qayerda yoziladi?', options: ['style atributida', 'Faqat .css faylda', 'Faqat <script>', 'URL da'], answer: 0 },
    { type: 'fill', q: 'Rang berish: color: ___;', answer: 'red' },
    { type: 'mc', q: 'Tashqi CSS qanday ulanadi?', options: ['<link rel="stylesheet">', '<style src="">', '<css>', '<import>'], answer: 0 },
  ],
  'fe-l8': [
    { type: 'mc', q: 'Fon rangi xususiyati?', options: ['background-color', 'bg-color', 'color-bg', 'fill'], answer: 0 },
    { type: 'mc', q: '#ff0000 qanday rang?', options: ['Qizil', 'Yashil', 'Ko‘k', 'Sariq'], answer: 0 },
    { type: 'tf', q: 'rgb(0,0,0) qora rang.', answer: true },
    { type: 'fill', q: 'Matn rangi: ___ : blue;', answer: 'color' },
    { type: 'mc', q: 'Opacity nima qiladi?', options: ['Shaffoflik', 'Kattalik', 'Shrift', 'Chegara'], answer: 0 },
  ],
  'fe-l9': [
    { type: 'mc', q: 'margin nima?', options: ['Tashqi bo‘shliq', 'Ichki bo‘shliq', 'Chegara', 'Shrift'], answer: 0 },
    { type: 'mc', q: 'padding nima?', options: ['Ichki bo‘shliq', 'Tashqi bo‘shliq', 'Rang', 'Animatsiya'], answer: 0 },
    { type: 'tf', q: 'border element chetini chizadi.', answer: true },
    { type: 'mc', q: 'border-radius nima uchun?', options: ['Yumaloq burchak', 'Rang', 'Shrift', 'Soyа'], answer: 0 },
    { type: 'fill', q: 'Yashirish: display: ___;', answer: 'none' },
  ],
  'fe-l10': [
    { type: 'mc', q: 'display: flex nima beradi?', options: ['Egilar dizayn', 'Jadval', 'Grid faqat', 'Hech narsa'], answer: 0 },
    { type: 'mc', q: 'justify-content nima uchun?', options: ['Gorizontal joylashuv', 'Vertikal shrift', 'Rang', 'Animatsiya'], answer: 0 },
    { type: 'tf', q: 'Flexbox bir o‘lchovli layout.', answer: true },
    { type: 'mc', q: 'align-items nima qiladi?', options: ['Cross-axis joylashuv', 'Faqat margin', 'Faqat padding', 'Z-index'], answer: 0 },
    { type: 'fill', q: 'Flex konteyner: display: ___;', answer: 'flex' },
  ],
  'fe-l11': [
    { type: 'mc', q: 'CSS asosiy vazifasi?', options: ['Ko‘rinishni boshqarish', 'Ma’lumot saqlash', 'Server', 'Xavfsizlik'], answer: 0 },
    { type: 'mc', q: 'Qaysi biri rang?', options: ['#00ff00', 'flex', 'margin', 'href'], answer: 0 },
    { type: 'tf', q: 'CSS da klass .nuqta bilan yoziladi.', answer: true },
    { type: 'match', pairs: [['color', 'Matn rangi'], ['margin', 'Tashqi bo‘shliq'], ['padding', 'Ichki bo‘shliq'], ['display', 'Ko‘rsatish turi']] },
    { type: 'mc', q: 'Responsive dizayn uchun nima kerak?', options: ['Media query', 'Faqat HTML', 'Faqat JS', 'PHP'], answer: 0 },
  ],
  'm-l1': [
    { type: 'mc', q: '7 + 5 = ?', options: ['12', '11', '13', '10'], answer: 0 },
    { type: 'mc', q: '15 + 8 = ?', options: ['23', '22', '24', '21'], answer: 0 },
    { type: 'fill', q: '9 + 6 = ___', answer: '15' },
    { type: 'mc', q: '100 + 25 = ?', options: ['125', '120', '130', '115'], answer: 0 },
    { type: 'tf', q: '0 + 5 = 5', answer: true },
  ],
  'm-l2': [
    { type: 'mc', q: '10 − 3 = ?', options: ['7', '6', '8', '5'], answer: 0 },
    { type: 'mc', q: '20 − 12 = ?', options: ['8', '7', '9', '10'], answer: 0 },
    { type: 'fill', q: '15 − 9 = ___', answer: '6' },
    { type: 'mc', q: '50 − 25 = ?', options: ['25', '20', '30', '15'], answer: 0 },
    { type: 'tf', q: '8 − 8 = 0', answer: true },
  ],
  'm-l3': [
    { type: 'mc', q: '4 + 9 = ?', options: ['13', '12', '14', '11'], answer: 0 },
    { type: 'mc', q: '16 − 7 = ?', options: ['9', '8', '10', '7'], answer: 0 },
    { type: 'fill', q: '11 + 11 = ___', answer: '22' },
    { type: 'mc', q: '30 − 18 = ?', options: ['12', '11', '13', '14'], answer: 0 },
    { type: 'tf', q: '5 + 0 = 0', answer: false },
  ],
  'm-l4': [
    { type: 'mc', q: '6 × 3 = ?', options: ['18', '16', '20', '12'], answer: 0 },
    { type: 'mc', q: '7 × 4 = ?', options: ['28', '24', '32', '21'], answer: 0 },
    { type: 'fill', q: '5 × 5 = ___', answer: '25' },
    { type: 'mc', q: '9 × 2 = ?', options: ['18', '16', '20', '11'], answer: 0 },
    { type: 'tf', q: '0 × 100 = 0', answer: true },
  ],
  'm-l5': [
    { type: 'mc', q: '12 ÷ 3 = ?', options: ['4', '3', '5', '6'], answer: 0 },
    { type: 'mc', q: '20 ÷ 5 = ?', options: ['4', '5', '3', '2'], answer: 0 },
    { type: 'fill', q: '16 ÷ 4 = ___', answer: '4' },
    { type: 'mc', q: '9 ÷ 3 = ?', options: ['3', '2', '4', '6'], answer: 0 },
    { type: 'tf', q: '10 ÷ 2 = 5', answer: true },
  ],
  'm-l6': [
    { type: 'mc', q: '8 + 7 = ?', options: ['15', '14', '16', '13'], answer: 0 },
    { type: 'mc', q: '6 × 6 = ?', options: ['36', '30', '42', '24'], answer: 0 },
    { type: 'mc', q: '18 ÷ 2 = ?', options: ['9', '8', '10', '6'], answer: 0 },
    { type: 'fill', q: '14 − 5 = ___', answer: '9' },
    { type: 'tf', q: '3 × 0 = 3', answer: false },
  ],
  'en-l1': [
    { type: 'mc', q: '“Hello” o‘zbekcha?', options: ['Salom', 'Xayr', 'Rahmat', 'Iltimos'], answer: 0 },
    { type: 'mc', q: '“Goodbye” = ?', options: ['Xayr', 'Salom', 'Ha', 'Yo‘q'], answer: 0 },
    { type: 'fill', q: 'Thank you = ___', answer: 'rahmat' },
    { type: 'tf', q: '“Please” — “Iltimos”.', answer: true },
    { type: 'mc', q: '“Good morning” = ?', options: ['Xayrli tong', 'Xayrli kech', 'Xayrli tun', 'Salom'], answer: 0 },
  ],
  'en-l2': [
    { type: 'mc', q: '“Mother” = ?', options: ['Ona', 'Ota', 'Aka', 'Opa'], answer: 0 },
    { type: 'mc', q: '“Father” = ?', options: ['Ota', 'Ona', 'Ukа', 'Buvi'], answer: 0 },
    { type: 'match', pairs: [['Brother', 'Aka/uka'], ['Sister', 'Opa/singil'], ['Family', 'Oila'], ['Child', 'Bola']] },
    { type: 'fill', q: 'Sister = ___', answer: 'opa' },
    { type: 'tf', q: '“Parents” — ota-ona.', answer: true },
  ],
  'en-l3': [
    { type: 'mc', q: '“Hello” javobi?', options: ['Hi / Hello', 'Bye', 'Thanks', 'Sorry'], answer: 0 },
    { type: 'mc', q: '“How are you?” = ?', options: ['Qandaysiz?', 'Qayerdasiz?', 'Nima qilasiz?', 'Kim siz?'], answer: 0 },
    { type: 'fill', q: 'I am fine = Men ___man', answer: 'yaxshi' },
    { type: 'tf', q: '“See you” — “Ko‘rishguncha”.', answer: true },
    { type: 'mc', q: '“Nice to meet you” = ?', options: ['Tanishganimdan xursandman', 'Xayr', 'Rahmat', 'Kechirasiz'], answer: 0 },
  ],
  'en-l4': [
    { type: 'mc', q: '“One” = ?', options: ['Bir', 'Ikki', 'Uch', 'To‘rt'], answer: 0 },
    { type: 'mc', q: '“Five” = ?', options: ['Besh', 'Olti', 'Yetti', 'Sakkiz'], answer: 0 },
    { type: 'fill', q: 'Ten = ___', answer: 'o‘n' },
    { type: 'tf', q: '“Three” — uch.', answer: true },
    { type: 'mc', q: '2 + 2 inglizcha?', options: ['Four', 'Three', 'Five', 'Six'], answer: 0 },
  ],
  'en-l5': [
    { type: 'mc', q: '“Red” = ?', options: ['Qizil', 'Yashil', 'Ko‘k', 'Sariq'], answer: 0 },
    { type: 'mc', q: '“Blue” = ?', options: ['Ko‘k', 'Qizil', 'Oq', 'Qora'], answer: 0 },
    { type: 'match', pairs: [['Green', 'Yashil'], ['Yellow', 'Sariq'], ['Black', 'Qora'], ['White', 'Oq']] },
    { type: 'fill', q: 'White = ___', answer: 'oq' },
    { type: 'tf', q: '“Orange” — to‘q sariq/apelsin rangi.', answer: true },
  ],
  'en-l6': [
    { type: 'mc', q: '“Thank you” = ?', options: ['Rahmat', 'Salom', 'Xayr', 'Ha'], answer: 0 },
    { type: 'mc', q: '“Mother” = ?', options: ['Ona', 'Ota', 'Aka', 'Do‘st'], answer: 0 },
    { type: 'mc', q: '“Seven” = ?', options: ['Yetti', 'Olti', 'Besh', 'Sakkiz'], answer: 0 },
    { type: 'fill', q: 'Green = ___', answer: 'yashil' },
    { type: 'tf', q: '“Hello” — salom.', answer: true },
  ],
};

// Generic fallback generator
function getQuestions(lessonId) {
  if (QUESTIONS[lessonId]) return QUESTIONS[lessonId].map((q, i) => ({ ...q, id: lessonId + '-' + i }));
  // fallback simple mc
  return [1,2,3,4,5].map((n, i) => ({
    id: lessonId + '-' + i,
    type: 'mc',
    q: `Savol ${n}: to‘g‘ri javobni tanlang`,
    options: ['To‘g‘ri javob', 'Noto‘g‘ri A', 'Noto‘g‘ri B', 'Noto‘g‘ri C'],
    answer: 0,
  }));
}

function getCourse(id) {
  return COURSES.find(c => c.id === id);
}

function allLessons(course) {
  return course.units.flatMap(u => u.lessons.map(l => ({ ...l, unitId: u.id })));
}

function findLesson(courseId, lessonId) {
  // Local COURSES + API orqali yuklangan window.COURSES
  const pools = [];
  if (typeof COURSES !== 'undefined') pools.push(COURSES);
  if (typeof window !== 'undefined' && window.COURSES && window.COURSES !== COURSES) {
    pools.push(window.COURSES);
  }
  for (const pool of pools) {
    const c = (pool || []).find(x => x.id === courseId);
    if (!c || !c.units) continue;
    for (const u of c.units) {
      const l = (u.lessons || []).find(x => x.id === lessonId);
      if (l) return { course: c, unit: u, lesson: l };
    }
  }
  // lessonId bo'yicha global qidiruv
  for (const pool of pools) {
    for (const c of (pool || [])) {
      for (const u of (c.units || [])) {
        const l = (u.lessons || []).find(x => x.id === lessonId);
        if (l) return { course: c, unit: u, lesson: l };
      }
    }
  }
  return null;
}


// Rasmli quiz savollari (Duolingo uslubi)
const IMAGE_QUESTIONS = {
  'en-l1': [
    { type: 'mc_img', badge: 'YANGI SO‘Z', q: 'Which one of these is “hello”?', options: [
      { img: '/assets/quiz/sun.svg', label: 'hello' },
      { img: '/assets/quiz/book.svg', label: 'book' },
      { img: '/assets/quiz/apple.svg', label: 'apple' },
    ], answer: 0 },
    { type: 'mc_img', badge: 'YANGI SO‘Z', q: 'Which one means “book”?', options: [
      { img: '/assets/quiz/car.svg', label: 'car' },
      { img: '/assets/quiz/book.svg', label: 'book' },
      { img: '/assets/quiz/tree.svg', label: 'tree' },
    ], answer: 1 },
    { type: 'mc', q: '“Salom” inglizcha?', options: ['Hello', 'Bye', 'Thanks', 'Please'], answer: 0 },
    { type: 'mc_img', badge: 'SO‘Z', q: 'Find “apple”', options: [
      { img: '/assets/quiz/dog.svg', label: 'dog' },
      { img: '/assets/quiz/cat.svg', label: 'cat' },
      { img: '/assets/quiz/apple.svg', label: 'apple' },
    ], answer: 2 },
    { type: 'tf', q: '“Goodbye” — xayrlashuv.', answer: true },
  ],
  'en-l2': [
    { type: 'mc_img', badge: 'OILA', q: 'Which one is “father” / dad?', options: [
      { img: '/assets/quiz/man.svg', label: 'father' },
      { img: '/assets/quiz/woman.svg', label: 'mother' },
      { img: '/assets/quiz/baby.svg', label: 'baby' },
    ], answer: 0 },
    { type: 'mc_img', badge: 'OILA', q: 'Which one is “mother”?', options: [
      { img: '/assets/quiz/baby.svg', label: 'baby' },
      { img: '/assets/quiz/woman.svg', label: 'mother' },
      { img: '/assets/quiz/man.svg', label: 'father' },
    ], answer: 1 },
    { type: 'mc_img', badge: 'OILA', q: 'Which one is a “baby”?', options: [
      { img: '/assets/quiz/man.svg', label: 'man' },
      { img: '/assets/quiz/woman.svg', label: 'woman' },
      { img: '/assets/quiz/baby.svg', label: 'baby' },
    ], answer: 2 },
    { type: 'mc', q: '“Mother” o‘zbekcha?', options: ['Ona', 'Ota', 'Aka', 'Opa'], answer: 0 },
    { type: 'tf', q: '“Sister” — opa/singil.', answer: true },
  ],
  'en-l4': [
    { type: 'mc_img', badge: 'RAQAM', q: 'Which one is “one”?', options: [
      { img: '/assets/quiz/num1.svg', label: 'one' },
      { img: '/assets/quiz/num2.svg', label: 'two' },
      { img: '/assets/quiz/num3.svg', label: 'three' },
    ], answer: 0 },
    { type: 'mc_img', badge: 'RAQAM', q: 'Find the number 3', options: [
      { img: '/assets/quiz/num5.svg', label: 'five' },
      { img: '/assets/quiz/num3.svg', label: 'three' },
      { img: '/assets/quiz/num1.svg', label: 'one' },
    ], answer: 1 },
    { type: 'mc_img', badge: 'RAQAM', q: 'Which is “two”?', options: [
      { img: '/assets/quiz/num4.svg', label: 'four' },
      { img: '/assets/quiz/num2.svg', label: 'two' },
      { img: '/assets/quiz/num5.svg', label: 'five' },
    ], answer: 1 },
    { type: 'mc', q: '2 + 2 = ?', options: ['4', '3', '5', '2'], answer: 0 },
    { type: 'tf', q: 'Five = 5', answer: true },
  ],
  'en-l5': [
    { type: 'mc_img', badge: 'RANG', q: 'Which one is “red”?', options: [
      { img: '/assets/quiz/color_red.svg', label: 'red' },
      { img: '/assets/quiz/color_blue.svg', label: 'blue' },
      { img: '/assets/quiz/color_green.svg', label: 'green' },
    ], answer: 0 },
    { type: 'mc_img', badge: 'RANG', q: 'Find “blue”', options: [
      { img: '/assets/quiz/color_yellow.svg', label: 'yellow' },
      { img: '/assets/quiz/color_green.svg', label: 'green' },
      { img: '/assets/quiz/color_blue.svg', label: 'blue' },
    ], answer: 2 },
    { type: 'mc_img', badge: 'RANG', q: 'Which is “green”?', options: [
      { img: '/assets/quiz/color_green.svg', label: 'green' },
      { img: '/assets/quiz/color_red.svg', label: 'red' },
      { img: '/assets/quiz/color_yellow.svg', label: 'yellow' },
    ], answer: 0 },
    { type: 'mc', q: '“Yellow” o‘zbekcha?', options: ['Sariq', 'Qizil', 'Ko‘k', 'Yashil'], answer: 0 },
    { type: 'tf', q: 'Sky is often blue.', answer: true },
  ],
  'en-l3': [
    { type: 'mc_img', badge: 'MASHQ', q: 'Which one is a “cat”?', options: [
      { img: '/assets/quiz/dog.svg', label: 'dog' },
      { img: '/assets/quiz/cat.svg', label: 'cat' },
      { img: '/assets/quiz/apple.svg', label: 'apple' },
    ], answer: 1 },
    { type: 'mc_img', badge: 'MASHQ', q: 'Find the “dog”', options: [
      { img: '/assets/quiz/cat.svg', label: 'cat' },
      { img: '/assets/quiz/tree.svg', label: 'tree' },
      { img: '/assets/quiz/dog.svg', label: 'dog' },
    ], answer: 2 },
    { type: 'mc_img', badge: 'MASHQ', q: 'Which one is a “car”?', options: [
      { img: '/assets/quiz/car.svg', label: 'car' },
      { img: '/assets/quiz/house.svg', label: 'house' },
      { img: '/assets/quiz/book.svg', label: 'book' },
    ], answer: 0 },
    { type: 'mc', q: 'Cat o‘zbekcha?', options: ['Mushuk', 'It', 'Qush', 'Ot'], answer: 0 },
    { type: 'tf', q: 'A dog says “meow”.', answer: false },
  ],
  'geo-l1': [
    { type: 'mc_img', badge: 'GEOGRAFIYA', q: 'Qaysi rasm “globus”?', options: [
      { img: '/assets/quiz/globe.svg', label: 'Globus' },
      { img: '/assets/quiz/mountain.svg', label: 'Tog‘' },
      { img: '/assets/quiz/water.svg', label: 'Suv' },
    ], answer: 0 },
    { type: 'mc_img', badge: 'GEOGRAFIYA', q: 'Tog‘ qaysi?', options: [
      { img: '/assets/quiz/tree.svg', label: 'Daraxt' },
      { img: '/assets/quiz/mountain.svg', label: 'Tog‘' },
      { img: '/assets/quiz/house.svg', label: 'Uy' },
    ], answer: 1 },
    { type: 'mc', q: 'O‘zbekiston qaysi qit’ada?', options: ['Osiyo', 'Yevropa', 'Afrika', 'Avstraliya'], answer: 0 },
    { type: 'mc_img', badge: 'TABIAT', q: 'Suv / okean belgisi?', options: [
      { img: '/assets/quiz/sun.svg', label: 'Quyosh' },
      { img: '/assets/quiz/water.svg', label: 'Suv' },
      { img: '/assets/quiz/tree.svg', label: 'O‘rmon' },
    ], answer: 1 },
    { type: 'tf', q: 'Yer — quyosh sistemasidagi sayyora.', answer: true },
  ],
  'math-l1': [
    { type: 'mc_img', badge: 'MATEMATIKA', q: 'Qaysi biri 2?', options: [
      { img: '/assets/quiz/num1.svg', label: '1' },
      { img: '/assets/quiz/num2.svg', label: '2' },
      { img: '/assets/quiz/num4.svg', label: '4' },
    ], answer: 1 },
    { type: 'mc', q: '3 + 1 = ?', options: ['4', '3', '5', '2'], answer: 0 },
    { type: 'mc_img', badge: 'MATEMATIKA', q: 'Beshlikni toping', options: [
      { img: '/assets/quiz/num5.svg', label: '5' },
      { img: '/assets/quiz/num3.svg', label: '3' },
      { img: '/assets/quiz/num1.svg', label: '1' },
    ], answer: 0 },
    { type: 'mc', q: '10 − 5 = ?', options: ['5', '4', '6', '15'], answer: 0 },
    { type: 'tf', q: '2 × 2 = 4', answer: true },
  ],
};

// Merge image questions into QUESTIONS
(function mergeImageQuestions() {
  if (typeof QUESTIONS === 'undefined') return;
  Object.keys(IMAGE_QUESTIONS).forEach(function (k) {
    QUESTIONS[k] = IMAGE_QUESTIONS[k];
  });
})();
