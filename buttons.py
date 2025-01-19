from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

# Обработчик кнопки "Обновить"
async def update_weather(update, context):
    city = context.user_data.get('city', None)
    if city:
        weather_info = await context.bot_data['get_weather'](city)
        keyboard = create_keyboard()  # Пересоздаём клавиатуру
        await update.message.reply_text(weather_info, reply_markup=keyboard)
    else:
        await update.message.reply_text("Пожалуйста, введите город с помощью команды /setcity или /start.", reply_markup=create_keyboard())

# Обработчик кнопки "Мой город"
async def show_city(update, context):
    city = context.user_data.get('city', None)
    if city:
        weather_info = await context.bot_data['get_weather'](city)
        keyboard = create_keyboard()  # Пересоздаём клавиатуру
        await update.message.reply_text(f"Ваш город: {city}\n{weather_info}", reply_markup=keyboard)
    else:
        await update.message.reply_text("Город не установлен. Пожалуйста, укажите его с помощью команды /setcity.", reply_markup=create_keyboard())

# Обработчик кнопки "Изменить город"
async def change_city(update, context):
    await update.message.reply_text("Пожалуйста, введите новый город:", reply_markup=create_keyboard())
    return "WAITING_FOR_CITY"

# Создание клавиатуры
def create_keyboard():
    keyboard = [
        [InlineKeyboardButton("Обновить", callback_data="update"),
         InlineKeyboardButton("Мой город", callback_data="my_city"),
         InlineKeyboardButton("Изменить город", callback_data="change_city")]
    ]
    return InlineKeyboardMarkup(keyboard)
