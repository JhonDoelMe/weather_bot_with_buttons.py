import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TELEGRAM_TOKEN
from weather import get_weather_update
from buttons import show_menu, button
from message_utils import send_message_with_retries

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
    await send_message_with_retries(bot, update.effective_chat.id, "Привет! Я бот для получения погоды и курсов валют. Просто введи название города на украинском языке, чтобы узнать погоду. 😃\nДля просмотра меню нажмите /menu.")

def main():
    # Создание бота и добавление обработчиков
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Обработчик команды /menu
    application.add_handler(CommandHandler("menu", show_menu))

    # Обработчик нажатий кнопок
    application.add_handler(CallbackQueryHandler(button))

    # Обработчик текстовых сообщений и команд
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_update))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
