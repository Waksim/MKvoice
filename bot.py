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

# Initialize the Telegram bot with the provided token
bot = Bot(token=TOKEN)

# Set up in-memory storage for finite state machine (FSM)
storage = MemoryStorage()

# Initialize the dispatcher with the storage
dp = Dispatcher(storage=storage)

# List to keep track of the latest user queries for logging or review purposes
user_queries = []

# Ensure the audio folder exists; create it if it doesn't
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Configure the logger to write logs to the specified log file
# Logs will rotate after reaching 1 MB, retained for 10 days, and compressed as ZIP
logger.add(LOG_FILE, rotation="1 MB", retention="10 days", compression="zip")


@dp.message(Command(commands=["s", "S", "ы", "Ы"]))
async def cmd_s(message: Message):
    """
    Handler for the commands /s, /S, /ы, /Ы.
    Accessible only to the administrator specified by ADMIN_ID.
    Sends the last 50 log messages from the log file.
    """
    # Log the receipt of the command (commented out to reduce verbosity)
    # logger.info(f"Received command {message.text} from user {message.from_user.id}")

    # Verify if the user is the administrator
    if message.from_user.id != ADMIN_ID:
        logger.warning(f"Access denied for user {message.from_user.id}")
        await message.reply("Access denied.")
        return

    try:
        # Log the attempt to read the log file (commented out)
        # logger.info(f"Reading log file from: {LOG_FILE}")

        # Check if the log file exists
        if not os.path.exists(LOG_FILE):
            logger.error(f"Log file {LOG_FILE} does not exist.")
            await message.reply("Log file does not exist.")
            return

        # Read the last 50 lines from the log file
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            last_n_lines = deque(f, 50)
        last_lines = ''.join(last_n_lines)

        # Log the number of lines read (commented out)
        # logger.info(f"Read {len(last_n_lines)} lines from log file.")

        if len(last_lines.strip()) == 0:
            # Log that no log messages were found (commented out)
            # logger.info("No log messages found.")
            await message.reply("No log messages.")
        else:
            # Telegram messages have a maximum length of 4096 characters
            if len(last_lines) > 4000:
                # If the log is too long, send it as a file instead of text
                log_file = FSInputFile(LOG_FILE)
                # Log the decision to send the log file as a document (commented out)
                # logger.info("Sending log file as document due to length.")
                await message.reply_document(document=log_file, caption="Last log messages:")
            else:
                # If the log is short enough, send it directly as a text message
                # logger.info("Sending log messages as text.")
                await message.reply(f"📝 Last 50 log messages:\n{last_lines}", parse_mode='HTML')

    except Exception as e:
        # Log the exception (commented out)
        # logger.exception("Failed to read log file.")
        await message.reply(f"Failed to read log file: {e}")


@dp.message(F.text.regexp(r'^https?://'))
async def handle_url(message: Message):
    """
    Handler for messages containing URLs.
    Extracts text from the webpage and converts it to audio.
    """
    url = message.text
    try:
        # Attempt to extract text using static extraction method
        text_page = await extract_text_from_url_static(url)

        # If the extracted text is too short, try dynamic extraction (e.g., using JavaScript rendering)
        if len(text_page) < 200:
            logger.info(f"Dynamic site detected, using Playwright: {url}")
            text_page = await extract_text_from_url_dynamic(url)

        # Convert the extracted text to an audio file using text-to-speech
        mp3_file = await synthesize_text_to_audio_edge(text_page, str(message.from_user.id), message, logger)

        # Prepare the audio file for sending
        audio = FSInputFile(mp3_file)

        # Send the audio file to the user
        await message.reply_audio(audio=audio)

        # Remove the audio file from the server after sending
        os.remove(mp3_file)
    except Exception as e:
        # Inform the user if text extraction fails
        await message.reply(f"Failed to extract text from the URL: {e}")


@dp.message(F.text)
async def handle_text(message: Message):
    """
    Handler for plain text messages.
    Converts the text to audio and sends it to the user.
    """
    text = message.text

    # Log the user's query, truncating if necessary
    user_queries.append(f"User @{message.from_user.username}: {text[:100]}...")

    # Convert the text to an audio file using text-to-speech
    mp3_file = await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger)

    # Prepare the audio file for sending
    audio = FSInputFile(mp3_file)

    # Send the audio file to the user
    await message.reply_audio(audio=audio)

    # Remove the audio file from the server after sending
    os.remove(mp3_file)


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
