#!/bin/bash
# Serverda loyihani deploy qilish/yangilash uchun.
# Foydalanish: repo root'da: ./scripts/deploy.sh

set -e
cd "$(dirname "$0")/.."

if [ ! -f .env.prod ]; then
    echo "XATO: .env.prod topilmadi. Avval quyidagini bajaring:"
    echo "  cp .env.prod.example .env.prod"
    echo "va qiymatlarni to'ldiring."
    exit 1
fi

git pull

docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build

echo ""
echo "== Holat =="
docker compose --env-file .env.prod -f docker-compose.prod.yml ps

echo ""
echo "== Backend loglari (oxirgi 30 qator) =="
docker compose --env-file .env.prod -f docker-compose.prod.yml logs --tail 30 backend
