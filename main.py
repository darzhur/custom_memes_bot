import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from telegram import Update
from supabase import create_client
from io import BytesIO
import base64
import aiohttp
import traceback
import asyncio
import random
from telegram.error import TimedOut

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("PROXYAPI_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------
# Сбрасываем webhook
# ----------------------------
async def reset_webhook(app):
    await app.bot.delete_webhook(drop_pending_updates=True)

# ----------------------------
# Мемы
# ----------------------------
async def fetch_random_memes(limit=5):
    try:
        resp = supabase.table("memepedia").select("title, content").execute()
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
# Скачивание фото
# ----------------------------
async def handle_photo(file, save_path=None, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            if save_path:
                await file.download_to_drive(custom_path=save_path)
                return save_path
            else:
                bio = BytesIO()
                await file.download_to_memory(out=bio)
                bio.seek(0)
                return bio
        except TimedOut:
            print(f"[handle_photo] Попытка {attempt} из {max_retries} — таймаут. Повтор через 2 сек.")
            await asyncio.sleep(2)
    raise TimedOut(f"Не удалось скачать файл после {max_retries} попыток")

# ----------------------------
# Хендлер фото + ProxyAPI
# ----------------------------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return
    try:
        file = await update.message.photo[-1].get_file()
        bio = await handle_photo(file)
        print("Фото скачано успешно")

        # Превращаем фото в base64
        bio.seek(0)
        image_bytes = bio.read()
        image_data_url = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"

        # Генерируем мемный контекст
        meme_context = await build_random_context()

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"""
Ты пишешь подписи к мемам.

Стиль:
- сарказм
- черный юмор
- дерзко
- коротко (1 предложение)

Примеры:
{meme_context}

Сделай 3 подписи (1,2,3).
"""}, 
                        {"type": "image_url", "image_url": {"url": image_data_url}}
                    ]
                }
            ],
            "max_tokens": 300
        }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.proxyapi.ru/openai/v1/chat/completions",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    await update.message.reply_text("Ошибка генерации 😅")
                    return
                result = await resp.json()

        # Обрабатываем ответ
        captions_list = []
        choices = result.get("choices")
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            captions_list = [c.strip() for c in content.split("\n") if c.strip()]
        if not captions_list:
            captions_list = ["Не удалось сгенерировать подпись 😅"]

        # Отправляем пользователю
        for caption in captions_list:
            await update.message.reply_text(caption)

        # Сохраняем в Supabase
        c1, c2, c3 = (captions_list + ["", "", ""])[:3]
        supabase.table("generated_memes").insert({
            "title": "Мем с подписью",
            "image_url": image_data_url,
            "caption1": c1,
            "caption2": c2,
            "caption3": c3
        }).execute()

    except Exception:
        print("ERROR in photo_handler:")
        traceback.print_exc()
        await update.message.reply_text("Что-то сломалось 😅")

# ----------------------------
# Основная функция
# ----------------------------
async def main_async():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).read_timeout(120).build()

    # Сбрасываем webhook
    await reset_webhook(app)

    # Добавляем хендлеры
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    print("Бот запущен (polling)")
    await app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main_async())