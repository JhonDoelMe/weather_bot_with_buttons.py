import logging
import json
from telegram.ext import CallbackContext
from user_data import load_user_data
from air_alarm import get_air_alarm_status, get_or_fetch_region
from message_utils import send_message_with_retries

logger = logging.getLogger(__name__)

async def check_air_alerts(context: CallbackContext):
    """Периодически проверяет статус воздушных тревог и отправляет уведомления."""
    try:
        # Получаем список всех пользователей
        try:
            with open('user_data.json', 'r', encoding='utf-8') as file:
                user_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка при загрузке файла user_data.json: {e}")
            return

        # Получаем данные о тревогах
        alarm_data = await get_air_alarm_status()
        if not alarm_data:
            logger.error("Не удалось получить данные о тревогах.")
            return

        for user_id, data in user_data.items():
            if data.get('subscriptions', {}).get('air_alarm', False):
                city = data.get('city')
                if city:
                    region = await get_or_fetch_region(city)
                    if region:
                        for alert in alarm_data:
                            if alert.get("regionName") == region:
                                active_alerts = alert.get("activeAlerts", [])
                                if active_alerts:
                                    await send_message_with_retries(
                                        context.bot,
                                        chat_id=user_id,
                                        text=f"🔴 Внимание! В вашем городе {city} объявлена воздушная тревога!"
                                    )
    except Exception as e:
        logger.error(f"Ошибка при проверке воздушных тревог: {e}")