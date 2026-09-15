from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.webapp import open_app_keyboard

router = Router(name="start")

WELCOME_TEXT = (
    "Bilim Sari'ga xush kelibsiz! 📖\n"
    "Har kuni bir qadam bilim sari.\n\n"
    "Boshlash uchun quyidagi tugmani bosing:"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    # Eslatma: foydalanuvchi shu yerda bazaga yozilmaydi — Mini App ochilganda
    # frontend /api/auth/telegram'ni chaqiradi va shu yerda user upsert bo'ladi
    # (yagona, ziddiyatsiz registratsiya yo'li).
    await message.answer(WELCOME_TEXT, reply_markup=open_app_keyboard())
