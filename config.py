import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LOG_FILE = os.getenv("LOG_FILE", "bot_log.log")
AUDIO_FOLDER = os.getenv("AUDIO_FOLDER", "audio")
