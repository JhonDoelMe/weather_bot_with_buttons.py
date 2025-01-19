import os
import logging
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
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
    raise ValueError("Необхідні токени відсутні. Перевірте їх у файлі .env")

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Кеш для даних про погоду
weather_cache = TTLCache(maxsize=100, ttl=600)

USER_DATA_FILE = "user_data.json"

# Эмодзи для разных погодных состояний
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

# Чтение данных из JSON файла
def read_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            logger.error("Файл user_data.json поврежден или пуст. Инициализируем новый файл.")
            return {}
    else:
        return {}

# Запись данных в JSON файл
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Функция для получения эмодзи погоды
def get_weather_emoji(description):
    for key in weather_emojis:
        if key in description:
            return weather_emojis[key]
    return ""

# Асинхронная функция для получения погоды
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

# Функция для создания клавиатуры с кнопками
def get_keyboard():
    return [
        [
            InlineKeyboardButton("Обновить", callback_data='update_weather'),
            InlineKeyboardButton("Мой город", callback_data='my_city'),
            InlineKeyboardButton("Изменить город", callback_data='change_city')
        ]
    ]

# Обработчик callback для кнопок
async def button(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == 'update_weather':
        city = context.user_data.get('city')
        if city:
            weather_info = await get_weather(city)
            await query.edit_message_text(weather_info)
        else:
            await query.edit_message_text("Пожалуйста, установите город с помощью команды /set_city.")

    elif query.data == 'my_city':
        city = context.user_data.get('city')
        if city:
            await query.edit_message_text(f"Ваш город: {city}")
        else:
            await query.edit_message_text("Пожалуйста, установите город с помощью команды /set_city.")

    elif query.data == 'change_city':
        await query.edit_message_text("Введите новый город.")

# Функция для обработки команды /start
async def start(update: Update, context):
    logger.info(f"Команда /start получена от пользователя {update.effective_user.id}")
    bot = context.bot
    # Отправка приветственного сообщения с клавиатурой
    await update.message.reply_text(
        "Привет! Я бот для получения погоды. Просто введи название города, чтобы узнать погоду.",
        reply_markup=InlineKeyboardMarkup(get_keyboard())
    )

# Обработчик для установки города
async def set_city(update: Update, context):
    city = update.message.text
    context.user_data['city'] = city  # Сохранение города
    save_user_data(context.user_data)  # Сохранение в файл
    await update.message.reply_text(f"Ваш город установлен как: {city}", reply_markup=InlineKeyboardMarkup(get_keyboard()))

# Основная функция для запуска бота
def main():
    # Создание объекта бота и добавление обработчиков
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Обработчик текстовых сообщений для установки города
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

    # Обработчик для кнопок
    application.add_handler(CallbackQueryHandler(button))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
