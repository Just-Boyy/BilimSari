# BilimSari — Telegram Mini App + Bot

## 1. Bot yaratish (BotFather)

1. Telegramda [@BotFather](https://t.me/BotFather) oching
2. `/newbot` — nom va username bering (masalan `BilimSariBot`)
3. **Token**ni saqlang (`123456:ABC-DEF...`)
4. `/newapp` — botni tanlang
   - Title: `BilimSari`
   - Description: `Bilim olish platformasi`
   - Photo: logo (ixtiyoriy)
   - Web App URL: `https://bilimsari-production.up.railway.app`
   - Short name: `app`
5. `/setmenubutton` — xuddi shu URL
6. `/setdomain` — `bilimsari-production.up.railway.app`

Havola: `https://t.me/YourBotUsername/app`

## 2. Railway Variables

BilimSari servisida:

| Variable | Qiymat |
|----------|--------|
| `BOT_TOKEN` | BotFather tokeni |
| `WEBAPP_URL` | `https://bilimsari-production.up.railway.app` |
| `DATABASE_URL` | (allaqachon bor) |

## 3. Worker (bot polling)

Procfile da `worker: python telegram_bot.py` bor.

Railway’da **New Service** → same repo, root `backend`, start command:
```
python telegram_bot.py
```
Yoki bir servisda worker process qo‘shing.

## 4. Oqim

1. Foydalanuvchi botga `/start`
2. **BilimSari’ni ochish** → Mini App
3. Frontend `initData` yuboradi → `/api/telegram/auth`
4. Avtomatik login → `learn.html`
