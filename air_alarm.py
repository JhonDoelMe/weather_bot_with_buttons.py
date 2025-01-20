import requests
import os
import logging

API_URL = "https://api.ukrainealarm.com/api/v3/alerts"
API_KEY = os.getenv("UKRAINE_ALARM_API_KEY")

logger = logging.getLogger(__name__)

def get_air_alarm_status():
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return parse_air_alarm_data(data)
    else:
        logger.error(f"Ошибка при запросе данных: {response.status_code} - {response.text}")
        return "Не удалось получить данные о воздушных тревогах."

def parse_air_alarm_data(data):
    alerts = data.get("alerts", [])
    if not alerts:
        return "Воздушных тревог нет."
    
    messages = []
    for alert in alerts:
        region = alert.get("region")
        status = alert.get("status")
        if status == "active":
            message = f"🔴 Внимание! Воздушная тревога в регионе: {region}."
        else:
            message = f"✅ Воздушная тревога снята в регионе: {region}."
        messages.append(message)
    
    return "\n".join(messages)
