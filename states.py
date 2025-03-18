from aiogram.fsm.state import StatesGroup, State

class ThoughtState(StatesGroup):
    waiting_for_text = State()
    waiting_for_custom_tag = State()

class ThoughtEditState(StatesGroup):
    waiting_for_new_text = State()