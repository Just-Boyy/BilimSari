# -*- coding: utf-8 -*-
"""5-sinf — Ona tili, Ingliz tili, Tabiiy fanlar, Adabiyot."""

UZBEK = {
    'key': 'uzbek',
    'topics': [
        {
            'slug': 'soz-turkumlari',
            'title': "So'z turkumlari",
            'summary': "Ot, sifat, son, fe'l va boshqalarni ajratishni o'rganamiz",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': "So'z turkumi nima?", 'body':
                 "Har bir so'z nimanidir bildiradi. Ma'nosiga va savoliga qarab so'zlar "
                 "guruhlarga — **so'z turkumlariga** ajratiladi."},
                {'type': 'table', 'head': ['Turkum', 'Savol', 'Misol'], 'rows': [
                    ['Ot', 'kim? nima?', 'bola, kitob, shahar'],
                    ['Sifat', 'qanday? qanaqa?', 'katta, chiroyli, qizil'],
                    ['Son', 'nechta? nechanchi?', 'besh, oltinchi, yuz'],
                    ['Olmosh', "ot o'rnida keladi", 'men, sen, u, bu'],
                    ["Fe'l", 'nima qildi?', "o'qidi, yozdi, keldi"],
                    ['Ravish', 'qanday? qachon?', 'tez, sekin, bugun'],
                ]},
                {'type': 'text', 'title': 'Ot', 'body':
                 "**Ot** — predmetni bildiradi. **Kim?** yoki **nima?** savoliga javob beradi.\n\n"
                 "**Atoqli ot** — bitta narsaning nomi, katta harf bilan: Toshkent, Alisher, Amudaryo\n"
                 "**Turdosh ot** — umumiy nom, kichik harf bilan: shahar, bola, daryo"},
                {'type': 'text', 'title': "Fe'l", 'body':
                 "**Fe'l** — harakat yoki holatni bildiradi.\n\n"
                 "**O'tgan zamon:** o'qidi, keldi, yozdi\n"
                 "**Hozirgi zamon:** o'qiyapti, kelyapti\n"
                 "**Kelasi zamon:** o'qiydi, keladi"},
                {'type': 'example', 'title': 'Gapni tahlil qilamiz', 'body':
                 "«Kichkina bola beshta kitobni tez o'qidi.»\n\n"
                 "**kichkina** — sifat (qanday?)\n"
                 "**bola** — ot (kim?)\n"
                 "**beshta** — son (nechta?)\n"
                 "**kitobni** — ot (nimani?)\n"
                 "**tez** — ravish (qanday?)\n"
                 "**o'qidi** — fe'l (nima qildi?)"},
                {'type': 'note', 'body':
                 "So'z turkumini aniqlash uchun unga **savol bering**. "
                 "Savol turkumni aniq ko'rsatadi."},
                {'type': 'life', 'body':
                 "So'z turkumlarini bilgan odam chiroyli gapiradi va xatosiz yozadi — "
                 "inshoda ham, xatda ham bu bilinadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "«kitob» so'zi qaysi turkumga kiradi?",
                 'options': ['Ot', 'Sifat', "Fe'l", 'Son'], 'answer': 0,
                 'explain': "«Nima?» savoliga javob beradi — ot."},
                {'type': 'mc', 'q': "«chiroyli» so'zi qaysi turkum?",
                 'options': ['Ot', 'Sifat', "Fe'l"], 'answer': 1,
                 'explain': "«Qanday?» savoliga javob beradi — sifat."},
                {'type': 'mc', 'q': "«yugurdi» so'zi qaysi turkum?",
                 'options': ['Ot', 'Ravish', "Fe'l"], 'answer': 2,
                 'explain': "Harakatni bildiradi — fe'l."},
                {'type': 'tf', 'q': "«Samarqand» — atoqli ot.", 'answer': True,
                 'explain': "To'g'ri — shahar nomi, katta harf bilan yoziladi."},
                {'type': 'mc', 'q': 'Qaysi savol otga beriladi?',
                 'options': ['Qanday?', 'Kim? Nima?', 'Nima qildi?'], 'answer': 1,
                 'explain': 'Ot «kim?» yoki «nima?» savoliga javob beradi.'},
                {'type': 'fill', 'q': "«beshta» so'zi qaysi turkum? (bir so'z bilan)",
                 'answer': 'son', 'explain': "«Nechta?» savoliga javob beradi — son."},
            ],
            'homework': {
                'intro': "So'zlarning turkumini aniqlang.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "«daryo» qaysi turkum?", 'answer': 'ot'},
                    {'id': 'h2', 'type': 'text', 'prompt': "«baland» qaysi turkum?", 'answer': 'sifat'},
                    {'id': 'h3', 'type': 'text', 'prompt': "«keldi» qaysi turkum?",
                     'answer': "fe'l", 'accept': ['fel', "fe'l", 'fe’l', 'feʼl']},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Bitta gap tuzing va undagi ot, sifat, fe'lni ko'rsating."},
                ],
            },
        },
        {
            'slug': 'gap-boaklari',
            'title': "Gap bo'laklari",
            'summary': "Ega, kesim va ikkinchi darajali bo'laklar",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Gapning asosi', 'body':
                 "Har bir gapda ikkita asosiy bo'lak bor — **ega** va **kesim**. "
                 "Ular gapning **bosh bo'laklari** deyiladi."},
                {'type': 'text', 'title': 'Ega', 'body':
                 "**Ega** — gapda kim yoki nima haqida gapirilayotganini bildiradi.\n"
                 "Savoli: **kim? nima?**\n\n"
                 "«**Bola** kitob o'qidi.» → ega — bola"},
                {'type': 'text', 'title': 'Kesim', 'body':
                 "**Kesim** — ega haqida nima deyilayotganini bildiradi.\n"
                 "Savoli: **nima qildi? nima qilyapti? qanday?**\n\n"
                 "«Bola kitob **o'qidi**.» → kesim — o'qidi"},
                {'type': 'text', 'title': "Ikkinchi darajali bo'laklar", 'body':
                 "**To'ldiruvchi** — kimni? nimani? kimga? nimaga?\n"
                 "«Bola **kitobni** o'qidi.»\n\n"
                 "**Aniqlovchi** — qanday? qaysi? nechta?\n"
                 "«**Qiziqarli** kitobni o'qidi.»\n\n"
                 "**Hol** — qayerda? qachon? qanday?\n"
                 "«**Kechqurun** kitobni o'qidi.»"},
                {'type': 'example', 'title': 'To\'liq tahlil', 'body':
                 "«Kichkina bola kechqurun qiziqarli kitobni o'qidi.»\n\n"
                 "**bola** — ega (kim?)\n"
                 "**o'qidi** — kesim (nima qildi?)\n"
                 "**kichkina** — aniqlovchi (qanday bola?)\n"
                 "**kechqurun** — hol (qachon?)\n"
                 "**kitobni** — to'ldiruvchi (nimani?)\n"
                 "**qiziqarli** — aniqlovchi (qanday kitob?)"},
                {'type': 'steps', 'title': 'Tahlil qilish tartibi', 'items': [
                    "Avval kesimni toping — harakatni bildiruvchi so'z.",
                    "Kesimdan «kim? nima?» deb so'rang — ega topiladi.",
                    "Qolgan so'zlarga savol bering.",
                    "Har birini tegishli bo'lakka ajrating.",
                ]},
                {'type': 'note', 'body':
                 "Ega va kesim — gapning asosi. Ular bo'lmasa gap tuzilmaydi. "
                 "Qolgan bo'laklar gapni to'ldiradi, boyitadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "«Dilnoza maktabga bordi» gapida ega qaysi?",
                 'options': ['Dilnoza', 'maktabga', 'bordi'], 'answer': 0,
                 'explain': "«Kim?» — Dilnoza. Bu ega."},
                {'type': 'mc', 'q': 'Shu gapda kesim qaysi?',
                 'options': ['Dilnoza', 'maktabga', 'bordi'], 'answer': 2,
                 'explain': "«Nima qildi?» — bordi. Bu kesim."},
                {'type': 'mc', 'q': "Gapning bosh bo'laklari qaysilar?",
                 'options': ["Ega va kesim", "Aniqlovchi va hol", "To'ldiruvchi va hol"], 'answer': 0,
                 'explain': "Ega va kesim — bosh bo'laklar."},
                {'type': 'tf', 'q': "Hol «qachon?» savoliga javob berishi mumkin.", 'answer': True,
                 'explain': "To'g'ri — hol payt, o'rin, tarzni bildiradi."},
                {'type': 'mc', 'q': "«Katta bog'da gullar ochildi» — «katta» qaysi bo'lak?",
                 'options': ['Ega', 'Aniqlovchi', 'Kesim'], 'answer': 1,
                 'explain': "«Qanday bog'?» — katta. Bu aniqlovchi."},
                {'type': 'fill', 'q': "«Kim? nima?» savoliga javob beradigan bosh bo'lak — ___",
                 'answer': 'ega', 'explain': 'Bu ega.'},
            ],
            'homework': {
                'intro': "«Mehnatkash dehqon erta tongda dalaga chiqdi» gapi bo'yicha:",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': 'Ega qaysi so\'z?',
                     'answer': 'dehqon'},
                    {'id': 'h2', 'type': 'text', 'prompt': 'Kesim qaysi so\'z?',
                     'answer': 'chiqdi'},
                    {'id': 'h3', 'type': 'text', 'prompt': "«Mehnatkash» qaysi bo'lak?",
                     'answer': 'aniqlovchi'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "O'zingiz gap tuzing va ega bilan kesimni ko'rsating."},
                ],
            },
        },
        {
            'slug': 'imlo-qoidalari',
            'title': 'Imlo qoidalari',
            'summary': "Tez-tez xato qilinadigan yozuv qoidalari",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': "Nima uchun imlo muhim?", 'body':
                 "Bitta harf xatosi ma'noni butunlay o'zgartiradi:\n\n"
                 "**bir** (son) — **bor** (fe'l)\n"
                 "**tosh** (jism) — **tush** (uyqu)\n\n"
                 "Savodli yozish — hurmat belgisi."},
                {'type': 'text', 'title': "O' va G' harflari", 'body':
                 "O'zbek alifbosida **oʻ** va **gʻ** harflari tutuq belgisi bilan yoziladi:\n\n"
                 "oʻzbek, koʻcha, oʻquvchi, toʻgʻri\n"
                 "gʻalaba, bogʻ, ogʻir, yaproq\n\n"
                 "Klaviaturada topilmasa, oddiy apostrof (') ham qabul qilinadi: o'zbek, g'alaba"},
                {'type': 'text', 'title': "Tutuq belgisi (ʼ)", 'body':
                 "Tutuq belgisi ikki holatda qo'yiladi:\n\n"
                 "**1.** Unlidan keyin — cho'ziq talaffuz: **maʼno**, **taʼlim**, **sanʼat**\n"
                 "**2.** Undoshdan keyin — ajratish: **sarʼat** emas, **inʼom**, **shoʼba**"},
                {'type': 'text', 'title': "Qo'shib va ajratib yozish", 'body':
                 "**Qo'shib yoziladi:**\n"
                 "beshinchi, o'ttiz, ellikbosh\n\n"
                 "**Ajratib yoziladi:**\n"
                 "bir necha, har xil, hech kim\n\n"
                 "**Chiziqcha bilan:**\n"
                 "ikki-uch, katta-kichik, ota-ona, oq-qora"},
                {'type': 'table', 'head': ["Noto'g'ri", "To'g'ri"], 'rows': [
                    ['maktap', 'maktab'],
                    ['kitob o‘qidim', "kitob o'qidim"],
                    ['ma’no', "ma'no"],
                    ['bir nechta', 'bir nechta (ajratib)'],
                    ['otaona', 'ota-ona'],
                ]},
                {'type': 'note', 'body':
                 "Jarangli undosh so'z oxirida jarangsizga o'xshab eshitiladi, "
                 "lekin **jarangli** yoziladi: kitob (kitop emas), maktab (maktap emas)."},
                {'type': 'life', 'body':
                 "Xato bilan yozilgan xabar e'tiborsizlik belgisi. "
                 "Bir necha qoidani bilish yozuvingizni sezilarli yaxshilaydi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Qaysi so\'z to\'g\'ri yozilgan?',
                 'options': ['maktap', 'maktab', 'mekteb'], 'answer': 1,
                 'explain': "So'z oxirida jarangli undosh saqlanadi: maktab."},
                {'type': 'mc', 'q': 'Qaysi so\'z chiziqcha bilan yoziladi?',
                 'options': ['ota ona', 'ota-ona', 'otaona'], 'answer': 1,
                 'explain': "Juft so'zlar chiziqcha bilan: ota-ona."},
                {'type': 'mc', 'q': "«kitob» so'zi nima uchun «kitop» emas?",
                 'options': ['Chunki jarangli undosh saqlanadi', 'Chunki uzun so\'z',
                             'Chunki chet so\'z'], 'answer': 0,
                 'explain': "Talaffuzda «p» eshitilsa ham, «b» yoziladi."},
                {'type': 'tf', 'q': "«ma'no» so'zida tutuq belgisi bor.", 'answer': True,
                 'explain': "To'g'ri — unlidan keyin tutuq belgisi qo'yiladi."},
                {'type': 'mc', 'q': 'Qaysi juftlik ajratib yoziladi?',
                 'options': ['bir necha', 'beshinchi', "o'ttiz"], 'answer': 0,
                 'explain': "«Bir necha» ajratib yoziladi."},
                {'type': 'fill', 'q': "«ta___lim» so'ziga qanday belgi tushadi? (belgi nomini yozing)",
                 'answer': 'tutuq', 'accept': ['tutuq belgisi', 'tutuq', 'apostrof'],
                 'explain': "Ta'lim — tutuq belgisi bilan."},
            ],
            'homework': {
                'intro': "Imlo qoidalarini qo'llang.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "«maktap» so'zini to'g'ri yozing.",
                     'answer': 'maktab'},
                    {'id': 'h2', 'type': 'text', 'prompt': "«katta kichik» juftligini to'g'ri yozing.",
                     'answer': 'katta-kichik'},
                    {'id': 'h3', 'type': 'text', 'prompt': "«kitop» so'zini to'g'ri yozing.",
                     'answer': 'kitob'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Tutuq belgisi ishlatiladigan 2 ta so'z yozing."},
                ],
            },
        },
        {
            'slug': 'matn-tuzish',
            'title': 'Matn tuzish',
            'summary': "Fikrni tartibli, bog'lanishli bayon qilish",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Matn nima?', 'body':
                 "**Matn** — bir mavzuga bag'ishlangan, mazmunan bog'langan gaplar to'plami.\n\n"
                 "Tasodifiy gaplar matn emas. Matnda gaplar bir-birini davom ettiradi."},
                {'type': 'steps', 'title': 'Matnning tuzilishi', 'items': [
                    "**Kirish** — mavzuni tanishtiradi (1-2 gap).",
                    "**Asosiy qism** — fikrni ochib beradi (3-5 gap).",
                    "**Xulosa** — yakunlaydi (1-2 gap).",
                ]},
                {'type': 'text', 'title': "Bog'lovchi so'zlar", 'body':
                 "Gaplarni bog'lash uchun quyidagi so'zlar ishlatiladi:\n\n"
                 "**Ketma-ketlik:** avvalo, keyin, so'ngra, nihoyat\n"
                 "**Qo'shimcha:** bundan tashqari, shuningdek, yana\n"
                 "**Sabab:** chunki, shuning uchun, natijada\n"
                 "**Qarama-qarshilik:** lekin, ammo, biroq"},
                {'type': 'example', 'title': 'Namuna matn', 'body':
                 "**Kirish:** Kitob o'qish — eng foydali odat.\n\n"
                 "**Asosiy qism:** Avvalo, kitob so'z boyligimizni oshiradi. "
                 "Bundan tashqari, u tasavvurni rivojlantiradi. "
                 "Kitob o'qigan bola chiroyli gapiradi va savodli yozadi. "
                 "Shuningdek, kitob bizga yangi bilim beradi.\n\n"
                 "**Xulosa:** Shuning uchun har kuni kitob o'qish kerak."},
                {'type': 'text', 'title': 'Matn turlari', 'body':
                 "**Hikoya** — voqeani so'zlab beradi (nima bo'ldi?)\n"
                 "**Tasvir** — narsani ta'riflaydi (qanday?)\n"
                 "**Mulohaza** — fikrni isbotlaydi (nima uchun?)"},
                {'type': 'note', 'body':
                 "Yozishdan oldin **reja** tuzing. Reja bo'lmasa fikr chalkashadi. "
                 "Reja — 3-4 ta qisqa jumla, matnning suyagi."},
                {'type': 'life', 'body':
                 "Insho yozish, ariza yozish, hatto uzun xabar yuborish — "
                 "hammasida matn tuzish ko'nikmasi kerak bo'ladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Matn necha qismdan iborat?',
                 'options': ['2', '3', '5'], 'answer': 1,
                 'explain': 'Kirish, asosiy qism, xulosa — 3 qism.'},
                {'type': 'mc', 'q': 'Qaysi so\'z SABABNI bildiradi?',
                 'options': ['lekin', 'chunki', 'yana'], 'answer': 1,
                 'explain': "«Chunki» sababni bildiradi."},
                {'type': 'mc', 'q': 'Voqeani so\'zlab beradigan matn turi qaysi?',
                 'options': ['Hikoya', 'Tasvir', 'Mulohaza'], 'answer': 0,
                 'explain': 'Hikoya — nima bo\'lganini aytadi.'},
                {'type': 'tf', 'q': 'Matn yozishdan oldin reja tuzish foydali.', 'answer': True,
                 'explain': "To'g'ri — reja fikrni tartibga soladi."},
                {'type': 'mc', 'q': "«lekin» so'zi nimani bildiradi?",
                 'options': ['Sabab', 'Qarama-qarshilik', 'Ketma-ketlik'], 'answer': 1,
                 'explain': "«Lekin» qarama-qarshi fikrni bog'laydi."},
                {'type': 'fill', 'q': "Matnning oxirgi, yakunlovchi qismi — ___",
                 'answer': 'xulosa', 'explain': 'Bu xulosa qismi.'},
            ],
            'homework': {
                'intro': 'Matn tuzish mashqi.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "«shuning uchun» — sababmi yoki qarama-qarshilikmi?",
                     'answer': 'sabab'},
                    {'id': 'h2', 'type': 'open',
                     'prompt': "«Mening oilam» mavzusida 3 gapdan iborat kirish yozing."},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Shu mavzuga xulosa yozing (1-2 gap)."},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Matningizda qaysi bog'lovchi so'zlarni ishlatdingiz?"},
                ],
            },
        },
    ],
}

ENGLISH = {
    'key': 'english',
    'topics': [
        {
            'slug': 'to-be',
            'title': 'The verb «to be»',
            'summary': "am, is, are — ingliz tilining eng muhim fe'li",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': "«to be» nima?", 'body':
                 "Ingliz tilida **to be** fe'li «bo'lmoq», «-dir» ma'nosini beradi. "
                 "U eng ko'p ishlatiladigan fe'l.\n\n"
                 "O'zbekchada ko'pincha tarjima qilinmaydi:\n"
                 "I **am** a student. → Men o'quvchiman."},
                {'type': 'table', 'head': ['Olmosh', 'to be', 'Misol'], 'rows': [
                    ['I', 'am', 'I am a pupil.'],
                    ['You', 'are', 'You are my friend.'],
                    ['He / She / It', 'is', 'She is a teacher.'],
                    ['We', 'are', 'We are students.'],
                    ['They', 'are', 'They are happy.'],
                ]},
                {'type': 'note', 'body':
                 "Eslab qoling: **I — am**, **He/She/It — is**, qolganlari — **are**."},
                {'type': 'text', 'title': 'Qisqa shakl', 'body':
                 "Gapirishda qisqartiriladi:\n\n"
                 "I am → **I'm**\n"
                 "You are → **You're**\n"
                 "He is → **He's**\n"
                 "She is → **She's**\n"
                 "They are → **They're**"},
                {'type': 'text', 'title': "Inkor va so'roq", 'body':
                 "**Inkor** — «not» qo'shiladi:\n"
                 "I am **not** tired. → Men charchamaganman.\n"
                 "She is **not** (isn't) here.\n\n"
                 "**So'roq** — fe'l oldinga chiqadi:\n"
                 "**Are** you ready? → Tayyormisan?\n"
                 "**Is** he a doctor? → U shifokormi?"},
                {'type': 'example', 'title': 'Misollar', 'body':
                 "My name **is** Aziz. → Mening ismim Aziz.\n"
                 "We **are** from Uzbekistan. → Biz O'zbekistondanmiz.\n"
                 "It **is** cold today. → Bugun sovuq.\n"
                 "They **are not** at school. → Ular maktabda emas."},
                {'type': 'life', 'body':
                 "Tanishishda birinchi aytadigan gapingiz ham «to be» bilan: "
                 "«Hello! I am Nodira. I am eleven years old.»"},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'I ___ a student.',
                 'options': ['am', 'is', 'are'], 'answer': 0,
                 'explain': "«I» bilan doim «am» ishlatiladi."},
                {'type': 'mc', 'q': 'She ___ my sister.',
                 'options': ['am', 'is', 'are'], 'answer': 1,
                 'explain': "He/She/It bilan «is»."},
                {'type': 'mc', 'q': 'They ___ from Tashkent.',
                 'options': ['am', 'is', 'are'], 'answer': 2,
                 'explain': "We/You/They bilan «are»."},
                {'type': 'tf', 'q': "«I'm» — bu «I am» ning qisqa shakli.", 'answer': True,
                 'explain': "To'g'ri."},
                {'type': 'mc', 'q': "«Tayyormisan?» ingliz tilida qanday?",
                 'options': ['You are ready?', 'Are you ready?', 'Ready you are?'], 'answer': 1,
                 'explain': "So'roqda fe'l oldinga chiqadi: Are you ready?"},
                {'type': 'fill', 'q': 'We ___ friends. (am / is / are)',
                 'answer': 'are', 'explain': "«We» bilan «are»."},
            ],
            'homework': {
                'intro': "Bo'sh joyni to'ldiring.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': 'He ___ a teacher.', 'answer': 'is'},
                    {'id': 'h2', 'type': 'text', 'prompt': 'You ___ my best friend.', 'answer': 'are'},
                    {'id': 'h3', 'type': 'text', 'prompt': 'I ___ eleven years old.', 'answer': 'am'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "O'zingiz haqingizda «to be» bilan 2 ta gap yozing."},
                ],
            },
        },
        {
            'slug': 'present-simple',
            'title': 'Present Simple',
            'summary': "Har kuni takrorlanadigan ishlar haqida gapirish",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Qachon ishlatiladi?', 'body':
                 "**Present Simple** quyidagi holatlarda ishlatiladi:\n\n"
                 "• Har kuni takrorlanadigan ish: I go to school every day.\n"
                 "• Doimiy haqiqat: The sun rises in the east.\n"
                 "• Odat: She drinks tea in the morning."},
                {'type': 'text', 'title': 'Asosiy qoida', 'body':
                 "**He, She, It** bilan fe'lga **-s** qo'shiladi. Boshqalarida qo'shilmaydi.\n\n"
                 "I work — He work**s**\n"
                 "You play — She play**s**\n"
                 "We read — It read**s**"},
                {'type': 'table', 'head': ['Olmosh', "Fe'l", 'Misol'], 'rows': [
                    ['I / You / We / They', "o'zgarmaydi", 'I play football.'],
                    ['He / She / It', '+ s', 'He plays football.'],
                ]},
                {'type': 'text', 'title': "-es qo'shiladigan holatlar", 'body':
                 "Fe'l **-s, -sh, -ch, -x, -o** bilan tugasa, **-es** qo'shiladi:\n\n"
                 "go → go**es**\n"
                 "watch → watch**es**\n"
                 "wash → wash**es**\n"
                 "teach → teach**es**\n\n"
                 "Undosh + **y** bo'lsa, y → **ies**:\n"
                 "study → stud**ies**, cry → cr**ies**"},
                {'type': 'text', 'title': "Inkor va so'roq", 'body':
                 "**do/does** yordamchi fe'li ishlatiladi.\n\n"
                 "**Inkor:**\n"
                 "I **do not** (don't) like fish.\n"
                 "He **does not** (doesn't) like fish.\n\n"
                 "**So'roq:**\n"
                 "**Do** you like tea?\n"
                 "**Does** she like tea?"},
                {'type': 'note', 'body':
                 "Diqqat! **does** ishlatilganda fe'lga **-s qo'shilmaydi**:\n"
                 "❌ Does she likes tea?\n"
                 "✅ Does she **like** tea?"},
                {'type': 'text', 'title': 'Vaqt so\'zlari', 'body':
                 "Present Simple bilan tez-tez keladi:\n\n"
                 "always (doim), usually (odatda), often (tez-tez), "
                 "sometimes (ba'zan), never (hech qachon), every day (har kuni)"},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'She ___ English every day.',
                 'options': ['study', 'studies', 'studys'], 'answer': 1,
                 'explain': "She + undosh+y → studies."},
                {'type': 'mc', 'q': 'They ___ football on Sunday.',
                 'options': ['play', 'plays', 'playes'], 'answer': 0,
                 'explain': "They bilan fe'l o'zgarmaydi."},
                {'type': 'mc', 'q': 'He ___ to school by bus.',
                 'options': ['go', 'gos', 'goes'], 'answer': 2,
                 'explain': "«go» -o bilan tugaydi → goes."},
                {'type': 'mc', 'q': 'Qaysi gap TO\'G\'RI?',
                 'options': ['Does she likes tea?', 'Does she like tea?', 'Do she like tea?'],
                 'answer': 1,
                 'explain': "«does» bo'lsa fe'l asl holida qoladi."},
                {'type': 'tf', 'q': "«always» so'zi Present Simple bilan ishlatiladi.",
                 'answer': True, 'explain': "To'g'ri — takroriylikni bildiradi."},
                {'type': 'fill', 'q': 'I ___ (not) like coffee. — qaysi so\'z kerak: don\'t yoki doesn\'t?',
                 'answer': "don't", 'accept': ['dont', "don't", 'do not'],
                 'explain': "«I» bilan «don't»."},
            ],
            'homework': {
                'intro': "To'g'ri shaklni yozing.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': 'He (watch) ___ TV every evening.',
                     'answer': 'watches'},
                    {'id': 'h2', 'type': 'text', 'prompt': 'We (live) ___ in Tashkent.',
                     'answer': 'live'},
                    {'id': 'h3', 'type': 'text', 'prompt': 'She (go) ___ to school at 8.',
                     'answer': 'goes'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Kuningiz haqida Present Simple da 2 ta gap yozing."},
                ],
            },
        },
        {
            'slug': 'plural-nouns',
            'title': 'Plural nouns',
            'summary': "Otlarning ko'plik shakli",
            'duration': 16,
            'lesson': [
                {'type': 'text', 'title': "Ko'plik nima?", 'body':
                 "Ingliz tilida bittadan ko'p narsa haqida gapirsak, otga **-s** qo'shamiz.\n\n"
                 "one book → two book**s**\n"
                 "a cat → three cat**s**"},
                {'type': 'text', 'title': "-es qo'shiladigan holatlar", 'body':
                 "Ot **-s, -ss, -sh, -ch, -x, -o** bilan tugasa → **-es**:\n\n"
                 "bus → bus**es**\n"
                 "box → box**es**\n"
                 "dish → dish**es**\n"
                 "watch → watch**es**\n"
                 "tomato → tomato**es**"},
                {'type': 'text', 'title': '-y bilan tugaganda', 'body':
                 "**Undosh + y** → y tushib, **-ies**:\n"
                 "city → cit**ies**, baby → bab**ies**, country → countr**ies**\n\n"
                 "**Unli + y** → oddiy **-s**:\n"
                 "boy → boy**s**, day → day**s**, key → key**s**"},
                {'type': 'table', 'head': ['Birlik', "Ko'plik", 'Izoh'], 'rows': [
                    ['man', 'men', "qoidasiz"],
                    ['woman', 'women', 'qoidasiz'],
                    ['child', 'children', 'qoidasiz'],
                    ['foot', 'feet', 'qoidasiz'],
                    ['tooth', 'teeth', 'qoidasiz'],
                    ['mouse', 'mice', 'qoidasiz'],
                    ['sheep', 'sheep', "o'zgarmaydi"],
                    ['fish', 'fish', "o'zgarmaydi"],
                ]},
                {'type': 'note', 'body':
                 "Qoidasiz ko'pliklarni **yodlab olish** kerak — ular qoidaga bo'ysunmaydi. "
                 "Ular kam, lekin juda ko'p ishlatiladi."},
                {'type': 'text', 'title': "-f / -fe bilan tugaganda", 'body':
                 "f → **ves** bo'ladi:\n\n"
                 "leaf → lea**ves**\n"
                 "knife → kni**ves**\n"
                 "wolf → wol**ves**\n"
                 "life → li**ves**"},
            ],
            'quiz': [
                {'type': 'mc', 'q': "«city» so'zining ko'pligi?",
                 'options': ['citys', 'cities', 'cityes'], 'answer': 1,
                 'explain': 'Undosh + y → ies: cities.'},
                {'type': 'mc', 'q': "«child» so'zining ko'pligi?",
                 'options': ['childs', 'childes', 'children'], 'answer': 2,
                 'explain': 'Qoidasiz ko\'plik: children.'},
                {'type': 'mc', 'q': "«box» so'zining ko'pligi?",
                 'options': ['boxs', 'boxes', 'boxies'], 'answer': 1,
                 'explain': '-x bilan tugaydi → boxes.'},
                {'type': 'mc', 'q': "«boy» so'zining ko'pligi?",
                 'options': ['boies', 'boys', 'boyes'], 'answer': 1,
                 'explain': 'Unli + y → oddiy -s: boys.'},
                {'type': 'tf', 'q': "«sheep» so'zining ko'pligi ham «sheep».", 'answer': True,
                 'explain': "To'g'ri — o'zgarmaydigan otlardan biri."},
                {'type': 'fill', 'q': "«knife» so'zining ko'pligini yozing.",
                 'answer': 'knives', 'explain': '-fe → -ves: knives.'},
            ],
            'homework': {
                'intro': "Ko'plik shaklini yozing.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': 'man → ?', 'answer': 'men'},
                    {'id': 'h2', 'type': 'text', 'prompt': 'country → ?', 'answer': 'countries'},
                    {'id': 'h3', 'type': 'text', 'prompt': 'tooth → ?', 'answer': 'teeth'},
                    {'id': 'h4', 'type': 'text', 'prompt': 'bus → ?', 'answer': 'buses'},
                    {'id': 'h5', 'type': 'open',
                     'prompt': "Qoidasiz ko'plikka 2 ta misol yozing."},
                ],
            },
        },
        {
            'slug': 'my-day',
            'title': 'My day — daily routine',
            'summary': "Kun tartibi haqida gapirish va vaqtni aytish",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': 'Kundalik fe\'llar', 'body':
                 "**wake up** — uyg'onmoq\n"
                 "**get up** — turmoq\n"
                 "**wash my face** — yuz yuvmoq\n"
                 "**have breakfast** — nonushta qilmoq\n"
                 "**go to school** — maktabga bormoq\n"
                 "**do homework** — uy vazifasini bajarmoq\n"
                 "**have dinner** — kechki ovqat yemoq\n"
                 "**go to bed** — uxlashga yotmoq"},
                {'type': 'text', 'title': 'Vaqtni aytish', 'body':
                 "**at 7 o'clock** — soat 7 da\n"
                 "**at half past seven** — 7:30 da\n"
                 "**at a quarter past seven** — 7:15 da\n"
                 "**at a quarter to eight** — 7:45 da\n\n"
                 "Oddiyroq usul: **at seven thirty** (7:30)"},
                {'type': 'text', 'title': 'Predloglar', 'body':
                 "**at** — aniq vaqt: at 8 o'clock, at night\n"
                 "**in** — qism: in the morning, in the evening\n"
                 "**on** — kun: on Monday, on Sunday"},
                {'type': 'example', 'title': 'Namuna matn', 'body':
                 "I wake up **at** 7 o'clock **in** the morning. "
                 "I wash my face and have breakfast. "
                 "I go to school **at** 8. "
                 "**In** the afternoon I do my homework. "
                 "I have dinner **at** 7 **in** the evening. "
                 "I go to bed **at** 10."},
                {'type': 'text', 'title': 'Hafta kunlari', 'body':
                 "Monday — dushanba\nTuesday — seshanba\nWednesday — chorshanba\n"
                 "Thursday — payshanba\nFriday — juma\nSaturday — shanba\nSunday — yakshanba"},
                {'type': 'note', 'body':
                 "Hafta kunlari va oylar **doim katta harf** bilan yoziladi: "
                 "Monday, September. Bu o'zbek tilidan farq qiladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "«uyg'onmoq» ingliz tilida?",
                 'options': ['get up', 'wake up', 'stand up'], 'answer': 1,
                 'explain': 'wake up — uyg\'onmoq.'},
                {'type': 'mc', 'q': 'I go to school ___ 8 o\'clock.',
                 'options': ['in', 'at', 'on'], 'answer': 1,
                 'explain': "Aniq vaqt bilan «at»."},
                {'type': 'mc', 'q': 'We have lunch ___ the afternoon.',
                 'options': ['in', 'at', 'on'], 'answer': 0,
                 'explain': "Kun qismi bilan «in»: in the afternoon."},
                {'type': 'mc', 'q': "«chorshanba» ingliz tilida?",
                 'options': ['Tuesday', 'Wednesday', 'Thursday'], 'answer': 1,
                 'explain': 'Wednesday — chorshanba.'},
                {'type': 'tf', 'q': "Hafta kunlari katta harf bilan yoziladi.", 'answer': True,
                 'explain': "To'g'ri: Monday, Friday."},
                {'type': 'fill', 'q': 'I do my homework ___ the evening. (in / at / on)',
                 'answer': 'in', 'explain': "in the evening."},
            ],
            'homework': {
                'intro': "To'g'ri so'zni yozing.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "«nonushta qilmoq» — ingliz tilida (2 so'z)",
                     'answer': 'have breakfast'},
                    {'id': 'h2', 'type': 'text', 'prompt': 'I get up ___ 7 o\'clock. (in/at/on)',
                     'answer': 'at'},
                    {'id': 'h3', 'type': 'text', 'prompt': "«juma» ingliz tilida?",
                     'answer': 'Friday', 'accept': ['friday']},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "O'z kuningiz haqida ingliz tilida 3 ta gap yozing."},
                ],
            },
        },
    ],
}

NATURE = {
    'key': 'nature',
    'topics': [
        {
            'slug': 'suv',
            'title': 'Suv va uning holatlari',
            'summary': "Suvning uch holati va tabiatdagi aylanishi",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': 'Suv — hayot manbai', 'body':
                 "Suvsiz hayot yo'q. Odam tanasining taxminan **70%** i suvdan iborat. "
                 "Yer yuzining ham 70% i suv bilan qoplangan."},
                {'type': 'text', 'title': 'Suvning uch holati', 'body':
                 "**Qattiq** — muz, qor, do'l (0°C dan past)\n"
                 "**Suyuq** — oddiy suv (0°C dan 100°C gacha)\n"
                 "**Gaz** — bug' (100°C dan yuqori)\n\n"
                 "Bir modda, uch xil ko'rinish!"},
                {'type': 'table', 'head': ['Jarayon', 'Nima bo\'ladi', 'Misol'], 'rows': [
                    ['Erish', 'Qattiq → suyuq', 'Muz eriydi'],
                    ['Muzlash', 'Suyuq → qattiq', 'Suv muzlaydi'],
                    ['Bug\'lanish', 'Suyuq → gaz', 'Choynakdan bug\''],
                    ['Kondensatsiya', 'Gaz → suyuq', 'Deraza terlashi'],
                ]},
                {'type': 'steps', 'title': 'Tabiatdagi suv aylanishi', 'items': [
                    "Quyosh dengiz va daryolardagi suvni isitadi.",
                    "Suv bug'lanib, yuqoriga ko'tariladi.",
                    "Yuqorida sovib, mayda tomchilarga aylanadi — bulut hosil bo'ladi.",
                    "Tomchilar yiriklashib, yomg'ir yoki qor bo'lib yog'adi.",
                    "Suv yana daryoga, dengizga qaytadi. Aylanish takrorlanadi.",
                ]},
                {'type': 'note', 'body':
                 "Suv **0°C** da muzlaydi va **100°C** da qaynaydi. "
                 "Bu raqamlarni yodda tuting — ular fizika va kimyoda ham kerak bo'ladi."},
                {'type': 'life', 'body':
                 "O'zbekistonda suv juda qadrli — biz quruq iqlimda yashaymiz. "
                 "Kranni behuda ochiq qoldirmang: bir daqiqada 10 litrgacha suv oqib ketadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Suv necha darajada muzlaydi?',
                 'options': ['0°C', '10°C', '100°C'], 'answer': 0,
                 'explain': 'Suv 0 darajada muzlaydi.'},
                {'type': 'mc', 'q': 'Muzning erishi qanday jarayon?',
                 'options': ['Qattiqdan suyuqqa', 'Suyuqdan gazga', 'Gazdan suyuqqa'], 'answer': 0,
                 'explain': 'Erish — qattiq holatdan suyuqqa o\'tish.'},
                {'type': 'mc', 'q': "Bulut qanday hosil bo'ladi?",
                 'options': ["Bug' sovib tomchilarga aylanadi", 'Shamol havoni ko\'taradi',
                             'Quyosh havoni quritadi'], 'answer': 0,
                 'explain': "Yuqorida bug' soviydi va mayda tomchilar — bulut hosil bo'ladi."},
                {'type': 'tf', 'q': 'Suv 100°C da qaynaydi.', 'answer': True,
                 'explain': "To'g'ri."},
                {'type': 'mc', 'q': 'Odam tanasining necha foizi suv?',
                 'options': ['20%', '50%', '70%'], 'answer': 2,
                 'explain': 'Taxminan 70%.'},
                {'type': 'fill', 'q': "Suvning gaz holati nima deyiladi? (bir so'z)",
                 'answer': "bug'", 'accept': ['bug', "bug'", 'bugʻ', 'bug‘'],
                 'explain': "Gaz holati — bug'."},
            ],
            'homework': {
                'intro': 'Suv haqida vazifalar.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': 'Suv necha darajada qaynaydi?', 'answer': '100'},
                    {'id': 'h2', 'type': 'text', 'prompt': "Qor suvning qaysi holati? (qattiq/suyuq/gaz)",
                     'answer': 'qattiq'},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Uyda suvni tejash uchun 2 ta usul yozing."},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Suv aylanishining bosqichlarini o'z so'zingiz bilan yozing."},
                ],
            },
        },
        {
            'slug': 'havo',
            'title': 'Havo va uning tarkibi',
            'summary': "Havo nimadan iborat va nima uchun kerak",
            'duration': 16,
            'lesson': [
                {'type': 'text', 'title': 'Havo nima?', 'body':
                 "**Havo** — Yerni o'rab turgan gazlar aralashmasi. "
                 "Havoni ko'rmaymiz, lekin uni sezamiz — shamol esganda."},
                {'type': 'table', 'head': ['Gaz', 'Ulushi', 'Vazifasi'], 'rows': [
                    ['Azot', '78%', 'Eng ko\'p, o\'simliklar uchun kerak'],
                    ['Kislorod', '21%', 'Nafas olish va yonish uchun'],
                    ['Boshqalar', '1%', 'Karbonat angidrid, argon va b.'],
                ]},
                {'type': 'text', 'title': 'Kislorod — eng muhimi', 'body':
                 "Havoning faqat **21%** i kislorod, lekin usiz hayot bo'lmaydi:\n\n"
                 "• Odam va hayvonlar kislorod bilan nafas oladi\n"
                 "• Yonish uchun kislorod kerak (olovni idish bilan yopsangiz o'chadi)\n"
                 "• Kislorodni **o'simliklar** ishlab chiqaradi"},
                {'type': 'text', 'title': 'Havoning xossalari', 'body':
                 "• Rangsiz, hidsiz, ta'msiz\n"
                 "• Og'irligi bor (lekin juda yengil)\n"
                 "• Isiganda kengayadi va yuqoriga ko'tariladi\n"
                 "• Sovuganda siqiladi va pastga tushadi\n\n"
                 "Shuning uchun issiq havo tepada, sovuq havo pastda bo'ladi."},
                {'type': 'text', 'title': 'Havo ifloslanishi', 'body':
                 "Havoni ifloslantiradigan narsalar:\n"
                 "zavod tutuni, avtomobil gazi, yonayotgan chiqindi, chang\n\n"
                 "Ifloslangan havo kasallik keltiradi: yo'tal, astma, bosh og'rig'i."},
                {'type': 'note', 'body':
                 "Bitta katta daraxt yiliga 4 kishiga yetadigan kislorod ishlab chiqaradi. "
                 "Daraxt ekish — havoni tozalashning eng yaxshi yo'li."},
                {'type': 'life', 'body':
                 "Xonani kuniga bir necha marta shamollating. "
                 "Toza havo diqqatni oshiradi — dars tayyorlash osonlashadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Havoda eng ko\'p qaysi gaz bor?',
                 'options': ['Kislorod', 'Azot', 'Karbonat angidrid'], 'answer': 1,
                 'explain': 'Azot — 78%.'},
                {'type': 'mc', 'q': 'Havoda kislorod necha foiz?',
                 'options': ['21%', '50%', '78%'], 'answer': 0,
                 'explain': 'Kislorod taxminan 21%.'},
                {'type': 'mc', 'q': 'Kislorodni kim ishlab chiqaradi?',
                 'options': ['Hayvonlar', "O'simliklar", 'Zavodlar'], 'answer': 1,
                 'explain': "O'simliklar kislorod ajratadi."},
                {'type': 'tf', 'q': 'Issiq havo yuqoriga ko\'tariladi.', 'answer': True,
                 'explain': "To'g'ri — isiganda havo kengayadi va yengillashadi."},
                {'type': 'mc', 'q': 'Qaysi biri havoni ifloslantiradi?',
                 'options': ['Daraxtlar', 'Avtomobil gazi', 'Yomg\'ir'], 'answer': 1,
                 'explain': 'Avtomobil gazi — asosiy ifloslantiruvchilardan.'},
                {'type': 'fill', 'q': "Nafas olish uchun kerak bo'lgan gaz nomi?",
                 'answer': 'kislorod', 'explain': 'Kislorod.'},
            ],
            'homework': {
                'intro': 'Havo haqida.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': 'Havoda azot necha foiz? (faqat son)',
                     'answer': '78'},
                    {'id': 'h2', 'type': 'text', 'prompt': "Yonish uchun qaysi gaz kerak?",
                     'answer': 'kislorod'},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Havoni toza saqlash uchun 2 ta taklif yozing."},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Shahringizda havo tozami? Nima uchun shunday deb o'ylaysiz?"},
                ],
            },
        },
        {
            'slug': 'tuproq',
            'title': 'Tuproq',
            'summary': "Tuproq nimadan iborat va nima uchun qadrli",
            'duration': 16,
            'lesson': [
                {'type': 'text', 'title': 'Tuproq nima?', 'body':
                 "**Tuproq** — yer yuzasining o'simlik o'sadigan yumshoq qatlami.\n\n"
                 "Tuproq juda sekin hosil bo'ladi: 1 sm tuproq uchun **100 yildan ortiq** vaqt kerak. "
                 "Shuning uchun uni asrash muhim."},
                {'type': 'text', 'title': 'Tuproq tarkibi', 'body':
                 "• **Chirindi (gumus)** — chirigan o'simlik va hayvon qoldiqlari. "
                 "Tuproqning eng qimmatli qismi, uni qora qiladi.\n"
                 "• **Qum va loy** — mineral zarralar\n"
                 "• **Suv** — o'simlik ildizi uchun\n"
                 "• **Havo** — ildiz ham nafas oladi\n"
                 "• **Tirik organizmlar** — chuvalchang, mikroblar"},
                {'type': 'text', 'title': 'Unumdorlik', 'body':
                 "**Unumdorlik** — tuproqning hosil berish qobiliyati.\n\n"
                 "Chirindi ko'p bo'lsa, tuproq unumdor bo'ladi. "
                 "Eng unumdor tuproq — **qora tuproq**."},
                {'type': 'text', 'title': "O'zbekiston tuproqlari", 'body':
                 "**Bo'z tuproq** — tekislik va adirlarda, sug'orilsa unumdor\n"
                 "**O'tloqi tuproq** — daryo bo'ylarida, juda unumdor\n"
                 "**Qumli tuproq** — cho'llarda, kam unumdor\n"
                 "**Sho'rxok** — tuz ko'p, o'simlik yomon o'sadi"},
                {'type': 'text', 'title': 'Tuproqni asrash', 'body':
                 "Tuproqqa zarar yetkazadigan narsalar:\n"
                 "shamol va suv yuvishi (eroziya), sho'rlanish, chiqindi, ortiqcha kimyoviy o'g'it\n\n"
                 "Himoya usullari: daraxt ekish, to'g'ri sug'orish, organik o'g'it ishlatish"},
                {'type': 'note', 'body':
                 "Chuvalchang — tuproqning do'sti. U yer kavlab, havo va suv o'tishini "
                 "osonlashtiradi hamda chirindini ko'paytiradi."},
                {'type': 'life', 'body':
                 "O'zbekistonda paxta va bug'doy tuproqqa bog'liq. "
                 "Sho'rlangan yerda hosil kam bo'ladi — shuning uchun to'g'ri sug'orish juda muhim."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "Tuproqning eng qimmatli qismi nima?",
                 'options': ['Qum', 'Chirindi', 'Tosh'], 'answer': 1,
                 'explain': 'Chirindi (gumus) unumdorlikni beradi.'},
                {'type': 'mc', 'q': '1 sm tuproq necha yilda hosil bo\'ladi?',
                 'options': ['1 yil', '10 yil', '100 yildan ortiq'], 'answer': 2,
                 'explain': 'Juda sekin — 100 yildan ortiq.'},
                {'type': 'mc', 'q': "O'zbekistonda keng tarqalgan tuproq turi?",
                 'options': ["Bo'z tuproq", 'Qora tuproq', 'Tundra tuprog\'i'], 'answer': 0,
                 'explain': "Bo'z tuproq — asosiy turi."},
                {'type': 'tf', 'q': 'Chuvalchang tuproqqa foyda keltiradi.', 'answer': True,
                 'explain': "To'g'ri — havo va suv o'tishini yaxshilaydi."},
                {'type': 'mc', 'q': 'Tuproqning hosil berish qobiliyati nima deyiladi?',
                 'options': ['Qattiqlik', 'Unumdorlik', 'Namlik'], 'answer': 1,
                 'explain': 'Unumdorlik.'},
                {'type': 'fill', 'q': "Tuproqda tuz ko'payib ketishi nima deyiladi?",
                 'answer': "sho'rlanish", 'accept': ['shorlanish', "sho'rlanish", 'shoʻrlanish'],
                 'explain': "Sho'rlanish — O'zbekistonda jiddiy muammo."},
            ],
            'homework': {
                'intro': 'Tuproq haqida.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "Tuproqni qora qiladigan qism nomi?",
                     'answer': 'chirindi', 'accept': ['chirindi', 'gumus']},
                    {'id': 'h2', 'type': 'text', 'prompt': "Eng unumdor tuproq turi qaysi?",
                     'answer': 'qora tuproq', 'accept': ['qora', 'qora tuproq']},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Tuproqni asrash uchun 2 ta usul yozing."},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Hovlingizdagi tuproq qanday rangda? Nima o'sadi?"},
                ],
            },
        },
        {
            'slug': 'organizmlar',
            'title': 'Tirik organizmlar',
            'summary': "Tiriklikning belgilari va organizmlar olamlari",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': 'Tiriklik belgilari', 'body':
                 "Har qanday tirik organizm quyidagilarni bajaradi:\n\n"
                 "**1. Nafas olish** — kislorod oladi\n"
                 "**2. Oziqlanish** — energiya oladi\n"
                 "**3. O'sish** — kattalashadi\n"
                 "**4. Ko'payish** — naslini qoldiradi\n"
                 "**5. Harakat** — joyini o'zgartiradi yoki qismlarini qimirlatadi\n"
                 "**6. Sezish** — atrofga javob beradi\n"
                 "**7. Ajratish** — keraksiz moddani chiqaradi"},
                {'type': 'text', 'title': 'Organizmlar olamlari', 'body':
                 "**O'simliklar** — o'zi oziq tayyorlaydi (fotosintez), harakatlanmaydi\n"
                 "**Hayvonlar** — tayyor oziq bilan oziqlanadi, harakatlanadi\n"
                 "**Zamburug'lar** — qo'ziqorin, mog'or, achitqi\n"
                 "**Bakteriyalar** — juda mayda, bir hujayrali"},
                {'type': 'text', 'title': 'Hujayra — hayot asosi', 'body':
                 "Har bir tirik organizm **hujayralardan** tuzilgan.\n\n"
                 "Ba'zilari bitta hujayradan iborat (bakteriya, amyoba), "
                 "ba'zilari milliardlab hujayradan (odam, daraxt).\n\n"
                 "Hujayrani faqat **mikroskop** orqali ko'rish mumkin."},
                {'type': 'text', 'title': 'Fotosintez', 'body':
                 "O'simliklar quyosh nuri yordamida o'zi uchun oziq tayyorlaydi. "
                 "Bu jarayon **fotosintez** deyiladi.\n\n"
                 "Kerak bo'ladi: suv + karbonat angidrid + quyosh nuri\n"
                 "Hosil bo'ladi: oziq modda + **kislorod**"},
                {'type': 'formula', 'body': 'suv + CO₂ + quyosh → oziq + kislorod'},
                {'type': 'note', 'body':
                 "Fotosintez tufayli havoda kislorod bor. "
                 "O'simliklar bo'lmasa, biz nafas ololmasdik."},
                {'type': 'life', 'body':
                 "Non achitqi (zamburug') yordamida ko'tariladi, qatiq bakteriya yordamida "
                 "tayyorlanadi. Mayda organizmlar oshxonamizda ham ishlaydi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Quyidagilardan qaysi biri tiriklik belgisi EMAS?',
                 'options': ["O'sish", "Ko'payish", 'Og\'ir bo\'lish'], 'answer': 2,
                 'explain': "Og'irlik tiriklik belgisi emas."},
                {'type': 'mc', 'q': "O'simliklar o'zi uchun oziq tayyorlaydigan jarayon?",
                 'options': ['Nafas olish', 'Fotosintez', 'Oziqlanish'], 'answer': 1,
                 'explain': 'Fotosintez.'},
                {'type': 'mc', 'q': 'Fotosintez natijasida qaysi gaz ajraladi?',
                 'options': ['Azot', 'Kislorod', 'Karbonat angidrid'], 'answer': 1,
                 'explain': "O'simlik kislorod ajratadi."},
                {'type': 'tf', 'q': 'Har bir tirik organizm hujayralardan tuzilgan.',
                 'answer': True, 'explain': "To'g'ri — hujayra hayot asosi."},
                {'type': 'mc', 'q': 'Qo\'ziqorin qaysi olamga kiradi?',
                 'options': ["O'simliklar", 'Hayvonlar', "Zamburug'lar"], 'answer': 2,
                 'explain': "Qo'ziqorin — zamburug'."},
                {'type': 'fill', 'q': "Hujayrani ko'rish uchun qanday asbob kerak?",
                 'answer': 'mikroskop', 'explain': 'Mikroskop.'},
            ],
            'homework': {
                'intro': 'Tirik organizmlar haqida.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "O'simlik oziq tayyorlaydigan jarayon nomi?",
                     'answer': 'fotosintez'},
                    {'id': 'h2', 'type': 'text', 'prompt': "Fotosintezda ajraladigan gaz?",
                     'answer': 'kislorod'},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Tiriklikning 3 ta belgisini yozing."},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Uyingizda zamburug' yoki bakteriya ishlatiladigan mahsulot bormi?"},
                ],
            },
        },
    ],
}

LITERATURE = {
    'key': 'literature',
    'topics': [
        {
            'slug': 'xalq-ogzaki-ijodi',
            'title': "Xalq og'zaki ijodi",
            'summary': "Maqol, topishmoq, ertak va doston",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': "Og'zaki ijod nima?", 'body':
                 "**Xalq og'zaki ijodi (folklor)** — xalq yaratgan va og'izdan-og'izga "
                 "o'tib kelgan asarlar.\n\n"
                 "Muallifi noma'lum, chunki uni bitta odam emas, butun xalq yaratgan."},
                {'type': 'text', 'title': 'Asosiy turlari', 'body':
                 "**Maqol** — qisqa, hikmatli gap\n"
                 "«Mehnat — baxt keltirar»\n\n"
                 "**Matal** — obrazli ifoda, to'liq fikr emas\n"
                 "«Ikki qo'chqorning boshi bir qozonda qaynamas»\n\n"
                 "**Topishmoq** — yashirin savol\n"
                 "«Oyoqsiz yuradi, qanotsiz uchadi» (bulut)\n\n"
                 "**Ertak** — sehrli hikoya\n\n"
                 "**Doston** — qahramonlik haqida uzun she'riy asar\n"
                 "«Alpomish», «Go'ro'g'li»"},
                {'type': 'text', 'title': 'Maqollarning ma\'nosi', 'body':
                 "**«Bilim — ziyo, bilimsizlik — zulmat»**\n"
                 "Bilimli odam yorug'likda, bilimsiz qorong'ilikda yuradi.\n\n"
                 "**«Yetti o'lchab, bir kes»**\n"
                 "Har ishni yaxshilab o'ylab, keyin bajar.\n\n"
                 "**«Til — dilning kaliti»**\n"
                 "So'z odamning ichki dunyosini ochadi."},
                {'type': 'text', 'title': '«Alpomish» dostoni', 'body':
                 "«Alpomish» — o'zbek xalqining eng mashhur qahramonlik dostoni.\n\n"
                 "Unda Alpomishning mardligi, Barchinning sadoqati, "
                 "vatanga va oilaga muhabbat tasvirlanadi.\n\n"
                 "Dostonni **baxshi**lar dutor jo'rligida aytgan."},
                {'type': 'note', 'body':
                 "Folklor — xalqning xotirasi. Unda ajdodlarimizning aql-zakovati, "
                 "hayot tajribasi va orzulari saqlangan."},
                {'type': 'life', 'body':
                 "Kundalik nutqda ham maqol ishlatamiz: «Sabr tagi — sariq oltin», "
                 "«Bir boshga — bir o'lim». Bu nutqni chiroyli va ta'sirchan qiladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "Xalq og'zaki ijodining muallifi kim?",
                 'options': ['Mashhur shoir', 'Xalq', 'Podshoh'], 'answer': 1,
                 'explain': 'Folklorni xalq yaratgan, muallifi noma\'lum.'},
                {'type': 'mc', 'q': "«Oyoqsiz yuradi, qanotsiz uchadi» — bu nima?",
                 'options': ['Maqol', 'Topishmoq', 'Doston'], 'answer': 1,
                 'explain': 'Yashirin savol — topishmoq.'},
                {'type': 'mc', 'q': "«Alpomish» qanday asar?",
                 'options': ['Ertak', 'Doston', 'She\'r'], 'answer': 1,
                 'explain': 'Qahramonlik dostoni.'},
                {'type': 'mc', 'q': "Dostonni aytuvchi san'atkor qanday ataladi?",
                 'options': ['Baxshi', 'Shoir', 'Yozuvchi'], 'answer': 0,
                 'explain': 'Baxshi — dostonchi.'},
                {'type': 'tf', 'q': "«Yetti o'lchab, bir kes» maqoli o'ylab ish qilishga chaqiradi.",
                 'answer': True, 'explain': "To'g'ri."},
                {'type': 'fill', 'q': "Qisqa, hikmatli xalq gapi nima deyiladi?",
                 'answer': 'maqol', 'explain': 'Maqol.'},
            ],
            'homework': {
                'intro': "Og'zaki ijod bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "«Alpomish» qaysi janrga kiradi?",
                     'answer': 'doston'},
                    {'id': 'h2', 'type': 'open', 'prompt': "Bitta maqol yozing va ma'nosini tushuntiring."},
                    {'id': 'h3', 'type': 'open', 'prompt': "Bitta topishmoq yozing va javobini ayting."},
                    {'id': 'h4', 'type': 'open', 'prompt': "Buvingiz aytgan biror ertak yoki maqolni eslang."},
                ],
            },
        },
        {
            'slug': 'sher-tuzilishi',
            'title': "She'riy asar tuzilishi",
            'summary': "Misra, band, qofiya va vazn",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': "She'r qanday tuzilgan?", 'body':
                 "**Misra** — she'rning bitta satri\n"
                 "**Band (bayt)** — bir necha misradan iborat guruh\n"
                 "**Qofiya** — misra oxirlarining ohangdosh bo'lishi\n"
                 "**Vazn** — she'rning ohang o'lchovi"},
                {'type': 'example', 'title': 'Tahlil qilamiz', 'body':
                 "Bahor keldi, ochildi gul,\n"
                 "Sayradi bulbul, kuyladi qul.\n\n"
                 "**2 ta misra** — bir band hosil qilgan.\n"
                 "**gul** va **qul** — qofiya."},
                {'type': 'text', 'title': 'Qofiya turlari', 'body':
                 "**Juft qofiya (aa bb):** 1-2, 3-4 misralar qofiyalanadi\n"
                 "**Kesishgan qofiya (abab):** 1-3, 2-4 misralar\n"
                 "**Qamrovchi qofiya (abba):** 1-4, 2-3 misralar"},
                {'type': 'text', 'title': "Badiiy tasvir vositalari", 'body':
                 "**O'xshatish** — bir narsani boshqasiga qiyoslash\n"
                 "«Yuzi oydek porlaydi»\n\n"
                 "**Sifatlash (epitet)** — obrazli belgi\n"
                 "«oltin kuz», «shirin uyqu»\n\n"
                 "**Jonlantirish** — jonsizga jonlilik berish\n"
                 "«Shamol shivirladi», «Daraxt bosh egdi»\n\n"
                 "**Mubolag'a** — kuchaytirib aytish\n"
                 "«Dengizdek ko'z yoshi to'kdi»"},
                {'type': 'text', 'title': "O'zbek shoirlari", 'body':
                 "**Alisher Navoiy** — o'zbek adabiyotining buyuk namoyandasi\n"
                 "**Zulfiya** — nozik tuyg'ular shoirasi\n"
                 "**Abdulla Oripov** — «O'zbekiston» she'ri muallifi\n"
                 "**Erkin Vohidov** — chuqur ma'noli she'rlar ijodkori"},
                {'type': 'note', 'body':
                 "She'rni tushunish uchun uni **ovoz chiqarib** o'qing. "
                 "Ohang va qofiya faqat eshitilganda seziladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "She'rning bitta satri nima deyiladi?",
                 'options': ['Band', 'Misra', 'Qofiya'], 'answer': 1,
                 'explain': 'Misra — bitta satr.'},
                {'type': 'mc', 'q': "«Yuzi oydek porlaydi» — qaysi tasvir vositasi?",
                 'options': ["O'xshatish", 'Jonlantirish', "Mubolag'a"], 'answer': 0,
                 'explain': "«-dek» qo'shimchasi o'xshatish bildiradi."},
                {'type': 'mc', 'q': "«Shamol shivirladi» — qaysi vosita?",
                 'options': ["O'xshatish", 'Jonlantirish', 'Sifatlash'], 'answer': 1,
                 'explain': 'Jonsizga inson xatti-harakati berilgan — jonlantirish.'},
                {'type': 'mc', 'q': "«O'zbekiston» she'rining muallifi kim?",
                 'options': ['Zulfiya', 'Abdulla Oripov', 'Erkin Vohidov'], 'answer': 1,
                 'explain': 'Abdulla Oripov.'},
                {'type': 'tf', 'q': "Qofiya — misra oxirlarining ohangdosh bo'lishi.",
                 'answer': True, 'explain': "To'g'ri."},
                {'type': 'fill', 'q': "«Oltin kuz» iborasida «oltin» — qaysi vosita? (bir so'z)",
                 'answer': 'sifatlash', 'accept': ['sifatlash', 'epitet'],
                 'explain': 'Obrazli belgi — sifatlash (epitet).'},
            ],
            'homework': {
                'intro': "She'riyat bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "She'rning satri nima deb ataladi?",
                     'answer': 'misra'},
                    {'id': 'h2', 'type': 'open', 'prompt': "Bitta o'xshatish o'ylab toping va yozing."},
                    {'id': 'h3', 'type': 'open', 'prompt': "Bitta jonlantirish yozing."},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Yod bilgan she'ringizdan 2 misra yozing va qofiyani ko'rsating."},
                ],
            },
        },
        {
            'slug': 'navoiy',
            'title': 'Alisher Navoiy',
            'summary': "Buyuk shoir hayoti va ijodi",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Hayoti', 'body':
                 "**Alisher Navoiy** (1441–1501) — o'zbek adabiyotining asoschisi, "
                 "shoir, olim va davlat arbobi.\n\n"
                 "Hirotda tug'ilgan. Yoshligidan she'r yozgan. "
                 "Sulton Husayn Boyqaro davrida vazir bo'lgan."},
                {'type': 'text', 'title': 'Asosiy xizmati', 'body':
                 "Navoiy davrida ilm va adabiyot asosan **fors tilida** yozilar edi. "
                 "Turkiy (o'zbek) til «qo'pol» deb hisoblanardi.\n\n"
                 "Navoiy buni rad etdi va **turkiy tilda** buyuk asarlar yaratib, "
                 "bu tilning boyligini isbotladi.\n\n"
                 "«Muhokamat ul-lug'atayn» asarida turkiy tilning fors tilidan "
                 "kam emasligini dalillar bilan ko'rsatdi."},
                {'type': 'text', 'title': '«Xamsa» — besh doston', 'body':
                 "Navoiyning eng mashhur asari — **«Xamsa»** (beshlik):\n\n"
                 "1. **Hayrat ul-abror** — pand-nasihat\n"
                 "2. **Farhod va Shirin** — muhabbat va mardlik\n"
                 "3. **Layli va Majnun** — sof ishq\n"
                 "4. **Sab'ai sayyor** — yetti sayyora hikoyalari\n"
                 "5. **Saddi Iskandariy** — Iskandar haqida"},
                {'type': 'text', 'title': 'Navoiy hikmatlari', 'body':
                 "«Odami ersang demagil odami,\n"
                 "Onikim yo'q xalq g'amidin g'ami»\n\n"
                 "Ma'nosi: xalqning g'amini o'ylamagan odamni inson dema.\n\n"
                 "Navoiy insonparvarlik, bilim, adolat va do'stlikni ulug'lagan."},
                {'type': 'note', 'body':
                 "Navoiy nomi bugun ham yashaydi: Navoiy viloyati, Navoiy shahri, "
                 "Alisher Navoiy nomidagi Milliy kutubxona, teatrlar va maktablar."},
                {'type': 'life', 'body':
                 "Navoiy o'z mablag'i bilan maktab, shifoxona, ko'prik va karvonsaroylar "
                 "qurdirgan. U nafaqat so'zda, amalda ham xalqqa xizmat qilgan."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Alisher Navoiy qaysi shaharda tug\'ilgan?',
                 'options': ['Samarqand', 'Hirot', 'Buxoro'], 'answer': 1,
                 'explain': 'Navoiy 1441-yilda Hirotda tug\'ilgan.'},
                {'type': 'mc', 'q': "«Xamsa» nechta dostondan iborat?",
                 'options': ['3', '5', '7'], 'answer': 1,
                 'explain': "«Xamsa» — beshlik, 5 ta doston."},
                {'type': 'mc', 'q': 'Navoiyning asosiy xizmati nima?',
                 'options': ['Fors tilida yozgani', 'Turkiy tilning boyligini isbotlagani',
                             'Arab tilini o\'rgatgani'], 'answer': 1,
                 'explain': 'U turkiy (o\'zbek) tilda buyuk asarlar yaratdi.'},
                {'type': 'mc', 'q': 'Quyidagilardan qaysi biri «Xamsa» ga kiradi?',
                 'options': ['Layli va Majnun', 'Alpomish', "Go'ro'g'li"], 'answer': 0,
                 'explain': "«Layli va Majnun» — Xamsaning uchinchi dostoni."},
                {'type': 'tf', 'q': "Navoiy davlat arbobi ham bo'lgan.", 'answer': True,
                 'explain': "To'g'ri — u Husayn Boyqaro davrida vazir bo'lgan."},
                {'type': 'fill', 'q': "Navoiyning turkiy til haqidagi asari: «Muhokamat ul-___» (bir so'z)",
                 'answer': "lug'atayn", 'accept': ['lugatayn', "lug'atayn", 'lugʻatayn'],
                 'explain': "«Muhokamat ul-lug'atayn» — ikki til muhokamasi."},
            ],
            'homework': {
                'intro': 'Navoiy haqida.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "Navoiy necha yilda tug'ilgan?",
                     'answer': '1441'},
                    {'id': 'h2', 'type': 'text', 'prompt': "«Xamsa» nechta dostondan iborat? (son bilan)",
                     'answer': '5'},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "«Xamsa» dostonlaridan birining nomini yozing."},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Navoiy hikmati sizga nimani o'rgatdi? O'z so'zingiz bilan yozing."},
                ],
            },
        },
    ],
}
