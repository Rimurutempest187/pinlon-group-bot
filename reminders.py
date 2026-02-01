import json
import random
import datetime
from utils import google_calendar

async def send_daily_verse(bot, users_file, verses_file):
    with open(users_file, "r") as f:
        users = json.load(f)
    with open(verses_file, "r") as f:
        verses = json.load(f)
    verse = random.choice(verses)
    for uid in users.keys():
        try:
            await bot.send_message(chat_id=int(uid), text=f"📖 Daily Verse:\n{verse}")
        except:
            continue

async def send_event_reminders(bot, users_file):
    with open(users_file, "r") as f:
        users = json.load(f)
    events = google_calendar.get_upcoming_events()
    now = datetime.datetime.utcnow()
    for event in events:
        start_time = event['start'].get('dateTime', event['start'].get('date'))
        dt = datetime.datetime.fromisoformat(start_time.replace('Z','+00:00'))
        if dt.date() == now.date() and dt.hour == now.hour and dt.minute == now.minute:
            for uid in users.keys():
                try:
                    await bot.send_message(chat_id=int(uid),
                                           text=f"⏰ Event Reminder: {event['summary']} starts now!")
                except:
                    continue
