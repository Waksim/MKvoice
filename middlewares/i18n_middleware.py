# ============================= FILE: middlewares/i18n_middleware.py =============================
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from utils.i18n import get_translator, get_user_lang

class I18nMiddleware(BaseMiddleware):
    """
    Middleware that injects the translator function into the handler data
    based on the user's saved language.
    """
    def __init__(self, get_translator_func):
        self.get_translator = get_translator_func
        super().__init__()

    async def __call__(self, handler, event, data):
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            user_id = None

        if user_id:
            lang_code = get_user_lang(user_id)
            translator = self.get_translator(lang_code)
        else:
            # Default language
            translator = self.get_translator('en')

        data["_"] = translator.gettext
        return await handler(event, data)