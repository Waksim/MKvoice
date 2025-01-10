# ============================= FILE: states.py =============================
"""
Contains FSM state classes for managing user interactions,
such as awaiting chunk size input.
"""

from aiogram.fsm.state import StatesGroup, State


class SettingsState(StatesGroup):
    """
    FSM states for handling user settings.
    """
    waiting_for_chunk_size = State()
