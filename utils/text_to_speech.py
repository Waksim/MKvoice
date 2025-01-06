# utils/text_to_speech.py
import time
import os
import edge_tts
from aiogram.types import Message, FSInputFile
from loguru import logger
from config import AUDIO_FOLDER
from .text_analysis import analyze_text

CHUNK_SIZE = 40000  # Примерное кол-во символов на часть


async def chunk_text(text: str, chunk_size: int = CHUNK_SIZE):
    """
    Разбивает текст на части по chunk_size символов.
    Возвращает список строк.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size
    return chunks


async def synthesize_chunk(text: str, mp3_path: str,
                           voice: str = "ru-RU-DmitryNeural",
                           rate: str = "+50%"):
    """
    Синтезирует отдельную часть текста и сохраняет её в mp3_path.
    """
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(mp3_path)


async def synthesize_text_to_audio_edge(text: str, filename_prefix: str, message: Message, logger):
    """
    Синтезирует *большой* текст по частям и
    сразу отправляет каждую часть пользователю (без возвращения списка).

    1. Анализируем текст (text_analysis) -> шлём summary.
    2. Разбиваем текст на части.
    3. Каждую часть синтезируем, отправляем, удаляем.
    """
    if not text.strip():
        logger.warning("Пустой текст для синтеза.")
        await message.reply("Не удалось озвучить: пустой текст.")
        return

    if len(text) > 1000000:
        logger.info(f"Слишком большой файл: {len(text)} символа\n\n")
        await message.reply("Текст для озвучки слишком большой. Напишите @maksenro если хотите повысить лимиты!")
        return

    logger.info(f"@{message.from_user.username}, длина - {len(text)}: {text[:100]}...\n\n")
    summary = await analyze_text(text)
    await message.reply(summary, parse_mode='HTML')

    # Генерируем имя файла (упрощённо)
    base_filename = f"{text[:25]}_{filename_prefix}"

    parts = await chunk_text(text)
    total_parts = len(parts)

    for i, chunked_text in enumerate(parts, start=1):
        part_filename = f"{i}_of_{total_parts}_{base_filename}.mp3"
        mp3_path = os.path.join(AUDIO_FOLDER, part_filename)

        start_time = time.time()
        await synthesize_chunk(chunked_text, mp3_path)
        end_time = time.time()

        logger.debug(f"Часть {i}/{total_parts} синтезирована за {round(end_time - start_time, 2)} сек.")

        audio_file = FSInputFile(mp3_path)
        await message.reply_audio(audio=audio_file)

        os.remove(mp3_path)
