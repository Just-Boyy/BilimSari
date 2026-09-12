# -*- coding: utf-8 -*-
"""9-sinf — Algebra va Fizika."""

ALGEBRA = {
    'key': 'algebra',
    'topics': [
        {
            'slug': 'kvadrat-tenglama',
            'title': 'Kvadrat tenglamalar',
            'summary': "ax² + bx + c = 0 tenglamasini diskriminant orqali yechish",
            'duration': 25,
            'lesson': [
                {'type': 'text', 'title': 'Kvadrat tenglama nima?', 'body':
                 "Noma'lumning eng katta darajasi **2** bo'lgan tenglama **kvadrat tenglama** deyiladi."},
                {'type': 'formula', 'body': 'ax² + bx + c = 0,  a ≠ 0'},
                {'type': 'text', 'title': 'Koeffitsiyentlar', 'body':
                 "**a** — bosh koeffitsiyent (x² oldidagi son)\n"
                 "**b** — ikkinchi koeffitsiyent (x oldidagi son)\n"
                 "**c** — ozod had (harfsiz son)\n\n"
                 "Masalan **3x² − 5x + 2 = 0** da: a = 3, b = −5, c = 2"},
                {'type': 'text', 'title': 'Diskriminant', 'body':
                 "Tenglamaning nechta ildizi borligini **diskriminant** aniqlaydi."},
                {'type': 'formula', 'body': 'D = b² − 4ac'},
                {'type': 'table', 'head': ['D', 'Ildizlar soni', 'Izoh'], 'rows': [
                    ['D > 0', '2 ta', 'Ikki xil ildiz'],
                    ['D = 0', '1 ta', 'Ildizlar teng'],
                    ['D < 0', "yo'q", 'Haqiqiy ildiz yo\'q'],
                ]},
                {'type': 'formula', 'body': 'x = (−b ± √D) / (2a)'},
                {'type': 'steps', 'title': 'Yechish tartibi', 'items': [
                    "Tenglamani ax² + bx + c = 0 ko'rinishiga keltiring.",
                    "a, b, c koeffitsiyentlarni yozib oling (ishorasi bilan!).",
                    "D = b² − 4ac ni hisoblang.",
                    "D ning ishorasiga qarab ildizlar sonini aniqlang.",
                    "Formula bo'yicha ildizlarni toping.",
                    "Javobni tenglamaga qo'yib tekshiring.",
                ]},
                {'type': 'example', 'title': 'Misol: x² − 5x + 6 = 0', 'body':
                 "a = 1, b = −5, c = 6\n\n"
                 "**D** = (−5)² − 4·1·6 = 25 − 24 = **1**\n"
                 "D > 0 → 2 ta ildiz\n\n"
                 "√D = √1 = 1\n\n"
                 "x₁ = (5 + 1) / 2 = **3**\n"
                 "x₂ = (5 − 1) / 2 = **2**\n\n"
                 "Tekshirish: 3² − 5·3 + 6 = 9 − 15 + 6 = 0 ✓"},
                {'type': 'text', 'title': 'Vyet teoremasi', 'body':
                 "Agar a = 1 bo'lsa (keltirilgan tenglama x² + px + q = 0):\n\n"
                 "x₁ + x₂ = −p\n"
                 "x₁ · x₂ = q\n\n"
                 "Yuqoridagi misolda: 3 + 2 = 5 = −(−5) ✓ va 3 · 2 = 6 ✓\n\n"
                 "Bu usul bilan oddiy tenglamalarni **og'zaki** yechish mumkin."},
                {'type': 'note', 'body':
                 "Eng ko'p uchraydigan xato — **ishorani** noto'g'ri olish. "
                 "b = −5 bo'lsa, b² = (−5)² = +25, lekin −b = +5. Diqqat bilan!"},
                {'type': 'life', 'body':
                 "Kvadrat tenglamalar fizikada (jism harakati), iqtisodda (foyda hisobi) "
                 "va muhandislikda keng qo'llanadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'x² − 7x + 12 = 0 tenglamada b nechchi?',
                 'options': ['7', '−7', '12', '1'], 'answer': 1,
                 'explain': "x oldidagi koeffitsiyent ishorasi bilan olinadi: b = −7."},
                {'type': 'mc', 'q': 'D = 0 bo\'lsa nechta ildiz bor?',
                 'options': ['0 ta', '1 ta', '2 ta'], 'answer': 1,
                 'explain': 'D = 0 → ildizlar teng, bitta ildiz.'},
                {'type': 'mc', 'q': 'x² − 5x + 6 = 0 tenglamaning diskriminanti?',
                 'options': ['1', '49', '−1', '25'], 'answer': 0,
                 'explain': 'D = 25 − 24 = 1.'},
                {'type': 'mc', 'q': 'x² − 4 = 0 tenglamaning ildizlari?',
                 'options': ['x = 2', 'x = 2 va x = −2', 'x = 4', 'Ildiz yo\'q'], 'answer': 1,
                 'explain': 'x² = 4 → x = ±2.'},
                {'type': 'tf', 'q': "D < 0 bo'lsa tenglamaning haqiqiy ildizi yo'q.",
                 'answer': True, 'explain': "To'g'ri — manfiy sondan kvadrat ildiz chiqmaydi."},
                {'type': 'fill', 'q': 'x² + 3x + 2 = 0 tenglamaning diskriminantini hisoblang.',
                 'answer': '1', 'explain': 'D = 9 − 8 = 1.'},
            ],
            'homework': {
                'intro': 'Tenglamalarni yeching. Javobni son bilan yozing.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': 'x² − 6x + 8 = 0 tenglamaning diskriminanti?',
                     'answer': '4', 'hint': 'D = 36 − 32'},
                    {'id': 'h2', 'type': 'number', 'prompt': 'Shu tenglamaning KATTA ildizini yozing.',
                     'answer': '4', 'hint': 'x = (6 ± 2)/2'},
                    {'id': 'h3', 'type': 'number', 'prompt': 'x² − 9 = 0 tenglamaning musbat ildizi?',
                     'answer': '3'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "D ning ishorasi ildizlar soniga qanday ta'sir qiladi? Tushuntiring."},
                ],
            },
        },
        {
            'slug': 'funksiya',
            'title': 'Funksiya va uning grafigi',
            'summary': "Chiziqli va kvadratik funksiyalar",
            'duration': 22,
            'lesson': [
                {'type': 'text', 'title': 'Funksiya nima?', 'body':
                 "**Funksiya** — har bir x qiymatiga **bitta** y qiymatini mos qo'yuvchi qoida.\n\n"
                 "y = f(x) deb yoziladi.\n"
                 "**x** — erkli o'zgaruvchi (argument)\n"
                 "**y** — erksiz o'zgaruvchi (funksiya qiymati)"},
                {'type': 'text', 'title': 'Chiziqli funksiya', 'body':
                 "Grafigi — **to'g'ri chiziq**."},
                {'type': 'formula', 'body': 'y = kx + b'},
                {'type': 'text', 'title': 'k va b nimani bildiradi?', 'body':
                 "**k** — burchak koeffitsiyenti (chiziqning qiyaligi)\n"
                 "• k > 0 → chiziq **o'sadi** (chapdan o'ngga ko'tariladi)\n"
                 "• k < 0 → chiziq **kamayadi**\n"
                 "• k = 0 → chiziq **gorizontal**\n\n"
                 "**b** — chiziq Oy o'qini kesib o'tgan nuqta"},
                {'type': 'example', 'title': 'y = 2x + 3 ni chizamiz', 'body':
                 "Ikkita nuqta yetarli (chiziq uchun):\n\n"
                 "x = 0 → y = 2·0 + 3 = **3** → nuqta (0; 3)\n"
                 "x = 1 → y = 2·1 + 3 = **5** → nuqta (1; 5)\n\n"
                 "Shu ikki nuqtani tutashtiring — chiziq tayyor.\n"
                 "k = 2 > 0, demak chiziq o'sadi."},
                {'type': 'text', 'title': 'Kvadratik funksiya', 'body':
                 "Grafigi — **parabola**."},
                {'type': 'formula', 'body': 'y = ax² + bx + c'},
                {'type': 'text', 'title': 'Parabola xossalari', 'body':
                 "• **a > 0** → shoxlari yuqoriga (piyola shaklida)\n"
                 "• **a < 0** → shoxlari pastga (soyabon shaklida)\n\n"
                 "**Uchi (cho'qqisi)** — eng past yoki eng baland nuqta:\n"
                 "x₀ = −b / (2a), so'ng y₀ ni hisoblaymiz.\n\n"
                 "Parabola uchidan o'tuvchi vertikal chiziq — **simmetriya o'qi**."},
                {'type': 'example', 'title': 'y = x² − 4x + 3 uchini topamiz', 'body':
                 "a = 1, b = −4\n\n"
                 "x₀ = −(−4) / (2·1) = 4/2 = **2**\n"
                 "y₀ = 2² − 4·2 + 3 = 4 − 8 + 3 = **−1**\n\n"
                 "Uchi: (2; −1). a > 0 → shoxlari yuqoriga."},
                {'type': 'note', 'body':
                 "Grafikni chizishdan oldin **jadval** tuzing: bir nechta x qiymati uchun "
                 "y ni hisoblang. Nuqtalar ko'p bo'lsa, grafik aniqroq chiqadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'y = 3x − 2 funksiyaning grafigi qanday?',
                 'options': ["To'g'ri chiziq", 'Parabola', 'Aylana'], 'answer': 0,
                 'explain': 'Chiziqli funksiya — grafigi to\'g\'ri chiziq.'},
                {'type': 'mc', 'q': 'y = kx + b da k < 0 bo\'lsa chiziq qanday?',
                 'options': ["O'sadi", 'Kamayadi', 'Gorizontal'], 'answer': 1,
                 'explain': 'k manfiy — chiziq pasayadi.'},
                {'type': 'mc', 'q': 'y = x² + 2x parabolaning shoxlari qayoqqa?',
                 'options': ['Yuqoriga', 'Pastga'], 'answer': 0,
                 'explain': 'a = 1 > 0 → yuqoriga.'},
                {'type': 'mc', 'q': 'y = 2x + 5 funksiyada x = 3 bo\'lsa y nechchi?',
                 'options': ['10', '11', '8'], 'answer': 1,
                 'explain': 'y = 2·3 + 5 = 11.'},
                {'type': 'tf', 'q': "Kvadratik funksiyaning grafigi parabola deyiladi.",
                 'answer': True, 'explain': "To'g'ri."},
                {'type': 'fill', 'q': 'y = x² − 6x + 5 parabolaning uchi x₀ nechchi?',
                 'answer': '3', 'explain': 'x₀ = 6/2 = 3.'},
            ],
            'homework': {
                'intro': 'Funksiyalar bilan ishlang.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': 'y = 4x − 7 da x = 2 bo\'lsa y nechchi?',
                     'answer': '1'},
                    {'id': 'h2', 'type': 'number', 'prompt': "y = x² − 8x + 1 parabolaning uchi x₀ nechchi?",
                     'answer': '4'},
                    {'id': 'h3', 'type': 'text', 'prompt': "y = −2x + 1 chizig'i o'sadimi yoki kamayadimi?",
                     'answer': 'kamayadi'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "y = x + 2 funksiya uchun 3 ta nuqta (x; y) yozing."},
                ],
            },
        },
        {
            'slug': 'progressiya',
            'title': 'Progressiyalar',
            'summary': "Arifmetik va geometrik progressiya",
            'duration': 22,
            'lesson': [
                {'type': 'text', 'title': 'Arifmetik progressiya', 'body':
                 "Har bir keyingi had oldingisiga **bir xil son qo'shish** bilan hosil bo'ladi. "
                 "Bu son — **ayirma (d)**.\n\n"
                 "Misol: 2, 5, 8, 11, 14, ... bu yerda d = 3"},
                {'type': 'formula', 'body': 'aₙ = a₁ + (n − 1)·d'},
                {'type': 'formula', 'body': 'Sₙ = (a₁ + aₙ)·n / 2'},
                {'type': 'example', 'title': 'Misol', 'body':
                 "Progressiya: 3, 7, 11, 15, ...\n\n"
                 "a₁ = 3, d = 7 − 3 = 4\n\n"
                 "**10-hadni topamiz:**\n"
                 "a₁₀ = 3 + (10 − 1)·4 = 3 + 36 = **39**\n\n"
                 "**Dastlabki 10 ta hadning yig'indisi:**\n"
                 "S₁₀ = (3 + 39)·10 / 2 = 42·5 = **210**"},
                {'type': 'text', 'title': 'Geometrik progressiya', 'body':
                 "Har bir keyingi had oldingisini **bir xil songa ko'paytirish** bilan hosil bo'ladi. "
                 "Bu son — **maxraj (q)**.\n\n"
                 "Misol: 2, 6, 18, 54, ... bu yerda q = 3"},
                {'type': 'formula', 'body': 'bₙ = b₁ · q^(n−1)'},
                {'type': 'example', 'title': 'Misol', 'body':
                 "Progressiya: 5, 10, 20, 40, ...\n\n"
                 "b₁ = 5, q = 10 / 5 = 2\n\n"
                 "**6-hadni topamiz:**\n"
                 "b₆ = 5 · 2⁵ = 5 · 32 = **160**"},
                {'type': 'table', 'head': ['Belgi', 'Arifmetik', 'Geometrik'], 'rows': [
                    ['Amal', "Qo'shish", "Ko'paytirish"],
                    ['Farq/maxraj', 'd = aₙ − aₙ₋₁', 'q = bₙ / bₙ₋₁'],
                    ['Misol', '1, 4, 7, 10', '1, 4, 16, 64'],
                ]},
                {'type': 'note', 'body':
                 "Turini aniqlash oson: hadlar orasidagi **ayirma** doimiy bo'lsa — arifmetik, "
                 "**nisbat** doimiy bo'lsa — geometrik."},
                {'type': 'life', 'body':
                 "Bank foizi — geometrik progressiya. Har oy bir xil summa yig'ish — "
                 "arifmetik progressiya. Progressiyalar moliyaviy savodxonlik uchun kerak."},
            ],
            'quiz': [
                {'type': 'mc', 'q': '2, 5, 8, 11, ... progressiyaning ayirmasi?',
                 'options': ['2', '3', '5'], 'answer': 1,
                 'explain': 'd = 5 − 2 = 3.'},
                {'type': 'mc', 'q': '3, 6, 12, 24, ... bu qanday progressiya?',
                 'options': ['Arifmetik', 'Geometrik'], 'answer': 1,
                 'explain': "Har had 2 ga ko'paytirilgan — geometrik."},
                {'type': 'mc', 'q': 'a₁ = 4, d = 3 bo\'lsa a₅ nechchi?',
                 'options': ['16', '19', '13'], 'answer': 0,
                 'explain': 'a₅ = 4 + 4·3 = 16.'},
                {'type': 'mc', 'q': 'b₁ = 2, q = 3 bo\'lsa b₄ nechchi?',
                 'options': ['18', '54', '24'], 'answer': 1,
                 'explain': 'b₄ = 2 · 3³ = 2 · 27 = 54.'},
                {'type': 'tf', 'q': "Arifmetik progressiyada hadlar qo'shish orqali hosil bo'ladi.",
                 'answer': True, 'explain': "To'g'ri."},
                {'type': 'fill', 'q': '1, 3, 5, 7, ... progressiyada 6-had nechchi?',
                 'answer': '11', 'explain': 'a₆ = 1 + 5·2 = 11.'},
            ],
            'homework': {
                'intro': 'Progressiyalar bo\'yicha.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': '5, 9, 13, ... progressiyaning ayirmasi?',
                     'answer': '4'},
                    {'id': 'h2', 'type': 'number', 'prompt': 'a₁ = 2, d = 5 bo\'lsa a₆ nechchi?',
                     'answer': '27'},
                    {'id': 'h3', 'type': 'number', 'prompt': 'b₁ = 3, q = 2 bo\'lsa b₅ nechchi?',
                     'answer': '48'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Hayotdan geometrik progressiyaga misol keltiring."},
                ],
            },
        },
        {
            'slug': 'tengsizliklar',
            'title': 'Tengsizliklar',
            'summary': "Chiziqli tengsizliklarni yechish qoidalari",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Tengsizlik nima?', 'body':
                 "Tenglamada **=**, tengsizlikda **>**, **<**, **≥**, **≤** belgilari bo'ladi.\n\n"
                 "Tenglamaning javobi — aniq son.\n"
                 "Tengsizlikning javobi — sonlar **to'plami** (oraliq)."},
                {'type': 'steps', 'title': 'Yechish qoidalari', 'items': [
                    "Ikki tomonga bir xil son qo'shish/ayirish mumkin — ishora o'zgarmaydi.",
                    "Ikki tomonni MUSBAT songa ko'paytirish/bo'lish mumkin — ishora o'zgarmaydi.",
                    "MANFIY songa ko'paytirsangiz/bo'lsangiz — ishora TESKARI aylanadi!",
                    "Noma'lumni bir tomonga, sonlarni ikkinchi tomonga to'plang.",
                ]},
                {'type': 'note', 'body':
                 "**Eng muhim qoida:** manfiy songa ko'paytirganda yoki bo'lganda "
                 "tengsizlik ishorasi **teskari** bo'ladi.\n\n"
                 "−2x > 6  →  x **<** −3  (> belgisi < ga aylandi)"},
                {'type': 'example', 'title': 'Misol 1: 3x + 5 < 14', 'body':
                 "3x + 5 < 14\n"
                 "3x < 14 − 5\n"
                 "3x < 9\n"
                 "x < 3\n\n"
                 "Javob: x < 3, ya'ni (−∞; 3)"},
                {'type': 'example', 'title': 'Misol 2: −4x ≥ 12', 'body':
                 "−4x ≥ 12\n\n"
                 "Ikki tomonni −4 ga bo'lamiz. **Manfiy son!** Ishora teskari:\n\n"
                 "x ≤ −3\n\n"
                 "Javob: x ≤ −3, ya'ni (−∞; −3]"},
                {'type': 'text', 'title': 'Oraliqlarni yozish', 'body':
                 "**x > 3** → (3; +∞) — qavs ochiq, 3 kirmaydi\n"
                 "**x ≥ 3** → [3; +∞) — kvadrat qavs, 3 kiradi\n"
                 "**2 < x ≤ 7** → (2; 7]\n\n"
                 "Cheksizlik doim **ochiq qavs** bilan yoziladi."},
                {'type': 'life', 'body':
                 "«Kamida 18 yosh» — bu x ≥ 18. «5 000 000 so'mdan kam» — bu x < 5 000 000. "
                 "Tengsizliklar shartlarni ifodalaydi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': '2x < 10 tengsizlikning yechimi?',
                 'options': ['x < 5', 'x > 5', 'x = 5'], 'answer': 0,
                 'explain': "Ikki tomonni 2 ga bo'lamiz: x < 5."},
                {'type': 'mc', 'q': '−3x > 9 tengsizlikning yechimi?',
                 'options': ['x > −3', 'x < −3', 'x > 3'], 'answer': 1,
                 'explain': "Manfiy songa bo'ldik — ishora teskari: x < −3."},
                {'type': 'mc', 'q': 'Qachon tengsizlik ishorasi teskari bo\'ladi?',
                 'options': ["Musbat songa ko'paytirganda", "Manfiy songa ko'paytirganda",
                             "Son qo'shganda"], 'answer': 1,
                 'explain': 'Faqat manfiy songa ko\'paytirish/bo\'lishda.'},
                {'type': 'mc', 'q': 'x ≥ 4 oraliq qanday yoziladi?',
                 'options': ['(4; +∞)', '[4; +∞)', '(−∞; 4]'], 'answer': 1,
                 'explain': '≥ bo\'lgani uchun kvadrat qavs: [4; +∞).'},
                {'type': 'tf', 'q': "Tengsizlikning yechimi odatda sonlar to'plami bo'ladi.",
                 'answer': True, 'explain': "To'g'ri — bitta son emas, oraliq."},
                {'type': 'fill', 'q': 'x + 7 < 12 tengsizlikda x qanday sonlardan kichik?',
                 'answer': '5', 'explain': 'x < 5.'},
            ],
            'homework': {
                'intro': 'Tengsizliklarni yeching.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': '4x < 20 → x qaysi sondan kichik?',
                     'answer': '5'},
                    {'id': 'h2', 'type': 'number', 'prompt': 'x − 3 ≥ 7 → x qaysi sondan katta yoki teng?',
                     'answer': '10'},
                    {'id': 'h3', 'type': 'text', 'prompt': "−2x > 8 yechimida ishora teskari bo'ladimi? (ha/yo'q)",
                     'answer': 'ha'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Nima uchun manfiy songa ko'paytirganda ishora o'zgaradi? Fikringizni yozing."},
                ],
            },
        },
    ],
}

PHYSICS = {
    'key': 'physics',
    'topics': [
        {
            'slug': 'harakat',
            'title': 'Mexanik harakat',
            'summary': "Tezlik, yo'l va vaqt orasidagi bog'liqlik",
            'duration': 22,
            'lesson': [
                {'type': 'text', 'title': 'Mexanik harakat', 'body':
                 "**Mexanik harakat** — jismning vaqt o'tishi bilan boshqa jismlarga nisbatan "
                 "o'z o'rnini o'zgartirishi.\n\n"
                 "Harakat doim **sanoq jismiga nisbatan** qaraladi. "
                 "Avtobusda o'tirgan yo'lovchi yer uchun harakatda, avtobus uchun tinch holatda."},
                {'type': 'text', 'title': 'Asosiy kattaliklar', 'body':
                 "**Yo'l (s)** — bosib o'tilgan masofa. Birligi: metr (m)\n"
                 "**Vaqt (t)** — harakat davomiyligi. Birligi: sekund (s)\n"
                 "**Tezlik (v)** — vaqt birligida bosilgan yo'l. Birligi: m/s"},
                {'type': 'formula', 'body': 'v = s / t'},
                {'type': 'formula', 'body': 's = v · t          t = s / v'},
                {'type': 'text', 'title': 'Birliklarni almashtirish', 'body':
                 "km/soat dan m/s ga: **3,6 ga bo'lamiz**\n"
                 "m/s dan km/soat ga: **3,6 ga ko'paytiramiz**\n\n"
                 "72 km/soat = 72 : 3,6 = **20 m/s**\n"
                 "10 m/s = 10 · 3,6 = **36 km/soat**"},
                {'type': 'example', 'title': 'Masala', 'body':
                 "Avtomobil 3 soatda 180 km yo'l bosdi. Tezligi qancha?\n\n"
                 "**Berilgan:** s = 180 km, t = 3 soat\n"
                 "**Topish kerak:** v\n\n"
                 "v = s / t = 180 / 3 = **60 km/soat**\n\n"
                 "m/s da: 60 : 3,6 ≈ **16,7 m/s**"},
                {'type': 'text', 'title': 'Harakat turlari', 'body':
                 "**Tekis harakat** — tezlik o'zgarmaydi (v = const)\n"
                 "**Notekis harakat** — tezlik o'zgaradi\n\n"
                 "Notekis harakatda **o'rtacha tezlik** hisoblanadi:\n"
                 "v(o'rt) = butun yo'l / butun vaqt"},
                {'type': 'note', 'body':
                 "Masala yechishda avval **barcha birliklarni bir xil tizimga** keltiring. "
                 "km va m ni, soat va sekundni aralashtirmang."},
                {'type': 'life', 'body':
                 "Yo'l belgisidagi «60» — soatiga 60 km. Bu 16,7 m/s degani: "
                 "mashina bir sekundda 16 metrdan ko'proq yuradi. Shuning uchun yo'ldan "
                 "o'tishda ehtiyot bo'ling."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Tezlik formulasi qaysi?',
                 'options': ['v = s · t', 'v = s / t', 'v = t / s'], 'answer': 1,
                 'explain': "Tezlik = yo'l / vaqt."},
                {'type': 'mc', 'q': 'Jism 2 soatda 120 km yurdi. Tezligi qancha?',
                 'options': ['60 km/soat', '240 km/soat', '120 km/soat'], 'answer': 0,
                 'explain': 'v = 120 / 2 = 60 km/soat.'},
                {'type': 'mc', 'q': '36 km/soat necha m/s?',
                 'options': ['10 m/s', '36 m/s', '100 m/s'], 'answer': 0,
                 'explain': "36 : 3,6 = 10 m/s."},
                {'type': 'mc', 'q': 'Tezlikning SI dagi birligi?',
                 'options': ['km/soat', 'm/s', 'm'], 'answer': 1,
                 'explain': 'SI tizimida tezlik m/s da o\'lchanadi.'},
                {'type': 'tf', 'q': "Harakat sanoq jismiga nisbatan qaraladi.",
                 'answer': True, 'explain': "To'g'ri — harakat nisbiy."},
                {'type': 'fill', 'q': "Tezligi 20 m/s bo'lgan jism 5 s da necha metr yuradi?",
                 'answer': '100', 'explain': 's = 20 · 5 = 100 m.'},
            ],
            'homework': {
                'intro': "Masalalarni yeching. Faqat son yozing.",
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "Jism 4 s da 60 m yurdi. Tezligi necha m/s?",
                     'answer': '15'},
                    {'id': 'h2', 'type': 'number', 'prompt': '72 km/soat necha m/s?', 'answer': '20'},
                    {'id': 'h3', 'type': 'number',
                     'prompt': "Tezligi 25 m/s bo'lgan jism 8 s da necha metr yuradi?",
                     'answer': '200'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Maktabgacha bo'lgan masofa va vaqtni taxminlab, tezligingizni hisoblang."},
                ],
            },
        },
        {
            'slug': 'kuch-nyuton',
            'title': 'Kuch va Nyuton qonunlari',
            'summary': "Nyutonning uchta qonuni va ularning ma'nosi",
            'duration': 25,
            'lesson': [
                {'type': 'text', 'title': 'Kuch nima?', 'body':
                 "**Kuch (F)** — jismlarning bir-biriga ta'siri o'lchovi. "
                 "Kuch jismning tezligini o'zgartiradi yoki uni deformatsiyalaydi.\n\n"
                 "Birligi — **Nyuton (N)**."},
                {'type': 'text', 'title': "Nyutonning 1-qonuni (inersiya qonuni)", 'body':
                 "Agar jismga **kuch ta'sir qilmasa** (yoki kuchlar muvozanatlashgan bo'lsa), "
                 "jism tinch turadi yoki **to'g'ri chiziqli tekis harakat** qiladi.\n\n"
                 "Ya'ni: jism o'z holatini saqlashga intiladi — bu **inersiya**."},
                {'type': 'life', 'body':
                 "Avtobus keskin to'xtaganda oldinga intilasiz — tanangiz inersiya tufayli "
                 "harakatni davom ettirmoqchi. Shuning uchun xavfsizlik kamari kerak."},
                {'type': 'text', 'title': "Nyutonning 2-qonuni", 'body':
                 "Jismga ta'sir etuvchi kuch unga **tezlanish** beradi."},
                {'type': 'formula', 'body': 'F = m · a'},
                {'type': 'text', 'title': 'Qonunning ma\'nosi', 'body':
                 "**F** — kuch (N)\n"
                 "**m** — massa (kg)\n"
                 "**a** — tezlanish (m/s²)\n\n"
                 "• Kuch qancha katta bo'lsa, tezlanish shuncha katta\n"
                 "• Massa qancha katta bo'lsa, tezlanish shuncha kichik\n\n"
                 "Shuning uchun yengil aravani itarish oson, og'irini qiyin."},
                {'type': 'example', 'title': 'Masala', 'body':
                 "Massasi 5 kg bo'lgan jismga 20 N kuch ta'sir qilmoqda. Tezlanishi qancha?\n\n"
                 "F = m · a  →  a = F / m\n\n"
                 "a = 20 / 5 = **4 m/s²**"},
                {'type': 'text', 'title': "Nyutonning 3-qonuni", 'body':
                 "Har qanday ta'sirga **teng va qarama-qarshi** qarshi ta'sir mavjud.\n\n"
                 "Jismlar bir-biriga **teng kattalikdagi**, lekin **qarama-qarshi yo'nalgan** "
                 "kuch bilan ta'sir qiladi."},
                {'type': 'text', 'title': 'Og\'irlik kuchi', 'body':
                 "Yer barcha jismlarni o'ziga tortadi. Bu — **og'irlik kuchi**."},
                {'type': 'formula', 'body': 'F = m · g,   g ≈ 9,8 m/s² ≈ 10 m/s²'},
                {'type': 'example', 'title': "Og'irlik kuchi", 'body':
                 "Massasi 60 kg bo'lgan odamga ta'sir etuvchi og'irlik kuchi:\n\n"
                 "F = 60 · 10 = **600 N**"},
                {'type': 'note', 'body':
                 "**Massa** va **og'irlik** — boshqa narsa!\n"
                 "Massa (kg) hamma joyda bir xil. Og'irlik (N) sayyoraga bog'liq: "
                 "Oyda og'irligingiz 6 marta kam bo'ladi, massangiz esa o'zgarmaydi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Kuchning birligi nima?',
                 'options': ['Kilogramm', 'Nyuton', 'Joul'], 'answer': 1,
                 'explain': 'Kuch Nyutonda (N) o\'lchanadi.'},
                {'type': 'mc', 'q': "Nyutonning 2-qonuni formulasi?",
                 'options': ['F = m / a', 'F = m · a', 'F = a / m'], 'answer': 1,
                 'explain': 'F = m · a.'},
                {'type': 'mc', 'q': "Massasi 4 kg jismga 12 N kuch ta'sir qilsa, tezlanish?",
                 'options': ['3 m/s²', '48 m/s²', '8 m/s²'], 'answer': 0,
                 'explain': 'a = F/m = 12/4 = 3 m/s².'},
                {'type': 'mc', 'q': "Avtobus to'xtaganda oldinga intilish qaysi hodisa?",
                 'options': ['Inersiya', "Og'irlik", 'Ishqalanish'], 'answer': 0,
                 'explain': 'Inersiya — harakat holatini saqlash.'},
                {'type': 'tf', 'q': "Massa va og'irlik — bir xil kattalik.", 'answer': False,
                 'explain': "Yo'q. Massa kg da, og'irlik N da; og'irlik sayyoraga bog'liq."},
                {'type': 'fill', 'q': "Massasi 20 kg jismning og'irlik kuchi necha N? (g = 10)",
                 'answer': '200', 'explain': 'F = 20 · 10 = 200 N.'},
            ],
            'homework': {
                'intro': 'Masalalarni yeching (g = 10 m/s²).',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "Massasi 8 kg jismga 40 N kuch. Tezlanish necha m/s²?",
                     'answer': '5'},
                    {'id': 'h2', 'type': 'number', 'prompt': "Massasi 50 kg jismning og'irlik kuchi necha N?",
                     'answer': '500'},
                    {'id': 'h3', 'type': 'number',
                     'prompt': "Jism massasi 3 kg, tezlanishi 6 m/s². Kuch necha N?",
                     'answer': '18'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Inersiyaga hayotdan bitta misol keltiring."},
                ],
            },
        },
        {
            'slug': 'energiya',
            'title': 'Ish, quvvat va energiya',
            'summary': "Mexanik ish, quvvat va energiya turlari",
            'duration': 22,
            'lesson': [
                {'type': 'text', 'title': 'Mexanik ish', 'body':
                 "Jismga kuch ta'sir qilib, jism **ko'chsa**, **ish** bajarilgan bo'ladi.\n\n"
                 "Jism ko'chmasa — ish nolga teng. Devorni itarib turgan odam "
                 "charchaydi, lekin fizik ma'noda ish bajarmaydi!"},
                {'type': 'formula', 'body': 'A = F · s      [A] = Joul (J)'},
                {'type': 'example', 'title': 'Ish hisoblash', 'body':
                 "50 N kuch bilan jismni 4 m ko'chirdik:\n\n"
                 "A = 50 · 4 = **200 J**"},
                {'type': 'text', 'title': 'Quvvat', 'body':
                 "**Quvvat (N)** — vaqt birligida bajarilgan ish. "
                 "Ya'ni ish qanchalik **tez** bajarilgani."},
                {'type': 'formula', 'body': 'N = A / t      [N] = Vatt (Vt)'},
                {'type': 'example', 'title': 'Quvvat hisoblash', 'body':
                 "200 J ish 10 sekundda bajarildi:\n\n"
                 "N = 200 / 10 = **20 Vt**"},
                {'type': 'text', 'title': 'Energiya', 'body':
                 "**Energiya** — jismning ish bajara olish qobiliyati. "
                 "Ish kabi **Joulda** o'lchanadi.\n\n"
                 "**Kinetik energiya** — harakat energiyasi\n"
                 "**Potensial energiya** — holat (balandlik) energiyasi"},
                {'type': 'formula', 'body': 'Eₖ = m·v² / 2'},
                {'type': 'formula', 'body': 'Eₚ = m·g·h'},
                {'type': 'text', 'title': 'Energiyaning saqlanish qonuni', 'body':
                 "Energiya yo'qdan paydo bo'lmaydi va yo'qolmaydi — "
                 "faqat **bir turdan boshqasiga aylanadi**.\n\n"
                 "Tosh balandda turganda — potensial energiya.\n"
                 "Tushayotganda — potensial kamayadi, kinetik ortadi.\n"
                 "Yerga tegish oldidan — deyarli hammasi kinetik."},
                {'type': 'example', 'title': 'Energiya hisoblash', 'body':
                 "Massasi 2 kg jism 10 m balandlikda (g = 10):\n"
                 "Eₚ = 2 · 10 · 10 = **200 J**\n\n"
                 "Massasi 2 kg jism 6 m/s tezlikda:\n"
                 "Eₖ = 2 · 6² / 2 = 2 · 36 / 2 = **36 J**"},
                {'type': 'note', 'body':
                 "Kinetik energiyada tezlik **kvadratga** ko'tariladi. "
                 "Tezlik 2 marta oshsa, energiya 4 marta oshadi — shuning uchun "
                 "tez yurgan mashina zarbasi juda kuchli bo'ladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Mexanik ish formulasi?',
                 'options': ['A = F / s', 'A = F · s', 'A = s / F'], 'answer': 1,
                 'explain': "Ish = kuch × ko'chish."},
                {'type': 'mc', 'q': 'Ishning birligi?',
                 'options': ['Nyuton', 'Joul', 'Vatt'], 'answer': 1,
                 'explain': 'Ish Joulda (J) o\'lchanadi.'},
                {'type': 'mc', 'q': '30 N kuch bilan 5 m ko\'chirilsa, ish qancha?',
                 'options': ['6 J', '150 J', '35 J'], 'answer': 1,
                 'explain': 'A = 30 · 5 = 150 J.'},
                {'type': 'mc', 'q': 'Quvvatning birligi?',
                 'options': ['Joul', 'Vatt', 'Nyuton'], 'answer': 1,
                 'explain': 'Quvvat Vattda (Vt).'},
                {'type': 'tf', 'q': "Devorni itarib turgan odam mexanik ish bajaradi.",
                 'answer': False,
                 'explain': "Yo'q — devor ko'chmagani uchun ish nolga teng."},
                {'type': 'fill', 'q': "Massasi 3 kg jism 5 m balandlikda. Eₚ necha J? (g = 10)",
                 'answer': '150', 'explain': 'Eₚ = 3 · 10 · 5 = 150 J.'},
            ],
            'homework': {
                'intro': 'Hisoblang (g = 10 m/s²).',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': '25 N kuch bilan 8 m ko\'chirildi. Ish necha J?',
                     'answer': '200'},
                    {'id': 'h2', 'type': 'number', 'prompt': '600 J ish 20 s da bajarildi. Quvvat necha Vt?',
                     'answer': '30'},
                    {'id': 'h3', 'type': 'number',
                     'prompt': "Massasi 4 kg jism 3 m balandlikda. Potensial energiya necha J?",
                     'answer': '120'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Energiya bir turdan boshqasiga aylanishiga misol keltiring."},
                ],
            },
        },
        {
            'slug': 'elektr',
            'title': 'Elektr toki',
            'summary': "Tok kuchi, kuchlanish, qarshilik va Om qonuni",
            'duration': 24,
            'lesson': [
                {'type': 'text', 'title': 'Elektr toki nima?', 'body':
                 "**Elektr toki** — zaryadlangan zarralarning tartibli harakati.\n\n"
                 "Metallarda tokni **erkin elektronlar** hosil qiladi."},
                {'type': 'text', 'title': 'Asosiy kattaliklar', 'body':
                 "**Tok kuchi (I)** — vaqt birligida o'tgan zaryad. Birligi: **Amper (A)**\n"
                 "**Kuchlanish (U)** — zaryadni ko'chirishda bajarilgan ish. Birligi: **Volt (V)**\n"
                 "**Qarshilik (R)** — o'tkazgichning tokka qarshiligi. Birligi: **Om (Ω)**"},
                {'type': 'text', 'title': 'Om qonuni', 'body':
                 "Zanjir qismidagi tok kuchi kuchlanishga **to'g'ri**, "
                 "qarshilikka **teskari** proporsional."},
                {'type': 'formula', 'body': 'I = U / R'},
                {'type': 'formula', 'body': 'U = I · R          R = U / I'},
                {'type': 'example', 'title': 'Masala', 'body':
                 "Kuchlanish 12 V, qarshilik 4 Ω. Tok kuchi qancha?\n\n"
                 "I = U / R = 12 / 4 = **3 A**"},
                {'type': 'text', 'title': 'Qarshilik nimaga bog\'liq?', 'body':
                 "• **Uzunlik** — uzun sim qarshiligi katta\n"
                 "• **Ko'ndalang kesim** — yo'g'on sim qarshiligi kichik\n"
                 "• **Material** — mis yaxshi o'tkazadi, nixrom yomon"},
                {'type': 'formula', 'body': 'R = ρ · l / S'},
                {'type': 'text', 'title': 'Ulanish turlari', 'body':
                 "**Ketma-ket ulanish:**\n"
                 "R = R₁ + R₂ (qarshiliklar qo'shiladi)\n"
                 "Tok hamma joyda bir xil: I = I₁ = I₂\n\n"
                 "**Parallel ulanish:**\n"
                 "1/R = 1/R₁ + 1/R₂\n"
                 "Kuchlanish bir xil: U = U₁ = U₂"},
                {'type': 'text', 'title': 'Tok quvvati', 'body':
                 "Elektr qurilmaning quvvati:"},
                {'type': 'formula', 'body': 'P = U · I'},
                {'type': 'note', 'body':
                 "**Xavfsizlik:** 36 V dan yuqori kuchlanish odam uchun xavfli. "
                 "Rozetka va simlarga hech qachon qo'l tegizmang, ho'l qo'l bilan "
                 "elektr qurilmasini ushlamang."},
                {'type': 'life', 'body':
                 "Lampochkadagi «60 Vt» — quvvati. 220 V tarmoqda tok kuchi: "
                 "I = P/U = 60/220 ≈ 0,27 A. Elektr hisobi shu quvvat asosida hisoblanadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Tok kuchining birligi?',
                 'options': ['Volt', 'Amper', 'Om'], 'answer': 1,
                 'explain': 'Tok kuchi Amperda (A).'},
                {'type': 'mc', 'q': 'Om qonuni formulasi?',
                 'options': ['I = U · R', 'I = U / R', 'I = R / U'], 'answer': 1,
                 'explain': 'I = U / R.'},
                {'type': 'mc', 'q': 'U = 20 V, R = 5 Ω. Tok kuchi qancha?',
                 'options': ['4 A', '100 A', '25 A'], 'answer': 0,
                 'explain': 'I = 20/5 = 4 A.'},
                {'type': 'mc', 'q': "Ketma-ket ulanishda qarshiliklar qanday hisoblanadi?",
                 'options': ["Qo'shiladi", "Ko'paytiriladi", "Bo'linadi"], 'answer': 0,
                 'explain': 'R = R₁ + R₂.'},
                {'type': 'tf', 'q': "Yo'g'on simning qarshiligi ingichkasidan kichik.",
                 'answer': True, 'explain': "To'g'ri — kesim katta bo'lsa qarshilik kichik."},
                {'type': 'fill', 'q': 'U = 12 V, I = 2 A. Qarshilik necha Om?',
                 'answer': '6', 'explain': 'R = 12/2 = 6 Ω.'},
            ],
            'homework': {
                'intro': 'Om qonunini qo\'llang.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': 'U = 24 V, R = 8 Ω. Tok kuchi necha A?',
                     'answer': '3'},
                    {'id': 'h2', 'type': 'number', 'prompt': 'I = 5 A, R = 4 Ω. Kuchlanish necha V?',
                     'answer': '20'},
                    {'id': 'h3', 'type': 'number',
                     'prompt': "R₁ = 3 Ω va R₂ = 7 Ω ketma-ket ulangan. Umumiy qarshilik necha Om?",
                     'answer': '10'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Elektr bilan ishlashda 2 ta xavfsizlik qoidasini yozing."},
                ],
            },
        },
    ],
}
