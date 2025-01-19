import aiohttp
import logging
from telegram import Update
from telegram.ext import CallbackContext
from message_utils import send_message_with_retries
from config import CURRENCY_API_KEY

logger = logging.getLogger(__name__)

async def get_currency_rate(update: Update, context: CallbackContext):
    url = f"https://openexchangerates.org/api/latest.json?app_id={CURRENCY_API_KEY}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = data['rates']
                    message = (
                        f"Курсы валют по отношению к USD:\n"
                        f"EUR: {rates['EUR']}\n"
                        f"GBP: {rates['GBP']}\n"
                        f"JPY: {rates['JPY']}\n"
                        f"UAH: {rates['UAH']}\n"
                        f"RUB: {rates['RUB']}\n"
                    )
                    await send_message_with_retries(context.bot, update.effective_chat.id, message)
                else:
                    await send_message_with_retries(context.bot, update.effective_chat.id, "Не удалось получить данные о курсах валют.")
    except (asyncio.TimeoutError, aiohttp.ClientError, aiohttp.ServerTimeoutError) as e:
        logger.error(f"Ошибка при получении данных о курсах валют: {e}")
        await send_message_with_retries(context.bot, update.effective_chat.id, "Произошла ошибка при получении данных о курсах валют. Попробуйте снова позже.")
