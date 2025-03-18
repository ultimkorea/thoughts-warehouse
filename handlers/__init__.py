from aiogram import Dispatcher
from .start import register_start_handlers
from .thoughts import register_thoughts_handlers
from .tags import register_tags_handlers

def register_all_handlers(dp: Dispatcher):
    register_start_handlers(dp)
    register_thoughts_handlers(dp)
    register_tags_handlers(dp)
