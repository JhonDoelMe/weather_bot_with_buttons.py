import logging
import asyncio
from telegram.error import TimedOut

logger = logging.getLogger(__name__)

async def send_message_with_retries(bot, chat_id, text, retries=3, delay=5):
    for attempt in range(retries):
        try:
            await bot.send_message(chat_id, text=text)
            logger.info(f"Сообщение успешно отправлено на попытке {attempt + 1}.")
            return
        except TimedOut:
            logger.error(f"Ошибка таймаута при отправке сообщения в чат {chat_id}. Попытка {attempt + 1} из {retries}.")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error(f"Не удалось отправить сообщение в чат {chat_id} после нескольких попыток.")
