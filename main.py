# ============================= FILE: main.py =============================
import asyncio

from aiogram import Bot
from aiogram.types import BotCommandScopeDefault, BotCommand

from bot import dp, bot
from project_structure.paths import DATABASE_PATH
import sqlite3


async def set_bot_commands(bot: Bot):
    """
    Sets default bot commands to guide the user.
    """
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="change_lang", description="Change language"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


def init_db():
    """
    Initializes the SQLite database and creates user_lang table if it does not exist.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_lang (
            user_id INTEGER PRIMARY KEY,
            lang_code TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

async def main():
    # Initialize database
    init_db()

    # Set bot commands
    await set_bot_commands(bot)

    # Start polling updates
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())