import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger
from config import TOKEN, AUDIO_FOLDER, LOG_FILE, ADMIN_ID
from utils.text_extraction import extract_text_from_url_static, extract_text_from_url_dynamic
from utils.text_to_speech import synthesize_text_to_audio_edge
from collections import deque

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Список последних запросов для логирования или обзора
user_queries = []
os.makedirs(AUDIO_FOLDER, exist_ok=True)
logger.add(LOG_FILE, rotation="1 MB", retention="10 days", compression="zip")

@dp.message(Command(commands=["s", "S", "ы", "Ы"]))
async def cmd_s(message: Message):
    """
    Обработчик команды /s, /S, /ы, /Ы.
    Доступен только для администратора с указанным ADMIN_ID.
    Выводит последние 50 сообщений из файла логов bot_log.log.
    """
    # logger.info(f"Received command {message.text} from user {message.from_user.id}")

    # Проверка, является ли пользователь администратором
    if message.from_user.id != ADMIN_ID:
        logger.warning(f"Access denied for user {message.from_user.id}")
        await message.reply("Access denied.")
        return

    try:
        # logger.info(f"Reading log file from: {LOG_FILE}")

        # Проверка существования файла логов
        if not os.path.exists(LOG_FILE):
            logger.error(f"Log file {LOG_FILE} does not exist.")
            await message.reply("Log file does not exist.")
            return

        # Чтение последних 50 строк из файла логов
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            last_n_lines = deque(f, 50)
        last_lines = ''.join(last_n_lines)

        # logger.info(f"Read {len(last_n_lines)} lines from log file.")

        if len(last_lines.strip()) == 0:
            # logger.info("No log messages found.")
            await message.reply("No log messages.")
        else:
            # Ограничение длины сообщения Telegram (4096 символов)
            if len(last_lines) > 4000:
                # Если лог слишком длинный, отправить его как файл
                log_file = FSInputFile(LOG_FILE)
                # logger.info("Sending log file as document due to length.")
                await message.reply_document(document=log_file, caption="Last log messages:")
            else:
                # logger.info("Sending log messages as text.")
                await message.reply(f"📝 Last 50 log messages:\n{last_lines}", parse_mode='HTML')

    except Exception as e:
        # logger.exception("Failed to read log file.")
        await message.reply(f"Failed to read log file: {e}")


@dp.message(F.text.regexp(r'^https?://'))
async def handle_url(message: Message):
    """
    Обработчик сообщений, содержащих URL.
    Извлекает текст со страницы и конвертирует его в аудио.
    """
    url = message.text
    try:
        # Попытка статического извлечения текста
        text_page = await extract_text_from_url_static(url)
        # Если текст слишком короткий, попытка динамического извлечения
        if len(text_page) < 200:
            logger.info(f"Dynamic site detected, using Playwright: {url}")
            text_page = await extract_text_from_url_dynamic(url)

        # Конвертация извлечённого текста в аудио
        mp3_file = await synthesize_text_to_audio_edge(text_page, str(message.from_user.id), message, logger)
        audio = FSInputFile(mp3_file)
        await message.reply_audio(audio=audio)

        # Удаление аудиофайла после отправки
        os.remove(mp3_file)
    except Exception as e:
        await message.reply(f"Failed to extract text from the URL: {e}")

@dp.message(F.text)
async def handle_text(message: Message):
    """
    Обработчик простых текстовых сообщений.
    Конвертирует текст в аудио и отправляет пользователю.
    """
    text = message.text
    user_queries.append(f"User @{message.from_user.username}: {text[:100]}...")
    mp3_file = await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger)
    audio = FSInputFile(mp3_file)
    await message.reply_audio(audio=audio)
    os.remove(mp3_file)

@dp.message(F.document)
async def handle_file(message: Message):
    """
    Обработчик загруженных текстовых файлов.
    Конвертирует содержимое файла в аудио и отправляет пользователю.
    """
    file = await bot.download(message.document)
    text = file.read().decode("utf-8")  # Чтение содержимого файла как текст
    mp3_file = await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger)
    audio = FSInputFile(mp3_file)
    await message.reply_audio(audio=audio)
    os.remove(mp3_file)
