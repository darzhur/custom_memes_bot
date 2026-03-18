FROM python:3.11

WORKDIR /app
COPY . .

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]