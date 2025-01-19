import os
import logging
import asyncio
import aiohttp
import json
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

# Файл для хранения данных о пользователях и их городах
USER_DATA_FILE = 'user_data.json'

# Чтение данных из JSON файла
def read_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as file:
            return json.load(file)
    return {}

# Запись данных в JSON файл
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Функция для получения погоды
async def get_weather(city):
    if not city:
        return "Назва міста не може бути порожньою."

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

                    weather_info = (
                        f"Погода в {city}:\n"
                        f"Опис: {weather}\n"
                        f"Температура: {temp}°C 🌡️\n"
                        f"Відчувається як: {feels_like}°C 🌡️\n"
                        f"Вологість: {humidity}% 💧\n"
                        f"Тиск: {pressure} hPa 🌬️\n"
                    )
                    return weather_info
                else:
                    return "Не вдалося отримати дані про погоду."
    except (asyncio.TimeoutError, ClientError, ServerTimeoutError) as e:
        logger.error(f"Помилка при отриманні даних про погоду: {e}")
        return "Сталася помилка при отриманні даних про погоду. Спробуйте знову пізніше."

# Функция для обработки команды /start
async def start(update: Update, context):
    logger.info(f"Команда /start отримана від користувача {update.effective_user.id}")
    bot = context.bot
    await bot.send_message(update.effective_chat.id, "Привіт! Я бот для отримання погоди. Введи назву міста, щоб дізнатися погоду.")

# Функция для получения данных о пользователе и его городе
async def get_weather_update(update: Update, context):
    user_data = read_user_data()
    user_id = str(update.effective_user.id)
    
    # Проверяем, есть ли данные о городе для этого пользователя
    if user_id in user_data:
        city = user_data[user_id]['city']
        weather_info = await get_weather(city)
        await update.message.reply_text(f"Погода в {city}:\n{weather_info}")
    else:
        await update.message.reply_text("Город не установлен. Используйте команду /setcity для установки города.")

# Функция для установки города пользователя
async def set_city(update: Update, context):
    user_id = str(update.effective_user.id)
    city = update.message.text
    user_data = read_user_data()

    # Сохраняем город для пользователя
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['city'] = city

    save_user_data(user_data)

    # Отправляем подтверждение и погоду
    weather_info = await get_weather(city)
    await update.message.reply_text(f"Ваш город установлен как: {city}\n{weather_info}")

# Функция для обработки команды /setcity
async def set_city_command(update: Update, context):
    await update.message.reply_text("Введите название города:")

def main():
    # Створення бота та додавання обробників
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setcity", set_city_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

    # Обработчик погоды
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_update))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
