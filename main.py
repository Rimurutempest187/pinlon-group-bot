import json
import asyncio
import random
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import config
import os

USERS_FILE = "data/users.json"
VERSES_FILE = "data/verses.json"
QUIZZES_FILE = "data/quizzes.json"
EVENTS_FILE = "data/events.json"
PDF_FOLDER = "media/pdfs"
AUDIO_FOLDER = "media/audio"
IMAGE_FOLDER = "media/images"

# -------------------------
# Helper functions
# -------------------------
def add_user(user_id):
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    except:
        users = {}
    if str(user_id) not in users:
        users[str(user_id)] = {"prayer_requests": []}
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

def file_path(folder, filename):
    return os.path.join(folder, filename)

# -------------------------
# Bot commands
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.message.from_user.id)
    await update.message.reply_text("🙏 Welcome! Use /help to see commands.")

async def help_command(update, context):
    text = """
/verse - Daily inspirational verse
/prayer <text> - Submit prayer request
/events - Show upcoming events
/quiz - Start a quiz
/answer <text> - Answer quiz (max 10 chars)
/broadcast <text> - Admin broadcast
/daily_inspiration - Motivational quote
/send_pdf <filename> - Send PDF to group
/send_audio <filename> - Send audio
/send_image <filename> - Send image
"""
    await update.message.reply_text(text)

async def verse(update, context):
    with open(VERSES_FILE, "r") as f:
        verses = json.load(f)
    await update.message.reply_text(f"📖 Daily Verse:\n{random.choice(verses)}")

async def prayer(update, context):
    user_id = str(update.message.from_user.id)
    if not context.args:
        await update.message.reply_text("Please provide a prayer request after /prayer")
        return
    text = " ".join(context.args)
    add_user(user_id)
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    users[user_id]["prayer_requests"].append(text)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)
    await update.message.reply_text("🙏 Prayer request recorded!")

async def events_command(update, context):
    with open(EVENTS_FILE, "r") as f:
        events = json.load(f)
    msg = "🗓 Upcoming Events:\n"
    for e in events:
        msg += f"{e['name']} at {e['time']}\n"
    await update.message.reply_text(msg)

async def quiz_command(update, context):
    with open(QUIZZES_FILE, "r") as f:
        quizzes = json.load(f)
    q = random.choice(quizzes)
    context.user_data["current_quiz"] = q
    await update.message.reply_text(f"❓ Quiz: {q['Question']}")

async def answer_command(update, context):
    if "current_quiz" not in context.user_data:
        await update.message.reply_text("Start a quiz first with /quiz")
        return
    user_answer = " ".join(context.args)[:10]
    correct_answer = context.user_data["current_quiz"]["Answer"]
    if user_answer.lower() == correct_answer.lower():
        await update.message.reply_text("✅ Correct!")
    else:
        await update.message.reply_text(f"❌ Wrong! Correct answer: {correct_answer}")

async def daily_inspiration(update, context):
    inspirations = [
        "🌟 Keep faith strong!",
        "🙏 God is always with you",
        "✨ Your acts matter"
    ]
    await update.message.reply_text(random.choice(inspirations))

async def broadcast_command(update, context):
    user_id = update.message.from_user.id
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Please provide a message to broadcast.")
        return
    text = " ".join(context.args)
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        for uid in users.keys():
            await context.bot.send_message(chat_id=int(uid), text=f"📢 Announcement:\n{text}")
        await update.message.reply_text("✅ Broadcast sent!")
    except:
        await update.message.reply_text("❌ Failed to send broadcast.")

# -------------------------
# Multimedia commands
# -------------------------
async def send_pdf(update, context):
    if update.message.from_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Provide filename after /send_pdf")
        return
    filename = context.args[0]
    path = file_path(PDF_FOLDER, filename)
    if os.path.exists(path):
        await update.message.reply_document(document=open(path, "rb"))
    else:
        await update.message.reply_text("❌ File not found")

async def send_audio(update, context):
    if update.message.from_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Provide filename after /send_audio")
        return
    filename = context.args[0]
    path = file_path(AUDIO_FOLDER, filename)
    if os.path.exists(path):
        await update.message.reply_audio(audio=open(path, "rb"))
    else:
        await update.message.reply_text("❌ File not found")

async def send_image(update, context):
    if update.message.from_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Provide filename after /send_image")
        return
    filename = context.args[0]
    path = file_path(IMAGE_FOLDER, filename)
    if os.path.exists(path):
        await update.message.reply_photo(photo=open(path, "rb"))
    else:
        await update.message.reply_text("❌ File not found")

# -------------------------
# Scheduler reminders
# -------------------------
async def daily_verse_reminder(bot):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    with open(VERSES_FILE, "r") as f:
        verses = json.load(f)
    verse = random.choice(verses)
    for uid in users.keys():
        try:
            await bot.send_message(chat_id=int(uid), text=f"📖 Daily Verse:\n{verse}")
        except:
            continue

async def event_reminder(bot):
    now = datetime.now().strftime("%H:%M")
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    with open(EVENTS_FILE, "r") as f:
        events = json.load(f)
    for e in events:
        if e["time"] == now:
            for uid in users.keys():
                try:
                    await bot.send_message(chat_id=int(uid),
                                           text=f"⏰ Event Reminder: {e['name']} is starting now!")
                except:
                    continue

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("verse", verse))
    app.add_handler(CommandHandler("prayer", prayer))
    app.add_handler(CommandHandler("events", events_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("answer", answer_command))
    app.add_handler(CommandHandler("daily_inspiration", daily_inspiration))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("send_pdf", send_pdf))
    app.add_handler(CommandHandler("send_audio", send_audio))
    app.add_handler(CommandHandler("send_image", send_image))

    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.run(daily_verse_reminder(app.bot)), 'cron', hour=8, minute=0)
    scheduler.add_job(lambda: asyncio.run(event_reminder(app.bot)), 'cron', minute='*')
    scheduler.start()

    print("Church Youth Bot (multimedia version) is running...")
    app.run_polling()
