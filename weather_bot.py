from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, JobQueue
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

# Эмодзи для различных состояний погоды
weather_emojis = {
    "ясно": "☀️",
    "переменная облачность": "⛅️",
    "облачно с прояснениями": "🌤",
    "облачно": "☁️",
    "дождь": "🌧",
    "гроза": "⛈",
    "снег": "❄️",
    "туман": "🌫"
}

# Функция для получения эмодзи по описанию погоды
def get_weather_emoji(description):
    for key in weather_emojis:
        if key in description:
            return weather_emojis[key]
    return ""

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
        weather_emoji = get_weather_emoji(weather)

        return (
            f"Погода в {city}:\n"
            f"Описание: {weather} {weather_emoji}\n"
            f"Температура: {temp}°C 🌡️\n"
            f"Ощущается как: {feels_like}°C 🌡️\n"
            f"Влажность: {humidity}% 💧\n"
            f"Давление: {pressure} hPa 🌬️\n"
            f"😃"
        )
    else:
        return "Не удалось получить данные о погоде."

# Функция для обработки команд /start
async def start(update: Update, context):
    logger.info(f"Команда /start получена от пользователя {update.effective_user.id}")
    await update.message.reply_text("Привет! Я бот для получения погоды. Просто введи название города на русском языке, чтобы узнать погоду. 😃")

# Функция для обработки текстовых сообщений и выдачи прогноза погоды
async def get_weather_update(update: Update, context):
    logger.info(f"Получено сообщение от пользователя {update.effective_user.id}")
    city = update.message.text
    context.user_data['city'] = city  # Сохраним город для обновлений
    context.user_data['chat_id'] = update.effective_chat.id  # Сохраним chat_id для обновлений
    weather_info = get_weather(city)
    await update.message.reply_text(weather_info)

    # Настроим автоматическое обновление прогноза
    context.job_queue.run_repeating(send_weather_update, interval=7200, first=0, context=context.user_data)

# Функция для отправки обновленного прогноза погоды
async def send_weather_update(context):
    job = context.job
    city = job.context['city']
    chat_id = job.context['chat_id']
    weather_info = get_weather(city)
    await context.bot.send_message(chat_id, text=weather_info)

def main():
    # Создание бота и добавление обработчиков
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обработчик команд /start
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик текстовых сообщений и команд
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_update))
    
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
