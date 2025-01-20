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

def escape_markdown(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def get_air_alarm_status():
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY  # Используем ключ без 'Bearer'
    }
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Полученные данные: {data}")  # Добавлено логирование полученных данных
        return parse_air_alarm_data(data)
    else:
        logger.error(f"Ошибка при запросе данных: {response.status_code} - {response.text}")
        return "Не удалось получить данные о воздушных тревогах."

def parse_air_alarm_data(data):
    if isinstance(data, list):
        alerts = data
    else:
        alerts = data.get("alerts", [])
    
    if not alerts:
        return "Воздушных тревог нет."
    
    messages = []
    for alert in alerts:
        region = escape_markdown(alert.get("regionName"))  # Используем 'regionName' для получения названия региона и экранируем
        active_alerts = alert.get("activeAlerts", [])
        for active_alert in active_alerts:
            type = active_alert.get("type")
            translated_type = ALERT_TYPES_TRANSLATIONS.get(type, type)
            translated_type = escape_markdown(translated_type)
            if type == "AIR":
                message = f"🔴 *{translated_type}* в регионе: {region}."
            else:
                message = f"⚠️ *{translated_type}* в регионе: {region}."
            messages.append(message)
    
    return "\n".join(messages)
