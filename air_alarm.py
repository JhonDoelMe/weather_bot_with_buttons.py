import json
import os
import logging
import aiohttp
import requests
from config import WEATHER_API_KEY, UKRAINE_ALARM_API_KEY
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env файла

logger = logging.getLogger(__name__)

# Путь к файлу с городами и регионами
CITIES_TO_REGIONS_FILE = 'cities_to_regions.json'

# API для получения данных о тревогах
API_URL = "https://api.ukrainealarm.com/api/v3/alerts"
API_KEY = UKRAINE_ALARM_API_KEY

ALERT_TYPES_TRANSLATIONS = {
    "AIR": "Воздушная тревога",
    "ARTILLERY": "Артиллерийская тревога",
    "URBAN_FIGHTS": "Городские бои",
    "MISSILE": "Ракетная тревога",
    "NUCLEAR": "Ядерная тревога",
    "CHEMICAL": "Химическая тревога",
    "OTHER": "Другая тревога"
}

def load_cities_to_regions():
    """Загружает словарь городов и регионов из JSON-файла."""
    try:
        if os.path.exists(CITIES_TO_REGIONS_FILE):
            with open(CITIES_TO_REGIONS_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            logger.error(f"Файл {CITIES_TO_REGIONS_FILE} не найден.")
            return {}
    except json.JSONDecodeError:
        logger.error(f"Ошибка при загрузке файла {CITIES_TO_REGIONS_FILE}: файл поврежден.")
        return {}
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла {CITIES_TO_REGIONS_FILE}: {e}")
        return {}

async def get_city_info(city):
    """Получает информацию о городе из OpenWeatherMap API."""
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={WEATHER_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    return data[0]  # Возвращаем первый результат
            return None

async def update_cities_json(city, region):
    """Добавляет новый город и регион в JSON-файл."""
    try:
        with open(CITIES_TO_REGIONS_FILE, 'r', encoding='utf-8') as file:
            cities_to_regions = json.load(file)
    except FileNotFoundError:
        cities_to_regions = {}

    cities_to_regions[city] = region

    with open(CITIES_TO_REGIONS_FILE, 'w', encoding='utf-8') as file:
        json.dump(cities_to_regions, file, ensure_ascii=False, indent=4)

async def get_or_fetch_region(city):
    """Возвращает регион для города, обновляя JSON-файл при необходимости."""
    cities_to_regions = load_cities_to_regions()
    if city in cities_to_regions:
        return cities_to_regions[city]

    # Если город не найден, запрашиваем данные из API
    city_info = await get_city_info(city)
    if city_info and 'state' in city_info:
        region = city_info['state']
        await update_cities_json(city, region)
        return region
    else:
        return None

def get_air_alarm_status():
    """Получает данные о воздушных тревогах через API."""
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY  # Используем ключ без 'Bearer'
    }
    try:
        response = requests.get(API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Полученные данные: {data}")
            return data
        else:
            logger.error(f"Ошибка при запросе данных: {response.status_code} - {response.text}")
            return None
    except (requests.Timeout, requests.ConnectionError, requests.RequestException) as e:
        logger.error(f"Ошибка при запросе данных: {e}")
        return None

def parse_air_alarm_data(data, city):
    """Парсит данные о тревогах и возвращает сообщение для пользователя."""
    region = get_or_fetch_region(city)
    if not region:
        return f"Город {city} не найден в списке регионов. Пожалуйста, введите другой город."

    for alert in data:
        if alert.get("regionName") == region:
            active_alerts = alert.get("activeAlerts", [])
            if active_alerts:
                return f"🔴 Внимание! В вашем городе {city} объявлена воздушная тревога!"
            else:
                return f"В вашем городе {city} тревог нет."
    return f"Данные для региона {region} не найдены."