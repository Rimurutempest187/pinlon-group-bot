# utils/broadcast.py
import json

async def broadcast_message(bot, users_file, message):
    with open(users_file, "r") as f:
        users = json.load(f)
    for uid in users.keys():
        try:
            await bot.send_message(chat_id=int(uid), text=f"📢 Announcement:\n{message}")
        except:
            continue

