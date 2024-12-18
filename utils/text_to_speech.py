import time
import os
import edge_tts
from aiogram.types import Message, FSInputFile
from .text_analysis import analyze_text
from config import AUDIO_FOLDER

async def synthesize_text_to_audio_edge(text: str, filename_prefix: str, message: Message, logger):
    """
    Synthesize speech from the given text using Microsoft Edge TTS.

    Steps:
    - Analyze the text and send the analysis to the user.
    - Synthesize the text into an MP3 file.
    - Measure processing time and send performance metrics.
    - Return the path to the generated MP3 file.
    """
    logger.info(f"@{message.from_user.username}: {text[:100]}...\n")

    # Create a filename based on the first few words of the text
    words = text.split()[:5]
    filename = "_".join(words) or "output"
    mp3_path = os.path.join(AUDIO_FOLDER, f"{filename}.mp3")

    # Send text analysis to the user
    summary = await analyze_text(text)
    await message.reply(summary, parse_mode='HTML')

    # Start the synthesis process
    communicate = edge_tts.Communicate(text=text, voice="ru-RU-DmitryNeural", rate="+50%")

    start_time = time.time()
    await communicate.save(mp3_path)
    end_time = time.time()

    # Calculate processing time and speed
    processing_time = round(end_time - start_time, 2)
    processing_minutes = int(processing_time // 60)
    processing_seconds = int(processing_time % 60)

    processing_time_str = ""
    if processing_minutes > 0:
        processing_time_str += f"{processing_minutes} min "
    if processing_seconds > 0 or processing_minutes == 0:
        processing_time_str += f"{processing_seconds} sec"

    characters_per_second = round(len(text) / processing_time, 2)

    # Send performance metrics to the user
    response = (
        f"⏳ Processing time: {processing_time_str}\n"
        f"⚡ Synthesis speed: {characters_per_second} chars/sec"
    )
    await message.reply(response, parse_mode='HTML')

    return mp3_path
