# bot.py
import os
import asyncio

import chardet
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger
from config import TOKEN, AUDIO_FOLDER, LOG_FILE, ADMIN_ID
from utils.text_extraction import extract_text_from_url_static, extract_text_from_url_dynamic
from utils.text_to_speech import synthesize_text_to_audio_edge
from utils.document_parsers import parse_docx, parse_fb2, parse_epub
from collections import deque
from pathlib import Path

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Создаём папку для аудио, если её нет
audio_path = Path(AUDIO_FOLDER)
audio_path.mkdir(parents=True, exist_ok=True)

logger.add(LOG_FILE, rotation="1 MB", retention="10 days", compression="zip")

MAX_MESSAGE_LENGTH = 4000


@dp.message(Command(commands=["s", "S", "ы", "Ы"]))
async def cmd_s(message: Message):
    """
    Команда /s, /S, /ы, /Ы — только для ADMIN_ID.
    Отправляет последние 15 строк лог-файла сообщениями.
    """
    if message.from_user.id != ADMIN_ID:
        logger.warning(f"Доступ запрещён для пользователя {message.from_user.id}")
        await message.reply("Access denied.")
        return

    try:
        log_file = Path(LOG_FILE)
        if not log_file.exists():
            logger.error(f"Лог-файл {LOG_FILE} не существует.")
            await message.reply("Log file does not exist.")
            return

        # Чтение последних 15 строк
        with log_file.open('r', encoding='utf-8') as f:
            last_n_lines = deque(f, 15)
        last_lines = ''.join(last_n_lines)

        if not last_lines.strip():
            await message.reply("No log messages.")
            return

        # Разделение на части <= MAX_MESSAGE_LENGTH
        messages = []
        current_message = ""
        for line in last_lines.splitlines(keepends=True):
            if len(current_message) + len(line) > MAX_MESSAGE_LENGTH:
                messages.append(current_message)
                current_message = line
            else:
                current_message += line
        if current_message:
            messages.append(current_message)

        for msg in messages:
            await message.reply(f"📝 Last log lines:\n{msg}", parse_mode='HTML')
            await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        await message.reply(f"Failed to read log file: {e}")


@dp.message(F.text.regexp(r'^https?://'))
async def handle_url(message: Message):
    """
    Пример обработки URL.
    """
    url = message.text
    try:
        text_page = await extract_text_from_url_static(url)
        if len(text_page) < 200:
            text_page = await extract_text_from_url_dynamic(url)
        if not text_page.strip():
            await message.reply("Не удалось извлечь текст.")
            return

        await synthesize_text_to_audio_edge(
            text_page,
            str(message.from_user.id),
            message,
            logger
        )

    except Exception as e:
        await message.reply(f"Failed to process URL: {e}")


@dp.message(F.text)
async def handle_text(message: Message):
    """
    Обычный текст -> синтезируем
    """
    text = message.text
    if not text.strip():
        await message.reply("Пустой текст.")
        return

    await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger)


@dp.message(F.document)
async def handle_file(message: Message):
    """
    Получает файл (docx, fb2, epub, txt).
    Извлекаем текст -> синтезируем и отправляем сразу по частям.
    """
    file_extension = os.path.splitext(message.document.file_name)[1].lower()
    local_file_path = os.path.join(AUDIO_FOLDER, message.document.file_name)

    try:
        with open(local_file_path, "wb") as f:
            download_stream = await bot.download(message.document)
            f.write(download_stream.read())

        # Определение кодировки
        with open(local_file_path, 'rb') as f:
            raw_data = f.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']
        confidence = detected['confidence']
        logger.info(f"Detected encoding for {message.document.file_name}: {encoding} with confidence {confidence}")

        # Парсим:
        if file_extension == ".docx":
            text = parse_docx(local_file_path)
        elif file_extension == ".fb2":
            text = parse_fb2(local_file_path)
        elif file_extension == ".epub":
            text = parse_epub(local_file_path)
        else:
            if encoding is None:
                encoding = 'utf-8'  # fallback
            with open(local_file_path, "r", encoding=encoding, errors='replace') as f:
                text = f.read()

        # Удаляем исходный файл
        os.remove(local_file_path)

        if not text.strip():
            await message.reply("Не удалось извлечь текст из документа.")
            return

        # Синтез и моментальная отправка частей
        await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger)

    except Exception as e:
        logger.error(f"Не удалось обработать документ: {e}")
        await message.reply(f"Не удалось обработать документ: {e}")
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
