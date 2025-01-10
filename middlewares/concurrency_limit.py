# ============================= FILE: middlewares/concurrency_limit.py =============================
import asyncio
from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

# Import translation utilities
from utils.i18n import get_translator, get_user_lang

class ConcurrencyLimitMiddleware(BaseMiddleware):
    """
    Restricts the number of concurrent long-running tasks per user.
    """
    def __init__(self, max_concurrent_tasks: int = 1):
        super().__init__()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphores = {}

    def get_semaphore_for_user(self, user_id: int) -> asyncio.Semaphore:
        """
        Returns (or creates) a semaphore object for the given user_id
        to track concurrency.
        """
        if user_id not in self.semaphores:
            self.semaphores[user_id] = asyncio.Semaphore(self.max_concurrent_tasks)
        return self.semaphores[user_id]

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Middleware handler that enforces concurrency limits.
        """
        # Check if the event is a message
        if isinstance(event, types.Message):
            user_id = event.from_user.id

            # Retrieve user's language preference
            lang_code = get_user_lang(user_id)
            translator = get_translator(lang_code)
            _ = translator.gettext  # Translation function

            semaphore = self.get_semaphore_for_user(user_id)

            if semaphore.locked():
                # Send a translatable message to the user
                await event.answer(
                    _("You already have an active task. Please wait for it to finish.")
                )
                return  # Exit without handling the message

            # Acquire semaphore and handle the message
            async with semaphore:
                return await handler(event, data)

        # For other types of events, proceed without restrictions
        return await handler(event, data)
