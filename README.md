# Bilim Sari

Telegram Mini App (WebApp) + bot ko'rinishidagi ta'lim platformasi. Sun'iy intellekt ishlatilmaydi —
barcha kontent admin tomonidan kiritiladi, tizim faqat ko'rsatadi, tekshiradi va hisoblaydi.

**Joriy holat: Bosqich 1** — to'liq DB sxemasi, Telegram auth, fanlar/bo'limlar/mavzular ko'rish,
dars (lesson) o'qish va progress belgilash ishlaydi. Test/Quiz/Uy vazifasi, gamifikatsiya, admin
panel UI — keyingi bosqichlar.

## Tuzilma

```
backend/    FastAPI + SQLAlchemy(async) + Alembic + PostgreSQL/Redis
bot/        aiogram 3.x Telegram bot (/start + Mini App tugmasi)
frontend/   React + TypeScript + Tailwind + @twa-dev/sdk (Vite)
```

## Talab qilinadigan vositalar

- Python 3.12+ (loyiha 3.14'da sinovdan o'tgan)
- Node.js 20+
- Docker Desktop (Postgres + Redis uchun)

## 1. Muhit sozlamalari

Root papkadagi `.env.example`ni nusxalab, qiymatlarni to'ldiring:

```bash
cp .env.example .env
```

Har bir servis o'z ishga tushirish papkasidan `.env` faylini o'qiydi, shuning uchun uni
`backend/.env`, `bot/.env` va (kerak bo'lsa) `frontend/.env` ga ham nusxalang — har birining
o'z `.env.example`i mavjud.

`BOT_TOKEN` — BotFather'dan olingan haqiqiy token (Telegram initData tekshiruvi shu token bilan
ishlaydi). `WEBAPP_URL` — Mini App joylashgan URL (lokal ishlab chiqishda ngrok/cloudflared kabi
tunnel orqali `http://localhost:5173`ni oching, chunki Telegram faqat HTTPS URL qabul qiladi).

## 2. Postgres + Redis

```bash
docker compose up -d postgres redis
```

## 3. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt

alembic upgrade head           # migratsiyalarni qo'llash
python -m scripts.seed         # namunaviy ma'lumotlar (10 fan, 20 mavzu, 3 tilda)

uvicorn app.main:app --reload  # http://localhost:8000
```

Testlarni ishga tushirish (Postgres+Redis ishlab turgan bo'lishi kerak — testlar dev bazasiga
ulanadi, jadvallarni o'chirmaydi):

```bash
pytest -q
```

## 4. Bot

```bash
cd bot
pip install -r requirements.txt
python -m bot.main
```

`/start` buyrug'i Mini App'ni ochish tugmasini yuboradi. Foydalanuvchi bazaga bot orqali emas,
Mini App ochilganda (`POST /api/auth/telegram`) yoziladi — bu yagona, ziddiyatsiz registratsiya
yo'li.

## 5. Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Telegram WebView'da sinash uchun `npm run dev` serverini ngrok/cloudflared bilan HTTPS'ga
tunnellang va shu URL'ni BotFather'dagi Menu Button / `WEBAPP_URL`ga qo'ying.

## 6. To'liq Docker (ixtiyoriy)

Backend/frontend uchun Dockerfile'lar tayyor, lekin standart dev oqimiga ulanmagan (tezroq
hot-reload uchun). To'liq konteynerlashtirilgan holatda ishga tushirish:

```bash
docker compose --profile full up -d --build
```

## Qo'lda tekshirish (smoke test)

1. `curl http://localhost:8000/health` → `{"status":"ok"}`
2. Telegram Mini App'ni ochib, Splash → Onboarding → Subjects → Sections → Topics → Dars
   oqimini bosib chiqing; "Tushundim" tugmasidan so'ng mavzu ✅ bo'lishi, 2-mavzu esa hali
   🔒 (Test bosqichi Bosqich-2'da qo'shiladi) bo'lib qolishi kerak.

## Bosqich-1'da QILINMAGAN

Test topshirish, Quiz, Uy vazifasi topshirish/tekshirish, gamifikatsiya yozish mantig'i, Admin
panel UI, Reyting, Statistika, Bot bildirishnomalari (eslatma/natija/haftalik xulosa).
