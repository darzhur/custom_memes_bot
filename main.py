from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram import Update
import os
from dotenv import load_dotenv
from io import BytesIO
import aiohttp
import httpx
from datetime import datetime
from supabase.client import AsyncClient

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = AsyncClient(SUPABASE_URL, SUPABASE_KEY)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("PROXYAPI_KEY")
# MCP_URL = "https://memepedia-nwyn.onrender.com/memes"
# test
# MCP_URL = "http://127.0.0.1:8000/memes"


# async def fetch_memes():
#     """Получаем текст последних мемов с MCP"""
#     async with httpx.AsyncClient() as client:
#         try:
#             resp = await client.get(MCP_URL)
#             if resp.status_code == 200:
#                 memes = resp.json()
#                 if not memes:
#                     return "Нет мемов"
#                 return "\n".join([m.get("title", "") for m in memes])
#         except Exception as e:
#             print("Ошибка MCP:", e)
#     return "Не удалось получить мемы"

async def fetch_memes(limit: int = 10):
    """Получаем последние мемы из таблицы memepedia"""
    try:
        resp = await supabase.table("memepedia")\
            .select("title, content")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        if resp.data:
            return "\n".join([f"{m['title']} - {m.get('content','')}" for m in resp.data])
        else:
            return "Нет мемов в базе"
    except Exception as e:
        print("Ошибка Supabase:", e)
        return "Не удалось получить мемы"


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Это не фото 😅")
        return

    # --- Получаем фото ---
    file = await update.message.photo[-1].get_file()
    bio = BytesIO()
    await file.download_to_memory(out=bio)
    bio.seek(0)

    # --- Загружаем на Catbox ---
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field("reqtype", "fileupload")
        data.add_field("fileToUpload", bio, filename="image.jpg", content_type="image/jpeg")
        try:
            async with session.post("https://catbox.moe/user/api.php", data=data) as resp:
                image_url = await resp.text()
        except Exception as e:
            await update.message.reply_text("Ошибка при загрузке на Catbox 😅")
            print(e)
            return

    if not image_url.startswith("http"):
        await update.message.reply_text("Не удалось загрузить фото на Catbox 😅")
        print("Catbox ответил:", image_url)
        return

    await update.message.reply_text(f"Фото загружено: {image_url}")

    # --- Получаем контекст мемов ---
    mcp_context = await fetch_memes()
    print("Контекст MCP:", mcp_context[:500])

    # --- ProxyAPI ---
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Ты — генератор мемов на русском языке: на основе загруженного пользователем изображения и переданной информации о свежих мемах и трендах придумай 3 варианта подписи (каждый с новой строки, пронумерованные 1, 2, 3), не более 1–2 предложений каждый, коротко, лаконично, в стиле черный юмор, саркастично, дерзко, пошло (без графических описаний и нарушений правил), без эмодзи, без объяснений и без вступлений, обязательно учитывая детали изображения и актуальный мемный контекст.\n{mcp_context}"},
                    {"type": "image_url", "image_url": {"url": image_url}}
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
        try:
            async with session.post(
                "https://api.proxyapi.ru/openai/v1/chat/completions",
                json=payload,
                headers=headers
            ) as resp:
                result = await resp.json()
        except Exception as e:
            await update.message.reply_text("Ошибка ProxyAPI 😅")
            print(e)
            return

    # --- Безопасно извлекаем подписи ---
    captions_list = []
    choices = result.get("choices")
    if choices and isinstance(choices, list):
        message_content = choices[0].get("message", {}).get("content")
        if isinstance(message_content, str):
            captions_list = [c for c in message_content.split("\n") if c.strip()]
        elif isinstance(message_content, list):
            captions_list = [c.get("text", "") for c in message_content if c.get("text")]
    if not captions_list:
        captions_list = ["Не удалось сгенерировать подпись 😅"]

    # --- Отправляем в Telegram ---
    for caption in captions_list:
        await update.message.reply_text(caption)

    # # --- Сохраняем в Supabase ---
    # try:
    #     for caption in captions_list:
    #         supabase.table("memes").insert({
    #             "image_url": image_url,
    #             "caption": caption
    #         }).execute()
    # except Exception as e:
    #     print("Ошибка сохранения в Supabase:", e)

    # --- Сохраняем придуманное в generated_memes ---
    # Берём первые 3 подписи
    c1, c2, c3 = (captions_list + ["", "", ""])[:3]

    await supabase.table("generated_memes").insert({
        "title": "Мем с подписью",
        "image_url": image_url,
        "caption1": c1,
        "caption2": c2,
        "caption3": c3
    }).execute()


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Бот запущен")
    app.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()