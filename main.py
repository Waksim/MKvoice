# ============================= FILE: main.py =============================
"""
This file initializes the database, sets up the bot commands, and runs the bot.
We also ensure that the Dispatcher uses MemoryStorage to handle user states for chunk size input.
"""
import asyncio
import sys
import aiosqlite  # Заменено

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from loguru import logger

from config import TOKEN
from handlers.group_chat_handlers import group_router
from handlers.private_chat_handlers import private_router
from middlewares.i18n_middleware import I18nMiddleware
from project_structure.paths import DATABASE_PATH
from utils.i18n import get_translator

# --- Правильная и ранняя настройка Loguru ---
# Убираем стандартный обработчик и настраиваем свой
logger.remove()
# Логи уровня INFO и выше будут выводиться в консоль
logger.add(sys.stderr, level="INFO")
# Логи уровня DEBUG и выше будут записываться в файл
logger.add("bot.log", level="DEBUG", rotation="10 MB", compression="zip")


async def init_db() -> None:  # Функция стала асинхронной
    """
    Creates (or updates) the necessary tables in the database:
      - user_lang (stores user's interface language)
      - user_settings (stores chunk_size and tts_speed)
    """
    logger.info("Initializing database...")
    try:
        # Используем aiosqlite для асинхронной работы с БД
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Table for user language
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_lang
                (
                    user_id  INTEGER PRIMARY KEY,
                    lang_code TEXT NOT NULL
                );
            """)

            # Table for user settings (chunk_size, tts_speed)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_settings
                (
                    user_id    INTEGER PRIMARY KEY,
                    chunk_size INTEGER DEFAULT 40000,
                    tts_speed  TEXT    DEFAULT '+0%'
                );
            """)
            await db.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


async def set_bot_commands(bot: Bot) -> None:
    """
    Sets default bot commands displayed in the Telegram interface.
    """
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="change_lang", description="Change language"),
        BotCommand(command="settings", description="User settings"),
        BotCommand(command="webapp", description="Open web app for large texts"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("Bot commands have been set.")


async def main() -> None:
    """
    Main entry point to:
    1) Initialize the database
    2) Configure the bot and dispatcher
    3) Start the bot
    """
    await init_db()  # Вызываем асинхронную функцию

    storage = MemoryStorage()

    # --- Используем DefaultBotProperties для установки parse_mode глобально ---
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)

    # Регистрация middleware для интернационализации
    i18n = I18nMiddleware(get_translator)
    dp.message.middleware(i18n)
    dp.callback_query.middleware(i18n)

    # Регистрация роутеров
    dp.include_router(private_router)
    dp.include_router(group_router)

    # Установка команд бота
    await set_bot_commands(bot)

    # Удаляем вебхук перед запуском, на случай если он был установлен
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"An error occurred during polling: {e}")
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Bot polling was interrupted.")