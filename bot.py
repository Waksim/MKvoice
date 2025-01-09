# ---- FILE: bot.py ----
import os
import asyncio
import chardet

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from config import TOKEN, AUDIO_FOLDER, LOG_FILE, ADMIN_ID

# i18n
from middlewares.i18n_middleware import I18nMiddleware

from utils.text_extraction import extract_text_from_url_static, extract_text_from_url_dynamic
from utils.text_to_speech import synthesize_text_to_audio_edge
from utils.document_parsers import parse_docx, parse_fb2, parse_epub
from utils.i18n import get_translator, get_user_lang, set_user_lang

from collections import deque
from pathlib import Path

# Подключаем middleware
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.concurrency_limit import ConcurrencyLimitMiddleware

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.message.middleware(RateLimitMiddleware(rate_limit=5.0))
dp.message.middleware(ConcurrencyLimitMiddleware(max_concurrent_tasks=1))
dp.message.middleware(I18nMiddleware())

audio_path = Path(AUDIO_FOLDER)
audio_path.mkdir(parents=True, exist_ok=True)

logger.add(LOG_FILE, rotation="1 MB", retention="10 days", compression="zip")

MAX_MESSAGE_LENGTH = 4000


@dp.message(Command('start'))
async def cmd_start(message: Message, _):
    user_id = message.from_user.id
    lang_code = get_user_lang(user_id)
    translator = get_translator(lang_code)
    __ = translator.gettext  # Если нужно локально

    await message.answer(_(
        "Привет! Отправь мне текст или файл, а я озвучу."
    ))


@dp.message(Command('lang'))
async def cmd_lang(message: Message, _):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(_("Usage: /lang <en|ru|uk|zh>"))
        return

    new_lang = parts[1].strip().lower()
    if new_lang not in ['en', 'ru', 'uk', 'zh']:
        await message.reply(_("Доступные языки: en, ru, uk, zh"))
        return

    set_user_lang(message.from_user.id, new_lang)

    t = get_translator(new_lang)
    await message.reply(t.gettext("Язык обновлён!"))


@dp.message(Command(commands=["s", "S", "ы", "Ы"]))
async def cmd_s(message: Message, _):
    if message.from_user.id != ADMIN_ID:
        logger.warning(f"Доступ запрещён для пользователя {message.from_user.id}")
        await message.reply(_("Access denied."))
        return

    try:
        log_file = Path(LOG_FILE)
        if not log_file.exists():
            logger.error(f"Лог-файл {LOG_FILE} не существует.")
            await message.reply(_("Log file does not exist."))
            return

        with log_file.open('r', encoding='utf-8') as f:
            last_n_lines = deque(f, 15)
        last_lines = ''.join(last_n_lines)

        if not last_lines.strip():
            await message.reply(_("No log messages."))
            return

        messages_list = []
        current_message = ""
        for line in last_lines.splitlines(keepends=True):
            if len(current_message) + len(line) > MAX_MESSAGE_LENGTH:
                messages_list.append(current_message)
                current_message = line
            else:
                current_message += line
        if current_message:
            messages_list.append(current_message)

        for msg in messages_list:
            await message.reply(_("📝 Last log lines:\n") + msg, parse_mode='HTML')
            await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        await message.reply(_("Failed to read log file: {error}").format(error=str(e)))


@dp.message(F.text.regexp(r'^https?://'))
async def handle_url(message: Message, _):
    url = message.text
    try:
        text_page = await extract_text_from_url_static(url)
        if len(text_page) < 200:
            text_page = await extract_text_from_url_dynamic(url)
        if not text_page.strip():
            await message.reply(_("Не удалось извлечь текст."))
            return

        await synthesize_text_to_audio_edge(
            text_page,
            str(message.from_user.id),
            message,
            logger,
            _
        )

    except Exception as e:
        await message.reply(_("Failed to process URL: {error}").format(error=str(e)))


@dp.message(F.text)
async def handle_text(message: Message, _):
    text = message.text
    if not text.strip():
        await message.reply(_("Пустой текст."))
        return

    await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger, _)


@dp.message(F.document)
async def handle_file(message: Message, _):
    if message.document.file_size > 20 * 1024 * 1024:
        await message.reply(_("Файл слишком большой (максимум 20 МБ)."))
        return

    file_extension = os.path.splitext(message.document.file_name)[1].lower()
    local_file_path = os.path.join(AUDIO_FOLDER, message.document.file_name)

    try:
        with open(local_file_path, "wb") as f:
            download_stream = await bot.download(message.document)
            f.write(download_stream.read())

        with open(local_file_path, 'rb') as f:
            raw_data = f.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']
        confidence = detected['confidence']
        logger.info(f"Detected encoding for {message.document.file_name}: {encoding} with confidence {confidence}")

        if file_extension == ".docx":
            text = parse_docx(local_file_path)
        elif file_extension == ".fb2":
            text = parse_fb2(local_file_path)
        elif file_extension == ".epub":
            text = parse_epub(local_file_path)
        else:
            if encoding is None:
                encoding = 'utf-8'
            with open(local_file_path, "r", encoding=encoding, errors='replace') as txt_f:
                text = txt_f.read()

        os.remove(local_file_path)

        if not text.strip():
            await message.reply(_("Не удалось извлечь текст из документа."))
            return

        await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger, _)

    except Exception as e:
        logger.error(f"Не удалось обработать документ: {e}")
        await message.reply(_("Не удалось обработать документ: {error}").format(error=str(e)))
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
