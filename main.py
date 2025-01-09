# ---- FILE: main.py ----
import asyncio
from bot import dp, bot
from project_structure.paths import DATABASE_PATH
import sqlite3

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_lang (
            user_id INTEGER PRIMARY KEY,
            lang_code TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
