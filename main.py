# main.py
import os
import json
import asyncio
import random
import logging
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config  # make sure .env loaded in config.py

# -----------------------
# Logging
# -----------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# -----------------------
# File paths (from config or defaults)
# -----------------------
USERS_FILE = getattr(config, "USERS_FILE", "data/users.json")
QUIZZES_FILE = getattr(config, "QUIZZES_FILE", "data/quizzes.json")
EVENTS_FILE = getattr(config, "EVENTS_FILE", "data/events.json")
VERSES_FILE = getattr(config, "VERSES_FILE", "data/verses.json")

MEDIA_PDFS = "media/pdfs"
MEDIA_AUDIO = "media/audio"
MEDIA_IMAGES = "media/images"

# -----------------------
# Ensure data folders/files exist (safe default creation)
# -----------------------
def ensure_paths():
    Path("data").mkdir(parents=True, exist_ok=True)
    Path(MEDIA_PDFS).mkdir(parents=True, exist_ok=True)
    Path(MEDIA_AUDIO).mkdir(parents=True, exist_ok=True)
    Path(MEDIA_IMAGES).mkdir(parents=True, exist_ok=True)

    def ensure_file(path, default):
        p = Path(path)
        if not p.exists():
            p.write_text(json.dumps(default, ensure_ascii=False, indent=2))

    ensure_file(USERS_FILE, {})      # dict: user_id -> { prayer_requests: [...] }
    ensure_file(QUIZZES_FILE, [])    # list of {Question, Answer}
    ensure_file(EVENTS_FILE, [])     # list of {name, time}
    ensure_file(VERSES_FILE, [])     # list of strings

ensure_paths()

# -----------------------
# Utilities: load/save JSON
# -----------------------
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to load %s: %s — recreating default", path, e)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -----------------------
# User management
# -----------------------
def add_user_if_missing(user_id: int):
    users = load_json(USERS_FILE, {})
    key = str(user_id)
    if key not in users:
        users[key] = {"prayer_requests": []}
        save_json(USERS_FILE, users)
        logger.info("Added new user %s to users.json", user_id)

def get_all_user_ids():
    users = load_json(USERS_FILE, {})
    # return list of ints
    return [int(uid) for uid in users.keys()]

# -----------------------
# Bot command handlers
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user_if_missing(user.id)
    await update.message.reply_text(
        "🙏 Welcome to Church Youth Bot!\nUse /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start - Register\n"
        "/help - This help\n"
        "/verse - Get a random verse\n"
        "/prayer <text> - Submit a prayer request\n"
        "/events - Show events (from data/events.json)\n"
        "/quiz - Start a quiz\n"
        "/answer <text> - Answer the current quiz\n"
        "/daily_inspiration - Short motivating message\n"
        "/broadcast <text> - (Admin) Broadcast to users\n"
        "/send_pdf <filename> - (Admin) send PDF from media/pdfs/\n"
        "/send_audio <filename> - (Admin) send audio from media/audio/\n"
        "/send_image <filename> - (Admin) send image from media/images/\n"
    )
    await update.message.reply_text(text)

async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    verses = load_json(VERSES_FILE, [])
    if not verses:
        await update.message.reply_text("No verses found. Please add entries to data/verses.json.")
        return
    await update.message.reply_text(f"📖 {random.choice(verses)}")

async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /prayer <your prayer request>")
        return
    user_id = str(update.effective_user.id)
    add_user_if_missing(update.effective_user.id)
    users = load_json(USERS_FILE, {})
    text = " ".join(context.args)
    users.setdefault(user_id, {}).setdefault("prayer_requests", []).append({
        "text": text,
        "time": datetime.now().isoformat()
    })
    save_json(USERS_FILE, users)
    await update.message.reply_text("🙏 Your prayer request has been recorded. We will pray for you.")

async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = load_json(EVENTS_FILE, [])
    if not events:
        await update.message.reply_text("No events found. Add events in data/events.json.")
        return
    lines = ["🗓 Upcoming events:"]
    for e in events:
        name = e.get("name", "Unnamed")
        time = e.get("time", "Unknown")
        lines.append(f"{name} — {time}")
    await update.message.reply_text("\n".join(lines))

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quizzes = load_json(QUIZZES_FILE, [])
    if not quizzes:
        await update.message.reply_text("No quizzes available. Add entries in data/quizzes.json.")
        return
    q = random.choice(quizzes)
    # store the correct answer in user_data for this chat/user
    context.user_data["current_quiz_answer"] = q.get("Answer", "")
    await update.message.reply_text(f"❓ Quiz: {q.get('Question', 'No question')}")

async def answer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "current_quiz_answer" not in context.user_data:
        await update.message.reply_text("Start a quiz first with /quiz")
        return
    if not context.args:
        await update.message.reply_text("Usage: /answer <your answer>")
        return
    user_answer = " ".join(context.args).strip()
    correct = context.user_data.get("current_quiz_answer", "").strip()
    # case-insensitive comparison, also ignore surrounding whitespace and normalize spaces
    if user_answer.lower().strip() == correct.lower().strip():
        await update.message.reply_text("✅ Correct!")
    else:
        await update.message.reply_text(f"❌ Wrong. Correct answer: {correct}")

async def daily_inspiration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    samples = [
        "🌟 Keep your faith strong!",
        "🙏 God is always with you.",
        "✨ Small acts of love change the world.",
        "🕊️ Peace be with you today."
    ]
    await update.message.reply_text(random.choice(samples))

# Admin-only helper
def is_admin(user_id: int) -> bool:
    admin_list = getattr(config, "ADMIN_IDS", [])
    return user_id in admin_list

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ You are not authorized to broadcast.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    user_ids = get_all_user_ids()
    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 Announcement:\n{message}")
            sent += 1
        except Exception as e:
            logger.warning("Broadcast to %s failed: %s", uid, e)
            failed += 1
    await update.message.reply_text(f"Broadcast finished. Sent: {sent}, Failed: {failed}")

# Multimedia admin commands
async def send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /send_pdf <filename.pdf>")
        return
    filename = context.args[0]
    path = os.path.join(MEDIA_PDFS, filename)
    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found.")
        return
    await update.message.reply_document(document=open(path, "rb"))

async def send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /send_audio <filename>")
        return
    filename = context.args[0]
    path = os.path.join(MEDIA_AUDIO, filename)
    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found.")
        return
    await update.message.reply_audio(audio=open(path, "rb"))

async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /send_image <filename>")
        return
    filename = context.args[0]
    path = os.path.join(MEDIA_IMAGES, filename)
    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found.")
        return
    await update.message.reply_photo(photo=open(path, "rb"))

# -----------------------
# Scheduler tasks (async)
# -----------------------
async def daily_verse_reminder(bot):
    users = load_json(USERS_FILE, {})
    verses = load_json(VERSES_FILE, [])
    if not verses:
        logger.info("No verses configured for daily reminders.")
        return
    verse = random.choice(verses)
    for uid in users:
        try:
            await bot.send_message(chat_id=int(uid), text=f"📖 Daily Verse:\n{verse}")
        except Exception as e:
            logger.debug("Failed to send daily verse to %s: %s", uid, e)

async def event_reminder(bot):
    users = load_json(USERS_FILE, {})
    events = load_json(EVENTS_FILE, [])
    if not events:
        return
    now = datetime.now().strftime("%H:%M")
    for event in events:
        evt_time = event.get("time")
        if evt_time == now:
            name = event.get("name", "Event")
            for uid in users:
                try:
                    await bot.send_message(chat_id=int(uid), text=f"⏰ Event Reminder: {name} is starting now!")
                except Exception as e:
                    logger.debug("Failed to send event reminder to %s: %s", uid, e)

# -----------------------
# Error handler for updates
# -----------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Update caused error: %s", context.error)
    # Optionally notify admins
    try:
        admin_ids = getattr(config, "ADMIN_IDS", [])
        for aid in admin_ids:
            await context.bot.send_message(chat_id=aid, text=f"Bot error: {context.error}")
    except Exception:
        pass

# -----------------------
# Main: build app and run
# -----------------------
async def start_scheduler(app):
    scheduler = AsyncIOScheduler()
    # run daily verse at 08:00
    scheduler.add_job(lambda: asyncio.create_task(daily_verse_reminder(app.bot)), "cron", hour=8, minute=0)
    # check every minute for events matching current time
    scheduler.add_job(lambda: asyncio.create_task(event_reminder(app.bot)), "cron", minute="*")
    scheduler.start()
    logger.info("Scheduler started with daily verse and event jobs.")

async def main():
    # Build application
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Register handlers
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

    # Error handler
    app.add_error_handler(error_handler)

    # Start scheduler as background task
    asyncio.create_task(start_scheduler(app))

    logger.info("Church Youth Bot is starting...")
    # Use run_polling which handles initialize/start internally
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
