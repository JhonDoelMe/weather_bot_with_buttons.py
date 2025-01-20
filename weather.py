import aiohttp
import asyncio
import logging
from telegram import Update, CallbackQuery
from telegram.ext import CallbackContext
from cachetools import TTLCache
from aiohttp import ClientError, ServerTimeoutError
from message_utils import send_message_with_retries
from config import WEATHER_API_KEY
from user_data import save_user_data, load_user_data
from datetime import datetime

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

wind_directions = [
    "северный", "северо-северо-восточный", "северо-восточный", "восточно-северо-восточный",
    "восточный", "восточно-юго-восточный", "юго-восточный", "юго-юго-восточный",
    "южный", "юго-юго-западный", "юго-западный", "западно-юго-западный",
    "западный", "западно-северо-западный", "северо-западный", "северо-северо-западный"
]

weather_cache = TTLCache(maxsize=500, ttl=600)

def get_weather_emoji(description):
    for key in weather_emojis:
        if key in description:
            return weather_emojis[key]
    return ""

def escape_markdown_v2(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!\\'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def convert_unix_to_time(unix_time, timezone):
    return datetime.utcfromtimestamp(unix_time + timezone).strftime('%H:%M:%S (%d %B %Y)')

def get_wind_direction(deg):
    if deg is None:
        return "N/A"
    index = round(deg / 22.5) % 16
    return wind_directions[index]

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

    url = f"http://api.openweathermap.org/data/2.5/weather?q={escape_markdown_v2(city)}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    logger.info(f"Отправка запроса на URL: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                logger.info(f"Получен ответ с кодом состояния: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Получены данные о погоде для города {city}")

                    weather = data.get('weather', [{}])[0].get('description', 'N/A')
                    temp = data.get('main', {}).get('temp', 'N/A')
                    feels_like = data.get('main', {}).get('feels_like', 'N/A')
                    temp_min = data.get('main', {}).get('temp_min', 'N/A')
                    temp_max = data.get('main', {}).get('temp_max', 'N/A')
                    humidity = data.get('main', {}).get('humidity', 'N/A')
                    pressure = data.get('main', {}).get('pressure', 'N/A')
                    wind_speed = data.get('wind', {}).get('speed', 'N/A')
                    wind_deg = data.get('wind', {}).get('deg', 'N/A')
                    wind_gust = data.get('wind', {}).get('gust', 'N/A')
                    sunrise = data.get('sys', {}).get('sunrise', 'N/A')
                    sunset = data.get('sys', {}).get('sunset', 'N/A')

                    weather_emoji = get_weather_emoji(weather)
                    wind_direction = get_wind_direction(wind_deg)
                    time_sunrise = convert_unix_to_time(sunrise, data.get('timezone', 0)) if sunrise != 'N/A' else 'N/A'
                    time_sunset = convert_unix_to_time(sunset, data.get('timezone', 0)) if sunset != 'N/A' else 'N/A'

                    weather_info = (
                        f"Погода в {city}: {weather} {weather_emoji}\n\n"
                        f"🌡️ Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                        f"🌡️ Минимум/Максимум: {temp_min}°C / {temp_max}°C\n\n"
                        f"💧 Влажность: {humidity}%\n"
                        f"🌬️ Давление: {pressure} hPa\n\n"
                        f"💨 Ветер: {wind_speed} м/с ({wind_direction}, порывы до {wind_gust} м/с)\n\n"
                        f"🌅 Восход: {time_sunrise.split(' ')[0]}\n"
                        f"🌇 Закат: {time_sunset.split(' ')[0]}"
                    )

                    weather_cache[city] = weather_info
                    return weather_info
                elif response.status == 404:
                    logger.warning("Город не найден. Проверьте правильность ввода.")
                    return "Город не найден. Проверьте правильность ввода."
                elif response.status == 429:
                    logger.warning("Превышен лимит запросов к API.")
                    return "Превышен лимит запросов. Попробуйте снова позже."
                else:
                    logger.error(f"Не удалось получить данные о погоде. Код состояния: {response.status}")
                    return "Не удалось получить данные о погоде."
    except (asyncio.TimeoutError, ClientError, ServerTimeoutError, aiohttp.ClientConnectorError, aiohttp.ContentTypeError) as e:
        logger.error(f"Ошибка при получении данных о погоде: {e}")
        return "Произошла ошибка при получении данных о погоде. Попробуйте снова позже."

async def get_weather_update(update: Update, context: CallbackContext):
    if isinstance(update, CallbackQuery):
        query = update
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        city = context.user_data.get('city')
        if not city:
            await request_city(update, context)
            return
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