# utils/reminders.py
import json
import datetime
import asyncio

async def send_daily_verse(bot, users_file, verses_file):
    with open(users_file, "r") as f:
        users = json.load(f)
    with open(verses_file, "r") as f:
        import random
        verses = json.load(f)
        verse = random.choice(verses)
    for uid in users.keys():
        try:
            await bot.send_message(chat_id=int(uid), text=f"📖 Daily Verse:\n{verse}")
        except:
            continue

async def send_event_reminders(bot, users_file, events_file):
    with open(users_file, "r") as f:
        users = json.load(f)
    with open(events_file, "r") as f:
        events = json.load(f)
    now = datetime.datetime.now().strftime("%H:%M")
    for event in events:
        if event["time"] == now:
            for uid in users.keys():
                try:
                    await bot.send_message(chat_id=int(uid), text=f"⏰ Event Reminder: {event['name']} starts now!")
                except:
                    continue
