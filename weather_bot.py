from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue
import requests
import logging

# Вставьте свои токены
TELEGRAM_TOKEN = "7533343666:AAFtXtHra2C5C_Wgl_tMs-m04plqjWItCzI"
WEATHER_API_KEY = "31ebd431e1fab770d9981dcdb8180f89"  # Ваш API ключ OpenWeatherMap

# Словарь для хранения выбранных городов пользователей
user_cities = {}

# Функция для получения погоды с OpenWeatherMap API
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    
    # Логирование URL запроса
    print(f"URL запроса: {url}")
    
    response = requests.get(url)
    print(f"Статус код ответа: {response.status_code}")  # Логирование статуса ответа
    
    if response.status_code == 200:
        data = response.json()
        print(f"Ответ API: {data}")  # Логирование данных ответа
        
        # Извлекаем необходимые данные
        weather = data['weather'][0]['description']
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']

        # Эмодзи для разных типов погоды
        weather_emoji = {
            "clear sky": "☀️",
            "few clouds": "🌤",
            "scattered clouds": "☁️",
            "broken clouds": "☁️",
            "shower rain": "🌧",
            "rain": "🌧",
            "thunderstorm": "⛈",
            "snow": "❄️",
            "mist": "🌫"
        }

        emoji = weather_emoji.get(weather, "🌥")

        weather_info = (
            f"{emoji} {weather.capitalize()}\n"
            f"Температура: {temp}°C\n"
            f"Ощущается как: {feels_like}°C\n"
            f"Влажность: {humidity}%\n"
            f"Атмосферное давление: {pressure} гПа"
        )
        return weather_info
    else:
        print(f"Ошибка API: {response.status_code}")
        return f"Не удалось получить погоду для города: {city}. Ошибка {response.status_code}"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Мой город"), KeyboardButton("Изменить город")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Привет! Я бот прогноза погоды. Вы можете узнать погоду для вашего города или изменить город.",
        reply_markup=reply_markup
    )

# Обработка кнопок
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "Мой город":
        if user_id in user_cities:
            city = user_cities[user_id]
            weather_info = get_weather(city)
            if weather_info:
                await update.message.reply_text(f"Ваш город: {city}\n{weather_info}")
            else:
                await update.message.reply_text(f"Не удалось получить погоду для города: {city}.")
        else:
            await update.message.reply_text("Вы ещё не установили город. Нажмите 'Изменить город', чтобы установить его.")

    elif text == "Изменить город":
        user_cities.pop(user_id, None)  # Удаляем текущий город, если он есть
        await update.message.reply_text("Введите название города, чтобы установить его.")

# Обработка текстовых сообщений для установки города
async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    city = update.message.text.strip()

    if not city:
        await update.message.reply_text("Пожалуйста, введите название города.")
        return

    # Сохраняем выбранный город
    user_cities[user_id] = city

    # Получаем погоду для нового города
    weather_info = get_weather(city)

    if weather_info:
        await update.message.reply_text(
            f"Ваш город установлен: {city}.\n\n{weather_info}"
        )
    else:
        await update.message.reply_text(f"Не удалось получить погоду для города: {city}. Проверьте правильность написания.")

# Функция для автоматической отправки погоды каждые 2 часа
async def send_weather(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_id = job.context['user_id']
    
    if user_id in user_cities:
        city = user_cities[user_id]
        weather_info = get_weather(city)
        if weather_info:
            await context.bot.send_message(user_id, f"Погода для города {city}:\n{weather_info}")
        else:
            await context.bot.send_message(user_id, f"Не удалось получить погоду для города: {city}.")
    else:
        await context.bot.send_message(user_id, "Вы ещё не установили город. Нажмите 'Изменить город', чтобы установить его.")

# Основная функция
def main():
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Получаем JobQueue для отправки погоды через каждые 2 часа
    job_queue = application.job_queue

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_click))
    application.add_handler(MessageHandler(filters.TEXT, set_city))

    # Устанавливаем периодическую задачу на 2 часа
    job_queue.run_repeating(send_weather, interval=7200, first=10, context={'user_id': 123456789})  # Замените 123456789 на ID пользователя

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
