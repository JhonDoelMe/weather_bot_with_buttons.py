from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def show_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("Погода", callback_data='weather')],
        [InlineKeyboardButton("Курс гривны", callback_data='currency')],
        [InlineKeyboardButton("Изменить город", callback_data='change_city')],
        [InlineKeyboardButton("Тревога", callback_data='air_alarm')]  # Добавлена новая кнопка "тревога"
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Меню:', reply_markup=reply_markup)

async def button(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'weather':
        await request_weather(update, context)
    elif query.data == 'currency':
        await request_currency(update, context)
    elif query.data == 'change_city':
        await request_city(update, context)
    elif query.data == 'air_alarm':
        await request_air_alarm(update, context)  # Добавлен обработчик для кнопки "тревога"
