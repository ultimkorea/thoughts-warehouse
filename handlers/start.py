from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from keyboards import main_keyboard

router = Router()

@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Выбери действие:", reply_markup=main_keyboard)

def register_start_handlers(dp):
    dp.include_router(router)
