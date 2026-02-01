import os
import json
import random
import asyncio
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv


# =========================
# LOAD ENV
# =========================

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in .env")


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# =========================
# PATHS
# =========================

DATA_DIR = "data"
MEDIA_DIR = "media"

USERS_FILE = f"{DATA_DIR}/users.json"
EVENTS_FILE = f"{DATA_DIR}/events.json"
VERSES_FILE = f"{DATA_DIR}/verses.json"
QUIZ_FILE = f"{DATA_DIR}/quizzes.json"

MEDIA_AUDIO = f"{MEDIA_DIR}/audio"
MEDIA_IMAGES = f"{MEDIA_DIR}/images"
MEDIA_PDFS = f"{MEDIA_DIR}/pdfs"


# =========================
# ADMINS
# =========================

ADMINS = [
    1812962224  # ❗ Replace with your Telegram ID
]


# =========================
# INIT FOLDERS & FILES
# =========================

def init_storage():

    os.makedirs(DATA_DIR, exist_ok=True)

    os.makedirs(MEDIA_AUDIO, exist_ok=True)
    os.makedirs(MEDIA_IMAGES, exist_ok=True)
    os.makedirs(MEDIA_PDFS, exist_ok=True)

    files = {
        USERS_FILE: [],
        EVENTS_FILE: [],
        VERSES_FILE: [],
        QUIZ_FILE: []
    }

    for file, default in files.items():
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2)


# =========================
# JSON HELPERS
# =========================

def load_json(path):

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except:
        return []


def save_json(path, data):

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =========================
# USER SYSTEM
# =========================

def add_user(user_id):

    users = load_json(USERS_FILE)

    if user_id not in users:
        users.append(user_id)
        save_json(USERS_FILE, users)


def is_admin(user_id):

    return user_id in ADMINS


# =========================
# COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    add_user(user.id)

    text = (
        "🙏 Welcome to Church Youth Bot!\n\n"
        "/verse - Daily Bible Verse\n"
        "/quiz - Bible Quiz\n"
        "/event - Church Events\n"
        "/help - Help"
    )

    await update.message.reply_text(text)


# -------------------------

async def help_cmd(update: Update, context):

    text = (
        "📌 Commands\n\n"
        "/start\n"
        "/verse\n"
        "/quiz\n"
        "/event\n"
        "/send_audio (admin)\n"
        "/send_image (admin)\n"
        "/send_pdf (admin)"
    )

    await update.message.reply_text(text)


# -------------------------

async def verse(update: Update, context):

    verses = load_json(VERSES_FILE)

    if not verses:
        await update.message.reply_text("❌ No verses yet.")
        return

    v = random.choice(verses)

    await update.message.reply_text(
        f"📖 {v['text']}\n\n— {v['ref']}"
    )


# -------------------------

async def quiz(update: Update, context):

    quizzes = load_json(QUIZ_FILE)

    if not quizzes:
        await update.message.reply_text("❌ No quizzes yet.")
        return

    q = random.choice(quizzes)

    msg = (
        f"🧠 {q['question']}\n\n"
        f"A. {q['A']}\n"
        f"B. {q['B']}\n"
        f"C. {q['C']}\n"
        f"D. {q['D']}\n\n"
        f"Answer: {q['answer']}"
    )

    await update.message.reply_text(msg)


# -------------------------

async def events(update: Update, context):

    events = load_json(EVENTS_FILE)

    if not events:
        await update.message.reply_text("❌ No events.")
        return

    msg = "📅 Church Events\n\n"

    for e in events:
        msg += f"• {e['title']} ({e['date']})\n"

    await update.message.reply_text(msg)


# =========================
# MEDIA (ADMIN)
# =========================

async def send_audio(update: Update, context):

    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: /send_audio file.mp3")
        return

    path = f"{MEDIA_AUDIO}/{context.args[0]}"

    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found")
        return

    with open(path, "rb") as f:
        await update.message.reply_audio(f)


# -------------------------

async def send_image(update: Update, context):

    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: /send_image img.jpg")
        return

    path = f"{MEDIA_IMAGES}/{context.args[0]}"

    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found")
        return

    with open(path, "rb") as f:
        await update.message.reply_photo(f)


# -------------------------

async def send_pdf(update: Update, context):

    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: /send_pdf file.pdf")
        return

    path = f"{MEDIA_PDFS}/{context.args[0]}"

    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found")
        return

    with open(path, "rb") as f:
        await update.message.reply_document(f)


# =========================
# REMINDERS
# =========================

async def daily_verse(bot):

    users = load_json(USERS_FILE)
    verses = load_json(VERSES_FILE)

    if not users or not verses:
        return

    verse = random.choice(verses)

    msg = f"📖 {verse['text']}\n— {verse['ref']}"

    for uid in users:
        try:
            await bot.send_message(uid, msg)
        except:
            pass


# -------------------------

async def event_reminder(bot):

    users = load_json(USERS_FILE)
    events = load_json(EVENTS_FILE)

    today = datetime.now().date()

    for e in events:

        date = datetime.strptime(
            e["date"], "%Y-%m-%d"
        ).date()

        if date == today:

            msg = f"⛪ Today Event: {e['title']}"

            for u in users:
                try:
                    await bot.send_message(u, msg)
                except:
                    pass


# =========================
# MAIN
# =========================

async def main():

    init_storage()

    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("verse", verse))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("event", events))

    app.add_handler(CommandHandler("send_audio", send_audio))
    app.add_handler(CommandHandler("send_image", send_image))
    app.add_handler(CommandHandler("send_pdf", send_pdf))


    # Scheduler
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        lambda: asyncio.create_task(
            daily_verse(app.bot)
        ),
        "cron",
        hour=7,
        minute=0
    )

    scheduler.add_job(
        lambda: asyncio.create_task(
            event_reminder(app.bot)
        ),
        "cron",
        hour=6,
        minute=0
    )

    scheduler.start()


    print("✅ Church Bot Running...")

    await app.run_polling()


# =========================

if __name__ == "__main__":
    asyncio.run(main())

