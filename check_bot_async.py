import asyncio
from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    info = await bot.get_me()  # await обязательно
    print(info)

asyncio.run(main())