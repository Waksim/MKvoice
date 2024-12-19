# config.py

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

# Administrator ID, retrieved from environment variables and converted to integer
# Defaults to 0 if not specified
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
