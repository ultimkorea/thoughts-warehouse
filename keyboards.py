from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главное меню
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Посмотреть мысли")],
        [KeyboardButton(text="Добавить мысль")]
    ],
    resize_keyboard=True
)

# Клавиатура для отмены ввода
cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
