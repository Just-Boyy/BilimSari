# -*- coding: utf-8 -*-
"""9-sinf — Tarix va Huquq."""

HISTORY = {
    'key': 'history',
    'topics': [
        {
            'slug': 'qadimgi-sharq',
            'title': 'Qadimgi Sharq sivilizatsiyalari',
            'summary': "Misr, Mesopotamiya va ilk davlatchilik",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Ilk sivilizatsiyalar qayerda paydo bo\'lgan?', 'body':
                 "Insoniyat tarixidagi eng qadimgi sivilizatsiyalar **daryo bo'ylarida** "
                 "paydo bo'lgan: Nil daryosi (Misr), Dajla va Frot daryolari (Mesopotamiya).\n\n"
                 "Sabab oddiy: unumdor tuproq va sug'orish imkoniyati dehqonchilikni "
                 "rivojlantirgan."},
                {'type': 'text', 'title': 'Qadimgi Misr', 'body':
                 "Qadimgi Misr davlati miloddan avvalgi **3100-yilda** birlashgan.\n\n"
                 "Boshqaruvchisi **fir'avn** deb atalgan va xudo sifatida hurmat qilingan. "
                 "Piramidalar fir'avnlar uchun qabr sifatida qurilgan."},
                {'type': 'table', 'head': ['Sivilizatsiya', 'Daryo', 'Mashhur yodgorlik'], 'rows': [
                    ['Qadimgi Misr', 'Nil', 'Giza piramidalari'],
                    ['Mesopotamiya', 'Dajla, Frot', 'Bobil osma bog\'lari'],
                    ['Qadimgi Hindiston', 'Ind', 'Xarappa shaharlari'],
                    ['Qadimgi Xitoy', 'Xuanxe', 'Xitoy devori (keyinroq)'],
                ]},
                {'type': 'text', 'title': 'Mesopotamiya va yozuv', 'body':
                 "Mesopotamiyada shumerlar **mixxat yozuvi**ni ixtiro qilgan — bu "
                 "insoniyat tarixidagi eng qadimgi yozuv tizimlaridan biri.\n\n"
                 "Ular loy taxtachalarga o'tkir tayoqcha bilan belgilar tushirgan."},
                {'type': 'example', 'title': 'Hammurapi qonunlari', 'body':
                 "Bobil podshosi **Hammurapi** (mil. avv. XVIII asr) tarixdagi birinchi "
                 "yozma qonunlar to'plamlaridan birini yaratgan.\n\n"
                 "Unda jinoyat va jazolar aniq belgilangan — \"ko'zga ko'z, tishga tish\" "
                 "tamoyili mashhur."},
                {'type': 'note', 'body':
                 "Yozuvning paydo bo'lishi — insoniyat tarixida \"tarixgacha\" va \"tarixiy\" "
                 "davrlarni ajratuvchi asosiy chegara hisoblanadi."},
                {'type': 'life', 'body':
                 "Bugungi kalendarimiz, matematikadagi 60 lik son tizimi (soat, minut) — "
                 "ko'p narsa aynan Mesopotamiyadan meros qolgan."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "Qadimgi Misr qaysi daryo bo'yida joylashgan?",
                 'options': ['Dajla', 'Nil', 'Frot'], 'answer': 1,
                 'explain': "Qadimgi Misr Nil daryosi bo'yida joylashgan."},
                {'type': 'mc', 'q': "Misr hukmdorlari qanday nomlangan?",
                 'options': ['Podshoh', "Fir'avn", 'Xon'], 'answer': 1,
                 'explain': "Misr hukmdorlari fir'avn deb atalgan."},
                {'type': 'mc', 'q': "Mixxat yozuvini kim ixtiro qilgan?",
                 'options': ['Misrliklar', 'Shumerlar', 'Xitoyliklar'], 'answer': 1,
                 'explain': "Mixxat yozuvini Mesopotamiyadagi shumerlar ixtiro qilgan."},
                {'type': 'tf', 'q': "Hammurapi qonunlari Bobilda yaratilgan.",
                 'answer': True, 'explain': "To'g'ri, Bobil podshosi Hammurapi tomonidan."},
                {'type': 'mc', 'q': "Nima uchun ilk sivilizatsiyalar daryo bo'ylarida paydo bo'lgan?",
                 'options': ['Iqlim sovuq bo\'lgani uchun', 'Unumdor tuproq va sug\'orish uchun',
                             'Tog\'lar yaqin bo\'lgani uchun'], 'answer': 1,
                 'explain': "Daryo bo'ylari dehqonchilik uchun qulay bo'lgan."},
                {'type': 'fill', 'q': "Giza piramidalari qaysi mamlakatda joylashgan?",
                 'answer': 'misr', 'accept': ['Misr', "misr", "Qadimgi Misr"],
                 'explain': "Giza piramidalari Misrda joylashgan."},
            ],
            'homework': {
                'intro': "Qadimgi Sharq sivilizatsiyalari bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "Mesopotamiya qaysi ikki daryo oralig'ida joylashgan?",
                     'answer': 'dajla va frot', 'accept': ['dajla va frot', 'frot va dajla', 'dajla, frot']},
                    {'id': 'h2', 'type': 'text', 'prompt': "Bobil qonunlarini yaratgan podshoning ismi?",
                     'answer': 'hammurapi', 'accept': ['hammurapi', 'Hammurapi']},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Nima uchun yozuvning ixtiro qilinishi insoniyat tarixida muhim voqea "
                               "hisoblanadi? Fikringizni yozing."},
                ],
            },
        },
        {
            'slug': 'amir-temur',
            'title': 'Amir Temur va Temuriylar davri',
            'summary': "Buyuk sarkarda va uning saltanati",
            'duration': 22,
            'lesson': [
                {'type': 'text', 'title': 'Amir Temur kim edi?', 'body':
                 "**Amir Temur** (1336–1405) — Movarounnahrda tug'ilib, jahon tarixidagi eng "
                 "buyuk sarkardalardan biriga aylangan davlat arbobi.\n\n"
                 "U 1370-yilda Balxda hokimiyat tepasiga kelib, ulkan saltanat barpo etdi."},
                {'type': 'text', 'title': 'Samarqand — poytaxt', 'body':
                 "Amir Temur **Samarqand**ni o'z saltanatining poytaxtiga aylantirdi va uni "
                 "jahonning eng go'zal shaharlaridan biriga aylantirishga harakat qildi.\n\n"
                 "Registon maydoni, Bibixonim masjidi kabi yodgorliklar shu davrda qurila "
                 "boshlangan."},
                {'type': 'table', 'head': ['Sana', 'Voqea'], 'rows': [
                    ['1336', "Amir Temur tug'ilgan (Shahrisabz yaqinida)"],
                    ['1370', 'Movarounnahrda hokimiyatni qo\'lga oladi'],
                    ['1380-1390', 'Harbiy yurishlar davri'],
                    ['1405', 'Amir Temur vafot etadi'],
                ]},
                {'type': 'example', 'title': "Mirzo Ulug'bek", 'body':
                 "Amir Temurning nabirasi **Mirzo Ulug'bek** buyuk olim va astronom bo'lgan.\n\n"
                 "U Samarqandda observatoriya qurdirib, yulduzlar jadvalini tuzgan — bu "
                 "jadval o'z davri uchun juda aniq bo'lgan."},
                {'type': 'text', 'title': 'Temuriylar merosi', 'body':
                 "Temuriylar davrida fan, san'at va me'morchilik yuksak darajada "
                 "rivojlangan.\n\n"
                 "Bu davr ko'pincha \"Temuriylar Renessansi\" deb ham ataladi."},
                {'type': 'note', 'body':
                 "Amir Temurning \"Kuch — adolatda\" degan so'zlari uning davlat "
                 "boshqaruvidagi asosiy tamoyili bo'lgan."},
                {'type': 'life', 'body':
                 "Bugungi kunda Toshkentdagi Amir Temur haykali va muzeyi — uning tarixiy "
                 "merosini eslatib turadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "Amir Temur qaysi shaharni o'z saltanatining poytaxtiga aylantirgan?",
                 'options': ['Buxoro', 'Samarqand', 'Xiva'], 'answer': 1,
                 'explain': "Amir Temur Samarqandni poytaxt qilgan."},
                {'type': 'mc', 'q': "Amir Temur qachon vafot etgan?",
                 'options': ['1370', '1405', '1336'], 'answer': 1,
                 'explain': "Amir Temur 1405-yilda vafot etgan."},
                {'type': 'mc', 'q': "Mirzo Ulug'bek qaysi soha bilan mashhur bo'lgan?",
                 'options': ['Harbiy san\'at', 'Astronomiya', 'Savdo'], 'answer': 1,
                 'explain': "Mirzo Ulug'bek buyuk astronom bo'lgan."},
                {'type': 'tf', 'q': "Mirzo Ulug'bek Amir Temurning nabirasi edi.",
                 'answer': True, 'explain': "To'g'ri."},
                {'type': 'mc', 'q': "Amir Temur qayerda tug'ilgan?",
                 'options': ['Samarqand yaqinida', 'Shahrisabz yaqinida', 'Buxoro yaqinida'],
                 'answer': 1, 'explain': "Amir Temur Shahrisabz yaqinida tug'ilgan."},
                {'type': 'fill', 'q': "Amir Temur qaysi yilda hokimiyat tepasiga kelgan?",
                 'answer': '1370', 'explain': "1370-yilda."},
            ],
            'homework': {
                'intro': "Amir Temur va Temuriylar davri bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "Amir Temurning nabirasi, buyuk astronom kim bo'lgan?",
                     'answer': 'mirzo ulug\'bek', 'accept': ["mirzo ulug'bek", "ulug'bek", "Ulug'bek"]},
                    {'id': 'h2', 'type': 'number', 'prompt': "Amir Temur qaysi yilda tug'ilgan?",
                     'answer': '1336'},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Amir Temur davridagi me'morchilik yodgorliklaridan birini yozing va "
                               "u haqida qisqacha ma'lumot bering."},
                ],
            },
        },
        {
            'slug': 'mustaqillik',
            'title': "O'zbekiston mustaqilligi",
            'summary': "1991-yil — yangi davlatning tug'ilishi",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': "Mustaqillik e'lon qilinishi", 'body':
                 "O'zbekiston Respublikasi **1991-yil 31-avgustda** mustaqilligini e'lon "
                 "qildi.\n\n"
                 "Bu kun mamlakatimizda **Mustaqillik kuni** sifatida har yili keng "
                 "nishonlanadi."},
                {'type': 'text', 'title': 'Mustaqillikdan oldingi davr', 'body':
                 "O'zbekiston uzoq yillar Sovet Ittifoqi tarkibida bo'lgan. 1980-yillar "
                 "oxirida SSSRda ijtimoiy-siyosiy o'zgarishlar boshlanib, ko'plab "
                 "respublikalar mustaqillikka intila boshladi."},
                {'type': 'table', 'head': ['Sana', 'Voqea'], 'rows': [
                    ['1990, 20-iyun', "O'zbekiston suvereniteti to'g'risidagi deklaratsiya"],
                    ['1991, 31-avgust', "Mustaqillik e'lon qilindi"],
                    ['1991, 29-dekabr', "Mustaqillik bo'yicha referendum"],
                    ['1992, 8-dekabr', "Birinchi Konstitutsiya qabul qilindi"],
                ]},
                {'type': 'example', 'title': 'Davlat ramzlari', 'body':
                 "Mustaqillikdan so'ng O'zbekiston o'zining davlat ramzlarini qabul qildi:\n\n"
                 "**Davlat bayrog'i** — 1991-yil 18-noyabr\n"
                 "**Davlat gerbi** — 1992-yil 2-iyul\n"
                 "**Davlat madhiyasi** — 1992-yil 10-dekabr"},
                {'type': 'text', 'title': 'Mustaqillikning ahamiyati', 'body':
                 "Mustaqillik O'zbekistonga o'z siyosatini, iqtisodiyotini va madaniyatini "
                 "mustaqil rivojlantirish imkonini berdi.\n\n"
                 "Yangi konstitutsiya, milliy valyuta (so'm) va xalqaro aloqalar shu "
                 "davrda shakllandi."},
                {'type': 'note', 'body':
                 "O'zbekiston BMTga 1992-yil 2-martda a'zo bo'lgan — bu mamlakatning "
                 "xalqaro maydonda tan olinishining muhim bosqichi edi."},
                {'type': 'life', 'body':
                 "Har yili 1-sentabrda maktablarda \"Bilim kuni\" bilan birga Mustaqillik "
                 "bayrami ham nishonlanadi — bu ikki voqea yaqin kunlarga to'g'ri keladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "O'zbekiston qachon mustaqilligini e'lon qilgan?",
                 'options': ['1990-yil 20-iyun', '1991-yil 31-avgust', '1992-yil 8-dekabr'],
                 'answer': 1, 'explain': "1991-yil 31-avgustda mustaqillik e'lon qilindi."},
                {'type': 'mc', 'q': "O'zbekistonning birinchi Konstitutsiyasi qachon qabul qilingan?",
                 'options': ['1991-yil', '1992-yil', '1993-yil'], 'answer': 1,
                 'explain': "1992-yil 8-dekabrda qabul qilingan."},
                {'type': 'mc', 'q': "O'zbekiston BMTga qachon a'zo bo'lgan?",
                 'options': ['1991-yil', '1992-yil', '1995-yil'], 'answer': 1,
                 'explain': "1992-yil 2-martda BMTga a'zo bo'lgan."},
                {'type': 'tf', 'q': "Mustaqillik kuni har yili 31-avgustda nishonlanadi.",
                 'answer': True, 'explain': "To'g'ri."},
                {'type': 'mc', 'q': "O'zbekistonning milliy valyutasi nima deb ataladi?",
                 'options': ['Rubl', "So'm", 'Tenge'], 'answer': 1,
                 'explain': "O'zbekiston milliy valyutasi — so'm."},
                {'type': 'fill', 'q': "O'zbekiston Davlat bayrog'i qaysi yilda qabul qilingan?",
                 'answer': '1991', 'explain': "1991-yil 18-noyabrda."},
            ],
            'homework': {
                'intro': "O'zbekiston mustaqilligi bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "O'zbekiston qaysi yilda mustaqillikka erishgan?",
                     'answer': '1991'},
                    {'id': 'h2', 'type': 'text', 'prompt': "O'zbekiston milliy valyutasining nomini yozing.",
                     'answer': "so'm", 'accept': ["so'm", 'som', "So'm"]},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Mustaqillik O'zbekiston uchun nima uchun muhim deb o'ylaysiz? "
                               "2-3 gap bilan yozing."},
                ],
            },
        },
    ],
}

LAW = {
    'key': 'law',
    'topics': [
        {
            'slug': 'konstitutsiya-asoslari',
            'title': 'Konstitutsiya asoslari',
            'summary': "Davlatning asosiy qonuni bilan tanishish",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Konstitutsiya nima?', 'body':
                 "**Konstitutsiya** — davlatning asosiy qonuni bo'lib, barcha boshqa "
                 "qonunlar unga muvofiq bo'lishi shart.\n\n"
                 "U davlat tuzilishi, hokimiyat organlari va fuqarolarning asosiy "
                 "huquq-burchlarini belgilaydi."},
                {'type': 'text', 'title': "O'zbekiston Konstitutsiyasi", 'body':
                 "O'zbekiston Respublikasining Konstitutsiyasi **1992-yil 8-dekabrda** "
                 "qabul qilingan.\n\n"
                 "Har yili shu sana **Konstitutsiya kuni** sifatida nishonlanadi."},
                {'type': 'table', 'head': ['Hokimiyat tarmog\'i', 'Vazifasi', 'Organ'], 'rows': [
                    ['Qonun chiqaruvchi', 'Qonunlar qabul qiladi', 'Oliy Majlis'],
                    ['Ijro etuvchi', 'Qonunlarni amalga oshiradi', 'Vazirlar Mahkamasi'],
                    ['Sud hokimiyati', 'Adolatni ta\'minlaydi', 'Sudlar'],
                ]},
                {'type': 'text', 'title': "Hokimiyatlar bo'linishi", 'body':
                 "Konstitutsiyaga ko'ra davlat hokimiyati **uch tarmoqqa** bo'linadi: "
                 "qonun chiqaruvchi, ijro etuvchi va sud hokimiyati.\n\n"
                 "Bu bo'linish hokimiyatning bir joyda to'planib ketishining oldini "
                 "oladi."},
                {'type': 'example', 'title': 'Konstitutsiyadagi asosiy tamoyillar', 'body':
                 "• O'zbekiston — demokratik, huquqiy davlat\n"
                 "• Xalq — davlat hokimiyatining yagona manbai\n"
                 "• Inson, uning hayoti, erkinligi va huquqlari — oliy qadriyat\n"
                 "• Qonun oldida hamma teng"},
                {'type': 'note', 'body':
                 "Konstitutsiyaga o'zgartirish kiritish oddiy qonundan farqli — bu "
                 "maxsus, murakkabroq tartibda amalga oshiriladi."},
                {'type': 'life', 'body':
                 "Pasport olganda, saylovda ovoz berganda yoki shikoyat yozganda — "
                 "hammasi Konstitutsiyada belgilangan huquqlaringizga asoslanadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "Konstitutsiya nima?",
                 'options': ['Oddiy qonun', "Davlatning asosiy qonuni", 'Xalqaro shartnoma'],
                 'answer': 1, 'explain': "Konstitutsiya — davlatning asosiy qonuni."},
                {'type': 'mc', 'q': "O'zbekiston Konstitutsiyasi qachon qabul qilingan?",
                 'options': ['1991-yil', '1992-yil', '1993-yil'], 'answer': 1,
                 'explain': "1992-yil 8-dekabrda qabul qilingan."},
                {'type': 'mc', 'q': "Davlat hokimiyati nechta tarmoqqa bo'linadi?",
                 'options': ['Ikki', 'Uch', "To'rt"], 'answer': 1,
                 'explain': "Uch tarmoqqa: qonun chiqaruvchi, ijro etuvchi, sud."},
                {'type': 'tf', 'q': "Oliy Majlis — qonun chiqaruvchi hokimiyat organi.",
                 'answer': True, 'explain': "To'g'ri."},
                {'type': 'mc', 'q': "Konstitutsiyaga ko'ra davlat hokimiyatining yagona manbai nima?",
                 'options': ['Prezident', 'Xalq', 'Parlament'], 'answer': 1,
                 'explain': "Xalq — davlat hokimiyatining yagona manbai."},
                {'type': 'fill', 'q': "Konstitutsiya kuni qaysi sanada nishonlanadi? (kun-oy, masalan 8-dekabr)",
                 'answer': '8-dekabr', 'accept': ['8-dekabr', '8 dekabr'],
                 'explain': "8-dekabr — Konstitutsiya kuni."},
            ],
            'homework': {
                'intro': "Konstitutsiya asoslari bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "O'zbekiston Konstitutsiyasi qaysi yilda qabul qilingan?",
                     'answer': '1992'},
                    {'id': 'h2', 'type': 'text', 'prompt': "Sud hokimiyatining vazifasi nima? (bir so'z bilan)",
                     'answer': 'adolat', 'accept': ['adolat', 'adolatni ta\'minlash']},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "\"Qonun oldida hamma teng\" tamoyili nimani anglatadi deb "
                               "o'ylaysiz? Fikringizni yozing."},
                ],
            },
        },
        {
            'slug': 'fuqaro-huquqlari',
            'title': 'Fuqarolik huquqlari va burchlari',
            'summary': "Har bir fuqaroning asosiy huquq va majburiyatlari",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': "Huquq va burch nima?", 'body':
                 "**Huquq** — davlat tomonidan kafolatlangan imkoniyat (masalan, ta'lim "
                 "olish huquqi).\n\n"
                 "**Burch** — har bir fuqaro bajarishi shart bo'lgan majburiyat "
                 "(masalan, qonunlarga rioya qilish)."},
                {'type': 'text', 'title': 'Asosiy fuqarolik huquqlari', 'body':
                 "• Hayot huquqi\n"
                 "• Erkinlik va shaxsiy daxlsizlik huquqi\n"
                 "• Ta'lim olish huquqi\n"
                 "• Mehnat qilish huquqi\n"
                 "• Tibbiy yordam olish huquqi\n"
                 "• Fikr va so'z erkinligi"},
                {'type': 'table', 'head': ['Huquq', 'Burch'], 'rows': [
                    ["Ta'lim olish", "Qonunlarga rioya qilish"],
                    ['Mulkka egalik qilish', 'Soliq to\'lash'],
                    ['Saylash va saylanish', "Vatanni himoya qilish"],
                    ["Dam olish", "Atrof-muhitni asrash"],
                ]},
                {'type': 'example', 'title': "Maktab hayotidan misol", 'body':
                 "O'quvchi bepul umumiy ta'lim olish **huquqi**ga ega, shu bilan birga "
                 "maktab qoidalariga rioya qilish, o'qituvchilarni hurmat qilish kabi "
                 "**burch**larga ham ega."},
                {'type': 'note', 'body':
                 "Huquq va burch bir-biri bilan uzviy bog'liq — huquqingizdan "
                 "foydalanganda boshqalarning huquqini buzmasligingiz kerak."},
                {'type': 'life', 'body':
                 "Yo'l harakati qoidalariga rioya qilish — bu ham fuqarolik burchi: bu "
                 "orqali o'zingiz va boshqalarning xavfsizligini ta'minlaysiz."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "Huquq nima?",
                 'options': ['Majburiyat', 'Davlat kafolatlagan imkoniyat', 'Jarima'],
                 'answer': 1, 'explain': "Huquq — davlat kafolatlagan imkoniyat."},
                {'type': 'mc', 'q': "Quyidagilardan qaysi biri fuqarolik burchiga misol?",
                 'options': ["Ta'lim olish", 'Qonunlarga rioya qilish', 'Dam olish'],
                 'answer': 1, 'explain': "Qonunlarga rioya qilish — burch."},
                {'type': 'mc', 'q': "Quyidagilardan qaysi biri huquqqa misol?",
                 'options': ['Soliq to\'lash', 'Ta\'lim olish', 'Vatanni himoya qilish'],
                 'answer': 1, 'explain': "Ta'lim olish — huquq."},
                {'type': 'tf', 'q': "Huquq va burch bir-biridan mustaqil, bog'liq emas.",
                 'answer': False, 'explain': "Yo'q, ular uzviy bog'liq."},
                {'type': 'mc', 'q': "O'quvchining maktabdagi burchiga nima kiradi?",
                 'options': ['Bepul ta\'lim olish', 'Maktab qoidalariga rioya qilish',
                             'Dam olish huquqidan foydalanish'], 'answer': 1,
                 'explain': "Maktab qoidalariga rioya qilish — burch."},
                {'type': 'fill', 'q': "Davlat tomonidan kafolatlangan imkoniyat qanday ataladi?",
                 'answer': 'huquq', 'explain': "Bu — huquq."},
            ],
            'homework': {
                'intro': "Huquq va burchlar bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "Fuqarolik burchiga bitta misol yozing.",
                     'answer': 'soliq to\'lash',
                     'accept': ["soliq to'lash", 'qonunlarga rioya qilish', 'vatanni himoya qilish']},
                    {'id': 'h2', 'type': 'text', 'prompt': "Fuqarolik huquqiga bitta misol yozing.",
                     'answer': "ta'lim olish",
                     'accept': ["ta'lim olish", 'mehnat qilish', 'tibbiy yordam olish']},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "O'zingizning kundalik hayotingizdan huquq va burchga ikkitadan "
                               "misol keltiring."},
                ],
            },
        },
        {
            'slug': 'voyaga-yetmaganlar-huquqi',
            'title': "Voyaga yetmaganlar huquqi",
            'summary': "18 yoshgacha bo'lgan shaxslarning huquqiy holati",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': "Voyaga yetmagan kim?", 'body':
                 "O'zbekiston qonunchiligiga ko'ra, **18 yoshga to'lmagan** shaxs "
                 "voyaga yetmagan hisoblanadi.\n\n"
                 "Ular uchun maxsus huquqiy himoya choralari mavjud."},
                {'type': 'text', 'title': 'Bolalar huquqlari', 'body':
                 "**Bola huquqlari to'g'risida**gi qonunga muvofiq har bir bola quyidagi "
                 "huquqlarga ega:\n\n"
                 "• Yashash va rivojlanish huquqi\n"
                 "• Oilada tarbiyalanish huquqi\n"
                 "• Bepul ta'lim olish huquqi\n"
                 "• O'z fikrini bildirish huquqi\n"
                 "• Zo'ravonlikdan himoyalanish huquqi"},
                {'type': 'table', 'head': ['Yosh', 'Huquqiy holat'], 'rows': [
                    ['0-6 yosh', "To'liq vasiylik ostida"],
                    ['7-13 yosh', "Cheklangan mustaqillik (masalan, kichik xaridlar)"],
                    ['14-17 yosh', "Qisman harakat qobiliyati (mehnat shartnomasi kabi)"],
                    ['18 yoshdan', "To'liq harakat qobiliyati"],
                ]},
                {'type': 'example', 'title': "14 yoshdan boshlanadigan huquqlar", 'body':
                 "O'zbekiston qonunchiligiga ko'ra 14 yoshga to'lgan o'smir ota-onasining "
                 "roziligi bilan ba'zi ishlarda mehnat shartnomasi tuzishi mumkin, "
                 "shuningdek jinoiy javobgarlik ba'zi og'ir jinoyatlar uchun 14 yoshdan "
                 "boshlanadi."},
                {'type': 'note', 'body':
                 "Voyaga yetmaganlarning huquqlari buzilganda ular ota-ona, o'qituvchi "
                 "yoki maxsus davlat organlariga (masalan, Bolalar ombudsmani) murojaat "
                 "qilishlari mumkin."},
                {'type': 'life', 'body':
                 "Maktabda haqoratlanish yoki zo'ravonlikka duch kelsangiz — bu sizning "
                 "huquqingiz buzilishi, va buni katta odamlarga aytish sizning huquqingiz."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "O'zbekistonda kim voyaga yetmagan hisoblanadi?",
                 'options': ['16 yoshgacha', '18 yoshgacha', '21 yoshgacha'], 'answer': 1,
                 'explain': "18 yoshga to'lmagan shaxs voyaga yetmagan hisoblanadi."},
                {'type': 'mc', 'q': "Quyidagilardan qaysi biri bola huquqiga misol?",
                 'options': ["Ta'lim olish", "Soliq to'lash", 'Saylanish'], 'answer': 0,
                 'explain': "Ta'lim olish — bolaning asosiy huquqi."},
                {'type': 'tf', 'q': "18 yoshdan boshlab shaxs to'liq harakat qobiliyatiga ega bo'ladi.",
                 'answer': True, 'explain': "To'g'ri."},
                {'type': 'mc', 'q': "Huquqi buzilgan bola kimga murojaat qilishi mumkin?",
                 'options': ['Hech kimga', 'Ota-ona yoki tegishli organlarga', "Faqat sudga"],
                 'answer': 1, 'explain': "Ota-ona, o'qituvchi yoki davlat organlariga murojaat qilish mumkin."},
                {'type': 'mc', 'q': "Necha yoshdan boshlab ba'zi mehnat shartnomalari tuzilishi mumkin?",
                 'options': ['12', '14', '16'], 'answer': 1,
                 'explain': "14 yoshdan boshlab, ota-ona roziligi bilan."},
                {'type': 'fill', 'q': "Bolalar huquqini himoya qiluvchi maxsus davlat lavozimi qanday ataladi? "
                                       "(bir so'z: ...)",
                 'answer': 'ombudsman', 'accept': ['ombudsman', 'Ombudsman'],
                 'explain': "Bolalar ombudsmani."},
            ],
            'homework': {
                'intro': "Voyaga yetmaganlar huquqi bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "O'zbekistonda necha yoshgacha shaxs voyaga yetmagan hisoblanadi?",
                     'answer': '18'},
                    {'id': 'h2', 'type': 'text', 'prompt': "Bola huquqlariga bitta misol yozing.",
                     'answer': "ta'lim olish",
                     'accept': ["ta'lim olish", 'yashash huquqi', 'himoyalanish huquqi']},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Sizningcha, maktab o'quvchilari uchun eng muhim huquq qaysi va "
                               "nega? Qisqacha fikringizni yozing."},
                ],
            },
        },
    ],
}
