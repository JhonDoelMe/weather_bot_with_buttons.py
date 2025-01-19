import logging
import asyncio
from telegram.error import TimedOut

logger = logging.getLogger(__name__)

async def send_message_with_retries(bot, chat_id, text, retries=3, delay=5):
    for attempt in range(retries):
        try:
            await bot.send_message(chat_id, text=text)
            return
        except TimedOut:
            logger.error(f"Ошибка таймаута при отправке сообщения. Попытка {attempt + 1} из {retries}.")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("Не удалось отправить сообщение после нескольких попыток.")
