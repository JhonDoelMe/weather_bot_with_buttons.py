import os
import logging
import asyncio
import aiohttp
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import TimedOut
from dotenv import load_dotenv
from cachetools import TTLCache
from aiohttp import ClientError, ServerTimeoutError

# Загрузка переменных окружения из файла .env
if not os.path.isfile('.env'):
    raise FileNotFoundError("Файл .env не найден. Убедитесь, что файл .env присутствует в корневой директории проекта.")
load_dotenv()

# Получение токенов из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Проверка наличия токенов
if not TELEGRAM_TOKEN or not WEATHER_API_KEY:
    raise ValueError("Отсутствуют необходимые токены. Убедитесь, что они указаны в файле .env")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Эмодзи для различных погодных состояний
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

# Кэш для данных о погоде
weather_cache = TTLCache(maxsize=100, ttl=600)

# Функция для получения эмодзи по описанию погоды
def get_weather_emoji(description):
    for key in weather_emojis:
        if key in description:
            return weather_emojis[key]
    return ""

# Асинхронная функция для получения погоды
async def get_weather(city):
    if not city:
        return "Название города не может быть пустым."

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
                    )
                    weather_cache[city] = weather_info
                    return weather_info
                elif response.status == 404:
                    return "Город не найден. Проверьте правильность ввода."
                else:
                    return "Не удалось получить данные о погоде."
    except (asyncio.TimeoutError, ClientError, ServerTimeoutError) as e:
        logger.error(f"Ошибка при получении данных о погоде: {e}")
        return "Произошла ошибка при получении данных о погоде. Попробуйте позже."

# Функция для сохранения данных пользователя в файл
def save_user_data(data):
    with open('user_data.json', 'w') as file:
        json.dump(data, file, indent=4)

# Функция для чтения данных пользователя из файла
def read_user_data():
    try:
        with open('user_data.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Обработка команды /start
async def start(update: Update, context):
    logger.info(f"Команда /start получена от пользователя {update.effective_user.id}")
    user_data = read_user_data()
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {"city": ""}
        save_user_data(user_data)
    await update.message.reply("Привет! Я бот для получения погоды. Просто введи название города, чтобы узнать погоду.", reply_markup=get_main_keyboard())

# Функция для создания клавиатуры с кнопками
def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Обновить", callback_data="update"),
            InlineKeyboardButton("Мой город", callback_data="my_city"),
            InlineKeyboardButton("Изменить город", callback_data="change_city")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработка нажатий на кнопки
async def button(update: Update, context):
    query = update.callback_query
    user_data = read_user_data()
    user_id = update.effective_user.id
    city = user_data.get(user_id, {}).get("city", "")
    if query.data == "update":
        if city:
            weather_info = await get_weather(city)
            await query.edit_message_text(f"Прогноз для {city}:\n{weather_info}", reply_markup=get_main_keyboard())
        else:
            await query.edit_message_text("Город не выбран. Используйте команду 'Изменить город', чтобы выбрать город.", reply_markup=get_main_keyboard())
    elif query.data == "my_city":
        if city:
            await query.edit_message_text(f"Ваш город: {city}", reply_markup=get_main_keyboard())
        else:
            await query.edit_message_text("Город не установлен. Используйте команду 'Изменить город', чтобы выбрать город.", reply_markup=get_main_keyboard())
    elif query.data == "change_city":
        await query.edit_message_text("Введите новый город:", reply_markup=None)

# Обработка ввода нового города
async def set_city(update: Update, context):
    user_data = read_user_data()
    user_id = update.effective_user.id
    city = update.message.text
    user_data[user_id]["city"] = city
    save_user_data(user_data)
    weather_info = await get_weather(city)
    await update.message.reply(f"Ваш город установлен как: {city}\n{weather_info}", reply_markup=get_main_keyboard())

# Обработка текста с городом
async def get_weather_update(update: Update, context):
    city = update.message.text
    await set_city(update, context)

def main():
    # Создание бота и добавление обработчиков
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_update))

    # Обработчик нажатий на кнопки
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_update))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
