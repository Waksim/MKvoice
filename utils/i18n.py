# ---- FILE: utils/i18n.py ----
import gettext
import os
import sqlite3
from project_structure.paths import DATABASE_PATH, PROJECT_ROOT

LOCALES_DIR = PROJECT_ROOT / "locales"

def get_translator(lang_code: str):
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

def get_user_lang(user_id: int) -> str:
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT lang_code FROM user_lang WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        else:
            return "ru"  # fallback
    except:
        return "ru"

def set_user_lang(user_id: int, lang_code: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_lang (user_id, lang_code)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET lang_code=excluded.lang_code
    """, (user_id, lang_code))
    conn.commit()
    conn.close()
