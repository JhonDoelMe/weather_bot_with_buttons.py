import os
import logging
import asyncio
import aiohttp
import json
from telegram import Update
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
    raise ValueError("Необходимые токены отсутствуют. Убедитесь, что они указаны в файле .env")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Установите уровень логирования на INFO для отладки
)
logger = logging.getLogger(__name__)

# Эмодзи для различных погодных условий
weather_emojis = {
    "ясно": "☀️",
    "переменная облачность": "⛅️",
    "облачно с прояснениями": "🌤",
    "облачно": "☁️",
    "пасмурно": "☁️",
    "дождь": "🌧",
    "гроза": "⛈",
    "снег": "❄️",
    "туман": "🌫"
}

# Кеш для данных о погоде
weather_cache = TTLCache(maxsize=100, ttl=600)

# Путь к файлу для хранения данных
USER_DATA_FILE = 'user_data.json'

# Функция для получения эмодзи по описанию погоды
def get_weather_emoji(description):
    for key in weather_emojis:
        if key in description:
            return weather_emojis[key]
    return ""

# Асинхронная функция для получения погоды из OpenWeatherMap API
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
                        f"Описание: {weather} {weather_emoji}\n"
                        f"Температура: {temp}°C 🌡️\n"
                        f"Ощущается как: {feels_like}°C 🌡️\n"
                        f"Влажность: {humidity}% 💧\n"
                        f"Давление: {pressure} hPa 🌬️\n"
                        f"😃"
                    )
                    weather_cache[city] = weather_info
                    return weather_info
                elif response.status == 404:
                    return "Город не найден. Проверьте правильность ввода."
                else:
                    return "Не удалось получить данные о погоде."
    except (asyncio.TimeoutError, ClientError, ServerTimeoutError) as e:
        logger.error(f"Ошибка при получении данных о погоде: {e}")
        return "Произошла ошибка при получении данных о погоде. Попробуйте снова позже."

# Функция для сохранения данных пользователя в файл JSON
def save_user_data(user_id, city):
    data = {}
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
    
    data[str(user_id)] = {'city': city}

    with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Функция для чтения данных пользователя из файла JSON
def load_user_data(user_id):
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get(str(user_id), None)
    return None

# Асинхронная функция для отправки сообщений с повторными попытками
async def send_message_with_retries(bot, chat_id, text, retries=3, delay=5):
    for attempt in range(retries):
        try:
            await bot.send_message(chat_id, text=text)
            return
        except TimedOut:
            logger.error(f"Ошибка таймаута при отправке сообщения. Попытка {attempt + 1} из {retries}.")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("Не удалось отправить сообщение после нескольких попыток.")

# Функция для обработки команды /start
async def start(update: Update, context):
    logger.info(f"Команда /start получена от пользователя {update.effective_user.id}")
    bot = context.bot
    await send_message_with_retries(bot, update.effective_chat.id, "Привет! Я бот для получения погоды. Просто введи название города на украинском языке, чтобы узнать погоду. 😃")

# Функция для обработки текстовых сообщений и предоставления прогноза погоды
async def get_weather_update(update: Update, context):
    logger.info(f"Получено сообщение от пользователя {update.effective_user.id}")
    city = update.message.text
    user_id = update.effective_user.id

    # Сохраним город пользователя в JSON файл
    save_user_data(user_id, city)

    context.user_data['city'] = city  # Сохраним город для обновлений
    context.user_data['chat_id'] = update.effective_chat.id  # Сохраним chat_id для обновлений
    weather_info = await get_weather(city)
    bot = context.bot

    await send_message_with_retries(bot, update.effective_chat.id, weather_info)
    # Сообщение о следующем обновлении прогноза
    await send_message_with_retries(bot, update.effective_chat.id, "Следующее обновление прогноза через 2 часа. 🌦️")

    # Настроим автоматическое обновление прогноза, избегая дублирования задач
    if 'job' in context.user_data:
        context.user_data['job'].schedule_removal()
    job = context.job_queue.run_repeating(send_weather_update, interval=7200, first=7200, data=context.user_data)
    context.user_data['job'] = job

# Функция для отправки обновленного прогноза погоды
async def send_weather_update(context):
    job = context.job
    city = job.data['city']
    chat_id = job.data['chat_id']
    weather_info = await get_weather(city)
    bot = context.bot
    await send_message_with_retries(bot, chat_id, weather_info)

def main():
    # Создание бота и добавление обработчиков
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Обработчик текстовых сообщений и команд
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_update))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
