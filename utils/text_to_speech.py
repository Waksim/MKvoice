import time
import os
import edge_tts
from aiogram.types import Message, FSInputFile
from loguru import logger
from config import AUDIO_FOLDER
from .text_analysis import analyze_text
from langdetect import detect, DetectorFactory, LangDetectException

# Чтобы результаты были воспроизводимыми
DetectorFactory.seed = 0

CHUNK_SIZE = 40000  # Примерное кол-во символов на часть

VOICE_MAP = {
    "ru": "ru-RU-DmitryNeural",       # Русский
    "en": "en-US-JennyNeural",        # Английский (США)
    "uk": "uk-UA-OstapNeural",        # Украинский
    "zh-cn": "zh-CN-XiaoxiaoNeural",  # Китайский (упрощённый)
    # Добавьте другие языки и голоса по необходимости
}

def detect_language(text: str) -> str:
    """
    Определяет язык текста.
    Возвращает код языка, например, 'ru', 'en', 'uk', 'zh-cn'.
    Если язык не определён, возвращает 'unknown'.
    """
    try:
        lang = detect(text)
        lang = lang.lower()
        if lang.startswith("zh"):
            return "zh-cn"  # или "zh-tw" для традиционного китайского
        return lang
    except LangDetectException:
        return "unknown"

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
    Использует указанный голос и скорость речи.
    """
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(mp3_path)

async def synthesize_text_to_audio_edge(text: str, filename_prefix: str, message: Message, logger, _):
    """
    Синтезирует *большой* текст по частям и
    сразу отправляет каждую часть пользователю (без возвращения списка).

    1. Анализируем текст (text_analysis) -> шлём summary.
    2. Определяем язык текста и выбираем голос.
    3. Разбиваем текст на части.
    4. Каждую часть синтезируем, отправляем, удаляем.
    """
    if not text.strip():
        logger.warning(_("Пустой текст для синтеза."))
        await message.reply(_("Не удалось озвучить: пустой текст."))
        return

    if len(text) > 1000000:
        logger.info(_("Слишком большой файл: {len_text} символов").format(len_text=len(text)))
        await message.reply(_("Текст для озвучки слишком большой. Напишите @maksenro если хотите повысить лимиты!"))
        return

    logger.info(_("@{username}, длина - {len_text}: {preview}...").format(
        username=message.from_user.username,
        len_text=len(text),
        preview=text[:100]
    ))
    summary = await analyze_text(text, _)
    await message.reply(summary, parse_mode='HTML')

    # Определяем язык текста
    lang = detect_language(text)
    if lang == "unknown":
        logger.warning(_("Не удалось определить язык текста. Используется голос по умолчанию."))
        voice = "ru-RU-DmitryNeural"  # Голос по умолчанию
        await message.reply(_("Не удалось определить язык текста. Используется голос по умолчанию."))
    else:
        voice = VOICE_MAP.get(lang, "ru-RU-DmitryNeural")  # fallback на русский
        logger.info(_("Определён язык: {lang}. Используется голос: {voice}").format(lang=lang, voice=voice))

    base_filename = f"{text[:25]}_{filename_prefix}"
    parts = await chunk_text(text)
    total_parts = len(parts)

    for i, chunked_text in enumerate(parts, start=1):
        part_filename = f"{i}_of_{total_parts}_{base_filename}.mp3"
        mp3_path = os.path.join(AUDIO_FOLDER, part_filename)

        start_time = time.time()
        await synthesize_chunk(chunked_text, mp3_path, voice=voice)
        end_time = time.time()

        logger.debug(_("Часть {i}/{total_parts} синтезирована за {seconds} сек.").format(
            i=i,
            total_parts=total_parts,
            seconds=round(end_time - start_time, 2)
        ))

        audio_file = FSInputFile(mp3_path)
        await message.reply_audio(audio=audio_file)
        os.remove(mp3_path)
