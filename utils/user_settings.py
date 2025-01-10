# ============================= FILE: utils/user_settings.py =============================
"""
Utility functions to get and set user-specific settings in the database,
such as chunk_size and tts_speed.
"""

import sqlite3
from project_structure.paths import DATABASE_PATH

def get_user_settings(user_id: int) -> dict:
    """
    Retrieves user settings (chunk_size, tts_speed) from the database.
    If no record is found, returns default values.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chunk_size, tts_speed FROM user_settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return {
            'chunk_size': 40000,  # default
            'tts_speed': '+0%'    # default
        }
    else:
        return {
            'chunk_size': row[0],
            'tts_speed': row[1]
        }

def save_user_chunk_size(user_id: int, chunk_size: int):
    """
    Saves or updates the chunk_size for the user in user_settings table.
    Uses ON CONFLICT to handle existing records.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_settings (user_id, chunk_size)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET chunk_size=excluded.chunk_size
    """, (user_id, chunk_size))
    conn.commit()
    conn.close()

def save_user_speed(user_id: int, speed_value: str):
    """
    Saves or updates the tts_speed for the user in user_settings table.
    Uses ON CONFLICT to handle existing records.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_settings (user_id, tts_speed)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET tts_speed=excluded.tts_speed
    """, (user_id, speed_value))
    conn.commit()
    conn.close()
