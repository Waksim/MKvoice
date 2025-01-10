# ============================= FILE: config.py =============================
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Determine the base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Telegram bot token retrieved from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Path to the log file, defaults to 'bot_log.log' if not specified
LOG_FILE = os.path.join(BASE_DIR, os.getenv("LOG_FILE", "bot_log.log"))

# Directory to store audio files, defaults to 'audio' if not specified
AUDIO_FOLDER = os.getenv("AUDIO_FOLDER", "audio")

# Administrator ID retrieved from environment variables, converted to integer (default 0)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Dictionary of available languages with corresponding flags
AVAILABLE_LANGUAGES = {
    'en': {'name': 'English', 'flag': '🇺🇸'},
    'ru': {'name': 'Russian', 'flag': '🇷🇺'},
    'uk': {'name': 'Ukrainian', 'flag': '🇺🇦'},
    'zh': {'name': 'Chinese', 'flag': '🇨🇳'},
}

# Maximum length of a message, used to split long logs or text
MAX_MESSAGE_LENGTH = 4000