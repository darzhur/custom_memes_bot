# main.py
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram import Update, Bot
import os
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import traceback
from context import build_context
from supabase import create_client, Client
import asyncio
import base64
import aiohttp

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("PROXYAPI_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------
# Сбрасываем webhook до запуска polling
# ----------------------------
async def reset_webhook():
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)

# запускаем reset разово
asyncio.run(reset_webhook())

# ----------------------------
# Вспомогательные функции
# ----------------------------
def build_meme_context(memes):
    lines = []
    for i, m in enumerate(memes, 1):
        caption = m.get("caption", "").strip()
        tags = m.get("tags", "")
        caption = caption[:120]
        lines.append(f"{i}. {caption} ({tags})")
    return "\n".join(lines)

async def fetch_good_memes(limit: int = 5):
    try:
        resp = supabase.table("good_memes")\
            .select("caption, tags")\
            .order("score", desc=True)\
            .limit(limit)\
            .execute()
        if not resp.data:
            return []
        return resp.data
    except Exception as e:
        print("Ошибка получения good_memes:", e)
        return []

# ----------------------------
# Основная функция обработки фото
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

        print("Image prepared, size:", len(image_base64))

        # Контекст мемов
        meme_context = build_context(supabase)
        if not meme_context:
            meme_context = "сарказм, черный юмор, дерзко"
        print("Контекст мемов:", meme_context)

        # Запрос к ProxyAPI
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
                status = resp.status
                text = await resp.text()
                print("ProxyAPI status:", status)
                print("ProxyAPI response:", text[:500])
                if status != 200:
                    await update.message.reply_text("Ошибка генерации 😅")
                    return
                result = await resp.json()

        # Извлекаем подписи
        captions_list = []
        choices = result.get("choices")
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            captions_list = [c.strip() for c in content.split("\n") if c.strip()]
        if not captions_list:
            captions_list = ["Не удалось сгенерировать подпись 😅"]

        for caption in captions_list:
            await update.message.reply_text(caption)

        # Сохраняем в Supabase
        c1, c2, c3 = (captions_list + ["", "", ""])[:3]
        supabase.table("generated_memes").insert({
            "title": "Мем с подписью",
            "image_url": "base64_embedded",
            "caption1": c1,
            "caption2": c2,
            "caption3": c3
        }).execute()

    except Exception as e:
        print("ERROR in handle_photo:")
        traceback.print_exc()
        await update.message.reply_text("Что-то сломалось 😅")

# ----------------------------
# Main
# ----------------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Бот запущен (polling)")
    # run_polling сам создаёт loop, не трогаем asyncio
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()