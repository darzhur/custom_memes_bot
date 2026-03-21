# main.py
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram import Update, Bot
from supabase import create_client, Client
from io import BytesIO
from PIL import Image
import base64
import aiohttp
import traceback
import asyncio
from telegram.error import TimedOut
import random

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("PROXYAPI_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------
# Сбрасываем webhook
# ----------------------------
async def reset_webhook():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(120)
        .build()
    )
    await bot.delete_webhook(drop_pending_updates=True)

# ----------------------------
# Получаем случайные мемы из memepedia
# ----------------------------
async def fetch_random_memes(limit=5):
    try:
        resp = await supabase.table("memepedia").select("title, content").execute()
        all_memes = resp.data or []
        return random.sample(all_memes, min(limit, len(all_memes)))
    except Exception as e:
        print("Ошибка fetch_random_memes:", e)
        return []

async def build_random_context():
    memes = await fetch_random_memes(limit=5)
    lines = [f"{i+1}. {m.get('title','')} - {m.get('content','')}" for i, m in enumerate(memes)]
    if not lines:
        lines = ["сарказм, черный юмор, дерзко"]
    return "\n".join(lines)

# ----------------------------
# Функция обработки фото
# ----------------------------
async def handle_photo(file, save_path=None, max_retries=3):
    """
    Скачивает файл Telegram с учётом таймаутов и повторов.
    
    :param file: объект telegram.File
    :param save_path: если указано, сохраняем на диск по этому пути, иначе в память
    :param max_retries: количество попыток при таймауте
    :return: байты файла, если save_path=None
    """
    for attempt in range(1, max_retries + 1):
        try:
            if save_path:
                # Скачиваем на диск
                await file.download_to_drive(custom_path=save_path)
                return save_path
            else:
                # Скачиваем в память
                import io
                bio = io.BytesIO()
                await file.download_to_memory(out=bio)
                bio.seek(0)
                return bio
        except TimedOut:
            print(f"[handle_photo] Попытка {attempt} из {max_retries} — таймаут. Повтор через 2 сек.")
            await asyncio.sleep(2)
    raise TimedOut(f"Не удалось скачать файл после {max_retries} попыток")
# ----------------------------
# Основная функция
# ----------------------------
async def main_async():
# создаём бота с увеличенным таймаутом
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(120)
        .build()
    )

    # добавляем хендлер-обёртку для фото
    async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.photo:
            return
        file = await update.message.photo[-1].get_file()
        try:
            bio = await handle_photo(file)  # или save_path="downloads/photo.jpg"
            print("Фото скачано успешно")
        except TimedOut:
            print("Не удалось скачать фото после нескольких попыток")

    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    # сброс webhook
    await reset_webhook()

    print("Бот запущен (polling)")
    await app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main_async())