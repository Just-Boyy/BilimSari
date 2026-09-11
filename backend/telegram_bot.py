"""
BilimSari Telegram Bot
/start — Mini App ochish tugmasi
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, MenuButtonWebApp
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://bilimsari-production.up.railway.app')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or 'do‘st'
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text='📚 BilimSari’ni ochish',
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [InlineKeyboardButton(
            text='🌐 Brauzerda ochish',
            url=WEBAPP_URL
        )],
    ])
    text = (
        f'Salom, {name}! 👋\n\n'
        f'<b>BilimSari</b> — bilim olish platformasi.\n'
        f'Kurslar, testlar, XP va streak — hammasi Telegram ichida.\n\n'
        f'Pastdagi tugma orqali ilovani oching 👇'
    )
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Buyruqlar:\n'
        '/start — ilovani ochish\n'
        '/help — yordam\n\n'
        'O‘rganish uchun Mini App tugmasini bosing.'
    )


async def post_init(app: Application):
    # Chat menyusida Mini App tugmasi
    try:
        await app.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text='BilimSari',
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        )
        logger.info('Menu button o‘rnatildi: %s', WEBAPP_URL)
    except Exception as e:
        logger.warning('Menu button: %s', e)


def main():
    if not BOT_TOKEN:
        raise SystemExit('BOT_TOKEN muhit o‘zgaruvchisi yo‘q')

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_cmd))

    logger.info('Bot ishga tushdi (polling)...')
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
