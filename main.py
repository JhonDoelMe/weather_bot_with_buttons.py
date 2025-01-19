import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from pytz import timezone
from config import TELEGRAM_TOKEN
from user_data import save_user_data, load_user_data
from menu import show_menu, button
from message_utils import send_message_with_retries
from utils import request_city
from notifications import send_notification, send_daily_weather_update, schedule_daily_weather_update, schedule_auto_update

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Исправлена опечатка в 'levellevel'
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context):
    try:
        user_id = update.effective_user.id
        user_data = load_user_data(user_id)
        
        if user_data and user_data.get('city'):
            city = user_data['city']
            await send_message_with_retries(context.bot, update.effective_chat.id, f"С возвращением! Ваш текущий город: {city}.")
            weather_info = await get_weather(city)
            await send_message_with_retries(context.bot, update.effective_chat.id, weather_info)
        else:
            save_user_data(user_id, city=None)
            await send_message_with_retries(context.bot, update.effective_chat.id, "Привет! Я бот для получения погоды и курса гривны. Пожалуйста, введите название города:")
            context.user_data['waiting_for_city'] = True
        
        await show_menu(update, context)
        schedule_daily_weather_update(context, update.effective_chat.id, timezone('Europe/Kiev'))  # Установите ваш часовой пояс
        
        # Проверяем, получал ли пользователь уведомление
        if not user_data or not user_data.get('notified'):
            context.job_queue.run_once(send_notification, 300, data={'chat_id': update.effective_chat.id, 'user_id': user_id})
    except Exception as e:
        logger.error(f"Ошибка в функции start: {e}")
        await send_message_with_retries(context.bot, update.effective_chat.id, "Произошла ошибка. Попробуйте снова позже.")
    schedule_auto_update(context, update.effective_chat.id)

async def save_city(update: Update, context):
    if context.user_data.get('waiting_for_city'):
        city = update.message.text
        if city.lower() in ['погода', 'курс гривны', 'изменить город']:  # Добавим проверку на текст кнопок
            await send_message_with_retries(context.bot, update.effective_chat.id, "Некорректный ввод. Пожалуйста, введите название города:")
            return
        
        user_id = update.effective_user.id
        save_user_data(user_id, city)
        context.user_data['waiting_for_city'] = False
        await send_message_with_retries(context.bot, update.effective_chat.id, f"Город {city} сохранен для пользователя {user_id}.")
        weather_info = await get_weather(city)
        await send_message_with_retries(context.bot, update.effective_chat.id, weather_info)
        await show_menu(update, context)
        schedule_daily_weather_update(context, update.effective_chat.id, timezone('Europe/Kiev'))  # Установите ваш часовой пояс

        # Проверяем, получал ли пользователь уведомление
        user_data = load_user_data(user_id)
        if not user_data.get('notified'):
            context.job_queue.run_once(send_notification, 300, data={'chat_id': update.effective_chat.id, 'user_id': user_id})
    elif context.user_data.get('waiting_for_new_city'):
        new_city = update.message.text
        if new_city.lower() in ['погода', 'курс гривны', 'изменить город']:  # Добавим проверку на текст кнопок
            await send_message_with_retries(context.bot, update.effective_chat.id, "Некорректный ввод. Пожалуйста, введите название нового города:")
            return

        user_id = update.effective_user.id
        save_user_data(user_id, new_city)
        context.user_data['waiting_for_new_city'] = False
        await send_message_with_retries(context.bot, update.effective_chat.id, f"Город успешно изменен на {new_city}.")
        weather_info = await get_weather(new_city)
        await send_message_with_retries(context.bot, update.effective_chat.id, weather_info)
        await show_menu(update, context)
        schedule_daily_weather_update(context, update.effective_chat.id, timezone('Europe/Kiev'))  # Установите ваш часовой пояс

        # Проверяем, получал ли пользователь уведомление
        user_data = load_user_data(user_id)
        if not user_data.get('notified'):
            context.job_queue.run_once(send_notification, 300, data={'chat_id': update.effective_chat.id, 'user_id': user_id})
    else:
        await button(update, context)
    schedule_auto_update(context, update.effective_chat.id)

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
