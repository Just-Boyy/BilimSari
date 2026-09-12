# -*- coding: utf-8 -*-
"""1-sinf o'quv dasturi."""

MATH = {
    'key': 'math',
    'topics': [
        {
            'slug': 'sonlar',
            'title': 'Sonlar',
            'summary': "1 dan 10 gacha sonlarni tanib olamiz va sanashni o'rganamiz",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': 'Son nima?', 'body':
                 "Son — bu narsalar nechtaligini bildiradigan belgi.\n\n"
                 "Stolda 3 ta olma bor desak, **3** — bu son. U olmalar nechtaligini aytib turadi."},
                {'type': 'text', 'title': '1 dan 10 gacha', 'body':
                 "Sanashni birdan boshlaymiz:\n\n"
                 "1 — bir\n2 — ikki\n3 — uch\n4 — to'rt\n5 — besh\n"
                 "6 — olti\n7 — yetti\n8 — sakkiz\n9 — to'qqiz\n10 — o'n"},
                {'type': 'example', 'title': "Sanab ko'ramiz", 'body':
                 "🍎🍎🍎 — bu yerda 3 ta olma bor.\n"
                 "⭐⭐⭐⭐⭐ — bu yerda 5 ta yulduzcha bor.\n"
                 "🐦🐦 — bu yerda 2 ta qushcha bor."},
                {'type': 'steps', 'title': "To'g'ri sanash qoidasi", 'items': [
                    "Chapdan o'ngga qarab sana.",
                    "Har bir narsani faqat BIR MARTA sana.",
                    "Hech bir narsani tashlab ketma.",
                    "Oxirgi aytgan soning — javob bo'ladi.",
                ]},
                {'type': 'text', 'title': 'Qaysi son katta?', 'body':
                 "Sanaganda keyin aytiladigan son — kattaroq bo'ladi.\n\n"
                 "5 soni 3 sonidan katta, chunki sanaganda 5 keyinroq keladi.\n"
                 "2 soni 7 sonidan kichik."},
                {'type': 'note', 'body':
                 "Katta sonni ko'rsatish uchun **>** belgisi, kichikni ko'rsatish uchun **<** belgisi ishlatiladi. "
                 "Belgining ochiq tomoni doim katta songa qaraydi: 7 > 4, 3 < 8."},
                {'type': 'life', 'body':
                 "Uyda ham sanash kerak bo'ladi: dasturxonda nechta likopcha bor, "
                 "sumkangizda nechta daftar bor, oilangizda nechta kishi bor — hammasi sanash."},
            ],
            'quiz': [
                {'type': 'mc', 'q': '🍎🍎🍎🍎 — bu yerda nechta olma bor?',
                 'options': ['3', '4', '5', '6'], 'answer': 1,
                 'explain': "Sanaymiz: bir, ikki, uch, to'rt. Javob — 4."},
                {'type': 'mc', 'q': '7 sonidan keyin qaysi son keladi?',
                 'options': ['6', '8', '9', '10'], 'answer': 1,
                 'explain': 'Sanash tartibi: 6, 7, **8**, 9, 10.'},
                {'type': 'mc', 'q': 'Qaysi son kattaroq: 9 yoki 5?',
                 'options': ['5', '9', 'Teng', "Bilib bo'lmaydi"], 'answer': 1,
                 'explain': 'Sanaganda 9 keyinroq keladi, demak 9 kattaroq.'},
                {'type': 'tf', 'q': '10 soni 1 dan 10 gacha sanoqdagi eng katta son.',
                 'answer': True,
                 'explain': "To'g'ri. 1 dan 10 gacha sanaganda oxirgisi — 10."},
                {'type': 'fill', 'q': "Bo'sh joyni to'ldiring: 4, 5, ___, 7",
                 'answer': '6', 'accept': ['olti'],
                 'explain': '5 dan keyin 6 keladi.'},
                {'type': 'mc', 'q': '3 ___ 8 — qaysi belgi to\'g\'ri?',
                 'options': ['>', '<', '='], 'answer': 1,
                 'explain': '3 kichik, 8 katta. Shuning uchun 3 < 8.'},
            ],
            'homework': {
                'intro': 'Uy ishini bajaring. Javoblarni raqam bilan yozing.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': '⭐⭐⭐⭐⭐⭐ — nechta yulduzcha bor?',
                     'answer': '6', 'hint': 'Chapdan boshlab sanang.'},
                    {'id': 'h2', 'type': 'number', 'prompt': '2 sonidan keyin keladigan sonni yozing.',
                     'answer': '3', 'hint': 'Sanash tartibini eslang.'},
                    {'id': 'h3', 'type': 'number', 'prompt': '1 dan 10 gacha sanoqdagi eng katta sonni yozing.',
                     'answer': '10'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': 'Uyingizdagi biror narsani sanang (masalan: derazalar, stullar). Nimani sanadingiz va nechta chiqdi?'},
                ],
            },
        },
        {
            'slug': 'qoshish-ayirish',
            'title': "Qo'shish va ayirish",
            'summary': "10 ichida qo'shish va ayirishni o'rganamiz",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': "Qo'shish nima?", 'body':
                 "Qo'shish — bu narsalarni **birlashtirish**.\n\n"
                 "Sizda 2 ta olma bor edi, onangiz yana 3 ta berdi. Endi hammasi bo'lib nechta?\n"
                 "2 va 3 ni birlashtiramiz — 5 ta bo'ladi."},
                {'type': 'formula', 'body': '2 + 3 = 5'},
                {'type': 'text', 'title': "Qo'shishning qismlari", 'body':
                 "**2** — birinchi qo'shiluvchi\n"
                 "**3** — ikkinchi qo'shiluvchi\n"
                 "**5** — yig'indi (javob)\n\n"
                 "**+** belgisi «qo'shish», **=** belgisi «teng» degani."},
                {'type': 'example', 'title': "Barmoq bilan qo'shamiz", 'body':
                 "4 + 3 = ?\n\n"
                 "Avval 4 ni yodda tutamiz. Keyin 3 ta barmoqni qo'shib sanaymiz:\n"
                 "4 → 5 → 6 → 7\n\n"
                 "Javob: 4 + 3 = 7"},
                {'type': 'text', 'title': 'Ayirish nima?', 'body':
                 "Ayirish — bu **olib tashlash**.\n\n"
                 "Sizda 7 ta shirinlik bor edi, 2 tasini yedingiz. Nechta qoldi?\n"
                 "7 dan 2 ni olib tashlaymiz — 5 ta qoladi."},
                {'type': 'formula', 'body': '7 − 2 = 5'},
                {'type': 'steps', 'title': 'Ayirishni qanday bajaramiz', 'items': [
                    'Katta sondan boshlaymiz (7).',
                    "Ayiriladigan son qancha bo'lsa, shuncha orqaga sanaymiz.",
                    "7 dan orqaga: 6, 5. Ikki marta orqaga sandik.",
                    'Javob — 5.',
                ]},
                {'type': 'note', 'body':
                 "Qo'shishda javob **kattalashadi**, ayirishda javob **kichrayadi**. "
                 "Agar ayirganda javob kattalashsa — xato qilgansiz, qaytadan tekshiring."},
                {'type': 'table', 'head': ['Misol', 'Javob'], 'rows': [
                    ['1 + 1', '2'], ['3 + 4', '7'], ['5 + 5', '10'],
                    ['6 − 1', '5'], ['9 − 4', '5'], ['10 − 7', '3'],
                ]},
                {'type': 'life', 'body':
                 "Do'konda 5000 so'm bor edi, 2000 so'mlik non oldingiz. "
                 "Qancha qoldi? 5000 − 2000 = 3000 so'm. Ayirish har kuni kerak bo'ladi!"},
            ],
            'quiz': [
                {'type': 'mc', 'q': '3 + 4 = ?', 'options': ['6', '7', '8', '5'], 'answer': 1,
                 'explain': '3 dan boshlab 4 ta oldinga sanaymiz: 4, 5, 6, 7.'},
                {'type': 'mc', 'q': '9 − 3 = ?', 'options': ['5', '6', '7', '4'], 'answer': 1,
                 'explain': '9 dan orqaga 3 marta: 8, 7, 6.'},
                {'type': 'mc', 'q': 'Sizda 4 ta daftar bor edi, yana 2 ta oldingiz. Hammasi nechta?',
                 'options': ['2', '5', '6', '8'], 'answer': 2,
                 'explain': 'Birlashtiramiz: 4 + 2 = 6.'},
                {'type': 'tf', 'q': 'Ayirganda javob har doim kichrayadi.', 'answer': True,
                 'explain': "To'g'ri — ayirish olib tashlash demak, shuning uchun natija kichrayadi."},
                {'type': 'fill', 'q': "5 + ___ = 8. Bo'sh joyga qaysi son kerak?",
                 'answer': '3', 'accept': ['uch'],
                 'explain': '5 dan 8 gacha 3 ta qadam bor: 6, 7, 8.'},
                {'type': 'mc', 'q': '10 − 10 = ?', 'options': ['0', '1', '10', '20'], 'answer': 0,
                 'explain': 'Hammasini olib tashlasak, hech narsa qolmaydi — 0.'},
            ],
            'homework': {
                'intro': 'Misollarni yeching va javoblarni yozing.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': '6 + 2 = ?', 'answer': '8'},
                    {'id': 'h2', 'type': 'number', 'prompt': '8 − 5 = ?', 'answer': '3'},
                    {'id': 'h3', 'type': 'number', 'prompt': "Bog'da 3 ta qush o'tirgan edi, yana 4 tasi uchib keldi. Hammasi nechta qush bo'ldi?",
                     'answer': '7', 'hint': "Qo'shish kerak."},
                    {'id': 'h4', 'type': 'number', 'prompt': 'Savatda 9 ta olma bor edi, 6 tasini oldik. Nechta qoldi?',
                     'answer': '3', 'hint': 'Ayirish kerak.'},
                    {'id': 'h5', 'type': 'open',
                     'prompt': "O'zingiz bitta qo'shish misoli o'ylab toping va javobini yozing."},
                ],
            },
        },
        {
            'slug': 'ondan-katta-sonlar',
            'title': '10 dan katta sonlar',
            'summary': '11 dan 20 gacha sonlar va ularning tuzilishi',
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': "O'ndan keyin nima bo'ladi?", 'body':
                 "10 dan keyin sanash to'xtamaydi. Sonlar davom etadi:\n\n"
                 "11 — o'n bir\n12 — o'n ikki\n13 — o'n uch\n14 — o'n to'rt\n15 — o'n besh\n"
                 "16 — o'n olti\n17 — o'n yetti\n18 — o'n sakkiz\n19 — o'n to'qqiz\n20 — yigirma"},
                {'type': 'text', 'title': 'Sirni bilasizmi?', 'body':
                 "Bu sonlarning nomiga qarang: **o'n** bir, **o'n** ikki, **o'n** uch...\n\n"
                 "Har bir sonda «o'n» bor! Chunki bu sonlar 10 va yana bir necha birlikdan tuzilgan."},
                {'type': 'formula', 'body': '13 = 10 + 3'},
                {'type': 'example', 'title': "Ajratib ko'ramiz", 'body':
                 '15 = 10 + 5\n17 = 10 + 7\n11 = 10 + 1\n20 = 10 + 10'},
                {'type': 'text', 'title': "O'nlik va birlik", 'body':
                 "Ikki xonali sonda ikkita raqam bo'ladi:\n\n"
                 "**16** sonida:\n"
                 "• 1 — o'nliklar soni (bitta o'nlik = 10)\n"
                 "• 6 — birliklar soni\n\n"
                 "Demak 16 = 1 ta o'nlik + 6 ta birlik."},
                {'type': 'note', 'body':
                 "Raqamlarning o'rni muhim! **12** va **21** — bular butunlay boshqa sonlar. "
                 "12 da bitta o'nlik bor, 21 da esa ikkita o'nlik bor."},
                {'type': 'life', 'body':
                 "Bir oyda 30 kun bor, sinfingizda 25 ta o'quvchi bo'lishi mumkin — "
                 "bular hammasi 10 dan katta sonlar."},
            ],
            'quiz': [
                {'type': 'mc', 'q': '14 sonidan keyin qaysi son keladi?',
                 'options': ['13', '15', '16', '40'], 'answer': 1,
                 'explain': 'Sanash tartibi: 13, 14, **15**, 16.'},
                {'type': 'mc', 'q': '18 soni nimadan tuzilgan?',
                 'options': ['10 + 8', '1 + 8', '10 + 18', '8 + 8'], 'answer': 0,
                 'explain': "O'n sakkiz = o'n va sakkiz, ya'ni 10 + 8."},
                {'type': 'mc', 'q': 'Qaysi son kattaroq: 12 yoki 19?',
                 'options': ['12', '19', 'Teng'], 'answer': 1,
                 'explain': 'Sanaganda 19 keyinroq keladi.'},
                {'type': 'tf', 'q': "20 soni ikkita o'nlikdan iborat.", 'answer': True,
                 'explain': "To'g'ri: 20 = 10 + 10, ya'ni 2 ta o'nlik."},
                {'type': 'fill', 'q': "11, 12, ___, 14 — bo'sh joyga qaysi son kerak?",
                 'answer': '13', 'explain': '12 dan keyin 13 keladi.'},
                {'type': 'mc', 'q': '17 sonida nechta birlik bor?',
                 'options': ['1', '7', '17', '10'], 'answer': 1,
                 'explain': '17 = 10 + 7. Birliklar — 7 ta.'},
            ],
            'homework': {
                'intro': 'Sonlarni tahlil qiling.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': '16 sonidan keyin keladigan sonni yozing.', 'answer': '17'},
                    {'id': 'h2', 'type': 'number', 'prompt': '10 + 9 = ?', 'answer': '19'},
                    {'id': 'h3', 'type': 'number', 'prompt': '15 sonida nechta birlik bor?', 'answer': '5'},
                    {'id': 'h4', 'type': 'text', 'prompt': "13 sonini so'z bilan yozing.",
                     'answer': "o'n uch", 'accept': ['on uch', 'o‘n uch'], 'hint': "Masalan: 12 — o'n ikki"},
                ],
            },
        },
        {
            'slug': 'geometrik-shakllar',
            'title': 'Geometrik shakllar',
            'summary': "Doira, kvadrat, uchburchak va to'rtburchakni tanib olamiz",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': 'Shakllar atrofimizda', 'body':
                 "Atrofimizdagi hamma narsaning o'z shakli bor. Non yumaloq, deraza to'rtburchak, "
                 "tom uchburchak bo'lishi mumkin. Keling, asosiy shakllar bilan tanishamiz."},
                {'type': 'text', 'title': '⭕ Doira', 'body':
                 "Doira — yumaloq shakl. Uning burchagi ham, tomoni ham yo'q.\n\n"
                 "Misollar: quyosh, non, soat, g'ildirak, tanga."},
                {'type': 'text', 'title': '🔺 Uchburchak', 'body':
                 "Uchburchakning **3 ta tomoni** va **3 ta burchagi** bor.\n\n"
                 "Misollar: uyning tomi, yo'l belgisi, bo'lak pitsa."},
                {'type': 'text', 'title': '🟦 Kvadrat', 'body':
                 "Kvadratning **4 ta tomoni** bor va hamma tomoni **bir xil uzunlikda**.\n\n"
                 "Misollar: shaxmat katagi, salfetka, kubik yuzasi."},
                {'type': 'text', 'title': "▭ To'g'ri to'rtburchak", 'body':
                 "Uning ham 4 ta tomoni bor, lekin qarama-qarshi tomonlari teng: "
                 "ikkitasi uzun, ikkitasi qisqa.\n\n"
                 "Misollar: daftar, eshik, telefon ekrani, doska."},
                {'type': 'table', 'head': ['Shakl', 'Tomonlar soni', 'Burchaklar soni'], 'rows': [
                    ['Doira', '0', '0'],
                    ['Uchburchak', '3', '3'],
                    ['Kvadrat', '4', '4'],
                    ["To'rtburchak", '4', '4'],
                ]},
                {'type': 'note', 'body':
                 "Kvadrat ham to'rtburchakning bir turi. Farqi: kvadratda BARCHA tomonlar teng."},
                {'type': 'life', 'body':
                 "Hozir atrofingizga qarang. Nechta to'rtburchak ko'rayapsiz? "
                 "Kitob, deraza, stol — bularning hammasi to'rtburchak."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Uchburchakning nechta tomoni bor?',
                 'options': ['2', '3', '4', '5'], 'answer': 1,
                 'explain': "Nomining o'zi aytib turibdi — UCH burchak, 3 ta tomon."},
                {'type': 'mc', 'q': "Qaysi shaklning burchagi yo'q?",
                 'options': ['Kvadrat', 'Uchburchak', 'Doira', "To'rtburchak"], 'answer': 2,
                 'explain': "Doira yumaloq — unda burchak ham, tomon ham yo'q."},
                {'type': 'mc', 'q': "Daftar qaysi shaklga o'xshaydi?",
                 'options': ['Doira', 'Uchburchak', "To'g'ri to'rtburchak"], 'answer': 2,
                 'explain': "Daftarning 2 ta uzun, 2 ta qisqa tomoni bor."},
                {'type': 'tf', 'q': 'Kvadratning hamma tomoni bir xil uzunlikda.', 'answer': True,
                 'explain': "To'g'ri — bu kvadratning asosiy belgisi."},
                {'type': 'mc', 'q': 'Soat siferblati odatda qanday shaklda?',
                 'options': ['Doira', 'Uchburchak', 'Kvadrat'], 'answer': 0,
                 'explain': "Ko'pchilik soat yumaloq — doira shaklida."},
                {'type': 'fill', 'q': 'Kvadratning nechta burchagi bor? (raqam bilan)',
                 'answer': '4', 'accept': ["to'rt", 'tort'],
                 'explain': 'Kvadratda 4 ta tomon va 4 ta burchak bor.'},
            ],
            'homework': {
                'intro': 'Atrofingizdagi shakllarni toping.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "To'g'ri to'rtburchakning nechta tomoni bor?", 'answer': '4'},
                    {'id': 'h2', 'type': 'text', 'prompt': "G'ildirak qaysi shaklga o'xshaydi?",
                     'answer': 'doira', 'accept': ['doira', 'yumaloq', 'aylana']},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Uyingizdan 3 ta to'rtburchak shaklidagi narsani toping va yozing."},
                    {'id': 'h4', 'type': 'open',
                     'prompt': 'Daftaringizga bitta uchburchak va bitta kvadrat chizing. Chizdingizmi? «Ha» deb yozing.'},
                ],
            },
        },
        {
            'slug': 'olchov',
            'title': "O'lchov: uzunlik va vaqt",
            'summary': "Uzun-qisqa, og'ir-yengil va soatni o'qishni o'rganamiz",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': "O'lchash nima?", 'body':
                 "O'lchash — narsaning qanchaligini aniqlash. Uzunligini, og'irligini yoki vaqtni o'lchaymiz."},
                {'type': 'text', 'title': 'Uzunlik', 'body':
                 "Uzunlikni **santimetr (sm)** bilan o'lchaymiz. Buning uchun chizg'ich kerak.\n\n"
                 "Qalam 15 sm, daftar 20 sm bo'lishi mumkin.\n\n"
                 "Katta masofalarni **metr (m)** bilan o'lchaymiz: 1 m = 100 sm."},
                {'type': 'steps', 'title': "Chizg'ich bilan qanday o'lchaymiz", 'items': [
                    "Narsaning bir chetini chizg'ichdagi **0** ga qo'ying.",
                    "Chizg'ichni narsaga tekis qo'ying.",
                    "Narsaning ikkinchi cheti qaysi raqamga to'g'ri kelishiga qarang.",
                    'Shu raqam — uzunlik.',
                ]},
                {'type': 'text', 'title': 'Taqqoslash', 'body':
                 "Ikki narsani solishtirsak, quyidagi so'zlarni ishlatamiz:\n\n"
                 "**uzun — qisqa** (arqon uzun, ip qisqa)\n"
                 "**baland — past** (daraxt baland, gul past)\n"
                 "**og'ir — yengil** (tosh og'ir, patcha yengil)\n"
                 "**keng — tor** (ko'cha keng, so'qmoq tor)"},
                {'type': 'text', 'title': 'Vaqt va soat', 'body':
                 "Bir kunda **24 soat** bor. Bir soatda **60 daqiqa** bor.\n\n"
                 "Soatda ikkita mil bo'ladi:\n"
                 "• **Kalta mil** — soatni ko'rsatadi\n"
                 "• **Uzun mil** — daqiqani ko'rsatadi"},
                {'type': 'example', 'title': "Soatni o'qiymiz", 'body':
                 "Kalta mil 3 da, uzun mil 12 da bo'lsa — **soat 3:00**.\n"
                 "Kalta mil 7 va 8 orasida, uzun mil 6 da bo'lsa — **soat 7:30** (yetti yarim)."},
                {'type': 'note', 'body':
                 'Bir haftada 7 kun bor: dushanba, seshanba, chorshanba, payshanba, juma, shanba, yakshanba.'},
                {'type': 'life', 'body':
                 "Maktabga kech qolmaslik uchun soatni bilish kerak. "
                 "Darslar soat 8:00 da boshlansa, siz 7:30 da uydan chiqishingiz kerak."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Bir soatda nechta daqiqa bor?',
                 'options': ['10', '24', '60', '100'], 'answer': 2,
                 'explain': 'Bir soat = 60 daqiqa.'},
                {'type': 'mc', 'q': "Uzunlikni o'lchash uchun nima kerak?",
                 'options': ['Tarozi', "Chizg'ich", 'Soat', 'Stakan'], 'answer': 1,
                 'explain': "Chizg'ich uzunlikni santimetrda o'lchaydi."},
                {'type': 'mc', 'q': 'Bir haftada nechta kun bor?',
                 'options': ['5', '7', '12', '30'], 'answer': 1,
                 'explain': 'Dushanbadan yakshanbagacha — 7 kun.'},
                {'type': 'tf', 'q': "Fil sichqondan og'irroq.", 'answer': True,
                 'explain': 'Albatta! Fil juda og\'ir hayvon.'},
                {'type': 'mc', 'q': '1 metr necha santimetrga teng?',
                 'options': ['10', '50', '100', '1000'], 'answer': 2,
                 'explain': '1 m = 100 sm.'},
                {'type': 'fill', 'q': 'Bir kunda nechta soat bor? (raqam bilan)',
                 'answer': '24', 'explain': 'Bir kecha-kunduz — 24 soat.'},
            ],
            'homework': {
                'intro': "O'lchash bilan bog'liq vazifalar.",
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': 'Bir soatda nechta daqiqa bor?', 'answer': '60'},
                    {'id': 'h2', 'type': 'number', 'prompt': '1 metrda nechta santimetr bor?', 'answer': '100'},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "Chizg'ich bilan qalamingizni o'lchang. Necha santimetr chiqdi?"},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Bugun soat nechada uyg'ondingiz? Yozing."},
                ],
            },
        },
        {
            'slug': 'masalalar',
            'title': 'Masalalar yechish',
            'summary': "Matnli masalalarni tushunib, to'g'ri yechishni o'rganamiz",
            'duration': 20,
            'lesson': [
                {'type': 'text', 'title': 'Masala nima?', 'body':
                 "Masala — bu hikoya ko'rinishidagi matematik savol.\n\n"
                 "Masalan: «Aliyda 5 ta qalam bor edi. U 2 tasini dugonasiga berdi. "
                 "Aliyda nechta qalam qoldi?»"},
                {'type': 'steps', 'title': 'Masalani yechish tartibi', 'items': [
                    "Masalani DIQQAT bilan o'qing (kerak bo'lsa 2 marta).",
                    'NIMA BERILGAN? — sonlarni toping (5 ta qalam, 2 tasini berdi).',
                    "NIMA SO'RALYAPTI? — savolni toping (nechta qoldi?).",
                    "Qaysi amal kerak? Qo'shishmi yoki ayirishmi?",
                    'Amalni bajaring va javob yozing.',
                ]},
                {'type': 'text', 'title': 'Qaysi amalni tanlash kerak?', 'body':
                 "Masalada bu so'zlar bo'lsa — **QO'SHISH**:\n"
                 "yana oldi, qo'shildi, keldi, jami, hammasi bo'lib, birgalikda\n\n"
                 "Masalada bu so'zlar bo'lsa — **AYIRISH**:\n"
                 "berdi, yedi, ketdi, sindi, qoldi, nechtaga kam"},
                {'type': 'example', 'title': 'Birinchi masalani yechamiz', 'body':
                 "«Aliyda 5 ta qalam bor edi. 2 tasini berdi. Nechta qoldi?»\n\n"
                 "Berilgan: 5 ta va 2 ta\n"
                 "So'ralyapti: nechta QOLDI\n"
                 "«Berdi», «qoldi» — demak AYIRISH\n\n"
                 "5 − 2 = 3\n\n"
                 "Javob: 3 ta qalam qoldi."},
                {'type': 'example', 'title': 'Ikkinchi masala', 'body':
                 "«Bog'da 4 ta olma daraxti va 3 ta nok daraxti bor. Jami nechta daraxt bor?»\n\n"
                 "Berilgan: 4 ta va 3 ta\n"
                 "So'ralyapti: JAMI nechta\n"
                 "«Jami» — demak QO'SHISH\n\n"
                 "4 + 3 = 7\n\n"
                 "Javob: 7 ta daraxt."},
                {'type': 'note', 'body':
                 "Javobni yozgandan keyin o'zingizdan so'rang: «Bu javob mantiqiymi?» "
                 "Masalan, 5 ta qalamdan 2 tasini bersangiz, 8 ta qololmaydi — bu xato bo'ladi."},
                {'type': 'life', 'body':
                 "Masalalar — hayotdagi haqiqiy vaziyatlar. "
                 "Do'kondan nima olasiz, qancha pul qoladi — bularning hammasi masala."},
            ],
            'quiz': [
                {'type': 'mc', 'q': '«Savatda 6 ta olma bor edi, 2 tasi yeyildi. Nechta qoldi?»',
                 'options': ['8', '4', '2', '6'], 'answer': 1,
                 'explain': '«Qoldi» — ayirish: 6 − 2 = 4.'},
                {'type': 'mc', 'q': '«Dilnozada 3 ta kitob bor, onasi yana 5 ta oldi. Jami nechta?»',
                 'options': ['2', '5', '8', '15'], 'answer': 2,
                 'explain': "«Jami», «yana oldi» — qo'shish: 3 + 5 = 8."},
                {'type': 'mc', 'q': 'Masalada «qoldi» so\'zi bo\'lsa, qaysi amalni bajaramiz?',
                 'options': ["Qo'shish", 'Ayirish', 'Sanash'], 'answer': 1,
                 'explain': "«Qoldi» — bir qismi ketgani, demak ayirish."},
                {'type': 'tf', 'q': "Masalani yechishdan oldin uni diqqat bilan o'qish kerak.",
                 'answer': True,
                 'explain': "To'g'ri. Masalani tushunmasdan yechib bo'lmaydi."},
                {'type': 'mc', 'q': '«Hovlida 2 ta mushuk va 4 ta kuchuk bor. Hammasi nechta hayvon?»',
                 'options': ['2', '4', '6', '8'], 'answer': 2,
                 'explain': "«Hammasi» — qo'shish: 2 + 4 = 6."},
                {'type': 'fill', 'q': "«Avtobusda 9 ta yo'lovchi bor edi, 5 tasi tushdi. Nechta qoldi?»",
                 'answer': '4', 'explain': '9 − 5 = 4.'},
            ],
            'homework': {
                'intro': 'Masalalarni yeching. Faqat javob sonini yozing.',
                'tasks': [
                    {'id': 'h1', 'type': 'number',
                     'prompt': 'Jamshidda 7 ta mashinacha bor edi. Ukasiga 3 tasini berdi. Nechta qoldi?',
                     'answer': '4'},
                    {'id': 'h2', 'type': 'number',
                     'prompt': "Bog'chada 5 ta qizcha va 4 ta bolakay o'ynayapti. Jami nechta bola bor?",
                     'answer': '9'},
                    {'id': 'h3', 'type': 'number',
                     'prompt': 'Onam 10 ta tuxum oldi, 6 tasidan ovqat qildi. Nechta tuxum qoldi?',
                     'answer': '4'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "O'zingiz bitta masala o'ylab toping va yechimini yozing."},
                ],
            },
        },
    ],
}
