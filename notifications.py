import logging
from datetime import time
from pytz import timezone
from telegram.ext import CallbackContext
from user_data import load_user_data, save_user_data
from message_utils import send_message_with_retries
from weather import get_weather

logger = logging.getLogger(__name__)

async def send_notification(context: CallbackContext):
    job = context.job
    user_id = job.data['user_id']
    await send_message_with_retries(context.bot, job.data['chat_id'], "Вы будете получать прогноз погоды каждое утро в 8 часов.")
    # Обновляем JSON, чтобы уведомление больше не отправлялось
    user_data = load_user_data(user_id)
    save_user_data(user_id, user_data['city'], notified=True)

async def send_daily_weather_update(context: CallbackContext):
    job = context.job
    user_id = job.data['user_id']
    user_data = load_user_data(user_id)
    if user_data and user_data.get('city'):
        city = user_data['city']
        weather_info = await get_weather(city)
        await send_message_with_retries(context.bot, job.data['chat_id'], weather_info)

def schedule_daily_weather_update(context: CallbackContext, chat_id, user_timezone):
    target_time = time(hour=8, minute=0, tzinfo=user_timezone)
    context.job_queue.run_daily(send_daily_weather_update, target_time, data={'chat_id': chat_id, 'user_id': chat_id})

def schedule_auto_update(context: CallbackContext, chat_id):
    job_queue = context.job_queue
    user_data = load_user_data(chat_id)
    city = user_data.get('city') if user_data else None
    if city:
        job_queue.run_repeating(auto_update, interval=7200, first=7200, data={'chat_id': chat_id, 'city': city})

async def auto_update(context: CallbackContext):
    job = context.job
    city = job.data.get('city')
    chat_id = job.data.get('chat_id')
    if city:
        weather_info = await get_weather(city)
        await send_message_with_retries(context.bot, chat_id, weather_info)
