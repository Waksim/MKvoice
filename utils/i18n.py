# ============================= FILE: utils/i18n.py =============================
import gettext
import os
import aiosqlite  # Заменено
from project_structure.paths import DATABASE_PATH, PROJECT_ROOT

LOCALES_DIR = PROJECT_ROOT / "locales"

def get_translator(lang_code: str):
    """
    Returns a gettext translation object for the specified lang_code.
    If not found, defaults to 'en'.
    """
    if lang_code not in ['en', 'ru', 'uk', 'zh']:
        lang_code = 'en'
    try:
        return gettext.translation(
            domain='messages',
            localedir=LOCALES_DIR,
            languages=[lang_code]
        )
    except FileNotFoundError:
        return gettext.translation(
            domain='messages',
            localedir=LOCALES_DIR,
            languages=['en']
        )

async def get_user_lang(user_id: int) -> str:  # Функция стала асинхронной
    """
    Retrieves the saved language code for a specific user from the database.
    Defaults to 'ru' if not found or on error.
    """
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT lang_code FROM user_lang WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
            if row:
                return row[0]
            else:
                return "ru"
    except Exception:
        return "ru"

async def set_user_lang(user_id: int, lang_code: str):  # Функция стала асинхронной
    """
    Updates or inserts the language code for a user in the database.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO user_lang (user_id, lang_code)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lang_code=excluded.lang_code
        """, (user_id, lang_code))
        await db.commit()