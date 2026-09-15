# Production deploy — Oracle Cloud Always Free

Bu qo'llanma Bilim Sari'ni Oracle Cloud Always Free VM'da (Docker Compose + Caddy)
doimiy, bepul va sleep'siz ishlaydigan holatda joylashtirish uchun.

## 1. Oracle Cloud VM yaratish

1. https://www.oracle.com/cloud/free/ da ro'yxatdan o'ting.
2. Console → Compute → Instances → **Create Instance**.
3. Shape: **VM.Standard.A1.Flex (Ampere ARM)** — Always Free, 4 OCPU / 24GB RAM'gacha bepul.
4. Image: **Ubuntu 22.04**.
5. SSH kalit juftligini yarating, private key'ni saqlab qo'ying.
6. Instance yaratilgach, **Public IP** manzilini eslab qoling.
7. **Networking → Virtual Cloud Networks → (VCN) → Security Lists** →
   Default Security List → Add Ingress Rules:
   - Source `0.0.0.0/0`, TCP, Destination Port `80`
   - Source `0.0.0.0/0`, TCP, Destination Port `443`

## 2. Serverga ulanish va sozlash

```bash
ssh -i /path/to/key.pem ubuntu@<PUBLIC_IP>

git clone <sizning-github-repo-url> bilimsari
cd bilimsari

chmod +x scripts/setup-server.sh
./scripts/setup-server.sh
# Docker guruhi ta'sir qilishi uchun:
newgrp docker
```

## 3. Muhit o'zgaruvchilarini sozlash

```bash
cp .env.prod.example .env.prod
nano .env.prod
```

To'ldirish kerak bo'lgan qiymatlar:
- `DOMAIN` — public IP'ni nip.io formatiga o'tkazing: `130.61.12.34` → `130-61-12-34.nip.io`
- `POSTGRES_PASSWORD` — kuchli parol
- `JWT_SECRET` — kuchli tasodifiy satr (generatsiya: `openssl rand -base64 48`)
- `CORS_ORIGINS` va `WEBAPP_URL` va `VITE_API_BASE_URL` — `https://<DOMAIN>` asosida
- `BOT_TOKEN` — BotFather'dan olingan haqiqiy token

## 4. Deploy

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Bu: image'larni quradi, Postgres/Redis/backend/bot/frontend/Caddy'ni ishga tushiradi,
alembic migratsiyalarni avtomatik qo'llaydi (`backend/entrypoint.sh`), Caddy esa
`DOMAIN` uchun Let's Encrypt orqali avtomatik HTTPS sertifikat oladi.

## 5. Tekshirish

```bash
curl https://<DOMAIN>/api/../health   # yoki brauzerda https://<DOMAIN>/health agar health / da bo'lsa
```

`https://<DOMAIN>` — frontend (Mini App), `https://<DOMAIN>/api/*` — backend API.

## 6. BotFather'da Menu Button URL'ni yangilash

BotFather → botingiz → Edit Menu Button (yoki Bot Settings → Menu Button) →
URL sifatida `https://<DOMAIN>` ni qo'ying.

## Keyingi yangilanishlar

Kodga o'zgartirish kiritib, GitHub'ga push qilgach, serverda:

```bash
cd bilimsari
./scripts/deploy.sh
```

## Monitoring / foydali buyruqlar

```bash
# Loglarni ko'rish
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f backend
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f bot

# Konteynerlar holati
docker compose --env-file .env.prod -f docker-compose.prod.yml ps

# To'xtatish
docker compose --env-file .env.prod -f docker-compose.prod.yml down
```
