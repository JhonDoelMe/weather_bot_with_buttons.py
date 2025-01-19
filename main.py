import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
from user_data import save_user_data, load_user_data
from buttons import show_menu, button
from message_utils import send_message_with_retries
from utils import request_city
from weather import get_weather  # Добавлен импорт

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context):
    try:
        user_id = update.effective_user.id
        logger.info(f"Команда /start получена от пользователя {user_id}")
        save_user_data(user_id, city=None)
        await send_message_with_retries(context.bot, update.effective_chat.id, "Привет! Я бот для получения погоды и курса гривны. Просто выберите нужную опцию. 😃")
        await show_menu(update, context)
    except Exception as e:
        logger.error(f"Ошибка в функции start: {e}")
        await send_message_with_retries(context.bot, update.effective_chat.id, "Произошла ошибка. Попробуйте снова позже.")

async def save_city(update: Update, context):
    if context.user_data.get('waiting_for_city'):
        city = update.message.text
        user_id = update.effective_user.id
        save_user_data(user_id, city)
        context.user_data['waiting_for_city'] = False
        await send_message_with_retries(context.bot, update.effective_chat.id, f"Город {city} сохранен для пользователя {user_id}.")
        weather_info = await get_weather(city)
        await send_message_with_retries(context.bot, update.effective_chat.id, weather_info)
        await show_menu(update, context)
    else:
        await button(update, context)

def main():
    logger.info("Запуск бота...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    logger.info("Добавление обработчика команды /start")
    application.add_handler(CommandHandler("start", start))
    
    logger.info("Добавление обработчика команды /menu")
    application.add_handler(CommandHandler("menu", show_menu))

    logger.info("Добавление обработчика текстовых сообщений")
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_city))
    
    logger.info("Запуск опроса...")
    application.run_polling()

if __name__ == "__main__":
    main()
