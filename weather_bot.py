import os
import logging
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, JobQueue, ConversationHandler
from telegram.error import TimedOut
from dotenv import load_dotenv
from cachetools import TTLCache
from aiohttp import ClientError, ServerTimeoutError

# Завантаження змінних середовища з файлу .env
if not os.path.isfile('.env'):
    raise FileNotFoundError("Файл .env не знайдено. Переконайтеся, що файл .env присутній у кореневій директорії проекту.")
load_dotenv()

# Отримання токенів зі змінних середовища
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Перевірка наявності токенів
if not TELEGRAM_TOKEN or not WEATHER_API_KEY:
    raise ValueError("Необхідні токени відсутні. Перевірте, що вони вказані у файлі .env")

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Встановіть рівень логування на INFO для відладки
)
logger = logging.getLogger(__name__)

# Емодзі для різних станів погоди
weather_emojis = {
    "ясно": "☀️",
    "перемінна хмарність": "⛅️",
    "хмарно з проясненнями": "🌤",
    "хмарно": "☁️",
    "пасмурно": "☁️",
    "дощ": "🌧",
    "гроза": "⛈",
    "сніг": "❄️",
    "туман": "🌫"
}

# Кеш для даних про погоду
weather_cache = TTLCache(maxsize=100, ttl=600)

# Функція для отримання емодзі за описом погоди
def get_weather_emoji(description):
    for key in weather_emojis:
        if key in description:
            return weather_emojis[key]
    return ""

# Асинхронна функція для отримання погоди з OpenWeatherMap API
async def get_weather(city):
    if not city:
        return "Назва міста не може бути порожньою."

    if city in weather_cache:
        return weather_cache[city]

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    weather = data['weather'][0]['description']
                    temp = data['main']['temp']
                    feels_like = data['main']['feels_like']
                    humidity = data['main']['humidity']
                    pressure = data['main']['pressure']
                    weather_emoji = get_weather_emoji(weather)

                    weather_info = (
                        f"Погода в {city}:\n"
                        f"Опис: {weather} {weather_emoji}\n"
                        f"Температура: {temp}°C 🌡️\n"
                        f"Відчувається як: {feels_like}°C 🌡️\n"
                        f"Вологість: {humidity}% 💧\n"
                        f"Тиск: {pressure} hPa 🌬️\n"
                        f"😃"
                    )
                    weather_cache[city] = weather_info
                    return weather_info
                elif response.status == 404:
                    return "Місто не знайдено. Перевірте правильність вводу."
                else:
                    return "Не вдалося отримати дані про погоду."
    except (asyncio.TimeoutError, ClientError, ServerTimeoutError) as e:
        logger.error(f"Помилка при отриманні даних про погоду: {e}")
        return "Сталася помилка при отриманні даних про погоду. Спробуйте знову пізніше."

# Функція для обробки команди /start
async def start(update: Update, context):
    logger.info(f"Команда /start отримана від користувача {update.effective_user.id}")
    bot = context.bot
    await send_message_with_retries(bot, update.effective_chat.id, "Привіт! Я бот для отримання погоди. Просто введи назву міста українською мовою, щоб дізнатися погоду. 😃")

# Функція для обробки текстових повідомлень та надання прогнозу погоди
async def get_weather_update(update: Update, context):
    logger.info(f"Отримано повідомлення від користувача {update.effective_user.id}")
    city = update.message.text
    context.user_data['city'] = city  # Збережемо місто для оновлень
    context.user_data['chat_id'] = update.effective_chat.id  # Збережемо chat_id для оновлень
    weather_info = await get_weather(city)
    bot = context.bot

    await send_message_with_retries(bot, update.effective_chat.id, weather_info)
    # Повідомлення про наступне оновлення прогнозу
    await send_message_with_retries(bot, update.effective_chat.id, "Наступне оновлення прогнозу через 2 години. 🌦️")

    # Налаштуємо автоматичне оновлення прогнозу, уникнувши дублювання завдань
    if 'job' in context.user_data:
        context.user_data['job'].schedule_removal()
    job = context.job_queue.run_repeating(send_weather_update, interval=7200, first=7200, data=context.user_data)
    context.user_data['job'] = job

# Функція для відправки оновленого прогнозу погоди
async def send_weather_update(context):
    job = context.job
    city = job.data['city']
    chat_id = job.data['chat_id']
    weather_info = await get_weather(city)
    bot = context.bot
    await send_message_with_retries(bot, chat_id, weather_info)

# Функція для відправлення повідомлень з повторними спробами
async def send_message_with_retries(bot, chat_id, text, retries=3, delay=5):
    for attempt in range(retries):
        try:
            await bot.send_message(chat_id, text=text)
            return
        except TimedOut:
            logger.error(f"Помилка таймауту при відправленні повідомлення. Спроба {attempt + 1} з {retries}.")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("Не вдалося відправити повідомлення після кількох спроб.")

# Команди для установки города
SET_CITY = 1

# Обработчик команды /setcity
async def set_city(update: Update, context):
    await update.message.reply_text("Пожалуйста, введите ваш город:")
    return SET_CITY

# Обработчик для получения города от пользователя
async def city_received(update: Update, context):
    city = update.message.text
    context.user_data['city'] = city
    context.user_data['chat_id'] = update.effective_chat.id
    weather_info = await get_weather(city)
    keyboard = create_keyboard()  # Пересоздаём клавиатуру
    await update.message.reply_text(f"Ваш город установлен как: {city}\n{weather_info}", reply_markup=keyboard)
    return ConversationHandler.END

def main():
    # Створення бота та додавання обробників
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_update))

    # Регистрация команды /setcity для установки города
    set_city_handler = ConversationHandler(
        entry_points=[CommandHandler("setcity", set_city)],
        states={
            SET_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city_received)],
        },
        fallbacks=[],
    )
    application.add_handler(set_city_handler)

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
