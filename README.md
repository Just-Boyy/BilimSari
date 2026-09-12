# BilimSari

O'zbek maktab o'quvchilari uchun raqamli ta'lim platformasi.

O'quvchi sinfini tanlaydi → o'z sinfidagi fanlarni ko'radi → mavzularni maktab
dasturi tartibida o'rganadi. Har bir mavzu uchta bosqichdan iborat:

```
Dars  →  Quiz  →  Uyga vazifa  →  Mavzu tugallandi  →  24 soat  →  Keyingi mavzu ochiladi
```

Kuniga faqat **bitta** mavzu yakunlanadi — bilim shoshilmasdan o'zlashtirilsin.

---

## Texnologiyalar

| Qatlam | Nima ishlatilgan |
|--------|------------------|
| Backend | Python 3 + Flask |
| Baza | PostgreSQL (ishlab chiqarish), SQLite (lokal — hech narsa o'rnatmasdan) |
| Frontend | Toza HTML + CSS + vanilla JS (framework yo'q), PWA |
| AI | Google Gemini — faqat **qo'shimcha** tushuntirish uchun |
| Kirish | Email/parol yoki Telegram Mini App |

---

## Lokal ishga tushirish

```bash
cd backend
python -m venv ../.venv
../.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source ../.venv/bin/activate && pip install -r requirements.txt  # Linux/Mac

python -m flask --app app run --port 5000
```

`DATABASE_URL` bo'lmasa avtomatik **SQLite** ga tushadi (`backend/bilimsari.db`) —
PostgreSQL o'rnatish shart emas.

Brauzerda oching: http://127.0.0.1:5000

---

## Muhit o'zgaruvchilari

| O'zgaruvchi | Kerakmi | Tavsif |
|-------------|---------|--------|
| `DATABASE_URL` | ishlab chiqarishda | PostgreSQL ulanishi. Bo'lmasa SQLite |
| `SECRET_KEY` | ha | Token va parol xeshi uchun. **Albatta o'zgartiring** |
| `BOT_TOKEN` | Telegram uchun | BotFather tokeni. **Kodda saqlanmaydi** |
| `WEBAPP_URL` | Telegram uchun | Mini App manzili |
| `GOOGLE_AI_API_KEY` | AI uchun | aistudio.google.com dan olinadi |
| `GEMINI_MODEL` | yo'q | Standart: `gemini-2.5-flash` |
| `QUIZ_PASS_PERCENT` | yo'q | Quizdan o'tish chegarasi, standart **70** |
| `COOLDOWN_HOURS` | yo'q | Mavzular orasidagi kutish, standart **24** |
| `AI_RATE_LIMIT` | yo'q | Bitta foydalanuvchiga daqiqasiga so'rov, standart 12 |

---

## Fayllar tuzilishi

```
backend/
├── app.py                  Flask ilovasi, auth, Telegram webhook
├── db.py                   Baza qatlami (PostgreSQL / SQLite)
├── auth_core.py            Token, parol xeshi (PBKDF2)
├── study.py                O'qish dvigateli: progress, 24 soat, baholash
├── study_api.py            /api/study/* endpointlari
├── ai_tutor.py             /api/ai/* — qo'shimcha AI yordamchi
├── curriculum/             ★ RASMIY DARSLAR (qo'lda yozilgan)
│   ├── __init__.py         Fanlar katalogi, sinflar registri
│   ├── grade01.py          1-sinf fanlar ro'yxati
│   ├── g01_math.py         1-sinf matematika mavzulari
│   └── ...
├── validate_curriculum.py  Darslarni tekshirish
├── test_flow.py            Backend testlari
├── tests/ui_test.js        Frontend testlari (jsdom)
│
├── css/app.css             Butun dizayn tizimi
├── js/api.js               API klienti
├── js/ui.js                Umumiy UI komponentlari
├── js/telegram.js          Telegram Mini App
│
├── index.html              Kirish ekrani
├── onboarding.html         Sinf va fan tanlash
├── dashboard.html          Bosh sahifa
├── subjects.html           Fanlar
├── topics.html             Mavzular yo'li
├── topic.html              Dars / Quiz / Uyga vazifa
├── progress.html           Natijalar
├── profile.html            Profil
│
└── learn.html, lesson.html, courses.html, review.html
    Eski AI-darslar oqimi — saqlanib qolgan, ishlaydi
```

---

## Yangi dars qo'shish

Darslar **kodda** saqlanadi (`curriculum/` papkasida), bazaga esa ishga tushganda
avtomatik ko'chiriladi. Shuning uchun dars qo'shish uchun bazaga tegish shart emas.

**1.** Fan fayli yarating, masalan `curriculum/g03_math.py`:

```python
MATH = {
    'key': 'math',                  # SUBJECT_CATALOG dagi kalit
    'topics': [
        {
            'slug': 'sonlar',       # URL da ishlatiladi, takrorlanmasin
            'title': 'Sonlar',
            'summary': 'Qisqa tavsif',
            'duration': 15,
            'lesson': [
                {'type': 'text', 'title': 'Sarlavha', 'body': 'Matn...'},
                {'type': 'example', 'title': 'Misol', 'body': '...'},
                {'type': 'note', 'body': 'Esda tuting: ...'},
            ],
            'quiz': [
                {'type': 'mc', 'q': 'Savol?', 'options': ['A', 'B'],
                 'answer': 0, 'explain': 'Chunki...'},
            ],
            'homework': {
                'intro': 'Vazifani bajaring.',
                'tasks': [
                    {'id': 'h1', 'type': 'number', 'prompt': '2 + 2 = ?', 'answer': '4'},
                    {'id': 'h2', 'type': 'open', 'prompt': 'O\'z misolingizni yozing.'},
                ],
            },
        },
    ],
}
```

**2.** Sinf faylini yarating — `curriculum/grade03.py`:

```python
from .g03_math import MATH
SUBJECTS = [MATH]
```

**3.** `curriculum/__init__.py` dagi `_GRADE_MODULES` ga qo'shing:

```python
_GRADE_MODULES = {
    1: 'curriculum.grade01',
    3: 'curriculum.grade03',   # ← yangi
    5: 'curriculum.grade05',
    9: 'curriculum.grade09',
}
```

**4.** Tekshiring va ishga tushiring:

```bash
python validate_curriculum.py   # xatolarni topadi
python -m flask --app app run   # baza avtomatik yangilanadi
```

### Blok turlari (dars matni uchun)

| Tur | Maydonlar | Ko'rinishi |
|-----|-----------|------------|
| `text` | title, body | Oddiy matn |
| `example` | title, body | Ko'k fonli misol |
| `note` | body | Sariq chiziqli eslatma |
| `life` | body | Yashil "Hayotdan" bloki |
| `formula` | body | Katta, markazlashgan formula |
| `steps` | title, items[] | Raqamlangan qadamlar |
| `table` | head[], rows[][] | Jadval |

`body` ichida `**qalin**` va qator ko'chirish (`\n`) ishlaydi.

### Savol turlari

| Tur | Maydonlar |
|-----|-----------|
| `mc` | q, options[], answer (indeks 0 dan), explain |
| `tf` | q, answer (True/False), explain |
| `fill` | q, answer, accept[] (muqobil javoblar), explain |

### Uy vazifasi turlari

| Tur | Izoh |
|-----|------|
| `number` | Son javob, avtomatik tekshiriladi |
| `text` | Matn javob, avtomatik tekshiriladi (`accept[]` bilan muqobillar) |
| `open` | Erkin javob — tekshirilmaydi, faqat yozilgani qayd etiladi |

---

## Testlar

```bash
cd backend

# 1. Darslar butunligi
python validate_curriculum.py

# 2. Backend: to'liq o'quv oqimi (73 ta tekshiruv)
python test_flow.py

# 3. Frontend: haqiqiy sahifalar jsdom da (63 ta tekshiruv)
python -m flask --app app run --port 5055 &
cd tests && npm install jsdom && node ui_test.js
```

---

## 24 soatlik qoida qanday ishlaydi

* Vaqt **serverda**, `user_progress.completed_at` ustuni asosida hisoblanadi
  (UTC da saqlanadi, foydalanuvchiga **Toshkent vaqtida** ko'rsatiladi).
* Brauzerni yangilash, chiqib qayta kirish, boshqa qurilma yoki kompyuter
  soatini o'zgartirish hech narsani o'zgartirmaydi.
* Kutish **global**: bir kunda jami bitta mavzu, hamma fanlar bo'yicha.
* Ikki joydan tekshiriladi:
  1. mavzuni **ochishda** — yangi mavzu qulflangan bo'ladi;
  2. mavzuni **yakunlashda** — allaqachon boshlangan mavzuni ham yakunlab bo'lmaydi.

## Xavfsizlik

* Quiz va uy vazifasining **to'g'ri javoblari frontendga yuborilmaydi** —
  baholash faqat serverda.
* Progress faqat `study.py` orqali o'zgaradi; `localStorage` ni tahrirlash
  hech qanday mavzuni ochmaydi.
* Parollar PBKDF2-HMAC-SHA256 (120 000 iteratsiya) bilan, har foydalanuvchi
  uchun alohida salt bilan xeshlanadi. Eski SHA-256 xeshlar kirish paytida
  avtomatik yangi formatga ko'chiriladi.
* `BOT_TOKEN` kodda saqlanmaydi — faqat muhit o'zgaruvchisidan olinadi.
* AI endpointlari avtorizatsiya talab qiladi va tezlik chegarasi bilan himoyalangan.

## AI yordamchining o'rni

AI **rasmiy darsni almashtirmaydi**. U mavzu sahifasida alohida, aniq belgilangan
blokda turadi va faqat o'quvchi hozir o'qiyotgan **sinf + fan + mavzu** doirasida
ishlaydi. Uchta rejimi bor: oddiyroq tushuntirish, qo'shimcha misollar, qisqa xulosa.
AI javoblari bazaga dars sifatida saqlanmaydi.
