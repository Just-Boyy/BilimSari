# -*- coding: utf-8 -*-
"""1-sinf — Ona tili."""

UZBEK = {
    'key': 'uzbek',
    'topics': [
        {
            'slug': 'tovush-harf',
            'title': 'Tovush va harf',
            'summary': "Tovush bilan harf orasidagi farqni tushunamiz",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': 'Tovush nima?', 'body':
                 "Gapirganimizda og'zimizdan **tovush** chiqadi. Tovushni biz **eshitamiz**.\n\n"
                 "Masalan, «ona» so'zini aytsangiz, uchta tovush eshitiladi: o - n - a"},
                {'type': 'text', 'title': 'Harf nima?', 'body':
                 "**Harf** — tovushning yozuvdagi belgisi. Harfni biz **ko'ramiz** va **yozamiz**.\n\n"
                 "Tovushni eshitamiz, harfni ko'ramiz. Mana shu — asosiy farq."},
                {'type': 'table', 'head': ['Tovush', 'Harf'], 'rows': [
                    ['Eshitamiz', "Ko'ramiz"],
                    ['Aytamiz', 'Yozamiz'],
                    ["Quloq bilan sezamiz", "Ko'z bilan sezamiz"],
                ]},
                {'type': 'text', 'title': "O'zbek alifbosi", 'body':
                 "O'zbek alifbosida **29 ta harf** va **1 ta tutuq belgisi (ʼ)** bor.\n\n"
                 "A a, B b, D d, E e, F f, G g, H h, I i, J j, K k, L l, M m, N n, "
                 "O o, P p, Q q, R r, S s, T t, U u, V v, X x, Y y, Z z, "
                 "Oʻ oʻ, Gʻ gʻ, Sh sh, Ch ch, Ng ng"},
                {'type': 'note', 'body':
                 "**Sh**, **Ch**, **Ng** — bular ikki belgidan yozilsa ham, BITTA harf hisoblanadi "
                 "va bitta tovushni bildiradi."},
                {'type': 'example', 'title': "So'zni tovushlarga ajratamiz", 'body':
                 "**kitob** → k - i - t - o - b (5 ta tovush, 5 ta harf)\n"
                 "**shar** → sh - a - r (3 ta tovush, lekin 4 ta belgi yozilgan)\n"
                 "**bola** → b - o - l - a (4 ta tovush)"},
                {'type': 'life', 'body':
                 "Ismingizni ovoz chiqarib ayting va har bir tovushni sanang. Nechta tovush bor?"},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Tovushni nima bilan sezamiz?',
                 'options': ["Ko'z bilan", 'Quloq bilan', 'Qo\'l bilan'], 'answer': 1,
                 'explain': 'Tovushni eshitamiz — demak quloq bilan.'},
                {'type': 'mc', 'q': "Harfni nima qilamiz?",
                 'options': ['Eshitamiz', 'Yozamiz va ko\'ramiz', 'Hidlaymiz'], 'answer': 1,
                 'explain': "Harf — yozuvdagi belgi, uni ko'ramiz va yozamiz."},
                {'type': 'mc', 'q': "O'zbek alifbosida nechta harf bor?",
                 'options': ['26', '29', '33', '40'], 'answer': 1,
                 'explain': "O'zbek alifbosida 29 ta harf bor."},
                {'type': 'tf', 'q': "«Sh» — bitta harf hisoblanadi.", 'answer': True,
                 'explain': "To'g'ri. Ikki belgi bilan yozilsa ham, bitta harf va bitta tovush."},
                {'type': 'mc', 'q': "«ota» so'zida nechta tovush bor?",
                 'options': ['2', '3', '4'], 'answer': 1,
                 'explain': 'o - t - a, jami 3 ta tovush.'},
                {'type': 'fill', 'q': "«non» so'zida nechta tovush bor? (raqam bilan)",
                 'answer': '3', 'explain': 'n - o - n, 3 ta tovush.'},
            ],
            'homework': {
                'intro': "So'zlarni tovushlarga ajrating.",
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "«kitob» so'zida nechta tovush bor?", 'answer': '5'},
                    {'id': 'h2', 'type': 'number', 'prompt': "«uy» so'zida nechta tovush bor?", 'answer': '2'},
                    {'id': 'h3', 'type': 'number', 'prompt': "O'zbek alifbosida nechta harf bor?", 'answer': '29'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "O'z ismingizni tovushlarga ajratib yozing. Masalan: Ali → a-l-i"},
                ],
            },
        },
        {
            'slug': 'unli-undosh',
            'title': 'Unli va undosh tovushlar',
            'summary': "Tovushlarni ikki guruhga ajratishni o'rganamiz",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': 'Unli tovushlar', 'body':
                 "**Unli** tovushlarni aytganda havo og'izdan **erkin** chiqadi. "
                 "Hech narsa to'sib turmaydi.\n\n"
                 "O'zbek tilida **6 ta unli** bor:\n\n"
                 "**a, e, i, o, u, oʻ**"},
                {'type': 'text', 'title': 'Undosh tovushlar', 'body':
                 "**Undosh** tovushlarni aytganda havo **to'siqqa** uchraydi — "
                 "til, lab yoki tishlar to'sib turadi.\n\n"
                 "Qolgan hamma tovushlar undosh: b, d, f, g, h, j, k, l, m, n, p, q, r, s, t, v, x, y, z, gʻ, sh, ch, ng"},
                {'type': 'steps', 'title': 'Qanday farqlaymiz?', 'items': [
                    'Tovushni cho\'zib ayting: a-a-a-a.',
                    "Agar oson cho'zilsa va hech narsa to'smasa — **unli**.",
                    "Agar til yoki lab to'sib tursa — **undosh**.",
                    "Qo'lingizni tomog'ingizga qo'ying: unlida ovoz kuchli titraydi.",
                ]},
                {'type': 'note', 'body':
                 "Unli tovushlarni yodlab oling: **a, e, i, o, u, oʻ** — bor-yo'g'i 6 ta! "
                 "Qolgan hammasi undosh."},
                {'type': 'example', 'title': "So'zlarni tahlil qilamiz", 'body':
                 "**ona** → o (unli), n (undosh), a (unli) = 2 unli, 1 undosh\n"
                 "**dars** → d (undosh), a (unli), r (undosh), s (undosh) = 1 unli, 3 undosh\n"
                 "**oila** → o, i, a — unli; l — undosh"},
                {'type': 'life', 'body':
                 "Qo'shiq aytganda unli tovushlarni cho'zamiz: «o-o-o-na jo-o-on». "
                 "Undoshni cho'zib bo'lmaydi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "O'zbek tilida nechta unli tovush bor?",
                 'options': ['5', '6', '10', '29'], 'answer': 1,
                 'explain': "a, e, i, o, u, oʻ — jami 6 ta unli."},
                {'type': 'mc', 'q': 'Qaysi tovush unli?',
                 'options': ['b', 'k', 'i', 'sh'], 'answer': 2,
                 'explain': "«i» — unli tovush. Qolganlari undosh."},
                {'type': 'mc', 'q': 'Qaysi tovush undosh?',
                 'options': ['a', 'o', 'm', 'u'], 'answer': 2,
                 'explain': "«m» — undosh, lab bilan to'siladi."},
                {'type': 'tf', 'q': "Unli tovushni aytganda havo erkin chiqadi.", 'answer': True,
                 'explain': "To'g'ri — bu unlining asosiy belgisi."},
                {'type': 'mc', 'q': "«ona» so'zida nechta unli tovush bor?",
                 'options': ['1', '2', '3'], 'answer': 1,
                 'explain': 'o va a — 2 ta unli.'},
                {'type': 'fill', 'q': "«bola» so'zida nechta undosh tovush bor? (raqam bilan)",
                 'answer': '2', 'explain': 'b va l — 2 ta undosh, o va a — unli.'},
            ],
            'homework': {
                'intro': "Tovushlarni ajrating.",
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "«kitob» so'zida nechta unli tovush bor?", 'answer': '2'},
                    {'id': 'h2', 'type': 'number', 'prompt': "«maktab» so'zida nechta unli tovush bor?", 'answer': '2'},
                    {'id': 'h3', 'type': 'text', 'prompt': "«a» tovushi unlimi yoki undoshmi?",
                     'answer': 'unli', 'accept': ['unli', 'unli tovush']},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Unli tovushlarni tartib bilan yozing."},
                ],
            },
        },
        {
            'slug': 'bogin',
            'title': "Bo'g'in",
            'summary': "So'zlarni bo'g'inlarga ajratishni o'rganamiz",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': "Bo'g'in nima?", 'body':
                 "**Bo'g'in** — so'zning bir nafas bilan aytiladigan bo'lagi.\n\n"
                 "So'zni sekin, bo'lib ayting: **ki-tob**. Bu yerda ikkita bo'lak bor — 2 ta bo'g'in."},
                {'type': 'note', 'body':
                 "**Eng muhim qoida:** so'zda nechta UNLI tovush bo'lsa, shuncha BO'G'IN bo'ladi!\n\n"
                 "Unlini sanang — bo'g'inni bilasiz."},
                {'type': 'example', 'title': "Bo'g'inlarga ajratamiz", 'body':
                 "**o-na** → 2 unli (o, a) = 2 bo'g'in\n"
                 "**ki-tob** → 2 unli (i, o) = 2 bo'g'in\n"
                 "**mak-tab** → 2 unli (a, a) = 2 bo'g'in\n"
                 "**o-i-la** → 3 unli (o, i, a) = 3 bo'g'in\n"
                 "**non** → 1 unli (o) = 1 bo'g'in"},
                {'type': 'steps', 'title': "Tekshirish usuli", 'items': [
                    "Qo'lingizni iyagingiz ostiga qo'ying.",
                    "So'zni ovoz chiqarib ayting.",
                    "Iyagingiz necha marta pastga tushsa — shuncha bo'g'in.",
                    "Yoki oddiygina: unlilarni sanang.",
                ]},
                {'type': 'text', 'title': "Nima uchun kerak?", 'body':
                 "Bo'g'in yozuvda ham kerak. Satr oxirida so'z sig'masa, uni bo'g'in bo'yicha "
                 "ko'chiramiz:\n\n"
                 "ki-\ntob\n\n"
                 "Bir bo'g'inni bo'lib tashlab bo'lmaydi."},
                {'type': 'life', 'body':
                 "She'r va qo'shiqlarning ohangi bo'g'inlarga qarab tuziladi. "
                 "Shuning uchun she'r o'qiganda bo'g'inlar teng-teng eshitiladi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': "«kitob» so'zida nechta bo'g'in bor?",
                 'options': ['1', '2', '3'], 'answer': 1,
                 'explain': "ki-tob → 2 unli, 2 bo'g'in."},
                {'type': 'mc', 'q': "So'zdagi bo'g'inlar soni nimaga bog'liq?",
                 'options': ['Harflar soniga', 'Unlilar soniga', 'Undoshlar soniga'], 'answer': 1,
                 'explain': "Nechta unli — shuncha bo'g'in."},
                {'type': 'mc', 'q': "«maktab» so'zi nechta bo'g'indan iborat?",
                 'options': ['1', '2', '3'], 'answer': 1,
                 'explain': "mak-tab → 2 bo'g'in."},
                {'type': 'tf', 'q': "«non» so'zi bitta bo'g'indan iborat.", 'answer': True,
                 'explain': "To'g'ri — unda faqat bitta unli (o) bor."},
                {'type': 'mc', 'q': "«o-i-la» so'zida nechta bo'g'in bor?",
                 'options': ['2', '3', '4'], 'answer': 1,
                 'explain': "3 ta unli (o, i, a) — 3 ta bo'g'in."},
                {'type': 'fill', 'q': "«ona» so'zida nechta bo'g'in bor? (raqam bilan)",
                 'answer': '2', 'explain': "o-na → 2 bo'g'in."},
            ],
            'homework': {
                'intro': "So'zlarni bo'g'inlarga ajrating.",
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': "«daftar» so'zida nechta bo'g'in bor?", 'answer': '2'},
                    {'id': 'h2', 'type': 'number', 'prompt': "«olma» so'zida nechta bo'g'in bor?", 'answer': '2'},
                    {'id': 'h3', 'type': 'number', 'prompt': "«gul» so'zida nechta bo'g'in bor?", 'answer': '1'},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "O'z ismingizni bo'g'inlarga ajrating. Masalan: Di-ldo-ra"},
                ],
            },
        },
        {
            'slug': 'soz-va-gap',
            'title': "So'z va gap",
            'summary': "So'zlardan gap tuzishni o'rganamiz",
            'duration': 18,
            'lesson': [
                {'type': 'text', 'title': "So'z nima?", 'body':
                 "**So'z** — ma'no bildiradigan tovushlar birikmasi.\n\n"
                 "«kitob», «bola», «yugurmoq» — bularning har biri biror narsani yoki ishni bildiradi."},
                {'type': 'text', 'title': 'Gap nima?', 'body':
                 "**Gap** — tugallangan fikrni bildiradigan so'zlar birikmasi.\n\n"
                 "«kitob» — bu faqat so'z, fikr tugallanmagan.\n"
                 "«Men kitob o'qiyapman.» — bu gap, chunki fikr to'liq."},
                {'type': 'example', 'title': "So'z va gapni solishtiramiz", 'body':
                 "❌ **olma** — so'z (nima haqida gapiryapmiz, tushunarsiz)\n"
                 "✅ **Olma shirin.** — gap (fikr tugallangan)\n\n"
                 "❌ **bola maktab**\n"
                 "✅ **Bola maktabga ketdi.**"},
                {'type': 'steps', 'title': "Gapning belgilari", 'items': [
                    "Gap **katta harf** bilan boshlanadi.",
                    "Gap oxirida **tinish belgisi** bo'ladi (. ? !).",
                    "Gapda tugallangan fikr bo'ladi.",
                    "So'zlar bir-biri bilan bog'langan bo'ladi.",
                ]},
                {'type': 'text', 'title': 'Gap turlari', 'body':
                 "**Darak gap** — biror narsani aytadi. Oxirida **nuqta (.)** qo'yiladi.\n"
                 "Misol: Bugun havo issiq.\n\n"
                 "**So'roq gap** — savol beradi. Oxirida **so'roq belgisi (?)** qo'yiladi.\n"
                 "Misol: Sen qayerga ketyapsan?\n\n"
                 "**His-hayajon gap** — kuchli his bildiradi. Oxirida **undov belgisi (!)** qo'yiladi.\n"
                 "Misol: Qanday go'zal bog'!"},
                {'type': 'life', 'body':
                 "Kun davomida siz yuzlab gap tuzasiz: «Ovqat yeyman», «Maktabga boraman». "
                 "Har birida tugallangan fikr bor."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Quyidagilardan qaysi biri GAP?',
                 'options': ['kitob', 'katta bog\'', 'Men maktabga bordim.', 'olma daraxt'], 'answer': 2,
                 'explain': 'Faqat unda tugallangan fikr bor va tinish belgisi qo\'yilgan.'},
                {'type': 'mc', 'q': "So'roq gap oxirida qaysi belgi qo'yiladi?",
                 'options': ['.', '?', '!', ','], 'answer': 1,
                 'explain': "So'roq gap oxirida so'roq belgisi (?) qo'yiladi."},
                {'type': 'mc', 'q': 'Gap qanday harf bilan boshlanadi?',
                 'options': ['Kichik harf', 'Katta harf', 'Raqam bilan'], 'answer': 1,
                 'explain': 'Har qanday gap katta harf bilan boshlanadi.'},
                {'type': 'tf', 'q': "«Bugun havo issiq.» — bu darak gap.", 'answer': True,
                 'explain': "To'g'ri — biror narsani darak qilyapti, oxirida nuqta bor."},
                {'type': 'mc', 'q': "«Qanday chiroyli gul!» — bu qanday gap?",
                 'options': ['Darak gap', "So'roq gap", 'His-hayajon gap'], 'answer': 2,
                 'explain': 'Undov belgisi bor — his-hayajon gap.'},
                {'type': 'fill', 'q': "Darak gap oxirida qanday belgi qo'yiladi? (belgining o'zini yozing)",
                 'answer': '.', 'accept': ['nuqta'], 'explain': "Darak gap oxirida nuqta (.) qo'yiladi."},
            ],
            'homework': {
                'intro': 'Gaplar bilan ishlang.',
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "«Sen nima qilyapsan» gapining oxiriga qanday belgi kerak?",
                     'answer': '?', 'accept': ["so'roq belgisi", 'soroq belgisi', '?']},
                    {'id': 'h2', 'type': 'open', 'prompt': "O'zingiz bitta darak gap tuzing."},
                    {'id': 'h3', 'type': 'open', 'prompt': "O'zingiz bitta so'roq gap tuzing."},
                    {'id': 'h4', 'type': 'open', 'prompt': "«maktab» so'zi bilan bitta gap tuzing."},
                ],
            },
        },
        {
            'slug': 'katta-harf',
            'title': 'Katta harf va tinish belgilari',
            'summary': "Qachon katta harf yozilishini va tinish belgilarini o'rganamiz",
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': 'Katta harf qachon yoziladi?', 'body':
                 "Katta harf uch holatda yoziladi:\n\n"
                 "**1. Gap boshida**\n"
                 "**M**en maktabga bordim.\n\n"
                 "**2. Kishi ismlarida**\n"
                 "**A**li, **D**ilnoza, **A**limov **B**otir\n\n"
                 "**3. Joy nomlarida**\n"
                 "**T**oshkent, **S**amarqand, **O**ʻzbekiston, **A**mudaryo"},
                {'type': 'example', 'title': 'To\'g\'ri va noto\'g\'ri', 'body':
                 "❌ men toshkentda yashayman.\n"
                 "✅ **M**en **T**oshkentda yashayman.\n\n"
                 "❌ ali maktabga bordi\n"
                 "✅ **A**li maktabga bordi**.**"},
                {'type': 'text', 'title': 'Tinish belgilari', 'body':
                 "**Nuqta (.)** — darak gap oxirida\n"
                 "Misol: Kitob stolda turibdi.\n\n"
                 "**So'roq belgisi (?)** — savol oxirida\n"
                 "Misol: Kitob qayerda?\n\n"
                 "**Undov belgisi (!)** — kuchli his bildirganda\n"
                 "Misol: Qanday zo'r kitob!\n\n"
                 "**Vergul (,)** — sanashda so'zlarni ajratadi\n"
                 "Misol: Men olma, nok va uzum yedim."},
                {'type': 'note', 'body':
                 "Hayvon nomlari (laqablari) ham katta harf bilan yoziladi: "
                 "mushugimning ismi **Mosh**, itimning ismi **Bo'ribosar**."},
                {'type': 'steps', 'title': 'Gap yozishdan oldin tekshiring', 'items': [
                    'Birinchi harf katta bo\'lsinmi? — Ha, doim.',
                    'Ism yoki joy nomi bormi? — Bo\'lsa, katta harf.',
                    'Gap oxirida belgi qo\'yildimi?',
                    'Sanash bo\'lsa vergul qo\'yildimi?',
                ]},
                {'type': 'life', 'body':
                 "Xat yozganingizda, telefonda xabar yuborganingizda ham shu qoidalar amal qiladi. "
                 "To'g'ri yozgan odam savodli hisoblanadi."},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Qaysi gap to\'g\'ri yozilgan?',
                 'options': ['men toshkentda yashayman.', 'Men toshkentda yashayman.',
                             'Men Toshkentda yashayman.', 'men Toshkentda yashayman'], 'answer': 2,
                 'explain': "Gap boshi katta harf, joy nomi ham katta harf."},
                {'type': 'mc', 'q': 'Kishi ismlari qanday yoziladi?',
                 'options': ['Kichik harf bilan', 'Katta harf bilan', 'Farqi yo\'q'], 'answer': 1,
                 'explain': "Ismlar doim katta harf bilan boshlanadi."},
                {'type': 'mc', 'q': 'Sanashda so\'zlarni qaysi belgi ajratadi?',
                 'options': ['Nuqta', 'Vergul', 'Undov belgisi'], 'answer': 1,
                 'explain': "Vergul (,) sanashda ishlatiladi."},
                {'type': 'tf', 'q': "«Samarqand» so'zi katta harf bilan yoziladi.", 'answer': True,
                 'explain': "To'g'ri — bu shahar nomi, ya'ni joy nomi."},
                {'type': 'mc', 'q': "«Sen kelasanmi» gapining oxiriga nima qo'yamiz?",
                 'options': ['.', '?', '!', ','], 'answer': 1,
                 'explain': "Bu savol — so'roq belgisi kerak."},
                {'type': 'fill', 'q': "«ali» so'zini to'g'ri yozing.",
                 'answer': 'Ali', 'explain': "Ism — katta harf bilan: Ali."},
            ],
            'homework': {
                'intro': "Qoidalarni qo'llang.",
                'tasks': [
                    {'id': 'h1', 'type': 'text', 'prompt': "«dilnoza» so'zini to'g'ri yozing.",
                     'answer': 'Dilnoza'},
                    {'id': 'h2', 'type': 'text', 'prompt': "«buxoro» so'zini to'g'ri yozing.",
                     'answer': 'Buxoro'},
                    {'id': 'h3', 'type': 'open',
                     'prompt': "O'z ismingiz va shahringiz bilan bitta gap tuzing."},
                    {'id': 'h4', 'type': 'open',
                     'prompt': "Vergul ishlatib, uchta mevani sanab gap tuzing."},
                ],
            },
        },
    ],
}
