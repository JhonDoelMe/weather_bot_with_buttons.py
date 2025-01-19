from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters

# Функция для создания клавиатуры
def create_keyboard():
    # Создаём разметку для клавиатуры
    keyboard = [
        [KeyboardButton("Обновить")],  # Первая строка с одной кнопкой
        [KeyboardButton("Мой город"), KeyboardButton("Изменить город")]  # Вторая строка с двумя кнопками
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Функция для регистрации обработчиков кнопок
def register_handlers(application):
    application.add_handler(MessageHandler(filters.Regex("Обновить"), update_weather))
    application.add_handler(MessageHandler(filters.Regex("Мой город"), show_city))
    application.add_handler(MessageHandler(filters.Regex("Изменить город"), change_city))

# Обработчик кнопки "Обновить"
async def update_weather(update, context):
    city = context.user_data.get('city', None)
    if city:
        weather_info = await context.bot_data['get_weather'](city)
        keyboard = create_keyboard()  # Пересоздаём клавиатуру
        await update.message.reply_text(weather_info, reply_markup=keyboard)
    else:
        await update.message.reply_text("Пожалуйста, введите город с помощью команды /start или /setcity.", reply_markup=create_keyboard())

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
