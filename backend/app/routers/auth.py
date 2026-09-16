import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.rate_limit import limiter
from app.db.models import User, UserLang
from app.deps import get_db
from app.schemas.auth import SimpleRegisterRequest, TelegramAuthRequest, TelegramAuthResponse, UserOut
from app.security.jwt import create_access_token
from app.security.telegram_auth import InitDataValidationError, validate_init_data

router = APIRouter(prefix="/api/auth", tags=["auth"])

_SUPPORTED_LANGS = {"uz", "ru", "en"}
# Faqat lokal brauzerda (Telegram'siz) UI'ni sinash uchun ishlatiladigan doimiy dev foydalanuvchi.
_DEV_TELEGRAM_ID = 1_000_000_001


async def _upsert_user(db: AsyncSession, telegram_id: int, username: str | None, first_name: str | None, lang: str) -> User:
    user = (await db.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()

    if user is None:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name, lang=UserLang(lang))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    changed = False
    if username and user.username != username:
        user.username = username
        changed = True
    if first_name and user.first_name != first_name:
        user.first_name = first_name
        changed = True
    if changed:
        await db.commit()
        await db.refresh(user)
    return user


@router.post("/telegram", response_model=TelegramAuthResponse)
@limiter.limit("20/minute")
async def auth_telegram(
    request: Request,
    payload: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> TelegramAuthResponse:
    try:
        data = validate_init_data(payload.init_data)
    except InitDataValidationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    lang_code = (data.get("language_code") or "uz")[:2]
    lang = lang_code if lang_code in _SUPPORTED_LANGS else "uz"

    user = await _upsert_user(db, data["telegram_id"], data.get("username"), data.get("first_name"), lang)

    token = create_access_token(user.id, user.telegram_id)
    return TelegramAuthResponse(token=token, user=UserOut.model_validate(user))


async def _generate_guest_telegram_id(db: AsyncSession) -> int:
    """Haqiqiy Telegram ID'lar doim musbat bo'lgani uchun manfiy raqamlar bilan
    to'qnashuv ehtimoli yo'q — shunchaki ism bilan ro'yxatdan o'tgan mehmon
    foydalanuvchilar uchun sun'iy, noyob identifikator."""
    for _ in range(5):
        candidate = -secrets.randbits(62)
        exists = (await db.execute(select(User.id).where(User.telegram_id == candidate))).scalar_one_or_none()
        if exists is None:
            return candidate
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="ID generatsiya qilib bo'lmadi")


@router.post("/register", response_model=TelegramAuthResponse)
@limiter.limit("20/minute")
async def auth_register(
    request: Request,
    payload: SimpleRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TelegramAuthResponse:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Ism bo'sh bo'lishi mumkin emas")

    guest_id = await _generate_guest_telegram_id(db)
    user = User(telegram_id=guest_id, username=None, first_name=name[:128], lang=UserLang.uz)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.telegram_id)
    return TelegramAuthResponse(token=token, user=UserOut.model_validate(user))


@router.post("/dev-login", response_model=TelegramAuthResponse)
async def auth_dev_login(db: AsyncSession = Depends(get_db)) -> TelegramAuthResponse:
    """Telegram'siz, oddiy brauzerda UI'ni sinash uchun — initData tekshiruvisiz kirish.

    Faqat ENV=development bo'lganda ishlaydi; production'da 404 qaytaradi
    (funksiya mavjudligini ham bildirmaslik uchun).
    """
    if settings.env != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    user = await _upsert_user(db, _DEV_TELEGRAM_ID, "dev_user", "Dev", "uz")
    token = create_access_token(user.id, user.telegram_id)
    return TelegramAuthResponse(token=token, user=UserOut.model_validate(user))
