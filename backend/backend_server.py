import os
import sys
from pathlib import Path
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from loguru import logger
from dotenv import load_dotenv

# Добавляем корневую директорию проекта в sys.path, чтобы работали импорты
# Это важно, так как uvicorn запускается из папки /app
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import TOKEN
from utils.text_to_speech import synthesize_text_to_audio_edge
from utils.i18n import get_translator, get_user_lang

# Загружаем переменные окружения из .env файла
load_dotenv()

# --- Настройка Loguru ---
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/backend.log", level="DEBUG", rotation="10 MB", compression="zip")

# --- Инициализация FastAPI ---
app = FastAPI(title="MKvoice Backend API")

# --- Настройка CORS ---
# Это КРИТИЧЕСКИ ВАЖНО, чтобы ваш Web App на домене github.io
# мог отправлять запросы на ваш сервер.
origins = [
    "https://waksim.github.io",  # Ваш домен Web App
    "http://localhost",         # Для локальной разработки
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Разрешаем все методы (GET, POST, и т.д.)
    allow_headers=["*"], # Разрешаем все заголовки
)

# --- Модель данных для входящего запроса ---
class TextToProcess(BaseModel):
    user_id: int = Field(..., description="Telegram User ID")
    text: str = Field(..., description="Text to synthesize")

# --- Инициализация бота ---
# Мы создаем объект бота один раз при старте сервера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

# --- Эндпоинт для обработки текста ---
@app.post("/process-text")
async def process_text_from_webapp(data: TextToProcess, request: Request):
    """
    Принимает user_id и текст из Web App, инициирует процесс синтеза речи.
    """
    user_id = data.user_id
    text = data.text
    client_host = request.client.host

    logger.info(f"Received request from {client_host} for user_id: {user_id}. Text length: {len(text)}")

    if not text.strip():
        logger.warning(f"Received empty text for user_id: {user_id}")
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        # Получаем язык пользователя для корректных сообщений
        lang_code = await get_user_lang(user_id)
        translator = get_translator(lang_code)
        _ = translator.gettext

        # Создаем "фейковый" объект Message, чтобы передать его в функцию синтеза
        # Это упрощает переиспользование существующего кода
        class FakeMessage:
            class FromUser:
                id = user_id
                username = "WebAppUser"
            from_user = FromUser()

            async def reply(self, text_to_reply, parse_mode=None):
                await bot.send_message(self.from_user.id, text_to_reply, parse_mode=parse_mode)

            async def reply_audio(self, audio):
                await bot.send_audio(self.from_user.id, audio)

        fake_message = FakeMessage()

        # Немедленно отвечаем пользователю, что задача принята
        await bot.send_message(user_id, _("Received your text from the web app. Starting synthesis..."))

        # Запускаем асинхронную задачу синтеза
        # Это позволяет сразу вернуть ответ "200 OK" в Web App, не дожидаясь окончания синтеза
        # asyncio.create_task(synthesize_text_to_audio_edge(text, str(user_id), fake_message, logger, _))
        # ИЗМЕНЕНИЕ: Вместо create_task, будем выполнять синхронно, чтобы дождаться результата
        # и корректно обработать ошибки. FastAPI хорошо справляется с async-запросами.
        await synthesize_text_to_audio_edge(text, str(user_id), fake_message, logger, _)

        logger.info(f"Successfully initiated synthesis for user_id: {user_id}")
        return {"status": "success", "message": "Text processing started."}

    except Exception as e:
        logger.error(f"Failed to process text for user_id {user_id}. Error: {e}", exc_info=True)
        # Уведомляем пользователя об ошибке в телеграме
        try:
            await bot.send_message(user_id, f"An internal error occurred on the server: {e}")
        except Exception as send_error:
            logger.error(f"Failed to send error notification to user {user_id}: {send_error}")

        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/")
def read_root():
    return {"message": "MKvoice Backend is running."}