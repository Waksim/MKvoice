# middlewares/rate_limit.py
import time
from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

class RateLimitMiddleware(BaseMiddleware):
    """
    Простое ограничение частоты запросов:
    - Не более 1 сообщения от пользователя за 'rate_limit' секунд.
    """
    def __init__(self, rate_limit: float = 5.0):
        super().__init__()
        self.rate_limit = rate_limit
        # user_id -> timestamp последнего принятого сообщения
        self.users_last_time = {}

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, types.Message):
            user_id = event.from_user.id
            current_time = time.time()
            last_time = self.users_last_time.get(user_id, 0)

            if (current_time - last_time) < self.rate_limit:
                # Слишком частые сообщения от этого пользователя
                await event.answer(
                    f"Слишком много запросов, попробуйте чуть позже (лимит: {self.rate_limit} c)."
                )
                return  # Блокируем дальнейшую обработку

            # Обновляем время последней успешной обработки
            self.users_last_time[user_id] = current_time

        return await handler(event, data)
