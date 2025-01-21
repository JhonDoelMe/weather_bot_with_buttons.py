import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from user_data import load_user_data, subscribe_user, unsubscribe_user
from message_utils import send_message_with_retries
from air_alarm import get_air_alarm_status
from weather import get_weather
from utils import request_city

logger = logging.getLogger(__name__)

async def show_menu(update, context):
    """Показывает меню с кнопками."""
    buttons = [
        [KeyboardButton('Погода'), KeyboardButton('Курс гривны')],
        [KeyboardButton('Изменить город')],
        [KeyboardButton('Тревога')]
    ]
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    try:
        if update.message:
            await update.message.reply_text('Выберите опцию:', reply_markup=keyboard)
        elif update.callback_query:
            await update.callback_query.message.reply_text('Выберите опцию:', reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка при показе меню: {e}")

async def button(update, context: CallbackContext):
    """Обрабатывает нажатия на кнопки."""
    if not update.message:
        logger.error("Нет сообщения для обработки кнопки.")
        return

    text = update.message.text
    logger.info(f"Нажата кнопка: {text}")
    try:
        if text == 'Погода':
            user_data = load_user_data(update.effective_user.id)
            if user_data and user_data.get('city'):
                city = user_data['city']
                weather_info = await get_weather(city)
                await send_message_with_retries(context.bot, update.effective_chat.id, weather_info)
            else:
                await send_message_with_retries(context.bot, update.effective_chat.id, "Город не установлен. Пожалуйста, введите название города:")
                context.user_data['waiting_for_city'] = True
        elif text == 'Курс гривны':
            # Здесь можно добавить логику для получения курса гривны
            await send_message_with_retries(context.bot, update.effective_chat.id, "Функция курса гривны пока не реализована.")
        elif text == 'Изменить город':
            await change_city(update, context)
        elif text == 'Тревога':
            await request_air_alarm(update, context)
    except Exception as e:
        logger.error(f"Ошибка при обработке кнопки: {e}")

async def request_air_alarm(update, context):
    """Запрашивает статус воздушной тревоги."""
    alarm_status = await get_air_alarm_status()
    await send_message_with_retries(context.bot, update.effective_chat.id, alarm_status, parse_mode='MarkdownV2')

async def change_city(update, context: CallbackContext):
    """Запрашивает у пользователя новый город."""
    user_data = load_user_data(update.effective_user.id)
    if user_data and user_data.get('city'):
        current_city = user_data['city']
        await send_message_with_retries(context.bot, update.effective_chat.id, f"Текущий город: {current_city}")
        await send_message_with_retries(context.bot, update.effective_chat.id, "Введите новый город:")
        context.user_data['waiting_for_new_city'] = True
    else:
        await send_message_with_retries(context.bot, update.effective_chat.id, "Город не установлен. Введите новый город:")
        context.user_data['waiting_for_new_city'] = True