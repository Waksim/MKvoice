# ============================= FILE: main.py =============================
"""
This file initializes the database, sets up the bot commands, and runs the bot.
We also ensure that the Dispatcher uses MemoryStorage to handle user states for chunk size input.
"""

import asyncio
import sqlite3
import json

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault, WebAppInfo
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, WEBAPP_URL
from middlewares.clear_state import ClearStateMiddleware
from middlewares.i18n_middleware import I18nMiddleware
from project_structure.paths import DATABASE_PATH
# from bot import bot  # Assumes you have a bot instance in bot.py
from handlers.private_chat_handlers import private_router
from handlers.group_chat_handlers import group_router
from utils.i18n import get_translator


# ---- Make sure you have i18n middleware if you use _() everywhere ----
# Example:
# from middlewares.i18n_middleware import I18nMiddleware


def init_db():
    """
    Creates (or updates) the necessary tables in the database:
      - user_lang (stores user's interface language)
      - user_settings (stores chunk_size and tts_speed)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Table for user language (if not already created)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_lang (
            user_id INTEGER PRIMARY KEY,
            lang_code TEXT NOT NULL
        );
    """)

    # Table for user settings (chunk_size, tts_speed)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            chunk_size INTEGER DEFAULT 40000,
            tts_speed TEXT DEFAULT '+0%'
        );
    """)

    conn.commit()
    conn.close()


async def set_bot_commands(bot: Bot):
    """
    Sets default bot commands displayed in the Telegram interface.
    """
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="change_lang", description="Change language"),
        BotCommand(command="settings", description="User settings"),
        BotCommand(command="webapp", description="Open web app for large texts"), # <-- НОВАЯ КОМАНДА
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def main():
    """
    Main entry point to:
    1) Initialize the database
    2) Configure the bot commands
    3) Start the bot
    """
    init_db()

    bot = Bot(token=TOKEN)

    # Create a Dispatcher with in-memory storage
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(private_router)
    dp.include_router(group_router)

    i18n = I18nMiddleware(get_translator)
    dp.message.middleware(i18n)
    dp.callback_query.middleware(i18n)
    dp.message.middleware(ClearStateMiddleware())
    dp.callback_query.middleware(ClearStateMiddleware())

    # Set commands
    await set_bot_commands(bot)

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())