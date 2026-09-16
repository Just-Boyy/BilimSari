# -*- coding: utf-8 -*-
"""5-sinf — Matematika."""

MATH = {
    'key': 'math',
    'topics': [
        {
            'slug': 'natural-sonlar',
            'title': 'Natural sonlar',
            'summary': "Natural sonlar, xona va sinflar, taqqoslash",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Natural son nima?', 'body':
                 "Narsalarni sanashda ishlatiladigan sonlar **natural sonlar** deyiladi:\n\n"
                 "1, 2, 3, 4, 5, ... va hokazo cheksiz davom etadi.\n\n"
                 "**0 natural son emas** — chunki hech narsani sanaganda 0 dan boshlamaymiz."},
                {'type': 'text', 'title': 'Xona va sinflar', 'body':
                 "Ko'p xonali sonni o'qish uchun uni o'ngdan boshlab 3 talik guruhlarga ajratamiz. "
                 "Har bir guruh — **sinf**.\n\n"
                 "**Birliklar sinfi:** birlik, o'nlik, yuzlik\n"
                 "**Minglar sinfi:** ming, o'n ming, yuz ming\n"
                 "**Millionlar sinfi:** million, o'n million, yuz million"},
                {'type': 'example', 'title': "Sonni o'qiymiz", 'body':
                 "**45 302 718**\n\n"
                 "O'ngdan 3 talab ajratamiz: 45 | 302 | 718\n\n"
                 "O'qiymiz: qirq besh million uch yuz ikki ming yetti yuz o'n sakkiz."},
                {'type': 'text', 'title': 'Xona qiymati', 'body':
                 "Raqamning qiymati uning **o'rniga** bog'liq.\n\n"
                 "**5 274** sonida:\n"
                 "• 5 — minglar xonasida, qiymati 5000\n"
                 "• 2 — yuzliklar xonasida, qiymati 200\n"
                 "• 7 — o'nliklar xonasida, qiymati 70\n"
                 "• 4 — birliklar xonasida, qiymati 4\n\n"
                 "Demak: 5274 = 5000 + 200 + 70 + 4"},
                {'type': 'text', 'title': 'Taqqoslash qoidasi', 'body':
                 "**1-qoida:** Xonalari ko'p bo'lgan son katta.\n"
                 "1523 > 999 (4 xonali son 3 xonalidan katta)\n\n"
                 "**2-qoida:** Xonalari teng bo'lsa, chapdan boshlab raqamlarni solishtiramiz.\n"
                 "4 **8** 12 va 4 **5** 30 → 8 > 5, demak 4812 > 4530"},
                {'type': 'note', 'body':
                 "Taqqoslash belgilari: **>** katta, **<** kichik, **=** teng. "
                 "Belgining uchli tomoni doim kichik songa qaraydi."},
                {'type': 'life', 'body':
                 "Narxlarni solishtirganda ham shu qoida ishlaydi: 125 000 so'm va 98 000 so'm — "
                 "birinchisi 6 xonali, ikkinchisi 5 xonali, demak birinchisi qimmat."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Qaysi son natural son EMAS?',
                 'options': ['1', '0', '100', '57'], 'answer': 1,
                 'explain': '0 natural son emas — sanash 1 dan boshlanadi.'},
                {'type': 'mc', 'q': '3 island 7 054 sonida 7 raqamining qiymati nechchi?',
                 'options': ['7', '70', '700', '7000'], 'answer': 3,
                 'explain': "7 minglar xonasida turibdi — qiymati 7000."},
                {'type': 'mc', 'q': 'Qaysi son kattaroq: 9 876 yoki 10 002?',
                 'options': ['9 876', '10 002', 'Teng'], 'answer': 1,
                 'explain': '10 002 — 5 xonali, 9 876 — 4 xonali. Xonasi ko\'p son katta.'},
                {'type': 'tf', 'q': '2 458 = 2000 + 400 + 50 + 8', 'answer': True,
                 'explain': "To'g'ri — bu sonning xona qo'shiluvchilariga yoyilishi."},
                {'type': 'mc', 'q': "12 345 678 sonida nechta sinf bor?",
                 'options': ['2', '3', '4'], 'answer': 1,
                 'explain': "12 | 345 | 678 — millionlar, minglar, birliklar: 3 ta sinf."},
                {'type': 'fill', 'q': "6 391 sonida yuzliklar xonasidagi raqamni yozing.",
                 'answer': '3', 'explain': "6-minglar, 3-yuzliklar, 9-o'nliklar, 1-birliklar."},
            ],
            'homework': {
                'intro': 'Sonlar bilan ishlang.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "8 452 sonida o'nliklar xonasidagi raqamni yozing.",
                     'answer': '5'},
                    {'id': 'h2', 'type': 'number', 'prompt': "3 000 + 700 + 20 + 6 = ? (sonni yozing)",
                     'answer': '3726'},
                    {'id': 'h3', 'type': 'text', 'prompt': "Qaysi son katta: 45 678 yoki 45 687? (sonni yozing)",
                     'answer': '45687', 'accept': ['45 687', '45687']},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "1 234 567 sonini so'z bilan o'qing va yozing."},
                ],
            },
        },
        {
            'slug': 'amallar-tartibi',
            'title': 'Amallar tartibi',
            'summary': "Qavslar, ko'paytirish va qo'shish qaysi tartibda bajariladi",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Nima uchun tartib kerak?', 'body':
                 "Quyidagi misolni yechaylik: **2 + 3 × 4**\n\n"
                 "Agar chapdan yechsak: (2+3)×4 = 20\n"
                 "Agar avval ko'paytirsak: 2 + 12 = 14\n\n"
                 "Ikki xil javob! Shuning uchun matematikada **qat'iy tartib** bor."},
                {'type': 'steps', 'title': 'Amallar tartibi', 'items': [
                    "**Qavs ichidagi** amallar — eng birinchi.",
                    "**Daraja** (kvadrat, kub) — ikkinchi.",
                    "**Ko'paytirish va bo'lish** — uchinchi, chapdan o'ngga.",
                    "**Qo'shish va ayirish** — oxirgi, chapdan o'ngga.",
                ]},
                {'type': 'formula', 'body': 'Qavs → Daraja → × ÷ → + −'},
                {'type': 'example', 'title': 'Misol 1', 'body':
                 "**2 + 3 × 4 = ?**\n\n"
                 "Qavs yo'q, daraja yo'q.\n"
                 "Avval ko'paytirish: 3 × 4 = 12\n"
                 "Keyin qo'shish: 2 + 12 = **14**"},
                {'type': 'example', 'title': 'Misol 2', 'body':
                 "**(15 − 7) × 3 + 4 = ?**\n\n"
                 "1) Qavs: 15 − 7 = 8\n"
                 "2) Ko'paytirish: 8 × 3 = 24\n"
                 "3) Qo'shish: 24 + 4 = **28**"},
                {'type': 'example', 'title': 'Misol 3 — bir xil darajadagi amallar', 'body':
                 "**36 ÷ 6 × 2 = ?**\n\n"
                 "Bo'lish va ko'paytirish bir darajada — **chapdan o'ngga** bajaramiz:\n"
                 "36 ÷ 6 = 6, keyin 6 × 2 = **12**\n\n"
                 "Agar o'ngdan boshlasak 3 chiqadi — bu XATO."},
                {'type': 'note', 'body':
                 "Ichma-ich qavslar bo'lsa, eng ichkisidan boshlanadi: "
                 "2 × (3 + (8 − 5)) = 2 × (3 + 3) = 2 × 6 = 12"},
                {'type': 'life', 'body':
                 "Do'konda 3 ta daftar (har biri 5000 so'm) va 1 ta ruchka (2000 so'm) oldingiz. "
                 "Jami: 3 × 5000 + 2000 = 15000 + 2000 = 17 000 so'm. "
                 "Bu yerda ham avval ko'paytirish!"},
            ],
            'quiz': [
                {'type': 'mc', 'q': '5 + 2 × 3 = ?',
                 'options': ['21', '11', '10', '13'], 'answer': 1,
                 'explain': 'Avval 2 × 3 = 6, keyin 5 + 6 = 11.'},
                {'type': 'mc', 'q': '(8 + 4) ÷ 3 = ?',
                 'options': ['4', '9', '12', '2'], 'answer': 0,
                 'explain': 'Avval qavs: 8 + 4 = 12, keyin 12 ÷ 3 = 4.'},
                {'type': 'mc', 'q': 'Qaysi amal birinchi bajariladi?',
                 'options': ["Qo'shish", "Ko'paytirish", 'Qavs ichidagi amal'], 'answer': 2,
                 'explain': 'Qavs har doim birinchi.'},
                {'type': 'tf', 'q': "24 ÷ 4 ÷ 2 misolida chapdan o'ngga hisoblanadi.",
                 'answer': True,
                 'explain': "To'g'ri: 24 ÷ 4 = 6, keyin 6 ÷ 2 = 3."},
                {'type': 'mc', 'q': '20 − 3 × 4 + 2 = ?',
                 'options': ['10', '70', '16', '6'], 'answer': 0,
                 'explain': '3 × 4 = 12; 20 − 12 = 8; 8 + 2 = 10.'},
                {'type': 'fill', 'q': '(10 − 4) × 5 = ?',
                 'answer': '30', 'explain': 'Qavs: 6, keyin 6 × 5 = 30.'},
            ],
            'homework': {
                'intro': 'Amallar tartibiga rioya qilib yeching.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': '7 + 4 × 5 = ?', 'answer': '27'},
                    {'id': 'h2', 'type': 'number', 'prompt': '(12 + 8) ÷ 4 = ?', 'answer': '5'},
                    {'id': 'h3', 'type': 'number', 'prompt': '30 − 2 × (3 + 4) = ?', 'answer': '16',
                     'hint': 'Avval ichki qavs.'},
                    {'id': 'h4', 'type': 'number', 'prompt': '48 ÷ 8 × 3 = ?', 'answer': '18',
                     'hint': "Chapdan o'ngga."},
                    {'id': 'h5', 'type': 'open',
                     'prompt': "Nima uchun amallar tartibi kerak? O'z so'zingiz bilan tushuntiring."},
                ],
            },
        },
        {
            'slug': 'bolinuvchanlik',
            'title': "Bo'linish belgilari",
            'summary': "2, 3, 5, 9, 10 ga bo'linish belgilarini o'rganamiz",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': "Bo'linish nima?", 'body':
                 "Agar bir son ikkinchisiga **qoldiqsiz** bo'linsa, u shu songa **bo'linadi** deymiz.\n\n"
                 "12 : 3 = 4 (qoldiq 0) → 12 soni 3 ga bo'linadi\n"
                 "13 : 3 = 4 va qoldiq 1 → 13 soni 3 ga bo'linmaydi"},
                {'type': 'table', 'head': ["Nechchiga", 'Belgi', 'Misol'], 'rows': [
                    ['2 ga', "Oxirgi raqami juft (0,2,4,6,8)", '134 — bo\'linadi'],
                    ['5 ga', 'Oxirgi raqami 0 yoki 5', "245 — bo'linadi"],
                    ['10 ga', 'Oxirgi raqami 0', "780 — bo'linadi"],
                    ['3 ga', "Raqamlar yig'indisi 3 ga bo'linsa", "123 → 1+2+3=6 → bo'linadi"],
                    ['9 ga', "Raqamlar yig'indisi 9 ga bo'linsa", "639 → 6+3+9=18 → bo'linadi"],
                ]},
                {'type': 'example', 'title': "Tekshirib ko'ramiz: 4 725", 'body':
                 "**2 ga?** Oxirgi raqam 5 — toq. Yo'q.\n"
                 "**5 ga?** Oxirgi raqam 5. Ha!\n"
                 "**10 ga?** Oxirgi raqam 0 emas. Yo'q.\n"
                 "**3 ga?** 4+7+2+5 = 18. 18 : 3 = 6. Ha!\n"
                 "**9 ga?** 18 : 9 = 2. Ha!"},
                {'type': 'text', 'title': 'Tub va murakkab sonlar', 'body':
                 "**Tub son** — faqat 1 ga va o'ziga bo'linadi.\n"
                 "2, 3, 5, 7, 11, 13, 17, 19, 23...\n\n"
                 "**Murakkab son** — boshqa bo'luvchilari ham bor.\n"
                 "4, 6, 8, 9, 10, 12...\n\n"
                 "**1 soni** na tub, na murakkab — u alohida."},
                {'type': 'note', 'body':
                 "**2** — yagona juft tub son. Qolgan barcha tub sonlar toq."},
                {'type': 'life', 'body':
                 "30 ta shirinlikni 5 ta bolaga teng bo'lish mumkinmi? "
                 "30 oxirida 0 bor → 5 ga bo'linadi. Ha, har biriga 6 tadan."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "Qaysi son 2 ga bo'linadi?",
                 'options': ['137', '245', '318', '991'], 'answer': 2,
                 'explain': "318 ning oxirgi raqami 8 — juft, demak 2 ga bo'linadi."},
                {'type': 'mc', 'q': "441 soni 3 ga bo'linadimi?",
                 'options': ['Ha', "Yo'q"], 'answer': 0,
                 'explain': "4+4+1 = 9, 9 : 3 = 3. Ha, bo'linadi."},
                {'type': 'mc', 'q': 'Qaysi son TUB son?',
                 'options': ['9', '15', '17', '21'], 'answer': 2,
                 'explain': '17 faqat 1 ga va 17 ga bo\'linadi — tub son.'},
                {'type': 'tf', 'q': "Oxirgi raqami 0 bo'lgan son 10 ga bo'linadi.", 'answer': True,
                 'explain': "To'g'ri — bu 10 ga bo'linish belgisi."},
                {'type': 'mc', 'q': "738 soni 9 ga bo'linadimi?",
                 'options': ['Ha', "Yo'q"], 'answer': 0,
                 'explain': "7+3+8 = 18, 18 : 9 = 2. Ha."},
                {'type': 'fill', 'q': "2 soni tub sonmi? (ha yoki yo'q)",
                 'answer': 'ha', 'explain': "2 — yagona juft tub son."},
            ],
            'homework': {
                'intro': "Bo'linish belgilarini qo'llang.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "576 soni 2 ga bo'linadimi? (ha/yo'q)",
                     'answer': 'ha'},
                    {'id': 'h2', 'type': 'text', 'prompt': "425 soni 3 ga bo'linadimi? (ha/yo'q)",
                     'answer': "yo'q", 'accept': ['yoq', "yo'q", 'yo‘q', 'yuq'],
                     'hint': "4+2+5 nechchi? U 3 ga bo'linadimi?"},
                    {'id': 'h3', 'type': 'number', 'prompt': "10 dan kichik nechta tub son bor?",
                     'answer': '4', 'hint': '2, 3, 5, 7'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "3 ga ham, 5 ga ham bo'linadigan bitta son toping."},
                ],
            },
        },
        {
            'slug': 'kasrlar',
            'title': 'Oddiy kasrlar',
            'summary': "Kasr nima, uni qanday o'qiymiz va taqqoslaymiz",
            'duration': 22,
            'lesson': [
                {'type': 'text', 'title': 'Kasr nima?', 'body':
                 "**Kasr** — butunning bir qismini bildiradi.\n\n"
                 "Tortni 4 ta teng bo'lakka bo'lib, 1 tasini olsangiz — sizda tortning "
                 "**1/4** (chorak) qismi bor."},
                {'type': 'formula', 'body': '3/4  —  surat 3, maxraj 4'},
                {'type': 'text', 'title': 'Surat va maxraj', 'body':
                 "**Maxraj** (pastdagi son) — butun nechta teng bo'lakka bo'lingani.\n"
                 "**Surat** (yuqoridagi son) — shulardan nechtasi olingani.\n\n"
                 "**3/4** — butun 4 ta bo'lakka bo'lingan, shundan 3 tasi olingan."},
                {'type': 'text', 'title': "Kasrlarni o'qish", 'body':
                 "1/2 — yarim (bir ikkidan)\n"
                 "1/3 — uchdan bir\n"
                 "1/4 — chorak (to'rtdan bir)\n"
                 "2/5 — beshdan ikki\n"
                 "7/10 — o'ndan yetti"},
                {'type': 'text', 'title': 'Kasr turlari', 'body':
                 "**To'g'ri kasr** — surat maxrajdan kichik, qiymati 1 dan kichik.\n"
                 "3/5, 1/2, 7/8\n\n"
                 "**Noto'g'ri kasr** — surat maxrajdan katta yoki teng, qiymati 1 dan katta.\n"
                 "7/5, 9/4, 5/5\n\n"
                 "**Aralash son** — butun va kasr birga.\n"
                 "2 1/3 (ikki butun uchdan bir)"},
                {'type': 'steps', 'title': "Bir xil maxrajli kasrlarni taqqoslash", 'items': [
                    "Maxrajlari bir xil bo'lsa, suratlarni solishtiring.",
                    "Surat katta bo'lgan kasr kattaroq: 3/7 < 5/7",
                    "Suratlari bir xil bo'lsa, maxraji KICHIK kasr kattaroq.",
                    "Chunki bo'laklar yiriklashadi: 1/3 > 1/5",
                ]},
                {'type': 'note', 'body':
                 "Maxraj hech qachon 0 bo'lolmaydi — nolga bo'lish mumkin emas!"},
                {'type': 'life', 'body':
                 "Pitsani 8 bo'lakka bo'ldingiz va 3 tasini yedingiz — 3/8 qismini yedingiz, "
                 "5/8 qoldi. Kasr har kuni kerak bo'ladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': '5/8 kasrida maxraj qaysi son?',
                 'options': ['5', '8', '13'], 'answer': 1,
                 'explain': 'Maxraj — pastdagi son, ya\'ni 8.'},
                {'type': 'mc', 'q': "Qaysi kasr to'g'ri kasr?",
                 'options': ['7/5', '9/4', '3/8', '6/6'], 'answer': 2,
                 'explain': "3/8 da surat maxrajdan kichik — to'g'ri kasr."},
                {'type': 'mc', 'q': 'Qaysi kasr kattaroq: 3/7 yoki 5/7?',
                 'options': ['3/7', '5/7', 'Teng'], 'answer': 1,
                 'explain': 'Maxrajlar teng — surat katta bo\'lgani kattaroq.'},
                {'type': 'mc', 'q': 'Qaysi kasr kattaroq: 1/3 yoki 1/6?',
                 'options': ['1/3', '1/6', 'Teng'], 'answer': 0,
                 'explain': "Suratlar teng, maxraj kichik bo'lgani katta: bo'laklar yirikroq."},
                {'type': 'tf', 'q': 'Kasrning maxraji 0 bo\'lishi mumkin.', 'answer': False,
                 'explain': "Yo'q — nolga bo'lish mumkin emas."},
                {'type': 'fill', 'q': "Tort 4 bo'lakka bo'lindi, 1 tasi yeyildi. Nechta bo'lak qoldi?",
                 'answer': '3', 'explain': '4 − 1 = 3 bo\'lak, ya\'ni 3/4 qismi.'},
            ],
            'homework': {
                'intro': 'Kasrlar bilan ishlang.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': '7/12 kasrida surat qaysi son?', 'answer': '7'},
                    {'id': 'h2', 'type': 'text', 'prompt': "2/9 va 5/9 — qaysi biri katta? (kasrni yozing)",
                     'answer': '5/9'},
                    {'id': 'h3', 'type': 'text', 'prompt': "11/4 qanday kasr? (to'g'ri yoki noto'g'ri)",
                     'answer': "noto'g'ri", 'accept': ['notogri', "noto'g'ri", 'noto‘g‘ri']},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Kunning 1/3 qismini uxlashga sarflasangiz, bu necha soat? Hisoblang."},
                ],
            },
        },
        {
            'slug': 'yuza-perimetr',
            'title': 'Perimetr va yuza',
            'summary': "To'rtburchak va kvadratning perimetri va yuzasini hisoblaymiz",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Perimetr nima?', 'body':
                 "**Perimetr (P)** — figuraning barcha tomonlari uzunliklarining yig'indisi. "
                 "Ya'ni figurani aylanib chiqsak, qancha yo'l bosamiz.\n\n"
                 "Perimetr uzunlik birligida o'lchanadi: sm, m, km."},
                {'type': 'formula', 'body': "To'g'ri to'rtburchak:  P = 2 × (a + b)"},
                {'type': 'formula', 'body': 'Kvadrat:  P = 4 × a'},
                {'type': 'example', 'title': 'Perimetrni hisoblaymiz', 'body':
                 "Tomonlari 5 sm va 3 sm bo'lgan to'rtburchak:\n\n"
                 "P = 2 × (5 + 3) = 2 × 8 = **16 sm**\n\n"
                 "Tomoni 4 sm bo'lgan kvadrat:\n\n"
                 "P = 4 × 4 = **16 sm**"},
                {'type': 'text', 'title': 'Yuza nima?', 'body':
                 "**Yuza (S)** — figura egallagan joyning kattaligi. "
                 "Ya'ni ichiga nechta birlik katak sig'adi.\n\n"
                 "Yuza kvadrat birliklarda o'lchanadi: sm², m², km²."},
                {'type': 'formula', 'body': "To'g'ri to'rtburchak:  S = a × b"},
                {'type': 'formula', 'body': 'Kvadrat:  S = a × a'},
                {'type': 'example', 'title': 'Yuzani hisoblaymiz', 'body':
                 "Tomonlari 5 sm va 3 sm bo'lgan to'rtburchak:\n\n"
                 "S = 5 × 3 = **15 sm²**\n\n"
                 "Tomoni 4 sm bo'lgan kvadrat:\n\n"
                 "S = 4 × 4 = **16 sm²**"},
                {'type': 'note', 'body':
                 "Perimetr va yuzani chalkashtirmang!\n"
                 "**Perimetr** — chegara uzunligi (devor uchun g'isht).\n"
                 "**Yuza** — ichki maydon (pol uchun gilam)."},
                {'type': 'life', 'body':
                 "Xonaga gilam olmoqchisiz — YUZA kerak (uzunlik × en). "
                 "Xonani plintus bilan o'ramoqchisiz — PERIMETR kerak."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Tomonlari 6 sm va 4 sm bo\'lgan to\'rtburchakning perimetri?',
                 'options': ['10 sm', '20 sm', '24 sm', '12 sm'], 'answer': 1,
                 'explain': 'P = 2 × (6 + 4) = 2 × 10 = 20 sm.'},
                {'type': 'mc', 'q': 'Shu to\'rtburchakning yuzasi?',
                 'options': ['10 sm²', '20 sm²', '24 sm²', '12 sm²'], 'answer': 2,
                 'explain': 'S = 6 × 4 = 24 sm².'},
                {'type': 'mc', 'q': "Tomoni 7 sm bo'lgan kvadratning yuzasi?",
                 'options': ['28 sm²', '49 sm²', '14 sm²'], 'answer': 1,
                 'explain': 'S = 7 × 7 = 49 sm².'},
                {'type': 'tf', 'q': "Yuza kvadrat birliklarda (sm²) o'lchanadi.", 'answer': True,
                 'explain': "To'g'ri — yuza har doim kvadrat birlikda."},
                {'type': 'mc', 'q': 'Xonaga gilam olish uchun nima kerak?',
                 'options': ['Perimetr', 'Yuza', 'Ikkalasi ham'], 'answer': 1,
                 'explain': 'Gilam polni qoplaydi — yuza kerak.'},
                {'type': 'fill', 'q': "Tomoni 5 sm bo'lgan kvadratning perimetri necha sm?",
                 'answer': '20', 'explain': 'P = 4 × 5 = 20 sm.'},
            ],
            'homework': {
                'intro': 'Hisoblang. Javobni faqat son bilan yozing.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': 'Tomonlari 8 sm va 3 sm. Perimetri necha sm?',
                     'answer': '22'},
                    {'id': 'h2', 'type': 'number', 'prompt': 'Tomonlari 8 sm va 3 sm. Yuzasi necha sm²?',
                     'answer': '24'},
                    {'id': 'h3', 'type': 'number', 'prompt': "Tomoni 9 sm bo'lgan kvadratning yuzasi?",
                     'answer': '81'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Xonangizning uzunligi va enini taxminan yozing. Yuzasi qancha chiqadi?"},
                ],
            },
        },
        {
            'slug': 'masalalar-5',
            'title': 'Matnli masalalar',
            'summary': "Murakkabroq masalalarni bosqichma-bosqich yechamiz",
            'duration': 22,
            'lesson': [
                {'type': 'text', 'title': "Masala — bu mantiq mashqi", 'body':
                 "5-sinf masalalarida bir necha amal bo'ladi. Shuning uchun ularni "
                 "**bosqichlarga** ajratib yechamiz."},
                {'type': 'steps', 'title': 'Yechish tartibi', 'items': [
                    "Masalani 2 marta o'qing.",
                    "Qisqa shart yozing: nima berilgan, nima so'ralgan.",
                    "Rejani tuzing: qaysi savolga avval javob topish kerak?",
                    "Har bir amalni alohida yozing va nima topganingizni belgilang.",
                    "Javobni tekshiring: mantiqqa to'g'ri keladimi?",
                ]},
                {'type': 'example', 'title': 'Namuna masala', 'body':
                 "«Do'konda 240 ta daftar bor edi. Birinchi kuni 1/4 qismi, "
                 "ikkinchi kuni 60 tasi sotildi. Nechta daftar qoldi?»\n\n"
                 "**1-amal.** Birinchi kuni sotilgani:\n"
                 "240 : 4 = 60 ta\n\n"
                 "**2-amal.** Jami sotilgani:\n"
                 "60 + 60 = 120 ta\n\n"
                 "**3-amal.** Qolgani:\n"
                 "240 − 120 = **120 ta**\n\n"
                 "Tekshirish: 120 < 240 — mantiqiy."},
                {'type': 'text', 'title': 'Tez-tez uchraydigan turlar', 'body':
                 "**Qismni topish:** «sonning 1/5 qismi» → songa bo'lish\n"
                 "**Necha marta ko'p:** → bo'lish\n"
                 "**Nechtaga ko'p:** → ayirish\n"
                 "**Tezlik masalasi:** yo'l = tezlik × vaqt"},
                {'type': 'formula', 'body': 's = v × t'},
                {'type': 'example', 'title': 'Tezlik masalasi', 'body':
                 "«Mashina 60 km/soat tezlik bilan 3 soat yurdi. Qancha yo'l bosdi?»\n\n"
                 "s = 60 × 3 = **180 km**"},
                {'type': 'note', 'body':
                 "«Necha marta» va «nechtaga» — butunlay boshqa savol! "
                 "8 va 2: 8 soni 2 dan 4 MARTA ko'p, lekin 6 TAGA ko'p."},
                {'type': 'life', 'body':
                 "Toshkentdan Samarqandga 300 km. Poyezd 150 km/soat tezlikda bo'lsa, "
                 "300 : 150 = 2 soatda yetadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': '120 sonining 1/4 qismi nechchi?',
                 'options': ['20', '30', '40', '60'], 'answer': 1,
                 'explain': '120 : 4 = 30.'},
                {'type': 'mc', 'q': "Velosipedchi 15 km/soat tezlikda 4 soat yurdi. Qancha yo'l bosdi?",
                 'options': ['19 km', '45 km', '60 km', '11 km'], 'answer': 2,
                 'explain': 's = 15 × 4 = 60 km.'},
                {'type': 'mc', 'q': '12 soni 3 dan necha MARTA ko\'p?',
                 'options': ['4 marta', '9 marta', '15 marta'], 'answer': 0,
                 'explain': "«Necha marta» — bo'lish: 12 : 3 = 4."},
                {'type': 'mc', 'q': "12 soni 3 dan nechtaga ko'p?",
                 'options': ['4 taga', '9 taga', '15 taga'], 'answer': 1,
                 'explain': "«Nechtaga» — ayirish: 12 − 3 = 9."},
                {'type': 'tf', 'q': 'Masalani yechgach javobni tekshirish kerak.', 'answer': True,
                 'explain': "To'g'ri — tekshirish xatolarni topadi."},
                {'type': 'fill', 'q': "200 ta olmaning 1/5 qismi nechta?",
                 'answer': '40', 'explain': '200 : 5 = 40.'},
            ],
            'homework': {
                'intro': 'Masalalarni yeching. Javobni son bilan yozing.',
                'tasks': [
                    {'id': 'h1', 'type': 'number',
                     'prompt': "Kutubxonada 360 ta kitob bor. 1/3 qismi berildi. Nechta kitob berildi?",
                     'answer': '120'},
                    {'id': 'h2', 'type': 'number',
                     'prompt': "Poyezd 80 km/soat tezlikda 5 soat yurdi. Necha km yo'l bosdi?",
                     'answer': '400'},
                    {'id': 'h3', 'type': 'number',
                     'prompt': "Bog'da 45 ta olma va 15 ta nok daraxti bor. Olma necha marta ko'p?",
                     'answer': '3'},
                    {'id': 'h4', 'type': 'number',
                     'prompt': "500 so'mdan 8 ta ruchka olindi. Qancha pul to'landi?",
                     'answer': '4000'},
                    {'id': 'h5', 'type': 'open',
                     'prompt': "O'zingiz 2 amalli masala tuzing va yeching."},
                ],
            },
        },
    ],
}
