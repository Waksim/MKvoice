import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger
from config import TOKEN, AUDIO_FOLDER
from utils.text_extraction import extract_text_from_url_static, extract_text_from_url_dynamic
from utils.text_to_speech import synthesize_text_to_audio_edge

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

user_queries = []
os.makedirs(AUDIO_FOLDER, exist_ok=True)
logger.add("bot_log.log", rotation="1 MB", retention="10 days", compression="zip")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Привет! Отправьте мне текст, файл с текстом или ссылку на статью, и я превращу это в аудио.")

@dp.message(Command("s"))
async def cmd_s(message: Message):
    if user_queries:
        response = "\n".join(user_queries[-50:])
    else:
        response = "Нет записанных запросов."
    await message.reply(response, parse_mode='HTML')

@dp.message(F.text.regexp(r'^https?://'))
async def handle_url(message: Message):
    url = message.text
    try:
        text_page = await extract_text_from_url_static(url)
        if len(text_page) < 200:
            logger.info(f"Динамический сайт, используем playwright: {url}")
            text_page = await extract_text_from_url_dynamic(url)

        mp3_file = await synthesize_text_to_audio_edge(text_page, str(message.from_user.id), message, logger)
        audio = FSInputFile(mp3_file)
        await message.reply_audio(audio=audio)
        os.remove(mp3_file)
    except Exception as e:
        await message.reply(f"Не удалось извлечь текст из ссылки: {e}")

@dp.message(F.text)
async def handle_text(message: Message):
    text = message.text
    user_queries.append(f"User @{message.from_user.username}: {text[:100]}...")
    mp3_file = await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger)
    audio = FSInputFile(mp3_file)
    await message.reply_audio(audio=audio)
    os.remove(mp3_file)

@dp.message(F.document)
async def handle_file(message: Message):
    file = await bot.download(message.document)
    text = file.read().decode("utf-8")
    mp3_file = await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger)
    audio = FSInputFile(mp3_file)
    await message.reply_audio(audio=audio)
    os.remove(mp3_file)
