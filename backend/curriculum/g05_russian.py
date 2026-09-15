# -*- coding: utf-8 -*-
"""5-sinf — Rus tili."""

RUSSIAN = {
    'key': 'russian',
    'topics': [
        {
            'slug': 'alfavit',
            'title': 'Русский алфавит',
            'summary': "Rus alifbosi — 33 ta harf bilan tanishish",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': 'Alifbo nechta harfdan iborat?', 'body':
                 "Rus alifbosida (кириллица) **33 ta harf** bor: 10 ta unli, 21 ta undosh "
                 "va 2 ta belgi (ъ, ь).\n\n"
                 "Ko'pgina harflar lotin alifbosidagidek yoziladi, lekin talaffuzi boshqacha."},
                {'type': 'table', 'head': ['Harf', 'Nomi', "O'qilishi"], 'rows': [
                    ['А а', 'а', "o'zbekcha «a» kabi"],
                    ['Б б', 'бэ', "«b» kabi"],
                    ['В в', 'вэ', "«v» kabi"],
                    ['Г г', 'гэ', "«g» kabi"],
                    ['Ё ё', 'ё', "«yo» kabi"],
                    ['Ж ж', 'жэ', "«j» (yumshoq) kabi"],
                    ['Й й', "и краткое", "qisqa «y» kabi"],
                    ['Ц ц', 'цэ', "«ts» kabi"],
                    ['Ч ч', 'чэ', "«ch» kabi"],
                    ['Щ щ', 'ща', "yumshoq «sh» kabi"],
                ]},
                {'type': 'text', 'title': 'Unli va undosh harflar', 'body':
                 "**Unlilar (10 ta):** а, е, ё, и, о, у, ы, э, ю, я\n\n"
                 "**Undoshlar (21 ta):** б, в, г, д, ж, з, й, к, л, м, н, п, р, с, т, ф, х, ц, ч, ш, щ\n\n"
                 "**Belgilar:** ъ (qattiqlik belgisi), ь (yumshoqlik belgisi) — alohida tovush "
                 "bildirmaydi."},
                {'type': 'example', 'title': "So'zlarni o'qish", 'body':
                 "мама → ona\n"
                 "папа → ota\n"
                 "дом → uy\n"
                 "школа → maktab\n"
                 "книга → kitob"},
                {'type': 'note', 'body':
                 "Ё harfi ustidagi ikki nuqta ba'zan yozilmaydi, lekin talaffuzda «yo» deb "
                 "o'qiladi: ёлка (archa)."},
                {'type': 'life', 'body':
                 "Rus alifbosini bilish — do'konlarda, avtobus bekatlarida va internetda "
                 "rus tilidagi yozuvlarni o'qishga yordam beradi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "Rus alifbosida nechta harf bor?",
                 'options': ['28', '33', '26'], 'answer': 1,
                 'explain': "Rus alifbosida 33 ta harf bor."},
                {'type': 'mc', 'q': '«Ё» harfi qanday o\'qiladi?',
                 'options': ['yo', 'e', 'yu'], 'answer': 0,
                 'explain': "Ё — «yo» deb o'qiladi."},
                {'type': 'mc', 'q': '«школа» so\'zi nimani anglatadi?',
                 'options': ['kitob', 'maktab', 'uy'], 'answer': 1,
                 'explain': "школа — maktab."},
                {'type': 'tf', 'q': "Ъ va Ь harflari alohida tovush bildiradi.",
                 'answer': False, 'explain': "Yo'q, ular belgi — alohida tovush bildirmaydi."},
                {'type': 'mc', 'q': "Quyidagilardan qaysi biri unli harf?",
                 'options': ['б', 'о', 'к'], 'answer': 1,
                 'explain': "«о» — unli harf."},
                {'type': 'fill', 'q': '«дом» so\'zini o\'zbekchaga tarjima qiling.',
                 'answer': 'uy', 'explain': "дом — uy."},
            ],
            'homework': {
                'intro': "Alifbo va so'zlar bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': '«мама» so\'zini tarjima qiling.',
                     'answer': 'ona'},
                    {'id': 'h2', 'type': 'text', 'prompt': '«книга» so\'zini tarjima qiling.',
                     'answer': 'kitob'},
                    {'id': 'h3', 'type': 'number', 'prompt': "Rus alifbosida nechta unli harf bor?",
                     'answer': '10'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "5 ta rus harfini yozib, ularning talaffuzini tushuntiring."},
                ],
            },
        },
        {
            'slug': 'salomlashish',
            'title': 'Приветствие и знакомство',
            'summary': "Salomlashish va tanishish iboralari",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': 'Salomlashish', 'body':
                 "Rus tilida vaqtga qarab har xil salomlashiladi:\n\n"
                 "**Привет!** — Salom! (do'stlar bilan)\n"
                 "**Здравствуйте!** — Assalomu alaykum! (hurmat bilan, kattalarga)\n"
                 "**Доброе утро!** — Xayrli tong!\n"
                 "**Добрый день!** — Xayrli kun!\n"
                 "**Добрый вечер!** — Xayrli kech!"},
                {'type': 'text', 'title': 'Tanishish', 'body':
                 "**Как тебя зовут?** — Isming nima?\n"
                 "**Меня зовут ...** — Mening ismim ...\n"
                 "**Сколько тебе лет?** — Necha yoshdasan?\n"
                 "**Мне ... лет.** — Men ... yoshdaman."},
                {'type': 'example', 'title': 'Suhbat namunasi', 'body':
                 "— Привет! Как тебя зовут?\n"
                 "— Меня зовут Дилноза. А тебя?\n"
                 "— Меня зовут Aziz. Сколько тебе лет?\n"
                 "— Мне 11 лет."},
                {'type': 'table', 'head': ['Ruscha', "O'zbekcha"], 'rows': [
                    ['Как дела?', 'Ishlar qalay?'],
                    ['Хорошо, спасибо!', 'Yaxshi, rahmat!'],
                    ['До свидания!', 'Xayr!'],
                    ['Пока!', 'Xayr! (do\'stona)'],
                ]},
                {'type': 'note', 'body':
                 "«Здравствуйте» — kattalarga va notanishlarga, «Привет» — do'stlarga va "
                 "tengdoshlarga ishlatiladi."},
                {'type': 'life', 'body':
                 "Ko'chada, do'konda yoki mehmonda rus tilida to'g'ri salomlashish — yaxshi "
                 "taassurot qoldiradi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': '«Assalomu alaykum» ruschada qanday aytiladi?',
                 'options': ['Привет', 'Здравствуйте', 'Пока'], 'answer': 1,
                 'explain': "Здравствуйте — hurmat bilan salomlashish."},
                {'type': 'mc', 'q': '«Как тебя зовут?» nimani so\'raydi?',
                 'options': ['Yoshingni', 'Ismingni', 'Uyingni'], 'answer': 1,
                 'explain': "Bu ibora ism so'rash uchun ishlatiladi."},
                {'type': 'mc', 'q': '«Мне 11 лет» nimani anglatadi?',
                 'options': ['Men 11 yoshdaman', 'Meni 11 deb chaqirishadi', 'Soat 11'], 'answer': 0,
                 'explain': "«Мне ... лет» — yoshni bildirish."},
                {'type': 'tf', 'q': '«Пока» — rasmiy xayrlashish iborasi.',
                 'answer': False, 'explain': "«Пока» do'stona, norasmiy xayrlashish."},
                {'type': 'mc', 'q': '«Доброе утро» qachon aytiladi?',
                 'options': ['Ertalab', 'Kechqurun', 'Tunda'], 'answer': 0,
                 'explain': "Доброе утро — Xayrli tong."},
                {'type': 'fill', 'q': '«Спасибо» so\'zini tarjima qiling.',
                 'answer': 'rahmat', 'explain': "Спасибо — rahmat."},
            ],
            'homework': {
                'intro': "Salomlashish iboralari bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': '«Xayr!» so\'zini ruschaga tarjima qiling (norasmiy).',
                     'answer': 'пока', 'accept': ['пока', 'Пока', 'Пока!']},
                    {'id': 'h2', 'type': 'text', 'prompt': '«Ishlar qalay?» ruschada qanday bo\'ladi?',
                     'answer': 'как дела', 'accept': ['как дела', 'Как дела?', 'как дела?']},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "O'zingizni ruscha tanishtiring: ismingiz va yoshingizni yozing."},
                ],
            },
        },
        {
            'slug': 'sonlar',
            'title': 'Числа',
            'summary': "1 dan 20 gacha sonlar",
            'duration': 16,
            'lesson': [
                {'type': 'text', 'title': "Sonlarni o'rganish", 'body':
                 "Rus tilida sonlarni bilish — narx so'rash, yosh aytish va vaqtni "
                 "ifodalash uchun zarur."},
                {'type': 'table', 'head': ['Son', 'Ruscha'], 'rows': [
                    ['1', 'один'],
                    ['2', 'два'],
                    ['3', 'три'],
                    ['4', 'четыре'],
                    ['5', 'пять'],
                    ['6', 'шесть'],
                    ['7', 'семь'],
                    ['8', 'восемь'],
                    ['9', 'девять'],
                    ['10', 'десять'],
                ]},
                {'type': 'text', 'title': '11 dan 20 gacha', 'body':
                 "11 dan 19 gacha sonlar **-надцать** qo'shimchasi bilan yasaladi:\n\n"
                 "11 — одиннадцать\n"
                 "12 — двенадцать\n"
                 "15 — пятнадцать\n"
                 "20 — двадцать (alohida so'z)"},
                {'type': 'example', 'title': 'Gaplarda ishlatish', 'body':
                 "У меня **два** брата. → Mening ikkita akam bor.\n"
                 "Мне **одиннадцать** лет. → Men o'n bir yoshdaman.\n"
                 "В классе **двадцать** учеников. → Sinfda yigirma o'quvchi bor."},
                {'type': 'note', 'body':
                 "«Один» (bir) otga qarab o'zgarishi mumkin: один мальчик (bir bola), "
                 "одна девочка (bir qiz) — lekin boshlang'ich darajada asosiy shaklni bilish yetarli."},
                {'type': 'life', 'body':
                 "Bozorda narx so'raganda yoki telefon raqamini aytganda sonlar doim kerak "
                 "bo'ladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': '«пять» qaysi songa mos keladi?',
                 'options': ['4', '5', '6'], 'answer': 1,
                 'explain': "пять — 5."},
                {'type': 'mc', 'q': '10 soni ruschada qanday yoziladi?',
                 'options': ['десять', 'девять', 'восемь'], 'answer': 0,
                 'explain': "десять — 10."},
                {'type': 'mc', 'q': '«двадцать» qaysi son?',
                 'options': ['12', '20', '2'], 'answer': 1,
                 'explain': "двадцать — 20."},
                {'type': 'tf', 'q': "11 dan 19 gacha sonlar «-надцать» bilan tugaydi.",
                 'answer': True, 'explain': "To'g'ri, masalan: одиннадцать, пятнадцать."},
                {'type': 'fill', 'q': '«три» soni nechaga teng?',
                 'answer': '3', 'explain': "три — 3."},
                {'type': 'mc', 'q': '«семь» soni?',
                 'options': ['6', '7', '8'], 'answer': 1,
                 'explain': "семь — 7."},
            ],
            'homework': {
                'intro': "Sonlar bo'yicha.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': '8 sonini ruschada yozing.',
                     'answer': 'восемь'},
                    {'id': 'h2', 'type': 'number', 'prompt': '«четырнадцать» qaysi songa mos keladi?',
                     'answer': '14'},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "1 dan 10 gacha sonlarni ruscha yozing."},
                ],
            },
        },
    ],
}
