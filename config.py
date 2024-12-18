# config.py
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Базовая директория проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Токен Telegram бота
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Конфигурация файла логов с абсолютным путем
LOG_FILE = os.path.join(BASE_DIR, os.getenv("LOG_FILE", "bot_log.log"))

# Папка для хранения аудиофайлов
AUDIO_FOLDER = os.getenv("AUDIO_FOLDER", "audio")

# ID администратора
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
