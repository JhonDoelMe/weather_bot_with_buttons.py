import logging
from telegram import Update
from telegram.ext import CallbackContext
from message_utils import send_message_with_retries

logger = logging.getLogger(__name__)

async def request_city(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    await send_message_with_retries(context.bot, chat_id, "Пожалуйста, введите название города:")
    context.user_data['waiting_for_city'] = True