import json
from config import USERS_FILE, EVENTS_FILE, VERSES_FILE
from telegram import Bot
import asyncio
import random

async def send_daily_verse(bot: Bot):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    with open(VERSES_FILE, "r") as f:
        verses = json.load(f)
    
    verse = random.choice(verses)
    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id, text=f"📖 Daily Verse:\n{verse}")
        except:
            pass

async def event_reminder(bot: Bot):
    import datetime
    now = datetime.datetime.now().strftime("%H:%M")
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    with open(EVENTS_FILE, "r") as f:
        events = json.load(f)
    
    for event in events:
        if event.get("time") == now:
            for user_id in users:
                try:
                    await bot.send_message(chat_id=user_id, text=f"⏰ Reminder: {event.get('name')} is happening now!")
                except:
                    pass
