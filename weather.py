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

weather_cache = TTLCache(maxsize=100, ttl=600)

def get_weather_emoji(description):
    for key in weather_emojis:
        if key in description:
            return weather_emojis[key]
    return ""

def convert_unix_to_time(unix_time, timezone):
    return datetime.utcfromtimestamp(unix_time + timezone).strftime('%H:%M:%S (%d %B %Y)')

def get_wind_direction(deg):
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
                    temp_min = data['main']['temp_min']
                    temp_max = data['main']['temp_max']
                    sea_level = data['main'].get('sea_level')
                    grnd_level = data['main'].get('grnd_level')
                    visibility = data.get('visibility', 'N/A')
                    wind_speed = data['wind']['speed']
                    wind_deg = data['wind']['deg']
                    wind_gust = data['wind'].get('gust')
                    clouds = data['clouds']['all']
                    dt = data['dt']
                    sys_country = data['sys']['country']
                    sunrise = data['sys']['sunrise']
                    sunset = data['sys']['sunset']
                    timezone = data['timezone']

                    weather_emoji = get_weather_emoji(weather)
                    wind_direction = get_wind_direction(wind_deg)
                    time_dt = convert_unix_to_time(dt, timezone)
                    time_sunrise = convert_unix_to_time(sunrise, timezone)
                    time_sunset = convert_unix_to_time(sunset, timezone)
                    timezone_hours = timezone // 3600

                    weather_info = (
                        f"Погода в {city}:\n"
                        f"Описание: {weather} {weather_emoji}\n"
                        f"Температура: {temp}°C 🌡️\n"
                        f"Ощущается как: {feels_like}°C 🌡️\n"
                        f"Минимальная температура: {temp_min}°C 🌡️\n"
                        f"Максимальная температура: {temp_max}°C 🌡️\n"
                        f"Влажность: {humidity}% 💧\n"
                        f"Давление: {pressure} hPa 🌬️\n"
                        f"Давление на уровне моря: {sea_level} hPa\n"
                        f"Давление на уровне земли: {grnd_level} hPa\n"
                        f"Видимость: {visibility} м\n"
                        f"Скорость ветра: {wind_speed} м/с 💨\n"
                        f"Направление ветра: {wind_direction} ({wind_deg}°) 🧭\n"
                        f"Порывы ветра: {wind_gust} м/с 🌪️\n"
                        f"Облачность: {clouds}% ☁️\n"
                        f"Время данных: {time_dt}\n"
                        f"Код страны: {sys_country}\n"
                        f"Время восхода: {time_sunrise} 🌅\n"
                        f"Время заката: {time_sunset} 🌇\n"
                        f"Часовой пояс: UTC{timezone_hours:+}\n"
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
