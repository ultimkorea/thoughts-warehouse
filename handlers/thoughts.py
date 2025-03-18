from database import save_thought
from keyboards import cancel_keyboard
from states import ThoughtState, ThoughtEditState
from handlers.tags import generate_tags_keyboard
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_all_thoughts
from keyboards import main_keyboard
from aiogram.fsm.context import FSMContext
from database import update_thought_text, delete_thought

router = Router()

PAGE_SIZE = 5  # Количество мыслей на одной странице


@router.callback_query(F.data.startswith("delete_thought:"))
async def ask_delete_thought(callback: CallbackQuery, state: FSMContext):
    """Запрашивает подтверждение на удаление мысли"""
    thought_id = int(callback.data.split(":")[1])
    await state.update_data(thought_id=thought_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="confirm_delete")],
            [InlineKeyboardButton(text="❌ Нет", callback_data="cancel_delete")]
        ]
    )

    await callback.message.edit_text("Вы уверены, что хотите удалить эту мысль?", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "confirm_delete")
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    """Удаляет мысль после подтверждения"""
    user_data = await state.get_data()
    thought_id = user_data["thought_id"]

    await delete_thought(thought_id)

    await callback.message.edit_text("✅ Мысль удалена!")

    # Обновляем список мыслей
    response, keyboard = await generate_thoughts_message(0)
    await callback.message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery, state: FSMContext):
    """Отменяет удаление мысли"""
    await callback.message.edit_text("❌ Удаление отменено.")
    await callback.answer()


@router.callback_query(F.data.startswith("edit_thought:"))
async def ask_edit_thought(callback: CallbackQuery, state: FSMContext):
    """Запрашивает новый текст для редактирования мысли"""
    thought_id = int(callback.data.split(":")[1])
    await state.update_data(thought_id=thought_id)

    await callback.message.answer("Введите новый текст для этой мысли:")
    await state.set_state(ThoughtEditState.waiting_for_new_text)
    await callback.answer()

@router.message(ThoughtEditState.waiting_for_new_text)
async def save_edited_thought(message: Message, state: FSMContext):
    """Сохраняет новый текст мысли"""
    user_data = await state.get_data()
    thought_id = user_data["thought_id"]

    await update_thought_text(thought_id, message.text)

    await message.answer("✅ Мысль обновлена!")
    await state.clear()

    # Обновляем список мыслей
    response, keyboard = await generate_thoughts_message(0)
    await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")


async def generate_thoughts_message(page: int):
    """Генерирует текст и inline-клавиатуру для списка мыслей с пагинацией и кнопками редактирования"""
    thoughts = await get_all_thoughts()

    if not thoughts:
        return "Нет сохранённых мыслей.", None

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    visible_thoughts = thoughts[start:end]

    # Формируем текст + кнопки редактирования и удаления
    response = []
    keyboard = []

    for t in visible_thoughts:
        text = f"{t.text} (📅 {t.created_at.strftime('%Y-%m-%d')})"
        if t.tag:
            text += f"\n_#{t.tag.name}_"
        response.append(text)

        # Добавляем кнопки редактирования и удаления для каждой мысли
        keyboard.append([
            InlineKeyboardButton(text=f"{text[0:10]}", callback_data="noop"),
            InlineKeyboardButton(text="✏️", callback_data=f"edit_thought:{t.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_thought:{t.id}")
        ])

    # Добавляем кнопки навигации (вперёд/назад)
    nav_buttons = []
    if start > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"thoughts_page:{page - 1}"))
    if end < len(thoughts):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"thoughts_page:{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    return "\n\n".join(response), InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text == "Посмотреть мысли")
async def show_all_thoughts(message: Message):
    """Отправляет первые 5 мыслей и кнопки навигации"""
    response, keyboard = await generate_thoughts_message(0)
    await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data.startswith("thoughts_page:"))
async def paginate_thoughts(callback: CallbackQuery):
    """Обрабатывает кнопки навигации (вперёд/назад)"""
    page = int(callback.data.split(":")[1])
    response, keyboard = await generate_thoughts_message(page)

    await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.message(F.text == "Добавить мысль")
async def start_thought_input(message: Message, state: FSMContext):
    await message.answer("Введите вашу мысль:", reply_markup=cancel_keyboard)
    await state.set_state(ThoughtState.waiting_for_text)

@router.message(ThoughtState.waiting_for_text)
async def receive_thought(message: Message, state: FSMContext):
    text = message.text
    if text == "❌ Отмена":
        await message.answer("Отменено.", reply_markup=main_keyboard)
        await state.clear()
        return

    thought_id = await save_thought(user_id=message.from_user.id, text=text)
    keyboard = await generate_tags_keyboard(thought_id)

    await message.answer("Записал! Выбери тег:", reply_markup=keyboard)
    await state.clear()

def register_thoughts_handlers(dp):
    dp.include_router(router)
