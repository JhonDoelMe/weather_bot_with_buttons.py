import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
from weather import get_weather_update
from buttons import show_menu, button
from message_utils import send_message_with_retries

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context):
    try:
        logger.info(f"Команда /start получена от пользователя {update.effective_user.id}")
        await send_message_with_retries(context.bot, update.effective_chat.id, "Привет! Я бот для получения погоды и курса гривны. Просто введи название города на украинском языке, чтобы узнать погоду. 😃\nДля просмотра меню нажмите /menu.")
        await show_menu(update, context)
    except Exception as e:
        logger.error(f"Ошибка в функции start: {e}")
        await send_message_with_retries(context.bot, update.effective_chat.id, "Произошла ошибка. Попробуйте снова позже.")

def main():
    logger.info("Запуск бота...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    logger.info("Добавление обработчика команды /start")
    application.add_handler(CommandHandler("start", start))
    
    logger.info("Добавление обработчика команды /menu")
    application.add_handler(CommandHandler("menu", show_menu))
    
    logger.info("Добавление обработчика текстовых сообщений")
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button))
    
    logger.info("Запуск опроса...")
    application.run_polling()

if __name__ == "__main__":
    main()
