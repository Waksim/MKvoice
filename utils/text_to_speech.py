# ============================= FILE: utils/text_to_speech.py =============================
"""
Handles text analysis and text-to-speech synthesis using Microsoft Edge TTS (edge-tts).
Includes dynamic retrieval of user settings: chunk_size and tts_speed.
Restores the file name based on sanitized text input.
"""

import time
import os
import re
import uuid

import edge_tts
from aiogram.types import Message, FSInputFile
from loguru import logger
from langdetect import detect, DetectorFactory, LangDetectException

from config import AUDIO_FOLDER
from .text_analysis import analyze_text
from utils.user_settings import get_user_settings

# If using i18n middleware, import _ here
# from utils.i18n import _

DetectorFactory.seed = 0

VOICE_MAP = {
    "ru": "ru-RU-DmitryNeural",
    "en": "en-US-JennyNeural",
    "uk": "uk-UA-OstapNeural",
    "zh-cn": "zh-CN-XiaoxiaoNeural",
}

def sanitize_filename(text: str, max_length: int = 50) -> str:
    """
    Removes or replaces characters that are invalid in most file systems.
    Cuts the result to max_length characters.
    """
    # Remove forbidden characters: <>:"/\\|?* and control chars (0x00-0x1F)
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', text)
    # Also remove trailing spaces and limit length
    sanitized = sanitized.strip()[:max_length]
    return sanitized

async def synthesize_text_to_audio_edge(text: str, filename_prefix: str, message: Message, logger, _):
    """
    Synthesizes large text in chunks, sends each audio chunk to the user.
    Respects user settings (chunk_size, tts_speed) from DB.
    Also restores the file name with a sanitized portion of the text or prefix.
    """
    user_id = message.from_user.id

    # 1) Retrieve user settings
    settings = get_user_settings(user_id)
    user_chunk_size = settings['chunk_size']
    user_speed = settings['tts_speed']  # e.g. '+25%' or '-50%', etc.

    if not text.strip():
        logger.warning(_("Empty text for synthesis."))
        await message.reply(_("Could not synthesize: empty text."))
        return

    # Example overall limit to avoid extremely large texts
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

    # Detect language for TTS voice
    lang = detect_language(text)
    if lang == "unknown":
        logger.warning(_("Could not detect language. Using default voice."))
        voice = "ru-RU-DmitryNeural"
        await message.reply(_("Could not detect language. Using default voice."))
    else:
        voice = VOICE_MAP.get(lang, "ru-RU-DmitryNeural")
        logger.info(_("Detected language: {lang}. Using voice: {voice}").format(lang=lang, voice=voice))

    # Split text into chunks according to user settings
    parts = await chunk_text(text, user_chunk_size)
    total_parts = len(parts)

    # Create a sanitized 'title' for the file from either the text or the filename_prefix
    # Example: take the first 25 characters of the text
    # If you prefer the user-defined prefix, just use that:
    sanitized_title = sanitize_filename(text[:25])  # or use filename_prefix

    for i, chunked_text in enumerate(parts, start=1):
        # We add a unique_id to avoid collisions
        unique_id = uuid.uuid4().hex

        if total_parts > 1:
            # For multi-chunk text
            part_filename = f"{i}_of_{total_parts}_{sanitized_title}_{unique_id}.mp3"
        else:
            # For a single chunk only
            part_filename = f"{sanitized_title}_{unique_id}.mp3"

        mp3_path = os.path.join(AUDIO_FOLDER, part_filename)

        start_time = time.time()
        try:
            await synthesize_chunk(chunked_text, mp3_path, voice=voice, rate=user_speed)
            end_time = time.time()

            logger.debug(_("Part {i}/{total_parts} synthesized in {seconds} sec.").format(
                i=i, total_parts=total_parts, seconds=round(end_time - start_time, 2)
            ))

            audio_file = FSInputFile(mp3_path)
            await message.reply_audio(audio=audio_file)
            logger.info(f"Sent audio part {i}/{total_parts} to user {user_id}.")
        except Exception as e:
            logger.error(f"Error synthesizing part {i}/{total_parts}: {e}")
            await message.reply(_("Failed to synthesize part {i}: {error}").format(i=i, error=str(e)))
        finally:
            # Clean up file after sending
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
                logger.info(f"Removed temporary audio file {mp3_path}.")

async def chunk_text(text: str, chunk_size: int) -> list[str]:
    """
    Splits the original text into chunks of up to chunk_size characters.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size
    return chunks

def detect_language(text: str) -> str:
    """
    Detects the language of the given text. Returns 'unknown' if detection fails.
    """
    from langdetect import detect, DetectorFactory, LangDetectException
    DetectorFactory.seed = 0
    try:
        lang = detect(text)
        lang = lang.lower()
        if lang.startswith("zh"):
            return "zh-cn"
        return lang
    except LangDetectException:
        return "unknown"

async def synthesize_chunk(text: str, mp3_path: str, voice: str, rate: str):
    """
    Synthesizes a single chunk of text with the specified voice and rate,
    then saves it to mp3_path.
    """
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(mp3_path)
