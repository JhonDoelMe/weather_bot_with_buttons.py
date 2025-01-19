import os
import logging
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import TimedOut
from dotenv import load_dotenv
from cachetools import TTLCache
from aiohttp import ClientError, ServerTimeoutError
from buttons import create_keyboard, register_handlers  # Импорт кнопок и их обработчиков

# Загрузка переменных окружения
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
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Эмодзи для разных погодных условий
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

# Кэш для данных о погоде
weather_cache = TTLCache(maxsize=100, ttl=600)

# Функция для получения эмодзи по описанию погоды
def get_weather_emoji(description):
    for key in weather_emojis:
        if key in description:
            return weather_emojis[key]
    return ""

# Асинхронная функция для получения данных о погоде
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
                        f"Давление: {pressure} hPa 🌬️"
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

# Функция для отправки сообщений с повторными попытками
async def send_message_with_retries(bot, chat_id, text, retries=3, delay=5, reply_markup=None):
    for attempt in range(retries):
        try:
            await bot.send_message(chat_id, text=text, reply_markup=reply_markup)
            return
        except TimedOut:
            logger.error(f"Тайм-аут при отправке сообщения. Попытка {attempt + 1} из {retries}.")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("Не удалось отправить сообщение после нескольких попыток.")

# Обработчик команды /start
async def start(update: Update, context):
    logger.info(f"Команда /start получена от пользователя {update.effective_user.id}")
    bot = context.bot
    keyboard = create_keyboard()  # Создаём клавиатуру с кнопками
    await send_message_with_retries(
        bot,
        update.effective_chat.id,
        "Привет! Я бот для получения погоды. Используй кнопки ниже или напиши название города.",
        reply_markup=keyboard  # Передаём клавиатуру в сообщение
    )

# Обработчик текстовых сообщений
async def get_weather_update(update: Update, context):
    logger.info(f"Получено сообщение от пользователя {update.effective_user.id}")
    city = update.message.text
    context.user_data['city'] = city
    context.user_data['chat_id'] = update.effective_chat.id
    weather_info = await get_weather(city)
    bot = context.bot

    await send_message_with_retries(bot, update.effective_chat.id, weather_info)

def main():
    # Создание приложения
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_update))

    # Регистрация обработчиков кнопок
    register_handlers(application)

    # Сохранение функции get_weather для использования в обработке кнопок
    application.bot_data['get_weather'] = get_weather

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
