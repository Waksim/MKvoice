from aiogram import BaseMiddleware
from aiogram.types import Update
from aiogram.fsm.context import FSMContext

class ClearStateMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        state: FSMContext = data.get("state")
        if state and await state.get_state():
            # Clear the state before handling the event
            await state.clear()
        return await handler(event, data)
