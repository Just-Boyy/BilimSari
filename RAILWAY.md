# Production deploy — Railway

Bilim Sari Railway'da 5ta servis sifatida ishlaydi (bitta `bilimsari` proyekt ichida,
`production` environment):

| Servis | Manba | Domen |
|---|---|---|
| Postgres | Railway managed plugin | ichki (`postgres.railway.internal`) |
| Redis | Railway managed plugin | ichki (`redis.railway.internal`) |
| backend | `backend/Dockerfile` | https://backend-production-ec58b.up.railway.app |
| bot | `bot/Dockerfile` (aiogram polling, portsiz) | — |
| frontend | `frontend/Dockerfile` (nginx, Vite build) | https://frontend-production-2cbf.up.railway.app |

Har bir servis o'z papkasidagi `railway.json` orqali **Dockerfile builder**'ga majburlangan
(Railway'ning standart Railpack auto-builder'i `backend/entrypoint.sh`dagi alembic
migratsiya qadamini chetlab o'tib yuborardi).

## Muhim: Railway trial

Hisob **$5 bir martalik trial kredit** bilan ishlaydi (30 kun yoki kredit tugaguncha).
Shundan keyin barcha konteynerlar to'xtaydi. Doimiy ishlashi uchun trial tugashidan oldin
Railway dashboard → Settings → Billing orqali **Hobby rejaga** ($5/oy dan boshlab, usage-based)
o'tish kerak.

## Muhit o'zgaruvchilari

`backend`:
- `DATABASE_URL` — `${{Postgres.PGUSER}}` va boshqa Postgres referencelari orqali (avtomatik yangilanadi)
- `REDIS_URL` — `${{Redis.REDIS_URL}}` referensi orqali
- `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `CORS_ORIGINS`, `DEFAULT_TEST_PASS_THRESHOLD`, `ENV=production`
- `BOT_TOKEN`, `WEBAPP_URL` (frontend domeniga)

`bot`: `BOT_TOKEN`, `WEBAPP_URL`

`frontend` (build-time, Dockerfile `ARG`): `VITE_API_BASE_URL` — backend domeni + `/api`

Ko'rish/o'zgartirish: `railway variable list --service <nomi> --kv`

## Qayta deploy qilish

Kod o'zgarganda (GitHub'ga push qilingandan keyin, lokal papkadan):

```bash
railway up ./backend --path-as-root --service backend --detach
railway up ./bot --path-as-root --service bot --detach
railway up ./frontend --path-as-root --service frontend --detach
```

Holatni tekshirish:

```bash
railway status
railway logs --service backend
```

## Keyingi qadam: BotFather

BotFather → botingiz → Bot Settings → Menu Button → URL sifatida qo'ying:

```
https://frontend-production-2cbf.up.railway.app
```

## Muqobil: Oracle Cloud

Agar kelajakda Railway'dan Oracle Cloud Always Free VM'ga o'tish kerak bo'lsa, to'liq
qo'llanma `DEPLOY.md`da tayyor turibdi (`docker-compose.prod.yml`, `Caddyfile`, `scripts/`).
