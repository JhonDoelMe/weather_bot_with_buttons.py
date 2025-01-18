from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import logging

# Вставьте свои токены
TELEGRAM_TOKEN = "7533343666:AAFtXtHra2C5C_Wgl_tMs-m04plqjWItCzI"
WEATHER_API_KEY = "31ebd431e1fab770d9981dcdb8180f89"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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

        return f"Погода в {city}: {weather}, температура: {temp}°C, ощущается как: {feels_like}°C, влажность: {humidity}%, давление: {pressure} hPa."
    else:
        return "Не удалось получить данные о погоде."

# Функция для обработки команд /start
async def start(update: Update, context):
    logger.info(f"Команда /start получена от пользователя {update.effective_user.id}")
    await update.message.reply_text("Привет! Я бот для получения погоды. Используй команду /weather <город>, чтобы узнать погоду. 😃")

# Функция для обработки команд /weather
async def weather(update: Update, context):
    logger.info(f"Команда /weather получена от пользователя {update.effective_user.id}")
    city = " ".join(context.args)
    weather_info = get_weather(city)
    await update.message.reply_text(weather_info + " 😃")

# Функция для обработки текстовых сообщений
async def echo(update: Update, context):
    logger.info(f"Получено сообщение от пользователя {update.effective_user.id}")
    await update.message.reply_text(update.message.text + " 😃")

def main():
    # Создание бота и добавление обработчиков
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обработчик команд /start
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик команд /weather
    application.add_handler(CommandHandler("weather", weather))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
