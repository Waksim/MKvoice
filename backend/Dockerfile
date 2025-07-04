# Используем тот же базовый образ, что и у бота
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# 1. Копируем ТОЛЬКО файлы зависимостей
COPY requirements.txt .
COPY backend/requirements.txt ./backend/requirements.txt

# 2. Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r backend/requirements.txt && \
    # ИЗМЕНЕНИЕ: Устанавливаем только chromium и его зависимости
    playwright install chromium && \
    playwright install-deps chromium

# 3. Копируем все остальные файлы проекта
COPY . .

# Команда для запуска uvicorn сервера
CMD ["uvicorn", "backend.backend_server:app", "--host", "0.0.0.0", "--port", "8000"]