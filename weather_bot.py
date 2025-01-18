from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue
import requests
import logging
from telegram.error import BadRequest

# Вставьте свои токены
TELEGRAM_TOKEN = "7533343666:AAFtXtHra2C5C_Wgl_tMs-m04plqjWItCzI"
WEATHER_API_KEY = "31ebd431e1fab770d9981dcdb8180f89"

# Словарь для хранения выбранных городов пользователей
user_cities = {}
user_authorized = {}
job_store = {}

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Функция для получения погоды с OpenWeatherMap API
def get_weather(city):
    if not city:
        return "Название города не может быть пустым."
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather = data['weather'][0]['description']
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']

        weather_emoji = {
            "clear sky": "☀️",
            "few clouds": "🌤",
            "scattered clouds": "☁️",
            "broken clouds": "☁️",
            "shower rain": "🌧",
