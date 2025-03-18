import asyncio
from aiogram import Bot, Dispatcher
from database import init_db
from handlers import register_all_handlers
import os

TOKEN_ENV = os.getenv("TOKEN")
if TOKEN_ENV == None:
    from config import TOKEN_FROM_CONFIG
    TOKEN = TOKEN_FROM_CONFIG
else:
    TOKEN = TOKEN_ENV

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    await init_db()
    register_all_handlers(dp)  # Подключаем все хендлеры
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
