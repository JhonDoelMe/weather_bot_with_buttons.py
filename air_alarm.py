import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env файла

API_URL = "https://api.ukrainealarm.com/api/v3/alerts"
API_KEY = os.getenv("UKRAINE_ALARM_API_KEY")

logger = logging.getLogger(__name__)

ALERT_TYPES_TRANSLATIONS = {
    "AIR": "Воздушная тревога",
    "ARTILLERY": "Артиллерийская тревога",
    "URBAN_FIGHTS": "Городские бои",
    "MISSILE": "Ракетная тревога",
    "NUCLEAR": "Ядерная тревога",
    "CHEMICAL": "Химическая тревога",
    "OTHER": "Другая тревога"
}

def escape_markdown_v2(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!\\'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def get_air_alarm_status():
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY  # Используем ключ без 'Bearer'
    }
    try:
        response = requests.get(API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Полученные данные: {data}")
            return parse_air_alarm_data(data)
        elif response.status_code == 404:
            logger.warning("Город не найден. Проверьте правильность ввода.")
            return "Город не найден. Проверьте правильность ввода."
        else:
            logger.error(f"Ошибка при запросе данных: {response.status_code} - {response.text}")
            return "Не удалось получить данные о воздушных тревогах."
    except (requests.Timeout, requests.ConnectionError, requests.RequestException) as e:
        logger.error(f"Ошибка при запросе данных: {e}")
        return "Произошла ошибка при получении данных о воздушных тревогах. Попробуйте снова позже."

def parse_air_alarm_data(data):
    if not data:
        return "Нет данных о воздушных тревогах."

    alerts = data if isinstance(data, list) else data.get("alerts", [])
    
    if not alerts:
        return "Воздушных тревог нет."
    
    messages = []
    for alert in alerts:
        region = escape_markdown_v2(alert.get("regionName", "Неизвестный регион"))
        active_alerts = alert.get("activeAlerts", [])
        for active_alert in active_alerts:
            alert_type = active_alert.get("type", "OTHER")
            translated_type = ALERT_TYPES_TRANSLATIONS.get(alert_type, alert_type)
            translated_type = escape_markdown_v2(translated_type)
            if alert_type == "AIR":
                message = f"🔴 *{translated_type}* в регионе: {region}\\."
            else:
                message = f"⚠️ *{translated_type}* в регионе: {region}\\."
            messages.append(message)
    
    return "\n".join(messages) if messages else "Нет активных тревог."