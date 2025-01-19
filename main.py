import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TELEGRAM_TOKEN
from weather import get_weather_update, send_weather_update
from message_utils import send_message_with_retries
from currency import get_currency_rate

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Функция для обработки команды /start
async def start(update: Update, context):
    logger.info(f"Команда /start получена от пользователя {update.effective_user.id}")
    bot = context.bot
    await send_message_with_retries(bot, update.effective_chat.id, "Привет! Я бот для получения погоды и курсов валют. Просто введи название города на украинском языке, чтобы узнать погоду. 😃")

# Функция для инициализации кнопок
async def show_buttons(update: Update, context):
    keyboard = [
        [
            InlineKeyboardButton("Погода", callback_data='weather'),
            InlineKeyboardButton("Курсы валют", callback_data='currency')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)

# Обработчик нажатия кнопок
async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == 'weather':
        await get_weather_update(update, context)
    elif query.data == 'currency':
        await get_currency_rate(update, context)

def main():
    # Создание бота и добавление обработчиков
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Обработчик команды /buttons
    application.add_handler(CommandHandler("buttons", show_buttons))

    # Обработчик нажатий кнопок
    application.add_handler(CallbackQueryHandler(button))

    # Обработчик текстовых сообщений и команд
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_update))

    # Запуск бота
    application.run_polling()

if __name__ == "main":
    main()
