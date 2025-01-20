import logging
from telegram.ext import CallbackContext
from user_data import load_user_data
from message_utils import send_message_with_retries
from weather import get_weather

logger = logging.getLogger(__name__)

async def send_notification(context: CallbackContext):
    pass  # Удаляем функционал

async def send_daily_weather_update(context: CallbackContext):
    pass  # Удаляем функционал

def schedule_daily_weather_update(context: CallbackContext, chat_id, user_timezone):
    pass  # Удаляем функционал

def schedule_auto_update(context: CallbackContext, chat_id):
    pass  # Удаляем функционал

async def auto_update(context: CallbackContext):
    pass  # Удаляем функционал
