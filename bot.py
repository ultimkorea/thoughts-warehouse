import asyncio
from aiogram import Bot, Dispatcher
from database import init_db
from handlers import register_all_handlers
import os
# Проверяем переменную окружения, иначе берём из config.py
TOKEN = os.environ("TOKEN")

if TOKEN is None:
    try:
        from config import TOKEN_FROM_CONFIG
        TOKEN = TOKEN_FROM_CONFIG
    except ImportError:
        raise RuntimeError("❌ Ошибка: Токен не найден ни в переменной окружения, ни в config.py!")


bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    await init_db()
    register_all_handlers(dp)  # Подключаем все хендлеры
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
