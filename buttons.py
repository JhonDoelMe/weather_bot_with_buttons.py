import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from weather import get_weather_update
from currency import get_currency_rate

logger = logging.getLogger(__name__)

async def show_menu(update, context):
    buttons = [[KeyboardButton('Погода'), KeyboardButton('Курс гривны')]]
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    if update.message:
        await update.message.reply_text('Выберите опцию:', reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.message.reply_text('Выберите опцию:', reply_markup=keyboard)

async def button(update, context: CallbackContext):
    text = update.message.text
    if text == 'Погода':
        await get_weather_update(update, context)
    elif text == 'Курс гривны':
        await get_currency_rate(update, context)
