import aiohttp
import asyncio
import logging
from telegram import Update, CallbackQuery
from telegram.ext import CallbackContext
from message_utils import send_message_with_retries
from config import CURRENCY_API_KEY

logger = logging.getLogger(__name__)

currency_emojis = {
    "USD": "🇺🇸",  # Флаг США
    "EUR": "🇪🇺",  # Флаг Европейского Союза
    "GBP": "🇬🇧",  # Флаг Великобритании
    "JPY": "🇯🇵",  # Флаг Японии
    "RUB": "🇷🇺"   # Флаг России
}

async def get_currency_rate(query: CallbackQuery, context: CallbackContext):
    url = f"https://openexchangerates.org/api/latest.json?app_id={CURRENCY_API_KEY}"
    chat_id = query.message.chat_id

    logger.info(f"Отправка запроса на URL: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                logger.info(f"Получен ответ с кодом состояния: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    rates = data.get('rates', {})
                    uah_rate = rates.get('UAH')
                    if not uah_rate:
                        await send_message_with_retries(context.bot, chat_id, "Не удалось получить курс гривны.")
                        return

                    # Проверяем наличие всех необходимых ключей
                    required_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'RUB']
                    if not all(currency in rates for currency in required_currencies):
                        await send_message_with_retries(context.bot, chat_id, "Не удалось получить данные для всех валют.")
                        return

                    message = (
                        f"Курс гривны (UAH):\n"
                        f"USD: {1 / rates['USD'] * uah_rate:.2f} {currency_emojis['USD']}\n"
                        f"EUR: {1 / rates['EUR'] * uah_rate:.2f} {currency_emojis['EUR']}\n"
                        f"GBP: {1 / rates['GBP'] * uah_rate:.2f} {currency_emojis['GBP']}\n"
                        f"JPY: {1 / rates['JPY'] * uah_rate:.2f} {currency_emojis['JPY']}\n"
                        f"RUB: {1 / rates['RUB'] * uah_rate:.2f} {currency_emojis['RUB']}\n"
                    )
                    await send_message_with_retries(context.bot, chat_id, message)
                else:
                    await send_message_with_retries(context.bot, chat_id, "Не удалось получить данные о курсах валют.")
    except (asyncio.TimeoutError, aiohttp.ClientError, aiohttp.ServerTimeoutError) as e:
        logger.error(f"Ошибка при получении данных о курсах валют: {e}")
        await send_message_with_retries(context.bot, chat_id, "Произошла ошибка при получении данных о курсах валют. Попробуйте снова позже.")