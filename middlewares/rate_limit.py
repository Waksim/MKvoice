# ============================= FILE: middlewares/rate_limit.py =============================
import time
from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

# Import translation utilities
from utils.i18n import get_translator, get_user_lang

class RateLimitMiddleware(BaseMiddleware):
    """
    Simple rate limit middleware: allows 1 message per user within 'rate_limit' seconds.
    """
    def __init__(self, rate_limit: float = 2.0):
        super().__init__()
        self.rate_limit = rate_limit
        self.users_last_time = {}

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Middleware handler that enforces rate limits.
        """
        # Check if the event is a message
        if isinstance(event, types.Message):
            user_id = event.from_user.id
            current_time = time.time()
            last_time = self.users_last_time.get(user_id, 0)

            # Retrieve user's language preference
            lang_code = get_user_lang(user_id)
            translator = get_translator(lang_code)
            _ = translator.gettext  # Translation function

            if (current_time - last_time) < self.rate_limit:
                # Send a translatable rate limit message to the user
                await event.answer(
                    _("Too many requests, please try again later (limit: {rate_limit} s).").format(rate_limit=self.rate_limit)
                )
                return  # Exit without handling the message

            # Update the last message time for the user
            self.users_last_time[user_id] = current_time

        # Proceed to handle the event
        return await handler(event, data)
