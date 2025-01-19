import os
import logging
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
USER_DATA_FILE = "user_data.json"
API_KEY = os.getenv("OPENWEATHER_API_KEY")  # Получите ваш API ключ на OpenWeather

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Чтение данных пользователей из JSON
def read_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# Запись данных пользователей в JSON
def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

# Функция для получения погоды из OpenWeather
async def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        description = data['weather'][0]['description']
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']
        return f"Погода в {city}:\nОпис: {description}\nТемпература: {temp}°C 🌡️\nВідчувається як: {feels_like}°C 🌡️\nВологість: {humidity}% 💧\nТиск: {pressure} hPa 🌬️"
    else:
        return "Не удалось получить данные о погоде."

# Функция для получения клавиатуры
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Обновить", callback_data="update_weather")],
        [InlineKeyboardButton("Мой город", callback_data="my_city")],
        [InlineKeyboardButton("Изменить город", callback_data="change_city")]
    ])

# Функция для обработки команды /start
async def start(update: Update, context):
    user_id = update.effective_user.id
    user_data = read_user_data()

    if user_id not in user_data:
        user_data[user_id] = {"city": ""}
        save_user_data(user_data)

    keyboard = get_keyboard()
    await update.message.reply_text(
        "Привет! Я бот для получения погоды. Просто введи название города, чтобы узнать погоду.",
        reply_markup=keyboard
    )

# Функция для обработки кнопок
async def button_handler(update: Update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    user_data = read_user_data()

    if query.data == "update_weather":
        # Обновляем погоду
        city = user_data.get(str(user_id), {}).get("city")
        if city:
            weather_info = await get_weather(city)
            await query.answer()
            await query.edit_message_text(text=weather_info)
        else:
            await query.answer()
            await query.edit_message_text(text="Город не установлен. Пожалуйста, установите город.")

    elif query.data == "my_city":
        # Выводим текущий город
        city = user_data.get(str(user_id), {}).get("city", "Город не установлен.")
        await query.answer()
        await query.edit_message_text(text=f"Ваш город: {city}")

    elif query.data == "change_city":
        # Запросить новый город
        await query.answer()
        await query.edit_message_text(text="Введите новый город:")

# Функция для обработки ввода города
async def set_city(update: Update, context):
    user_id = update.effective_user.id
    city = update.message.text
    user_data = read_user_data()

    # Сохраняем новый город
    user_data[str(user_id)] = {"city": city}
    save_user_data(user_data)

    # Отправляем подтверждение
    await update.message.reply_text(f"Ваш город установлен как: {city}")
    await update.message.reply_text("Выберите действие:", reply_markup=get_keyboard())

# Запуск бота
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

    # Запуск
    application.run_polling()

if __name__ == "__main__":
    main()
