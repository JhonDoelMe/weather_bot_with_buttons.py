import asyncio
import logging

logger = logging.getLogger(__name__)

async def send_message_with_retries(bot, chat_id, text, parse_mode=None):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
            break
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                logger.error(f"Не удалось отправить сообщение после {max_retries} попыток.")
                raise e