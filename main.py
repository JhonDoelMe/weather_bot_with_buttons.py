import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import TELEGRAM_TOKEN
from user_data import save_user_data, load_user_data, subscribe_user, unsubscribe_user
from message_utils import send_message_with_retries
from air_alarm import get_air_alarm_status, get_or_fetch_region, parse_air_alarm_data
from weather import get_weather
from menu import show_menu
from notifications import check_air_alerts  # Импортируем функцию check_air_alerts

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

INVALID_CITY_NAMES = ['погода', 'курс гривны', 'изменить город', 'тревога']

async def start(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id
        user_data = load_user_data(user_id)

        if user_data and user_data.get('city'):
            city = user_data['city']
            await update.message.reply_text(f"С возвращением! Ваш текущий город: {city}.")
            weather_info = await get_weather(city)
            if weather_info:
                await update.message.reply_text(weather_info)
            else:
                logger.error("Не удалось получить данные о погоде.")
        else:
            save_user_data(user_id, city=None)
            await update.message.reply_text("Привет! Я бот для получения погоды и курса гривны. Пожалуйста, введите название города:")
            context.user_data['waiting_for_city'] = True
        
        await show_menu(update, context)
    except Exception as e:
        logger.error(f"Ошибка в функции start: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте снова позже.")

async def save_city(update: Update, context: CallbackContext):
    if context.user_data.get('waiting_for_city'):
        city = update.message.text
        region = await get_or_fetch_region(city)
        
        if not region:
            await update.message.reply_text(
                f"Не удалось найти информацию о городе {city}. Пожалуйста, введите другой город."
            )
            return
        
        user_id = update.effective_user.id
        save_user_data(user_id, city)
        context.user_data['waiting_for_city'] = False
        await update.message.reply_text(f"Город {city} сохранен для пользователя {user_id}.")
        
        weather_info = await get_weather(city)
        if weather_info:
            await update.message.reply_text(weather_info)
        else:
            await update.message.reply_text("Не удалось получить данные о погоде.")
        
        await show_menu(update, context)

def main():
    logger.info("Запуск бота...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_city))

    # Запускаем периодическую проверку тревог
    application.job_queue.run_repeating(check_air_alerts, interval=300, first=10)

    application.run_polling()

if __name__ == "__main__":
    main()