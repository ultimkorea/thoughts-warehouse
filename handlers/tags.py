from aiogram.fsm.context import FSMContext
from database import add_tag, update_thought_tag, get_tag_usage_counts
from keyboards import cancel_keyboard
from states import ThoughtState
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import get_thoughts_by_tag
from keyboards import main_keyboard

router = Router()
PAGE_SIZE = 5  # Количество мыслей на странице

async def generate_tagged_thoughts_message(tag: str, page: int):
    """Генерирует текст и inline-клавиатуру для мыслей с определённым тегом"""
    thoughts = await get_thoughts_by_tag(tag)

    if not thoughts:
        return f"Нет мыслей с тегом #{tag}.", None

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    visible_thoughts = thoughts[start:end]

    response = []
    keyboard = []

    for t in visible_thoughts:
        text = f"{t.text} (📅 {t.created_at.strftime('%Y-%m-%d')})"
        response.append(text)

        keyboard.append([
            InlineKeyboardButton(text=f"{text[0:10]}", callback_data="noop"),
            InlineKeyboardButton(text="✏️", callback_data=f"edit_thought:{t.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_thought:{t.id}")
        ])

    # Навигация (если мыслей больше 5)
    nav_buttons = []
    if start > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"tag_page:{tag}:{page-1}"))
    if end < len(thoughts):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"tag_page:{tag}:{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    return f"Мысли с тегом _#{tag}_:\n\n" + "\n\n".join(response), InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(F.text.startswith("#"))
async def show_thoughts_by_tag(message: Message):
    """Обрабатывает сообщения с тегами (например, #учеба)"""
    tag_name = message.text[1:].strip().lower()  # Убираем # и приводим к нижнему регистру
    response, keyboard = await generate_tagged_thoughts_message(tag_name, 0)

    await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("tag_page:"))
async def paginate_tag_thoughts(callback: CallbackQuery):
    """Обрабатывает кнопки навигации для мыслей с тегом"""
    _, tag, page = callback.data.split(":")
    page = int(page)

    response, keyboard = await generate_tagged_thoughts_message(tag, page)

    await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


async def generate_tags_keyboard(thought_id: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру с тегами, отсортированными по популярности (максимум 7)"""

    tag_counts = await get_tag_usage_counts()

    # Сортируем по частоте использования (по убыванию) и берём максимум 7 тегов
    top_tags = sorted(tag_counts, key=lambda t: t.usage_count, reverse=True)[:7]

    buttons = [
        [InlineKeyboardButton(text=f"{tag.name} ({tag.usage_count})", callback_data=f"tag:{thought_id}:{tag.id}")]
        for tag in top_tags
    ]

    # Оставляем только кнопку "Добавить свой тег"
    buttons.append([
        InlineKeyboardButton(text="➕ Добавить свой тег", callback_data=f"custom_tag:{thought_id}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("tag:"))
async def set_tag(callback: CallbackQuery):
    _, thought_id, tag_id = callback.data.split(":")
    await update_thought_tag(int(thought_id), int(tag_id))

    # Отправляем подтверждение + кнопки "Добавить мысль" и "Посмотреть мысли"
    await callback.message.edit_text("✅ Тег присвоен, мысль сохранена в хранилище!")  # Убираем клавиатуру
    await callback.message.answer("Что дальше?", reply_markup=main_keyboard)  # Отправляем новое сообщение с кнопками

    await callback.answer()


@router.callback_query(F.data.startswith("custom_tag:"))
async def ask_for_custom_tag(callback: CallbackQuery, state: FSMContext):
    _, thought_id = callback.data.split(":")
    await state.update_data(thought_id=int(thought_id))
    await callback.message.answer("Введите свой тег:", reply_markup=cancel_keyboard)
    await state.set_state(ThoughtState.waiting_for_custom_tag)
    await callback.answer()


@router.message(ThoughtState.waiting_for_custom_tag)
async def save_custom_tag(message: Message, state: FSMContext):
    user_data = await state.get_data()
    thought_id = user_data["thought_id"]
    tag_id = await add_tag(message.text.strip())
    await update_thought_tag(thought_id, tag_id)

    await message.answer("✅ Тег присвоен, мысль сохранена в хранилище!")
    await message.answer("Что дальше?", reply_markup=main_keyboard)  # Отправляем новое сообщение с кнопками

    await state.clear()


def register_tags_handlers(dp):
    dp.include_router(router)
