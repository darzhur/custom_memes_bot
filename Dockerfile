FROM python:3.10

WORKDIR /app
COPY . .

# Устанавливаем необходимые библиотеки для сборки aiohttp
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    python3-dev \
    gcc \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]