# middlewares/concurrency_limit.py
import asyncio
from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

class ConcurrencyLimitMiddleware(BaseMiddleware):
    """
    Ограничение на одновременные "долгие" задачи (например, парсинг+синтез).
    - max_concurrent_tasks: максимум параллельных задач на пользователя.
    - semaphores: dict[user_id -> asyncio.Semaphore]
    """
    def __init__(self, max_concurrent_tasks: int = 1):
        super().__init__()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphores = {}

    def get_semaphore_for_user(self, user_id: int) -> asyncio.Semaphore:
        """
        Создаёт (при необходимости) и возвращает семафор для пользователя.
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
        if isinstance(event, types.Message):
            user_id = event.from_user.id
            semaphore = self.get_semaphore_for_user(user_id)

            # Пытаемся занять "слот"
            if semaphore.locked():
                # Уже все слоты заняты => откажем
                await event.answer(
                    "У вас уже есть активная задача. Дождитесь завершения предыдущей."
                )
                return

            # otherwise, оборачиваем обработку в контекст
            async with semaphore:
                # Пока в контексте, слот занят; выходим из контекста — слот освободился
                return await handler(event, data)

        return await handler(event, data)
