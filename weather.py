import aiohttp
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from cachetools import TTLCache
from aiohttp import ClientError, ServerTimeoutError
from message_utils import send_message_with_retries
from config import WEATHER_API_KEY
from user_data import save_user_data

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

async def get_weather_update(update: Update, context):
    logger.info(f"Получено сообщение от пользователя {update.effective_user.id}")
    city = update.message.text
    user_id = update.effective_user.id

    save_user_data(user_id, city)

    context.user_data['city'] = city
    context.user_data['chat_id'] = update.effective_chat.id
    weather_info = await get_weather(city)
    bot = context.bot

    await send_message_with_retries(bot, update.effective_chat.id, weather_info)
    await send_message_with_retries(bot, update.effective_chat.id, "Следующее обновление прогноза через 2 часа. 🌦️")

    if 'job' in context.user_data:
        context.user_data['job'].schedule_removal()
    job = context.job_queue.run_repeating(send_weather_update, interval=7200, first=7200, data=context.user_data)
    context.user_data['job'] = job

async def send_weather_update(context):
    job = context.job
    city = job.data['city']
    chat_id = job.data['chat_id']
    weather_info = await get_weather(city)
    bot = context.bot
    await send_message_with_retries(bot, chat_id, weather_info)
