# -*- coding: utf-8 -*-
"""1-sinf — O'qish va Tabiiy fanlar."""

READING = {
    'key': 'reading',
    'topics': [
        {
            'slug': 'togri-oqish',
            'title': "To'g'ri o'qish",
            'summary': "Ravon va tushunarli o'qish qoidalari",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': "O'qish nima uchun kerak?", 'body':
                 "O'qish — bilim olishning eng asosiy yo'li. Kitob o'qigan bola ko'p narsa biladi, "
                 "chiroyli gapiradi va savodli yozadi."},
                {'type': 'steps', 'title': "To'g'ri o'qish qoidalari", 'items': [
                    "Kitobni ko'zdan 30-35 sm uzoqlikda ushlang.",
                    "Yorug' joyda o'qing — ko'zingizni asrang.",
                    "Bo'g'inlab emas, butun so'z bilan o'qishga harakat qiling.",
                    "Tinish belgilarida to'xtang: nuqtada uzunroq, vergulda qisqa.",
                    "Ovoz chiqarib o'qiganda so'zlarni aniq talaffuz qiling.",
                ]},
                {'type': 'text', 'title': 'Tinish belgilari va ohang', 'body':
                 "**Nuqta (.)** — ovozni pasaytiring va to'xtang.\n"
                 "**So'roq belgisi (?)** — ovozni ko'taring, savol ohangida o'qing.\n"
                 "**Undov belgisi (!)** — hayajon bilan, kuchli o'qing.\n"
                 "**Vergul (,)** — qisqa to'xtab, davom eting."},
                {'type': 'example', 'title': "Ohang bilan o'qiymiz", 'body':
                 "Bugun havo issiq. ← ovoz pasayadi\n"
                 "Sen maktabga borasanmi? ← ovoz ko'tariladi\n"
                 "Qanday chiroyli bog'! ← hayajon bilan"},
                {'type': 'note', 'body':
                 "Har kuni kamida 15 daqiqa o'qing. Bir oyda o'qish tezligingiz sezilarli oshadi."},
                {'type': 'life', 'body':
                 "Do'kondagi yozuvlar, dori qutisidagi ko'rsatma, telefondagi xabar — "
                 "hammasini o'qish kerak. O'qiy olmaydigan odam qiynaladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "Kitobni ko'zdan qancha uzoqlikda ushlash kerak?",
                 'options': ['10 sm', '30-35 sm', '1 metr'], 'answer': 1,
                 'explain': "30-35 sm — ko'z uchun eng qulay masofa."},
                {'type': 'mc', 'q': "Nuqtani ko'rganda nima qilamiz?",
                 'options': ['Ovozni ko\'taramiz', "Ovozni pasaytirib to'xtaymiz", 'Baqiramiz'], 'answer': 1,
                 'explain': "Nuqta — fikr tugadi, ovoz pasayadi va to'xtaymiz."},
                {'type': 'mc', 'q': "So'roq belgisini ko'rganda ovoz qanday bo'ladi?",
                 'options': ['Pasayadi', "Ko'tariladi", "O'zgarmaydi"], 'answer': 1,
                 'explain': "Savol ohangida ovoz ko'tariladi."},
                {'type': 'tf', 'q': "Qorong'i joyda o'qish ko'zga zarar qiladi.", 'answer': True,
                 'explain': "To'g'ri — doim yorug' joyda o'qing."},
                {'type': 'mc', 'q': "Vergulda nima qilamiz?",
                 'options': ['Uzoq to\'xtaymiz', 'Qisqa to\'xtaymiz', "To'xtamaymiz"], 'answer': 1,
                 'explain': "Vergulda qisqa to'xtab, gapni davom ettiramiz."},
                {'type': 'fill', 'q': "Kuniga kamida necha daqiqa o'qish tavsiya etiladi? (raqam bilan)",
                 'answer': '15', 'explain': "Kuniga 15 daqiqa — yaxshi odat."},
            ],
            'homework': {
                'intro': "O'qish bo'yicha vazifalar.",
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "Kitobni ko'zdan necha santimetr uzoqlikda ushlash kerak? (kichik sonni yozing)",
                     'answer': '30'},
                    {'id': 'h2', 'type': 'text', 'prompt': "So'roq belgisini ko'rganda ovoz pasayadimi yoki ko'tariladimi?",
                     'answer': "ko'tariladi", 'accept': ['kotariladi', "ko'tariladi", 'koʻtariladi']},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Bugun qanday kitob yoki matn o'qidingiz? Nomini yozing."},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "O'qigan narsangizdan bitta yangi so'z yozing."},
                ],
            },
        },
        {
            'slug': 'ertaklar',
            'title': 'Ertaklar',
            'summary': "Ertak nima va undan qanday saboq olamiz",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': 'Ertak nima?', 'body':
                 "**Ertak** — xalq o'ylab topgan sehrli hikoya. Unda bo'lmaydigan narsalar bo'ladi: "
                 "hayvonlar gapiradi, gilam uchadi, devlar yashaydi.\n\n"
                 "Ertaklarni bobo-buvilarimiz avloddan-avlodga aytib kelgan."},
                {'type': 'steps', 'title': 'Ertakning tuzilishi', 'items': [
                    "**Boshlanish** — «Bor ekan, yo'q ekan...»",
                    "**Voqea** — qahramon muammoga duch keladi.",
                    "**Kurash** — qahramon qiyinchilikni yengadi.",
                    "**Tugash** — yaxshilik g'alaba qozonadi.",
                ]},
                {'type': 'text', 'title': 'Ertak qahramonlari', 'body':
                 "**Yaxshi qahramonlar:** mehnatkash bola, aqlli qiz, mehribon ona\n"
                 "**Yomon qahramonlar:** dev, yalqov, ochko'z boy\n\n"
                 "Ertakda doim yaxshilik yutadi — bu ertakning asosiy qoidasi."},
                {'type': 'text', 'title': "O'zbek xalq ertaklari", 'body':
                 "«Zumrad va Qimmat» — mehnatkashlik va yalqovlik haqida\n"
                 "«Susambil» — hayvonlarning do'stligi haqida\n"
                 "«Ur to'qmoq» — adolat haqida\n"
                 "«Uch og'a-ini botirlar» — jasorat haqida"},
                {'type': 'note', 'body':
                 "Har bir ertakda **saboq** (o'git) bor. Ertakni o'qib bo'lgach o'zingizdan so'rang: "
                 "«Bu ertak menga nimani o'rgatdi?»"},
                {'type': 'life', 'body':
                 "«Zumrad va Qimmat» ertagi mehnat qilgan odam mukofot olishini o'rgatadi. "
                 "Bu hayotda ham shunday — harakat qilgan odam yutadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Ertak odatda qanday boshlanadi?',
                 'options': ["«Bor ekan, yo'q ekan...»", '«Bugun...»', '«Men...»'], 'answer': 0,
                 'explain': "O'zbek ertaklari an'anaviy «Bor ekan, yo'q ekan» bilan boshlanadi."},
                {'type': 'mc', 'q': 'Ertakda oxirida kim yutadi?',
                 'options': ['Yomonlik', 'Yaxshilik', 'Hech kim'], 'answer': 1,
                 'explain': 'Ertakda doim yaxshilik g\'alaba qozonadi.'},
                {'type': 'mc', 'q': "«Zumrad va Qimmat» ertagi nima haqida?",
                 'options': ['Urush haqida', 'Mehnatkashlik va yalqovlik haqida', 'Kosmos haqida'], 'answer': 1,
                 'explain': 'Zumrad mehnatkash, Qimmat yalqov edi.'},
                {'type': 'tf', 'q': 'Ertakda hayvonlar gapirishi mumkin.', 'answer': True,
                 'explain': "To'g'ri — ertakda sehrli narsalar bo'ladi."},
                {'type': 'mc', 'q': 'Ertakni kim yaratgan?',
                 'options': ['Bitta yozuvchi', 'Xalq', 'Podshoh'], 'answer': 1,
                 'explain': 'Xalq ertaklarini xalq yaratgan va og\'izdan-og\'izga o\'tkazgan.'},
                {'type': 'fill', 'q': "Har bir ertakda o'quvchiga beriladigan o'git — bu nima? (bir so'z)",
                 'answer': 'saboq', 'accept': ['saboq', 'ogit', "o'git", 'xulosa'],
                 'explain': "Ertakdan olinadigan saboq (o'git) — uning eng muhim qismi."},
            ],
            'homework': {
                'intro': 'Ertaklar bilan ishlang.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': 'Ertakda oxirida yaxshilik yutadimi yoki yomonlik?',
                     'answer': 'yaxshilik'},
                    {'id': 'h2', 'type': 'open', 'prompt': "Sizga eng yoqadigan ertak qaysi? Nomini yozing."},
                    {'id': 'h3', 'type': 'open', 'prompt': "Shu ertak sizga nimani o'rgatdi?"},
                    {'id': 'h4', 'type': 'open', 'prompt': "Ertakdagi eng yoqqan qahramoningizni yozing."},
                ],
            },
        },
        {
            'slug': 'sherlar',
            'title': "She'r o'qish",
            'summary': "She'rning tuzilishi va ifodali o'qish",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': "She'r nima?", 'body':
                 "**She'r** — ohangdor, qofiyali yozilgan asar. She'rni o'qiganda musiqadek eshitiladi.\n\n"
                 "She'r **misra**lardan (satrlardan) iborat bo'ladi."},
                {'type': 'text', 'title': 'Qofiya nima?', 'body':
                 "**Qofiya** — misralar oxiridagi o'xshash tovushlar.\n\n"
                 "Masalan:\n"
                 "Bahor keldi bog'imiz**ga**,\n"
                 "Gul ochildi bog'imiz**da**.\n\n"
                 "«-ga» va «-da» — o'xshash eshitiladi, bu qofiya."},
                {'type': 'steps', 'title': "She'rni ifodali o'qish", 'items': [
                    "Avval she'rni ichingizda o'qib chiqing, ma'nosini tushuning.",
                    "Har bir misra oxirida biroz to'xtang.",
                    "Muhim so'zlarni ovoz bilan ajratib o'qing.",
                    "Shoshilmang — she'r sekin va ohang bilan o'qiladi.",
                    "Yod olganda misralarni bo'lib-bo'lib yodlang.",
                ]},
                {'type': 'text', 'title': "O'zbek shoirlari", 'body':
                 "**Quddus Muhammadiy** — bolalar uchun tabiat haqida she'rlar yozgan\n"
                 "**Po'lat Mo'min** — quvnoq bolalar she'rlari muallifi\n"
                 "**Zafar Diyor** — bolalarga atalgan go'zal she'rlar yozgan"},
                {'type': 'note', 'body':
                 "She'r yodlash xotirani kuchaytiradi. Haftada bitta she'r yodlab boring — "
                 "bir yilda 50 dan ortiq she'r bilasiz!"},
                {'type': 'life', 'body':
                 "Bayram va tadbirlarda she'r aytish kerak bo'ladi. Ifodali o'qiy olgan bola "
                 "hamma diqqatini tortadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "She'rning har bir satri nima deyiladi?",
                 'options': ['Misra', 'Bo\'g\'in', 'Gap'], 'answer': 0,
                 'explain': "She'rning satri — misra deb ataladi."},
                {'type': 'mc', 'q': 'Qofiya — bu nima?',
                 'options': ["Misralar oxiridagi o'xshash tovushlar", "She'r nomi", 'Shoirning ismi'], 'answer': 0,
                 'explain': "Qofiya — misra oxirlarining o'xshash yangrashi."},
                {'type': 'mc', 'q': "She'rni qanday o'qish kerak?",
                 'options': ['Juda tez', 'Sekin va ohang bilan', 'Pichirlab'], 'answer': 1,
                 'explain': "She'r sekin, ifoda va ohang bilan o'qiladi."},
                {'type': 'tf', 'q': "She'r yodlash xotirani kuchaytiradi.", 'answer': True,
                 'explain': "To'g'ri — yodlash miyani mashq qildiradi."},
                {'type': 'mc', 'q': 'Quddus Muhammadiy kim?',
                 'options': ['Sportchi', 'Bolalar shoiri', 'Olim'], 'answer': 1,
                 'explain': "U bolalar uchun tabiat haqida ko'p she'r yozgan shoir."},
                {'type': 'fill', 'q': "«bog'imizga» va «bog'imizda» — bu nima hodisasi? (bir so'z)",
                 'answer': 'qofiya', 'explain': "Misra oxirlari o'xshash — bu qofiya."},
            ],
            'homework': {
                'intro': "She'r bilan ishlang.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "She'rning bitta satri nima deb ataladi?",
                     'answer': 'misra'},
                    {'id': 'h2', 'type': 'open', 'prompt': "Yod bilgan bitta she'ringizning birinchi misrasini yozing."},
                    {'id': 'h3', 'type': 'open', 'prompt': "«kitob» so'ziga qofiya bo'ladigan so'z toping."},
                    {'id': 'h4', 'type': 'open', 'prompt': "Sizga yoqadigan shoir yoki she'r nomini yozing."},
                ],
            },
        },
        {
            'slug': 'matnni-tushunish',
            'title': 'Matnni tushunish',
            'summary': "O'qiganini tushunish va savollarga javob berish",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': "O'qish va tushunish — bir xil emas", 'body':
                 "So'zlarni o'qish oson. Lekin **tushunish** — bu boshqa narsa.\n\n"
                 "Matnni o'qib bo'lgach, o'zingizdan so'rang: «Men nima haqida o'qidim?» "
                 "Agar javob bera olmasangiz — qayta o'qish kerak."},
                {'type': 'steps', 'title': 'Matnni tushunish usuli', 'items': [
                    'Matnni birinchi marta oxirigacha o\'qing.',
                    "Tushunmagan so'zlarni belgilab qo'ying va ma'nosini so'rang.",
                    "Ikkinchi marta sekin o'qing.",
                    "O'zingizga savol bering: Kim? Nima qildi? Qayerda? Qachon? Nima uchun?",
                    "Matnni o'z so'zingiz bilan qisqacha aytib bering.",
                ]},
                {'type': 'text', 'title': "Asosiy fikr", 'body':
                 "Har bir matnda **asosiy fikr** bo'ladi — muallif aytmoqchi bo'lgan eng muhim narsa.\n\n"
                 "Asosiy fikrni topish uchun so'rang: «Bu matn nima haqida?» "
                 "Javobni bitta gap bilan ayting."},
                {'type': 'example', 'title': 'Mashq qilamiz', 'body':
                 "Matn: «Anvar har kuni ertalab turib, mashq qiladi. Keyin nonushta qiladi "
                 "va maktabga boradi. U hech qachon kech qolmaydi.»\n\n"
                 "**Kim haqida?** — Anvar haqida\n"
                 "**Nima qiladi?** — Mashq qiladi, nonushta qiladi, maktabga boradi\n"
                 "**Asosiy fikr:** Anvar tartibli bola."},
                {'type': 'note', 'body':
                 "Tushunmagan so'zni tashlab ketmang! Lug'atdan qarang yoki kattalardan so'rang. "
                 "Bitta so'z butun gapning ma'nosini o'zgartirishi mumkin."},
                {'type': 'life', 'body':
                 "Masala yechishda ham matnni tushunish kerak. Ko'p bolalar matematikani emas, "
                 "masala matnini tushunmagani uchun xato qiladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "Matnni o'qib bo'lgach avval nima qilish kerak?",
                 'options': ['Yopib qo\'yish', "Nima haqida o'qiganini o'ylash", 'Boshqa matn o\'qish'], 'answer': 1,
                 'explain': "Tushunganingizni tekshirish uchun o'zingizga savol bering."},
                {'type': 'mc', 'q': "Tushunmagan so'zni nima qilish kerak?",
                 'options': ['Tashlab ketish', "Ma'nosini bilib olish", "O'chirib tashlash"], 'answer': 1,
                 'explain': "Har bir so'z ma'noga ta'sir qiladi — bilib olish kerak."},
                {'type': 'mc', 'q': 'Matnning asosiy fikri — bu nima?',
                 'options': ['Birinchi gap', 'Muallif aytmoqchi bo\'lgan eng muhim narsa', 'Eng uzun gap'], 'answer': 1,
                 'explain': 'Asosiy fikr — matnning mag\'zi.'},
                {'type': 'tf', 'q': "Matnni bir marta o'qish har doim yetarli.", 'answer': False,
                 'explain': "Yo'q — qiyin matnni 2-3 marta o'qish kerak bo'ladi."},
                {'type': 'mc', 'q': 'Matnni tushunish uchun qanday savollar beriladi?',
                 'options': ['Kim? Nima qildi? Qayerda?', 'Qancha turadi?', 'Kim yozgan?'], 'answer': 0,
                 'explain': "Kim, nima, qayerda, qachon, nima uchun — asosiy savollar."},
                {'type': 'fill', 'q': "Matn nima haqida ekanini bildiradigan eng muhim fikr — ___ fikr.",
                 'answer': 'asosiy', 'explain': "Asosiy fikr deyiladi."},
            ],
            'homework': {
                'intro': "Quyidagi matnni o'qing va savollarga javob bering:\n\n"
                         "«Dilnoza kutubxonaga bordi. U ertaklar kitobini oldi. Uyga kelib, "
                         "kechgacha o'qidi. Kitob unga juda yoqdi.»",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': 'Matnda kim haqida gapirilyapti?',
                     'answer': 'Dilnoza', 'accept': ['dilnoza']},
                    {'id': 'h2', 'type': 'text', 'prompt': 'Dilnoza qayerga bordi?',
                     'answer': 'kutubxonaga', 'accept': ['kutubxona', 'kutubxonaga']},
                    {'id': 'h3', 'type': 'text', 'prompt': 'U qanday kitob oldi?',
                     'answer': 'ertaklar', 'accept': ['ertaklar', 'ertaklar kitobi', 'ertak']},
                    {'id': 'h4', 'type': 'open', 'prompt': "Bu matnning asosiy fikri nima? O'z so'zingiz bilan yozing."},
                ],
            },
        },
    ],
}

NATURE = {
    'key': 'nature',
    'topics': [
        {
            'slug': 'jonli-jonsiz',
            'title': 'Jonli va jonsiz tabiat',
            'summary': "Atrofimizdagi olamni ikki guruhga ajratamiz",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': 'Tabiat nima?', 'body':
                 "**Tabiat** — bizni o'rab turgan hamma narsa: quyosh, havo, suv, tosh, "
                 "o'simlik, hayvon, odam.\n\n"
                 "Tabiat ikkiga bo'linadi: **jonli** va **jonsiz**."},
                {'type': 'text', 'title': 'Jonli tabiat', 'body':
                 "Jonli narsalar: **o'simliklar, hayvonlar, odamlar, mikroblar**\n\n"
                 "Jonli narsaning belgilari:\n"
                 "• Nafas oladi\n"
                 "• Ovqatlanadi\n"
                 "• O'sadi\n"
                 "• Ko'payadi\n"
                 "• Harakat qiladi\n"
                 "• Bir kun o'ladi"},
                {'type': 'text', 'title': 'Jonsiz tabiat', 'body':
                 "Jonsiz narsalar: **quyosh, havo, suv, tosh, tuproq, tog', bulut**\n\n"
                 "Ular nafas olmaydi, ovqatlanmaydi, o'smaydi va ko'paymaydi."},
                {'type': 'table', 'head': ['Belgi', 'Jonli', 'Jonsiz'], 'rows': [
                    ['Nafas oladi', 'Ha', "Yo'q"],
                    ['Ovqatlanadi', 'Ha', "Yo'q"],
                    ["O'sadi", 'Ha', "Yo'q"],
                    ['Ko\'payadi', 'Ha', "Yo'q"],
                ]},
                {'type': 'note', 'body':
                 "Diqqat! Stol, kitob, mashina — bular tabiat emas, ular **odam yasagan** narsalar. "
                 "Tabiat o'zi paydo bo'lgan narsalardir."},
                {'type': 'life', 'body':
                 "Jonli tabiatga g'amxo'rlik qiling: daraxtni sindirmang, hayvonni ranjitmang. "
                 "Ular ham his qiladi va yashashni xohlaydi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Quyidagilardan qaysi biri jonli tabiat?',
                 'options': ['Tosh', 'Daraxt', 'Suv', 'Bulut'], 'answer': 1,
                 'explain': "Daraxt o'sadi, nafas oladi — demak jonli."},
                {'type': 'mc', 'q': 'Qaysi biri jonsiz tabiat?',
                 'options': ['Mushuk', 'Gul', 'Tog\'', 'Odam'], 'answer': 2,
                 'explain': "Tog' o'smaydi va nafas olmaydi — jonsiz."},
                {'type': 'mc', 'q': 'Jonli narsaning belgisi qaysi?',
                 'options': ['Qattiq bo\'lish', "O'sish va ko'payish", 'Og\'ir bo\'lish'], 'answer': 1,
                 'explain': "O'sish, ko'payish, nafas olish — jonlilik belgilari."},
                {'type': 'tf', 'q': 'Mashina jonli tabiatga kiradi.', 'answer': False,
                 'explain': "Yo'q — mashina odam yasagan narsa, tabiat emas."},
                {'type': 'mc', 'q': 'Odam qaysi guruhga kiradi?',
                 'options': ['Jonli tabiat', 'Jonsiz tabiat', 'Hech qaysi'], 'answer': 0,
                 'explain': 'Odam nafas oladi, o\'sadi — jonli tabiat.'},
                {'type': 'fill', 'q': "Quyosh jonli tabiatgami yoki jonsizga kiradi? (bir so'z)",
                 'answer': 'jonsiz', 'explain': 'Quyosh nafas olmaydi, o\'smaydi — jonsiz.'},
            ],
            'homework': {
                'intro': 'Tabiatni kuzating.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "Gul jonlimi yoki jonsizmi?", 'answer': 'jonli'},
                    {'id': 'h2', 'type': 'text', 'prompt': 'Tosh jonlimi yoki jonsizmi?', 'answer': 'jonsiz'},
                    {'id': 'h3', 'type': 'open', 'prompt': "Hovlingizdan 3 ta jonli narsani toping va yozing."},
                    {'id': 'h4', 'type': 'open', 'prompt': "3 ta jonsiz tabiat narsasini yozing."},
                ],
            },
        },
        {
            'slug': 'osimliklar',
            'title': "O'simliklar",
            'summary': "O'simlikning qismlari va ularning vazifasi",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': "O'simlik qismlari", 'body':
                 "Har bir o'simlikda asosan 5 ta qism bo'ladi:\n\n"
                 "🌱 **Ildiz** — yerda, suv va oziq so'radi\n"
                 "🌿 **Poya** — o'simlikni ko'taradi, suvni yuqoriga olib chiqadi\n"
                 "🍃 **Barg** — nafas oladi va oziq tayyorlaydi\n"
                 "🌸 **Gul** — urug' hosil qilish uchun\n"
                 "🍎 **Meva** — ichida urug' bo'ladi"},
                {'type': 'text', 'title': "O'simlikka nima kerak?", 'body':
                 "O'simlik o'sishi uchun 4 narsa kerak:\n\n"
                 "☀️ **Yorug'lik** (quyosh)\n"
                 "💧 **Suv**\n"
                 "🌬️ **Havo**\n"
                 "🟤 **Tuproq** (oziq moddalar)\n\n"
                 "Bulardan biri yo'q bo'lsa, o'simlik qurib qoladi."},
                {'type': 'text', 'title': "O'simlik turlari", 'body':
                 "**Daraxt** — yo'g'on va baland poyali (olma, terak, tut)\n"
                 "**Buta** — past, ko'p ingichka poyali (na'matak, atirgul)\n"
                 "**O't** — yumshoq, past poyali (maysa, jag'-jag')"},
                {'type': 'note', 'body':
                 "O'simliklar bizga **kislorod** beradi — biz nafas oladigan havo. "
                 "Shuning uchun daraxt ekish juda foydali ish."},
                {'type': 'life', 'body':
                 "Uyda gul o'stiring: har kuni suv quying, yorug' joyga qo'ying. "
                 "Gulning o'sishini kuzatish juda qiziqarli."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "O'simlikning qaysi qismi suv so'radi?",
                 'options': ['Barg', 'Gul', 'Ildiz', 'Meva'], 'answer': 2,
                 'explain': "Ildiz yerdan suv va oziq moddalarni so'radi."},
                {'type': 'mc', 'q': "O'simlik o'sishi uchun nima kerak emas?",
                 'options': ['Suv', "Yorug'lik", 'Musiqa', 'Havo'], 'answer': 2,
                 'explain': "Musiqa kerak emas. Suv, yorug'lik, havo va tuproq kerak."},
                {'type': 'mc', 'q': 'Mevaning ichida nima bo\'ladi?',
                 'options': ['Ildiz', "Urug'", 'Barg'], 'answer': 1,
                 'explain': "Meva ichida urug' bo'ladi — undan yangi o'simlik o'sadi."},
                {'type': 'tf', 'q': "O'simliklar bizga kislorod beradi.", 'answer': True,
                 'explain': "To'g'ri — shuning uchun daraxt ekish muhim."},
                {'type': 'mc', 'q': 'Olma daraxti qaysi guruhga kiradi?',
                 'options': ['Daraxt', 'Buta', "O't"], 'answer': 0,
                 'explain': "Olma — yo'g'on va baland poyali daraxt."},
                {'type': 'fill', 'q': "O'simlikning nafas oladigan va oziq tayyorlaydigan qismi — ___",
                 'answer': 'barg', 'explain': 'Barg nafas oladi va oziq tayyorlaydi.'},
            ],
            'homework': {
                'intro': "O'simliklarni kuzating.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "O'simlikning yerdagi qismi qanday ataladi?",
                     'answer': 'ildiz'},
                    {'id': 'h2', 'type': 'number', 'prompt': "O'simlik o'sishi uchun nechta asosiy narsa kerak?",
                     'answer': '4'},
                    {'id': 'h3', 'type': 'open', 'prompt': "Hovlingizdagi biror o'simlikni yozing va qismlarini sanang."},
                    {'id': 'h4', 'type': 'open', 'prompt': "Sizga yoqadigan meva qaysi? U qaysi daraxtda o'sadi?"},
                ],
            },
        },
        {
            'slug': 'hayvonlar',
            'title': 'Hayvonlar',
            'summary': "Yovvoyi va uy hayvonlari bilan tanishamiz",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': 'Hayvonlar qayerda yashaydi?', 'body':
                 "**Uy hayvonlari** — odam boqadi, odamga foyda keltiradi:\n"
                 "sigir (sut), qo'y (jun), tovuq (tuxum), ot (yuk tashiydi), it (qo'riqlaydi), mushuk\n\n"
                 "**Yovvoyi hayvonlar** — o'zi tabiatda yashaydi, o'ziga ovqat topadi:\n"
                 "bo'ri, tulki, ayiq, quyon, kiyik, sher, fil"},
                {'type': 'text', 'title': 'Hayvonlar nima yeydi?', 'body':
                 "**O't yeydiganlar** — quyon, sigir, qo'y, ot, kiyik\n"
                 "**Go'sht yeydiganlar** — bo'ri, sher, tulki, burgut\n"
                 "**Aralash yeydiganlar** — ayiq, cho'chqa, odam"},
                {'type': 'text', 'title': 'Hayvonlar guruhlari', 'body':
                 "🐦 **Qushlar** — pati bor, tuxum qo'yadi, uchadi (chumchuq, laylak, burgut)\n"
                 "🐟 **Baliqlar** — suvda yashaydi, jabra bilan nafas oladi\n"
                 "🐛 **Hasharotlar** — 6 ta oyoq (chumoli, asalari, kapalak)\n"
                 "🐄 **Sutemizuvchilar** — bolasini sut bilan boqadi (sigir, it, odam)"},
                {'type': 'note', 'body':
                 "Hayvonlar ham jonli — ular og'riqni sezadi. Hayvonlarni ranjitmang, "
                 "uy hayvonlariga g'amxo'rlik qiling."},
                {'type': 'life', 'body':
                 "Sigir bizga sut beradi, sutdan qatiq, pishloq, sariyog' tayyorlanadi. "
                 "Tovuq tuxum beradi. Hayvonlar hayotimizda katta o'rin tutadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Qaysi biri uy hayvoni?',
                 'options': ["Bo'ri", 'Sigir', 'Tulki', 'Ayiq'], 'answer': 1,
                 'explain': 'Sigirni odam boqadi — uy hayvoni.'},
                {'type': 'mc', 'q': 'Qaysi hayvon faqat go\'sht yeydi?',
                 'options': ['Quyon', 'Sigir', "Bo'ri", 'Ot'], 'answer': 2,
                 'explain': "Bo'ri — yirtqich hayvon, go'sht yeydi."},
                {'type': 'mc', 'q': 'Qushlarning asosiy belgisi nima?',
                 'options': ['Pati bor va tuxum qo\'yadi', 'Suvda yashaydi', '6 ta oyog\'i bor'], 'answer': 0,
                 'explain': "Qushlarning pati bor va ular tuxum qo'yadi."},
                {'type': 'tf', 'q': 'Baliq suvda jabra bilan nafas oladi.', 'answer': True,
                 'explain': "To'g'ri — baliqlar jabra orqali suvdagi kislorodni oladi."},
                {'type': 'mc', 'q': 'Hasharotlarning nechta oyog\'i bor?',
                 'options': ['4', '6', '8'], 'answer': 1,
                 'explain': "Hasharotlarning 6 ta oyog'i bor."},
                {'type': 'fill', 'q': "Tovuq bizga nima beradi? (bir so'z)",
                 'answer': 'tuxum', 'explain': 'Tovuq tuxum beradi.'},
            ],
            'homework': {
                'intro': 'Hayvonlar haqida.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': 'Sigir uy hayvonimi yoki yovvoyimi?',
                     'answer': 'uy', 'accept': ['uy', 'uy hayvoni']},
                    {'id': 'h2', 'type': 'text', 'prompt': 'Qaysi hayvon bizga sut beradi?',
                     'answer': 'sigir'},
                    {'id': 'h3', 'type': 'open', 'prompt': "3 ta yovvoyi hayvon nomini yozing."},
                    {'id': 'h4', 'type': 'open', 'prompt': "Sizga yoqadigan hayvon qaysi va nima uchun?"},
                ],
            },
        },
        {
            'slug': 'fasllar',
            'title': 'Fasllar',
            'summary': "Yilning to'rt fasli va ularning belgilari",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': "Yilda nechta fasl bor?", 'body':
                 "Bir yilda **4 ta fasl** bor. Har bir fasl **3 oy** davom etadi.\n\n"
                 "Bir yilda jami 12 oy: 4 × 3 = 12"},
                {'type': 'text', 'title': '🌸 Bahor (mart, aprel, may)', 'body':
                 "Havo isiydi, qor eriydi.\n"
                 "Daraxtlar gullaydi, maysalar ko'karadi.\n"
                 "Qushlar issiq o'lkalardan qaytadi.\n"
                 "Dehqonlar ekin ekadi. Navro'z bayrami nishonlanadi."},
                {'type': 'text', 'title': "☀️ Yoz (iyun, iyul, avgust)", 'body':
                 "Eng issiq fasl. Kun uzun, tun qisqa.\n"
                 "Mevalar pishadi: o'rik, shaftoli, uzum, tarvuz.\n"
                 "O'quvchilar ta'tilda bo'ladi."},
                {'type': 'text', 'title': '🍂 Kuz (sentabr, oktabr, noyabr)', 'body':
                 "Havo salqinlashadi, yomg'ir ko'p yog'adi.\n"
                 "Barglar sarg'ayadi va to'kiladi.\n"
                 "Hosil yig'ib olinadi. Qushlar issiq o'lkalarga uchib ketadi.\n"
                 "1-sentabrda o'quv yili boshlanadi."},
                {'type': 'text', 'title': '❄️ Qish (dekabr, yanvar, fevral)', 'body':
                 "Eng sovuq fasl. Qor yog'adi, suv muzlaydi.\n"
                 "Kun qisqa, tun uzun.\n"
                 "Daraxtlar barglarsiz turadi. Ba'zi hayvonlar uyquga ketadi."},
                {'type': 'table', 'head': ['Fasl', 'Oylar', 'Belgi'], 'rows': [
                    ['Bahor', 'Mart, aprel, may', 'Gullar ochiladi'],
                    ['Yoz', 'Iyun, iyul, avgust', 'Issiq, mevalar pishadi'],
                    ['Kuz', 'Sentabr, oktabr, noyabr', "Barglar to'kiladi"],
                    ['Qish', 'Dekabr, yanvar, fevral', 'Qor yog\'adi'],
                ]},
                {'type': 'life', 'body':
                 "Fasllarga qarab kiyinamiz: qishda paltoyu qalpoq, yozda yengil kiyim. "
                 "Fasl bizning kundalik hayotimizni belgilaydi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Bir yilda nechta fasl bor?',
                 'options': ['2', '3', '4', '12'], 'answer': 2,
                 'explain': 'Bahor, yoz, kuz, qish — 4 ta fasl.'},
                {'type': 'mc', 'q': 'Har bir fasl necha oy davom etadi?',
                 'options': ['1', '2', '3', '4'], 'answer': 2,
                 'explain': 'Har fasl 3 oy: 4 × 3 = 12 oy.'},
                {'type': 'mc', 'q': 'Barglar qaysi faslda to\'kiladi?',
                 'options': ['Bahor', 'Yoz', 'Kuz', 'Qish'], 'answer': 2,
                 'explain': 'Kuzda barglar sarg\'ayib to\'kiladi.'},
                {'type': 'tf', 'q': 'Qish eng sovuq fasl.', 'answer': True,
                 'explain': "To'g'ri — qishda qor yog'adi va suv muzlaydi."},
                {'type': 'mc', 'q': 'Navro\'z bayrami qaysi faslda nishonlanadi?',
                 'options': ['Bahor', 'Yoz', 'Kuz', 'Qish'], 'answer': 0,
                 'explain': "Navro'z — 21-martda, bahor faslida."},
                {'type': 'fill', 'q': "Bir yilda nechta oy bor? (raqam bilan)",
                 'answer': '12', 'explain': '4 fasl × 3 oy = 12 oy.'},
            ],
            'homework': {
                'intro': 'Fasllar haqida vazifalar.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': 'Bir yilda nechta fasl bor?', 'answer': '4'},
                    {'id': 'h2', 'type': 'text', 'prompt': 'Qor qaysi faslda yog\'adi?', 'answer': 'qish',
                     'accept': ['qish', 'qishda']},
                    {'id': 'h3', 'type': 'open', 'prompt': "Sizga qaysi fasl yoqadi va nima uchun?"},
                    {'id': 'h4', 'type': 'open', 'prompt': "Hozir qaysi fasl? Uning 3 ta belgisini yozing."},
                ],
            },
        },
    ],
}
