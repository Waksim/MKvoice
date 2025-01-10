# ============================= FILE: bot.py =============================
import os
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from config import TOKEN, AUDIO_FOLDER, LOG_FILE, ADMIN_ID, AVAILABLE_LANGUAGES

# Import routers
from handlers.group_chat_handlers import group_router
from handlers.private_chat_handlers import private_router

# Import middleware
from middlewares.i18n_middleware import I18nMiddleware

from utils.text_extraction import extract_text_from_url_static, extract_text_from_url_dynamic
from utils.text_to_speech import synthesize_text_to_audio_edge
from utils.document_parsers import parse_docx, parse_fb2, parse_epub
from utils.i18n import get_translator, get_user_lang, set_user_lang

from collections import deque
from pathlib import Path


# Initialize Bot and Dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Register the i18n middleware
i18n = I18nMiddleware(get_translator)
dp.message.middleware(i18n)
dp.callback_query.middleware(i18n)

# Include routers
dp.include_router(private_router)
dp.include_router(group_router)

# Create the audio folder if it does not exist
audio_path = Path(AUDIO_FOLDER)
audio_path.mkdir(parents=True, exist_ok=True)

# Configure logging
logger.add(LOG_FILE, rotation="1 MB", retention="10 days", compression="zip")

# Maximum message length
MAX_MESSAGE_LENGTH = 4000

# Run the bot
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())