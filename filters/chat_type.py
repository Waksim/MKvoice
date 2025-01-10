# ============================= FILE: filters/chat_type.py =============================
from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message

class ChatTypeFilter(BaseFilter):
    """
    A filter to allow messages only from specified chat types (e.g., private, group, supergroup).
    """
    def __init__(self, chat_type: Union[str, list]):
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type