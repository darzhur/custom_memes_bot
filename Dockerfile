# Dockerfile
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Экспорт переменных окружения (если нужно)
# ENV TOKEN=твой_токен

# Команда запуска
CMD ["python", "main.py"]