# ============================= FILE: utils/text_to_speech.py =============================
import time
import os
import edge_tts
from aiogram.types import Message, FSInputFile
from loguru import logger
from config import AUDIO_FOLDER
from .text_analysis import analyze_text
from langdetect import detect, DetectorFactory, LangDetectException
import re
import uuid  # for generating unique identifiers

DetectorFactory.seed = 0

CHUNK_SIZE = 40000

VOICE_MAP = {
    "ru": "ru-RU-DmitryNeural",
    "en": "en-US-JennyNeural",
    "uk": "uk-UA-OstapNeural",
    "zh-cn": "zh-CN-XiaoxiaoNeural",
}

def detect_language(text: str) -> str:
    """
    Detects the language of the text.
    Returns language code (e.g., 'ru', 'en', 'uk', 'zh-cn').
    If detection fails, returns 'unknown'.
    """
    try:
        lang = detect(text)
        lang = lang.lower()
        if lang.startswith("zh"):
            return "zh-cn"
        return lang
    except LangDetectException:
        return "unknown"

async def chunk_text(text: str, chunk_size: int = CHUNK_SIZE):
    """
    Splits text into parts of up to chunk_size characters.
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
    Synthesizes a single chunk of text and saves it to mp3_path using Edge TTS.
    """
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(mp3_path)

def sanitize_filename(text: str) -> str:
    """
    Sanitizes the input text to create a valid filename.
    Removes or replaces characters that are not allowed in filenames.
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', text)
    # Replace spaces with underscores
    sanitized = re.sub(r'\s+', '_', sanitized)
    # Limit the filename length to 50 characters
    return sanitized[:50] if len(sanitized) > 50 else sanitized

async def synthesize_text_to_audio_edge(text: str, filename_prefix: str, message: Message, logger, _):
    """
    Synthesizes large text by parts and sends each part to the user immediately:
    1. Analyze text and send summary.
    2. Detect language and pick a corresponding voice.
    3. Split text into parts.
    4. Synthesize and send each part, then remove the file.
    """
    if not text.strip():
        logger.warning(_("Empty text for synthesis."))
        await message.reply(_("Could not synthesize: empty text."))
        return

    if len(text) > 1000000:
        logger.info(_("The text is too large: {len_text} characters").format(len_text=len(text)))
        await message.reply(_("The text is too large. Contact @maksenro if you want to increase limits!"))
        return

    logger.info(_("@{username}, length - {len_text}: {preview}...").format(
        username=message.from_user.username if message.from_user.username else "User",
        len_text=len(text),
        preview=text[:100]
    ))
    summary = await analyze_text(text, _)
    await message.reply(summary, parse_mode='HTML')

    lang = detect_language(text)
    if lang == "unknown":
        logger.warning(_("Could not detect language. Using default voice."))
        voice = "ru-RU-DmitryNeural"
        await message.reply(_("Could not detect language. Using default voice."))
    else:
        voice = VOICE_MAP.get(lang, "ru-RU-DmitryNeural")
        logger.info(_("Detected language: {lang}. Using voice: {voice}").format(lang=lang, voice=voice))

    # Create base filename by sanitizing the first 25 characters of the text
    base_text = text[:25]
    sanitized_base = sanitize_filename(base_text)
    base_filename = f"{sanitized_base}_{filename_prefix}"
    parts = await chunk_text(text)
    total_parts = len(parts)

    for i, chunked_text in enumerate(parts, start=1):
        # Generate a unique filename using UUID for extra uniqueness
        unique_id = uuid.uuid4().hex
        if total_parts > 1:
            part_filename = f"{i}_of_{total_parts}_{base_filename}_{unique_id}.mp3"
        else:
            part_filename = f"{base_filename}_{unique_id}.mp3"
        mp3_path = os.path.join(AUDIO_FOLDER, part_filename)

        start_time = time.time()
        try:
            await synthesize_chunk(chunked_text, mp3_path, voice=voice)
            end_time = time.time()

            logger.debug(_("Part {i}/{total_parts} synthesized in {seconds} sec.").format(
                i=i,
                total_parts=total_parts,
                seconds=round(end_time - start_time, 2)
            ))

            audio_file = FSInputFile(mp3_path)
            await message.reply_audio(audio=audio_file)
            logger.info(f"Sent audio part {i}/{total_parts} to user {message.from_user.id}.")
        except Exception as e:
            logger.error(f"Error synthesizing part {i}/{total_parts}: {e}")
            await message.reply(_("Failed to synthesize part {i}: {error}").format(i=i, error=str(e)))
        finally:
            # Remove the file if it exists
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
                logger.info(f"Removed temporary audio file {mp3_path}.")