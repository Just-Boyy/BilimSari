import random

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.base import Base
from app.db.session import engine
from app.main import app
from scripts.seed import seed as seed_data
from tests.helpers import build_init_data


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_database():
    # DIQQAT: bu testlar odatiy dev Postgres bazasiga ulanadi (alohida test bazasi
    # yo'q — Bosqich-1 sodda sozlamasi). create_all/seed idempotent bo'lgani uchun
    # xavfsiz qayta ishga tushiriladi; shuning uchun ataylab drop_all QILINMAYDI —
    # aks holda testlar tugagach dev bazadagi barcha jadvallar o'chib ketardi.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_token(client):
    # Har bir test o'z alohida foydalanuvchisiga ega bo'lishi uchun tasodifiy
    # telegram_id - bu testlar orasida progress holati aralashib ketmasligini ta'minlaydi.
    init_data = build_init_data(telegram_id=random.randint(10**9, 2 * 10**9))
    resp = await client.post("/api/auth/telegram", json={"init_data": init_data})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]
