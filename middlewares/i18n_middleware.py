# ---- FILE: middlewares/i18n_middleware.py ----
import gettext
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware

import os

from utils.i18n import get_user_lang, get_translator

class I18nMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
            lang_code = get_user_lang(user_id)
            t = get_translator(lang_code)
            data["_"] = t.gettext
        else:
            data["_"] = gettext.gettext

        return await handler(event, data)
