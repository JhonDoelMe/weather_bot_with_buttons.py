import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import TELEGRAM_TOKEN
from user_data import save_user_data, load_user_data
from menu import show_menu, button  # Обновлен импорт
from message_utils import send_message_with_retries
from utils import request_city
from weather import get_weather

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
    schedule_auto_update(context, update.effective_chat.id)

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
    elif context.user_data.get('waiting_for_new_city'):
        new_city = update.message.text
        user_id = update.effective_user.id
        save_user_data(user_id, new_city)
        context.user_data['waiting_for_new_city'] = False
        await send_message_with_retries(context.bot, update.effective_chat.id, f"Город успешно изменен на {new_city}.")
        weather_info = await get_weather(new_city)
        await send_message_with_retries(context.bot, update.effective_chat.id, weather_info)
        await show_menu(update, context)
    else:
        await button(update, context)
    schedule_auto_update(context, update.effective_chat.id)

async def auto_update(context: CallbackContext):
    job = context.job
    city = job.data.get('city')
    chat_id = job.data.get('chat_id')
    if city:
        weather_info = await get_weather(city)
        await send_message_with_retries(context.bot, chat_id, weather_info)

def schedule_auto_update(context: CallbackContext, chat_id):
    job_queue = context.job_queue
    user_data = load_user_data(chat_id)
    city = user_data.get('city') if user_data else None
    if city:
        job_queue.run_repeating(auto_update, interval=7200, first=7200, data={'chat_id': chat_id, 'city': city})

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
