# main.py
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram import Update, Bot
from supabase import create_client, Client
from context import build_context
from io import BytesIO
from PIL import Image
import base64
import aiohttp
import traceback

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
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)

# ----------------------------
# Функция обработки фото
# ----------------------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Это не фото 😅")
        return
    try:
        file = await update.message.photo[-1].get_file()
        bio = BytesIO()
        await file.download_to_memory(out=bio)
        bio.seek(0)

        img = Image.open(bio)
        img_format = img.format.lower() if img.format else "jpeg"
        image_base64 = base64.b64encode(bio.getvalue()).decode()
        image_data_url = f"data:image/{img_format};base64,{image_base64}"

        meme_context = build_context(supabase)
        if not meme_context:
            meme_context = "сарказм, черный юмор, дерзко"

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

        captions_list = []
        choices = result.get("choices")
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            captions_list = [c.strip() for c in content.split("\n") if c.strip()]
        if not captions_list:
            captions_list = ["Не удалось сгенерировать подпись 😅"]

        for caption in captions_list:
            await update.message.reply_text(caption)

        c1, c2, c3 = (captions_list + ["", "", ""])[:3]
        supabase.table("generated_memes").insert({
            "title": "Мем с подписью",
            "image_url": "base64_embedded",
            "caption1": c1,
            "caption2": c2,
            "caption3": c3
        }).execute()

    except Exception:
        print("ERROR in handle_photo:")
        traceback.print_exc()
        await update.message.reply_text("Что-то сломалось 😅")

# ----------------------------
# Основная функция
# ----------------------------
async def main_async():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # сброс webhook
    await reset_webhook()

    print("Бот запущен (polling)")
    await app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # разрешаем повторное использование loop в Docker/Jupyter
    asyncio.run(main_async())