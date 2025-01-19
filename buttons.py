import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from weather import get_weather_update
from currency import get_currency_rate

logger = logging.getLogger(__name__)

async def show_menu(update, context):
    keyboard = [
        [
            InlineKeyboardButton("Погода", callback_data='weather'),
            InlineKeyboardButton("Курсы валют", callback_data='currency')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)

async def button(update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == 'weather':
        await get_weather_update_callback(update, context)
    elif query.data == 'currency':
        await get_currency_rate_callback(update, context)

async def get_weather_update_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await get_weather_update(query, context)

async def get_currency_rate_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await get_currency_rate(query, context)
