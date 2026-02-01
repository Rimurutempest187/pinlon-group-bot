import asyncio, random, logging
from db import get_conn
from telegram import Bot

logger = logging.getLogger(__name__)

async def daily_verse(bot: Bot):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users")
    users = [row["telegram_id"] for row in c.fetchall()]
    c.execute("SELECT text FROM verses")
    verses = [row["text"] for row in c.fetchall()]
    conn.close()
    if not verses:
        return
    verse = random.choice(verses)
    for uid in users:
        try:
            await bot.send_message(chat_id=uid, text=f"📖 Daily Verse:\n{verse}")
        except Exception as e:
            logger.warning("Failed to send verse to %s: %s", uid, e)
