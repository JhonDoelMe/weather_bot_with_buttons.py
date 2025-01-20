import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import TELEGRAM_TOKEN
from user_data import save_user_data, load_user_data
from menu import show_menu, button
from message_utils import send_message_with_retries
from air_alarm import get_air_alarm_status  # Импортируем функцию для получения статуса воздушной тревоги
from weather import get_weather

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Исправлена опечатка
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
            if weather_info:
                await send_message_with_retries(context.bot, update.effective_chat.id, weather_info)
            else:
                logger.error("Не удалось получить данные о погоде.")
        else:
            save_user_data(user_id, city=None)
            await send_message_with_retries(context.bot, update.effective_chat.id, "Привет! Я бот для получения погоды и курса гривны. Пожалуйста, введите название города:")
            context.user_data['waiting_for_city'] = True
        
        await show_menu(update, context)
    except Exception as e:
        logger.error(f"Ошибка в функции start: {e}")
        await send_message_with_retries(context.bot, update.effective_chat.id, "Произошла ошибка. Попробуйте снова позже.")

async def save_city(update: Update, context):
    if context.user_data.get('waiting_for_city'):
        city = update.message.text
        if city.lower() in ['погода', 'курс гривны', 'изменить город']:
            await send_message_with_retries(context.bot, update.effective_chat.id, "Некорректный ввод. Пожалуйста, введите название города:")
            return
        
        user_id = update.effective_user.id
        save_user_data(user_id, city)
        context.user_data['waiting_for_city'] = False
        await send_message_with_retries(context.bot, update.effective_chat.id, f"Город {city} сохранен для пользователя {user_id}.")
        weather_info = await get_weather(city)
        if weather_info:
            await send_message_with_retries(context.bot, update.effective_chat.id, weather_info)
        else:
            logger.error("Не удалось получить данные о погоде.")
        await show_menu(update, context)
    elif context.user_data.get('waiting_for_new_city'):
        new_city = update.message.text
        if new_city.lower() in ['погода', 'курс гривны', 'изменить город']:
            await send_message_with_retries(context.bot, update.effective_chat.id, "Некорректный ввод. Пожалуйста, введите название нового города:")
            return

        user_id = update.effective_user.id
        save_user_data(user_id, new_city)
        context.user_data['waiting_for_new_city'] = False
        await send_message_with_retries(context.bot, update.effective_chat.id, f"Город успешно изменен на {new_city}.")
        weather_info = await get_weather(new_city)
        if weather_info:
            await send_message_with_retries(context.bot, update.effective_chat.id, weather_info)
        else:
            logger.error("Не удалось получить данные о погоде.")
        await show_menu(update, context)
    else:
        await button(update, context)

async def request_air_alarm(update: Update, context):
    alarm_status = get_air_alarm_status()
    if alarm_status:
        await send_message_with_retries(context.bot, update.effective_chat.id, alarm_status)
    else:
        await send_message_with_retries(context.bot, update.effective_chat.id, "Не удалось получить данные о воздушных тревогах.")

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
