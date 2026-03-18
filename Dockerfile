# Dockerfile
FROM python:3.10

WORKDIR /app

# Копируем проект
COPY . .

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Команда запуска бота
CMD ["python", "main.py"]