# ============================= FILE: utils/user_settings.py =============================
"""
Utility functions to get and set user-specific settings in the database,
such as chunk_size and tts_speed.
"""

import aiosqlite  # Заменено
from project_structure.paths import DATABASE_PATH

async def get_user_settings(user_id: int) -> dict:  # Функция стала асинхронной
    """
    Retrieves user settings (chunk_size, tts_speed) from the database.
    If no record is found, returns default values.
    """
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT chunk_size, tts_speed FROM user_settings WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
    except Exception:
        row = None

    if row is None:
        return {
            'chunk_size': 40000,  # default
            'tts_speed': '+50%'   # default
        }
    else:
        return {
            'chunk_size': row[0],
            'tts_speed': row[1]
        }

async def save_user_chunk_size(user_id: int, chunk_size: int):  # Функция стала асинхронной
    """
    Saves or updates the chunk_size for the user in user_settings table.
    Uses ON CONFLICT to handle existing records.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO user_settings (user_id, chunk_size)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET chunk_size=excluded.chunk_size
        """, (user_id, chunk_size))
        await db.commit()

async def save_user_speed(user_id: int, speed_value: str):  # Функция стала асинхронной
    """
    Saves or updates the tts_speed for the user in user_settings table.
    Uses ON CONFLICT to handle existing records.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO user_settings (user_id, tts_speed)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET tts_speed=excluded.tts_speed
        """, (user_id, speed_value))
        await db.commit()