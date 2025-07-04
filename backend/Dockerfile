# Используем тот же базовый образ, что и у бота
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .
COPY backend/requirements.txt ./backend/requirements.txt

# Устанавливаем зависимости
# Сначала общие, потом специфичные для бэкенда
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r backend/requirements.txt && \
    playwright install && \
    playwright install-deps

# Копируем все файлы проекта в контейнер
# Это необходимо, так как бэкенд использует утилиты из папки /utils
COPY . .

# Команда для запуска uvicorn сервера
# 0.0.0.0 нужен, чтобы сервер был доступен извне контейнера
CMD ["uvicorn", "backend.backend_server:app", "--host", "0.0.0.0", "--port", "8000"]