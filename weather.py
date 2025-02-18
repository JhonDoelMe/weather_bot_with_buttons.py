import aiohttp
import logging
from telegram import Update, CallbackQuery
from telegram.ext import CallbackContext
from cachetools import TTLCache
from aiohttp import ClientError, ServerTimeoutError
from message_utils import send_message_with_retries
from config import WEATHER_API_KEY
from user_data import save_user_data, load_user_data

logger = logging.getLogger(__name__)

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

weather_cache = TTLCache(maxsize=100, ttl=600)

def get_weather_emoji(description):
    for key in weather_emojis:
        if key in description:
            return weather_emojis[key]
    return ""

async def fetch_weather_data(session, url):
    async with session.get(url, timeout=10) as response:
        return await response.json()

async def get_weather(city):
    if not city:
        logger.warning("Название города не может быть пустым.")
        return "Название города не может быть пустым."

    if city in weather_cache:
        logger.info(f"Погода для города {city} взята из кэша.")
        return weather_cache[city]

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    logger.info(f"Отправка запроса на URL: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                logger.info(f"Получен ответ с кодом состояния: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Получены данные: {data}")
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
                    logger.warning("Город не найден. Проверьте правильность ввода.")
                    return "Город не найден. Проверьте правильность ввода."
                else:
                    logger.error("Не удалось получить данные о погоде.")
                    return "Не удалось получить данные о погоде."
    except (asyncio.TimeoutError, ClientError, ServerTimeoutError, aiohttp.ClientConnectorError, aiohttp.ContentTypeError) as e:
        logger.error(f"Ошибка при получении данных о погоде: {e}")
        return "Произошла ошибка при получении данных о погоде. Попробуйте снова позже."

async def get_weather_update(update: Update, context: CallbackContext):
    if isinstance(update, CallbackQuery):
        query = update
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        city = context.user_data.get('city', 'Неизвестно')
    else:
        user_data = load_user_data(update.effective_user.id)
        city = user_data.get('city') if user_data else None

        if city:
            weather_info = await get_weather(city)
            await send_message_with_retries(context.bot, update.effective_chat.id, weather_info)
        else:
            await request_city(update, context)

async def send_weather_update(context: CallbackContext):
    job = context.job
    city = job.data['city']
    chat_id = job.data['chat_id']
    weather_info = await get_weather(city)
    bot = context.bot
    await send_message_with_retries(bot, chat_id, weather_info)
