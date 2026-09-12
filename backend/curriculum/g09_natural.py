# -*- coding: utf-8 -*-
"""9-sinf — Kimyo va Biologiya."""

CHEMISTRY = {
    'key': 'chemistry',
    'topics': [
        {
            'slug': 'atom-tuzilishi',
            'title': 'Atom tuzilishi',
            'summary': "Proton, neytron, elektron va davriy jadval",
            'duration': 24,
            'lesson': [
                {'type': 'text', 'title': 'Atom nima?', 'body':
                 "**Atom** — moddaning kimyoviy xossalarini saqlaydigan eng kichik zarrasi.\n\n"
                 "Atom ikki qismdan iborat: **yadro** va **elektron qobiq**."},
                {'type': 'table', 'head': ['Zarra', 'Joyi', 'Zaryadi', 'Massasi'], 'rows': [
                    ['Proton (p)', 'Yadroda', '+1', '1 a.b.'],
                    ['Neytron (n)', 'Yadroda', '0', '1 a.b.'],
                    ['Elektron (e)', 'Qobiqda', '−1', 'juda kichik'],
                ]},
                {'type': 'text', 'title': 'Muhim qoidalar', 'body':
                 "**Tartib raqami (Z)** = protonlar soni = elektronlar soni\n"
                 "**Massa soni (A)** = protonlar + neytronlar\n"
                 "**Neytronlar soni** = A − Z\n\n"
                 "Atom neytral — musbat va manfiy zaryadlar teng."},
                {'type': 'example', 'title': 'Misol: Natriy (Na)', 'body':
                 "Davriy jadvalda: tartib raqami **11**, massa soni **23**\n\n"
                 "Protonlar = **11**\n"
                 "Elektronlar = **11**\n"
                 "Neytronlar = 23 − 11 = **12**"},
                {'type': 'text', 'title': 'Elektron qobiqlar', 'body':
                 "Elektronlar yadro atrofida qatlamlarda (qobiqlarda) joylashadi.\n\n"
                 "Har bir qobiqda ko'pi bilan: **2n²** ta elektron\n"
                 "1-qobiq: 2 ta\n"
                 "2-qobiq: 8 ta\n"
                 "3-qobiq: 18 ta\n\n"
                 "**Tashqi qobiqdagi** elektronlar kimyoviy xossalarni belgilaydi — "
                 "ular **valent elektronlar** deyiladi."},
                {'type': 'text', 'title': 'Davriy jadval', 'body':
                 "**D. I. Mendeleyev** 1869-yilda kashf etgan.\n\n"
                 "**Davr** (gorizontal qator) — elektron qobiqlar soni\n"
                 "**Guruh** (vertikal ustun) — tashqi qobiqdagi elektronlar soni\n\n"
                 "Bir guruhdagi elementlar **o'xshash xossaga** ega."},
                {'type': 'note', 'body':
                 "Davriy qonun: elementlarning xossalari ularning **yadro zaryadiga** "
                 "(tartib raqamiga) davriy bog'liq."},
                {'type': 'life', 'body':
                 "Osh tuzi — NaCl: natriy va xlor atomlaridan. "
                 "Suv — H₂O: ikki vodorod va bitta kislorod. "
                 "Butun olam atomlardan tuzilgan."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Protonning zaryadi qanday?',
                 'options': ['Musbat', 'Manfiy', 'Neytral'], 'answer': 0,
                 'explain': 'Proton musbat zaryadli (+1).'},
                {'type': 'mc', 'q': 'Tartib raqami nimani bildiradi?',
                 'options': ['Neytronlar sonini', 'Protonlar sonini', 'Massani'], 'answer': 1,
                 'explain': 'Tartib raqami = protonlar soni = elektronlar soni.'},
                {'type': 'mc', 'q': "Kislorod (Z = 8, A = 16) da nechta neytron bor?",
                 'options': ['8', '16', '24'], 'answer': 0,
                 'explain': 'N = A − Z = 16 − 8 = 8.'},
                {'type': 'mc', 'q': 'Davriy jadvalni kim yaratgan?',
                 'options': ['Nyuton', 'Mendeleyev', 'Eynshteyn'], 'answer': 1,
                 'explain': 'D. I. Mendeleyev, 1869-yil.'},
                {'type': 'tf', 'q': "Atom neytral zarra — protonlar va elektronlar soni teng.",
                 'answer': True, 'explain': "To'g'ri."},
                {'type': 'fill', 'q': "Birinchi elektron qobiqda ko'pi bilan nechta elektron bo'ladi?",
                 'answer': '2', 'explain': '2n² = 2·1² = 2.'},
            ],
            'homework': {
                'intro': 'Atom tuzilishi bo\'yicha.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "Uglerod Z = 6. Nechta elektroni bor?",
                     'answer': '6'},
                    {'id': 'h2', 'type': 'number', 'prompt': "Alyuminiy Z = 13, A = 27. Nechta neytron bor?",
                     'answer': '14'},
                    {'id': 'h3', 'type': 'text', 'prompt': "Yadroda qaysi ikki zarra bor? (biror birini yozing)",
                     'answer': 'proton', 'accept': ['proton', 'neytron', 'proton va neytron']},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Davriy jadvalda davr va guruh nimani bildiradi?"},
                ],
            },
        },
        {
            'slug': 'kimyoviy-boglanish',
            'title': "Kimyoviy bog'lanish",
            'summary': "Ion va kovalent bog'lanish turlari",
            'duration': 22,
            'lesson': [
                {'type': 'text', 'title': "Nima uchun atomlar birikadi?", 'body':
                 "Atomlar **barqaror** holatga intiladi. Barqarorlik uchun tashqi qobiqda "
                 "**8 ta elektron** bo'lishi kerak (oktet qoidasi).\n\n"
                 "Shuning uchun atomlar elektron beradi, oladi yoki bo'lishadi — "
                 "natijada **kimyoviy bog'lanish** hosil bo'ladi."},
                {'type': 'text', 'title': "Ion bog'lanish", 'body':
                 "Metall elektronni **beradi**, metallmas **oladi**. "
                 "Natijada zaryadlangan **ionlar** hosil bo'lib, bir-birini tortadi.\n\n"
                 "**Katio n** — musbat ion (elektron bergan): Na⁺\n"
                 "**Anion** — manfiy ion (elektron olgan): Cl⁻"},
                {'type': 'example', 'title': "NaCl hosil bo'lishi", 'body':
                 "Na atomining tashqi qobig'ida 1 ta elektron bor — uni berish oson.\n"
                 "Cl atomining tashqi qobig'ida 7 ta — bittasi yetishmaydi.\n\n"
                 "Na → Na⁺ + e⁻\n"
                 "Cl + e⁻ → Cl⁻\n\n"
                 "Na⁺ va Cl⁻ bir-birini tortadi → **NaCl** (osh tuzi)"},
                {'type': 'text', 'title': "Kovalent bog'lanish", 'body':
                 "Ikki metallmas atom elektronlarni **bo'lishib** oladi — "
                 "umumiy elektron juftligi hosil bo'ladi.\n\n"
                 "**Qutbsiz kovalent** — bir xil atomlar orasida: H₂, O₂, N₂, Cl₂\n"
                 "**Qutbli kovalent** — har xil atomlar orasida: H₂O, HCl, NH₃"},
                {'type': 'text', 'title': 'Elektromanfiylik', 'body':
                 "**Elektromanfiylik** — atomning elektronni o'ziga tortish qobiliyati.\n\n"
                 "Eng elektromanfiy element — **ftor (F)**.\n\n"
                 "Farq katta bo'lsa → **ion** bog'lanish\n"
                 "Farq kichik bo'lsa → **qutbli kovalent**\n"
                 "Farq nol bo'lsa → **qutbsiz kovalent**"},
                {'type': 'table', 'head': ['Bog\'lanish', 'Kimlar orasida', 'Misol'], 'rows': [
                    ['Ion', 'Metall + metallmas', 'NaCl, KBr, CaO'],
                    ['Qutbli kovalent', 'Har xil metallmas', 'H₂O, HCl'],
                    ['Qutbsiz kovalent', 'Bir xil atomlar', 'H₂, O₂, N₂'],
                    ['Metall', 'Metall + metall', 'Fe, Cu, Al'],
                ]},
                {'type': 'note', 'body':
                 "Bog'lanish turini aniqlash: modda **metall va metallmasdan** iborat bo'lsa — "
                 "ion; **faqat metallmaslardan** — kovalent."},
                {'type': 'life', 'body':
                 "Suvning qutbli bo'lishi tufayli u tuzni eritadi. "
                 "Shuning uchun osh tuzi suvda eriydi, lekin yog'da erimaydi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "NaCl da qanday bog'lanish bor?",
                 'options': ['Ion', 'Kovalent', 'Metall'], 'answer': 0,
                 'explain': 'Na — metall, Cl — metallmas: ion bog\'lanish.'},
                {'type': 'mc', 'q': "H₂ molekulasida qanday bog'lanish?",
                 'options': ['Ion', 'Qutbsiz kovalent', 'Qutbli kovalent'], 'answer': 1,
                 'explain': 'Bir xil atomlar — qutbsiz kovalent.'},
                {'type': 'mc', 'q': 'Musbat zaryadlangan ion qanday ataladi?',
                 'options': ['Anion', 'Kation', 'Neytron'], 'answer': 1,
                 'explain': 'Kation — musbat ion.'},
                {'type': 'mc', 'q': 'Eng elektromanfiy element qaysi?',
                 'options': ['Kislorod', 'Ftor', 'Natriy'], 'answer': 1,
                 'explain': 'Ftor (F) — eng elektromanfiy.'},
                {'type': 'tf', 'q': "H₂O da qutbli kovalent bog'lanish bor.", 'answer': True,
                 'explain': "To'g'ri — har xil metallmaslar orasida."},
                {'type': 'fill', 'q': "Barqarorlik uchun tashqi qobiqda nechta elektron bo'lishi kerak?",
                 'answer': '8', 'explain': 'Oktet qoidasi — 8 ta elektron.'},
            ],
            'homework': {
                'intro': "Bog'lanish turini aniqlang.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "KCl da qanday bog'lanish? (ion/kovalent)",
                     'answer': 'ion'},
                    {'id': 'h2', 'type': 'text', 'prompt': "O₂ da qanday bog'lanish? (ion/kovalent)",
                     'answer': 'kovalent'},
                    {'id': 'h3', 'type': 'text', 'prompt': "Elektron olgan ion nima deyiladi?",
                     'answer': 'anion'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Nima uchun atomlar bir-biri bilan birikadi? Tushuntiring."},
                ],
            },
        },
        {
            'slug': 'reaksiyalar',
            'title': 'Kimyoviy reaksiyalar',
            'summary': "Reaksiya turlari va tenglamalarni tenglashtirish",
            'duration': 24,
            'lesson': [
                {'type': 'text', 'title': 'Kimyoviy reaksiya', 'body':
                 "**Kimyoviy reaksiya** — bir moddadan boshqa modda hosil bo'lishi.\n\n"
                 "Belgilari: rang o'zgarishi, gaz ajralishi, cho'kma tushishi, "
                 "issiqlik chiqishi yoki yutilishi."},
                {'type': 'text', 'title': 'Reaksiya turlari', 'body':
                 "**Birikish:** A + B → AB\n"
                 "2H₂ + O₂ → 2H₂O\n\n"
                 "**Parchalanish:** AB → A + B\n"
                 "2H₂O → 2H₂ + O₂\n\n"
                 "**O'rin olish:** A + BC → AC + B\n"
                 "Zn + 2HCl → ZnCl₂ + H₂\n\n"
                 "**Almashinish:** AB + CD → AD + CB\n"
                 "NaOH + HCl → NaCl + H₂O"},
                {'type': 'text', 'title': 'Massa saqlanish qonuni', 'body':
                 "**Lomonosov–Lavuazye qonuni:**\n\n"
                 "Reaksiyaga kirishgan moddalar massasi hosil bo'lgan moddalar "
                 "massasiga **teng**.\n\n"
                 "Sababi: atomlar yo'qolmaydi va paydo bo'lmaydi — faqat qayta joylashadi. "
                 "Shuning uchun tenglamani **tenglashtirish** kerak."},
                {'type': 'steps', 'title': 'Tenglashtirish tartibi', 'items': [
                    "Reaksiya sxemasini yozing.",
                    "Har bir element atomlarini chap va o'ng tomonda sanang.",
                    "Koeffitsiyent qo'yib tenglashtiring (indeksni O'ZGARTIRMANG!).",
                    "Metallardan boshlang, vodorod va kislorodni oxirida tenglang.",
                    "Yakunda barcha atomlarni qayta sanab tekshiring.",
                ]},
                {'type': 'example', 'title': "Tenglashtiramiz: H₂ + O₂ → H₂O", 'body':
                 "Chapda: H = 2, O = 2\n"
                 "O'ngda: H = 2, O = 1 → kislorod teng emas\n\n"
                 "H₂O oldiga 2 qo'yamiz:\n"
                 "H₂ + O₂ → **2**H₂O\n"
                 "Endi o'ngda H = 4, O = 2\n\n"
                 "H₂ oldiga 2 qo'yamiz:\n"
                 "**2**H₂ + O₂ → **2**H₂O\n\n"
                 "Tekshirish: chapda H=4, O=2; o'ngda H=4, O=2 ✓"},
                {'type': 'note', 'body':
                 "**Diqqat!** Indeksni (pastdagi kichik raqam) o'zgartirish mumkin emas — "
                 "u moddaning o'zini o'zgartiradi. Faqat **koeffitsiyent** (oldidagi katta raqam) "
                 "qo'yiladi.\n\n"
                 "H₂O — suv, H₂O₂ — vodorod peroksid. Butunlay boshqa moddalar!"},
                {'type': 'life', 'body':
                 "Non pishirish, temirning zanglashi, ovqat hazm bo'lishi, "
                 "o'tin yonishi — hammasi kimyoviy reaksiya."},
            ],
            'quiz': [
                {'type': 'mc', 'q': '2H₂ + O₂ → 2H₂O qanday reaksiya?',
                 'options': ['Birikish', 'Parchalanish', 'Almashinish'], 'answer': 0,
                 'explain': "Ikki moddadan bitta modda hosil bo'ldi — birikish."},
                {'type': 'mc', 'q': 'Massa saqlanish qonunini kim kashf etgan?',
                 'options': ['Mendeleyev', 'Lomonosov va Lavuazye', 'Nyuton'], 'answer': 1,
                 'explain': "Lomonosov va Lavuazye."},
                {'type': 'mc', 'q': "Zn + 2HCl → ZnCl₂ + H₂ qanday reaksiya?",
                 'options': ['Birikish', "O'rin olish", 'Parchalanish'], 'answer': 1,
                 'explain': "Zn vodorod o'rnini oldi — o'rin olish."},
                {'type': 'mc', 'q': "Tenglashtirishda nimani o'zgartirish MUMKIN EMAS?",
                 'options': ['Koeffitsiyentni', 'Indeksni', 'Ikkalasini ham'], 'answer': 1,
                 'explain': "Indeks moddani o'zgartiradi — unga tegmaymiz."},
                {'type': 'tf', 'q': "Reaksiyada atomlar soni saqlanadi.", 'answer': True,
                 'explain': "To'g'ri — massa saqlanish qonuni."},
                {'type': 'fill', 'q': "2H₂ + O₂ → 2H₂O tenglamasida chap tomonda nechta H atomi bor?",
                 'answer': '4', 'explain': '2 × 2 = 4 ta vodorod atomi.'},
            ],
            'homework': {
                'intro': 'Reaksiyalar bo\'yicha.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "CaO + H₂O → Ca(OH)₂ qanday reaksiya?",
                     'answer': 'birikish'},
                    {'id': 'h2', 'type': 'number',
                     'prompt': "2H₂O → 2H₂ + O₂ da o'ng tomonda nechta kislorod atomi bor?",
                     'answer': '2'},
                    {'id': 'h3', 'type': 'text',
                     'prompt': "Tenglashtirishda faqat nimani qo'yish mumkin? (bir so'z)",
                     'answer': 'koeffitsiyent'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Kundalik hayotdan 2 ta kimyoviy reaksiyaga misol keltiring."},
                ],
            },
        },
    ],
}

BIOLOGY = {
    'key': 'biology',
    'topics': [
        {
            'slug': 'hujayra',
            'title': 'Hujayra tuzilishi',
            'summary': "Hujayra qismlari va ularning vazifalari",
            'duration': 22,
            'lesson': [
                {'type': 'text', 'title': 'Hujayra — hayot birligi', 'body':
                 "**Hujayra** — barcha tirik organizmlarning tuzilish va faoliyat birligi.\n\n"
                 "1665-yilda **Robert Guk** po'kak kesimini mikroskopda ko'rib, "
                 "«cellula» (hujayra) deb nomlagan."},
                {'type': 'table', 'head': ['Qism', 'Vazifasi'], 'rows': [
                    ['Hujayra membranasi', "Himoya, modda almashinuvini boshqaradi"],
                    ['Sitoplazma', "Ichki suyuqlik, organoidlar joylashadi"],
                    ['Yadro', "Irsiy ma'lumot (DNK), hujayrani boshqaradi"],
                    ['Mitoxondriya', "Energiya ishlab chiqaradi — «elektr stansiyasi»"],
                    ['Ribosoma', "Oqsil sintezi"],
                    ['Xloroplast', "Fotosintez (faqat o'simlikda)"],
                    ['Vakuola', "Suv va oziq zaxirasi"],
                ]},
                {'type': 'text', 'title': "O'simlik va hayvon hujayrasi farqi", 'body':
                 "**Faqat o'simlik hujayrasida bor:**\n"
                 "• **Hujayra devori** (sellulozadan) — mustahkamlik beradi\n"
                 "• **Xloroplast** — yashil rang, fotosintez\n"
                 "• **Katta vakuola** — hujayraning katta qismini egallaydi\n\n"
                 "**Faqat hayvon hujayrasida:**\n"
                 "• Hujayra markazi (sentriola)\n"
                 "• Shakli o'zgaruvchan (devor yo'q)"},
                {'type': 'text', 'title': 'Yadro va DNK', 'body':
                 "**Yadro** — hujayraning boshqaruv markazi. Unda **xromosomalar** bor, "
                 "xromosomalar **DNK** dan tuzilgan.\n\n"
                 "**DNK** irsiy ma'lumotni saqlaydi — ko'z rangi, bo'y, qon guruhi "
                 "shu yerda yozilgan.\n\n"
                 "Odam hujayrasida **46 ta** xromosoma (23 juft) bor."},
                {'type': 'text', 'title': "Hujayra bo'linishi", 'body':
                 "**Mitoz** — oddiy bo'linish. Bitta hujayradan **2 ta bir xil** hujayra. "
                 "O'sish va yaralarni tuzatish uchun.\n\n"
                 "**Meyoz** — jinsiy hujayralar hosil bo'lishi. "
                 "Xromosomalar soni **ikki barobar kamayadi**."},
                {'type': 'note', 'body':
                 "Mitoxondriya — «hujayraning elektr stansiyasi». "
                 "Mushak hujayralarida ular juda ko'p, chunki mushak katta energiya talab qiladi."},
                {'type': 'life', 'body':
                 "Jarohat bitganda mitoz sodir bo'ladi — hujayralar bo'linib, "
                 "teri qayta tiklanadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Hujayrada energiya qayerda ishlab chiqariladi?',
                 'options': ['Yadroda', 'Mitoxondriyada', 'Ribosomada'], 'answer': 1,
                 'explain': "Mitoxondriya — energiya manbai."},
                {'type': 'mc', 'q': "Qaysi qism FAQAT o'simlik hujayrasida bor?",
                 'options': ['Yadro', 'Xloroplast', 'Sitoplazma'], 'answer': 1,
                 'explain': "Xloroplast — fotosintez uchun, faqat o'simlikda."},
                {'type': 'mc', 'q': 'Irsiy axborot qayerda saqlanadi?',
                 'options': ['Membranada', 'Yadroda (DNK da)', 'Vakuolada'], 'answer': 1,
                 'explain': 'Yadrodagi DNK da.'},
                {'type': 'mc', 'q': 'Odam hujayrasida nechta xromosoma bor?',
                 'options': ['23', '46', '92'], 'answer': 1,
                 'explain': '46 ta (23 juft).'},
                {'type': 'tf', 'q': "Mitoz natijasida 2 ta bir xil hujayra hosil bo'ladi.",
                 'answer': True, 'explain': "To'g'ri."},
                {'type': 'fill', 'q': "Hujayrani birinchi bo'lib kim ko'rgan? (familiyasi)",
                 'answer': 'Guk', 'accept': ['guk', 'robert guk', 'huk'],
                 'explain': 'Robert Guk, 1665-yil.'},
            ],
            'homework': {
                'intro': 'Hujayra haqida.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "Hujayraning boshqaruv markazi qaysi qism?",
                     'answer': 'yadro'},
                    {'id': 'h2', 'type': 'number', 'prompt': "Odam hujayrasidagi xromosomalar soni?",
                     'answer': '46'},
                    {'id': 'h3', 'type': 'text', 'prompt': "Fotosintez qaysi organoidda boradi?",
                     'answer': 'xloroplast'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "O'simlik va hayvon hujayrasining 2 ta farqini yozing."},
                ],
            },
        },
        {
            'slug': 'irsiyat',
            'title': 'Irsiyat asoslari',
            'summary': "Genlar, Mendel qonunlari va belgilarning o'tishi",
            'duration': 24,
            'lesson': [
                {'type': 'text', 'title': 'Irsiyat nima?', 'body':
                 "**Irsiyat** — ota-onadagi belgilarning bolalarga o'tishi.\n\n"
                 "**Gen** — DNK ning bitta belgini boshqaruvchi bo'lagi.\n"
                 "**Genotip** — organizmning barcha genlari to'plami.\n"
                 "**Fenotip** — ko'rinadigan belgilar (ko'z rangi, bo'y)."},
                {'type': 'text', 'title': 'Dominant va retsessiv', 'body':
                 "Har bir belgi uchun ikkita gen bor — biri otadan, biri onadan.\n\n"
                 "**Dominant gen (A)** — kuchli, o'zini ko'rsatadi\n"
                 "**Retsessiv gen (a)** — kuchsiz, faqat juft bo'lganda ko'rinadi\n\n"
                 "**AA** — dominant gomozigota → dominant belgi\n"
                 "**Aa** — geterozigota → dominant belgi ko'rinadi\n"
                 "**aa** — retsessiv gomozigota → retsessiv belgi"},
                {'type': 'text', 'title': 'Gregor Mendel', 'body':
                 "**Gregor Mendel** (1822–1884) — irsiyat qonunlarini kashf etgan olim. "
                 "U no'xat o'simligida tajriba o'tkazgan.\n\n"
                 "Mendel genlar haqida hech narsa bilmagan, lekin matematik hisob orqali "
                 "irsiyat qonuniyatlarini topgan."},
                {'type': 'text', 'title': 'Mendelning 1-qonuni', 'body':
                 "**Birinchi avlod bir xilligi qonuni.**\n\n"
                 "Toza liniyali ota-onalarni chatishtirsak (AA × aa), "
                 "birinchi avlod **hammasi bir xil** (Aa) bo'ladi va "
                 "**dominant belgi** ko'rinadi."},
                {'type': 'text', 'title': 'Mendelning 2-qonuni', 'body':
                 "**Belgilarning ajralish qonuni.**\n\n"
                 "Birinchi avlodni o'zaro chatishtirsak (Aa × Aa), "
                 "ikkinchi avlodda belgilar **3 : 1** nisbatda ajraladi."},
                {'type': 'example', 'title': 'Punnett katakchasi: Aa × Aa', 'body':
                 "```\n"
                 "        A        a\n"
                 "  A    AA       Aa\n"
                 "  a    Aa       aa\n"
                 "```\n\n"
                 "Natija: **AA : Aa : Aa : aa**\n\n"
                 "Genotip bo'yicha — 1 : 2 : 1\n"
                 "Fenotip bo'yicha — **3 : 1** (3 ta dominant, 1 ta retsessiv)"},
                {'type': 'note', 'body':
                 "Punnett katakchasi — irsiyat masalalarini yechishning eng oson usuli. "
                 "Yuqoriga otaning, chapga onaning gametalarini yozing."},
                {'type': 'life', 'body':
                 "Qo'ng'ir ko'z (A) ko'k ko'zga (a) nisbatan dominant. "
                 "Ikkala ota-ona qo'ng'ir ko'z (Aa) bo'lsa, bolaning ko'k ko'z bo'lish "
                 "ehtimoli 25% (aa)."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Irsiyat qonunlarini kim kashf etgan?',
                 'options': ['Darvin', 'Mendel', 'Pavlov'], 'answer': 1,
                 'explain': 'Gregor Mendel.'},
                {'type': 'mc', 'q': "O'zini ko'rsatadigan kuchli gen qanday ataladi?",
                 'options': ['Retsessiv', 'Dominant', 'Neytral'], 'answer': 1,
                 'explain': 'Dominant gen.'},
                {'type': 'mc', 'q': 'Aa × Aa chatishtirishda fenotip nisbati qanday?',
                 'options': ['1 : 1', '3 : 1', '1 : 2 : 1'], 'answer': 1,
                 'explain': 'Fenotip bo\'yicha 3 : 1.'},
                {'type': 'mc', 'q': 'Retsessiv belgi qachon ko\'rinadi?',
                 'options': ['AA bo\'lganda', 'Aa bo\'lganda', 'aa bo\'lganda'], 'answer': 2,
                 'explain': 'Faqat ikkala gen retsessiv bo\'lganda (aa).'},
                {'type': 'tf', 'q': "Genotip — organizmning genlar to'plami.", 'answer': True,
                 'explain': "To'g'ri. Fenotip esa ko'rinadigan belgilar."},
                {'type': 'fill', 'q': "Mendel qaysi o'simlikda tajriba o'tkazgan?",
                 'answer': "no'xat", 'accept': ['noxat', "no'xat", 'noʻxat', 'gorox'],
                 'explain': "No'xat o'simligida."},
            ],
            'homework': {
                'intro': 'Irsiyat bo\'yicha.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "Aa genotipi qanday ataladi? (bir so'z)",
                     'answer': 'geterozigota'},
                    {'id': 'h2', 'type': 'text', 'prompt': "Ko'rinadigan belgilar to'plami nima deyiladi?",
                     'answer': 'fenotip'},
                    {'id': 'h3', 'type': 'number',
                     'prompt': "Aa × Aa da retsessiv belgi necha foiz ehtimol bilan chiqadi?",
                     'answer': '25'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Oilangizda qaysi belgi ota-onadan o'tganini payqadingiz?"},
                ],
            },
        },
        {
            'slug': 'inson-organizmi',
            'title': 'Inson organizmi tizimlari',
            'summary': "Asosiy organ tizimlari va ularning vazifasi",
            'duration': 22,
            'lesson': [
                {'type': 'text', 'title': 'Tuzilish darajalari', 'body':
                 "**Hujayra** → **To'qima** → **Organ** → **Organ tizimi** → **Organizm**\n\n"
                 "O'xshash hujayralar to'qimani, to'qimalar organni, "
                 "organlar tizimni hosil qiladi."},
                {'type': 'table', 'head': ['Tizim', 'Asosiy organlar', 'Vazifasi'], 'rows': [
                    ['Nafas olish', "O'pka, traxeya, burun", 'Kislorod olish'],
                    ['Qon aylanish', 'Yurak, qon tomirlar', 'Modda tashish'],
                    ['Hazm qilish', "Oshqozon, ichak, jigar", 'Oziqni parchalash'],
                    ['Ayirish', 'Buyrak, siydik pufagi', 'Keraksiz moddani chiqarish'],
                    ['Asab', 'Bosh miya, orqa miya', 'Boshqarish'],
                    ['Suyak-mushak', 'Suyak, mushak', 'Harakat va himoya'],
                ]},
                {'type': 'text', 'title': 'Qon aylanish tizimi', 'body':
                 "**Yurak** — 4 kamerali nasos: 2 bo'lmacha, 2 qorincha. "
                 "Kuniga ~100 000 marta uradi.\n\n"
                 "**Arteriya** — yurakdan qonni olib ketadi\n"
                 "**Vena** — yurakka qonni qaytaradi\n"
                 "**Kapillyar** — eng mayda tomir, modda almashinuvi shu yerda\n\n"
                 "Qon tarkibi: eritrotsit (kislorod tashiydi), leykotsit (himoya), "
                 "trombotsit (qon ivishi), plazma."},
                {'type': 'text', 'title': 'Nafas olish tizimi', 'body':
                 "Havo yo'li: burun → halqum → hiqildoq → traxeya → bronx → **alveola**\n\n"
                 "**Alveola** — o'pkadagi mayda pufakcha. Aynan shu yerda "
                 "kislorod qonga o'tadi, karbonat angidrid chiqariladi.\n\n"
                 "O'pkada ~300 million alveola bor."},
                {'type': 'text', 'title': 'Hazm qilish tizimi', 'body':
                 "Og'iz → qizilo'ngach → oshqozon → ingichka ichak → yo'g'on ichak\n\n"
                 "**Og'izda** — so'lak kraxmalni parchalaydi\n"
                 "**Oshqozonda** — xlorid kislota oqsilni parchalaydi\n"
                 "**Ingichka ichakda** — asosiy so'rilish sodir bo'ladi\n"
                 "**Jigar** — zaharli moddalarni zararsizlantiradi"},
                {'type': 'note', 'body':
                 "Barcha tizimlar bir-biriga bog'liq. Nafas tizimi kislorod oladi, "
                 "qon aylanish tizimi uni hujayralarga yetkazadi, hujayra undan energiya oladi."},
                {'type': 'life', 'body':
                 "Sport bilan shug'ullanish yurakni kuchaytiradi, o'pka hajmini oshiradi. "
                 "To'g'ri ovqatlanish hazm tizimini asraydi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Yurak nechta kameradan iborat?',
                 'options': ['2', '3', '4'], 'answer': 2,
                 'explain': "2 bo'lmacha va 2 qorincha — 4 kamera."},
                {'type': 'mc', 'q': "O'pkada gaz almashinuvi qayerda sodir bo'ladi?",
                 'options': ['Traxeyada', 'Alveolada', 'Bronxda'], 'answer': 1,
                 'explain': 'Alveolalarda kislorod qonga o\'tadi.'},
                {'type': 'mc', 'q': 'Qonda kislorod tashiydigan hujayra?',
                 'options': ['Leykotsit', 'Eritrotsit', 'Trombotsit'], 'answer': 1,
                 'explain': 'Eritrotsit (qizil qon tanachasi).'},
                {'type': 'mc', 'q': "Yurakdan qonni olib ketadigan tomir?",
                 'options': ['Vena', 'Arteriya', 'Kapillyar'], 'answer': 1,
                 'explain': 'Arteriya yurakdan qonni olib ketadi.'},
                {'type': 'tf', 'q': "Jigar zaharli moddalarni zararsizlantiradi.",
                 'answer': True, 'explain': "To'g'ri — jigarning muhim vazifasi."},
                {'type': 'fill', 'q': "Oziq moddalar asosan qaysi organda so'riladi? (ichakning turi)",
                 'answer': 'ingichka', 'accept': ['ingichka ichak', 'ingichka'],
                 'explain': 'Ingichka ichakda.'},
            ],
            'homework': {
                'intro': 'Inson organizmi bo\'yicha.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "Qon aylanish tizimining markaziy organi?",
                     'answer': 'yurak'},
                    {'id': 'h2', 'type': 'text', 'prompt': "Himoya vazifasini bajaruvchi qon hujayrasi?",
                     'answer': 'leykotsit'},
                    {'id': 'h3', 'type': 'text', 'prompt': "Organizmni boshqaruvchi tizim nomi?",
                     'answer': 'asab', 'accept': ['asab', 'asab tizimi', 'nerv']},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Sog'lom bo'lish uchun 3 ta qoida yozing."},
                ],
            },
        },
    ],
}
