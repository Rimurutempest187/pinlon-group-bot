import os
import json
import asyncio
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN
from reminders import start_scheduler
from games import send_quiz
from broadcast import broadcast_message


# ---------------- LOGGING ---------------- #

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ---------------- FILE PATHS ---------------- #

DATA_DIR = "data"

USERS_FILE = os.path.join(DATA_DIR, "users.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
VERSES_FILE = os.path.join(DATA_DIR, "verses.json")
QUIZ_FILE = os.path.join(DATA_DIR, "quizzes.json")


# ---------------- INIT FILES ---------------- #

def init_storage():

    # Create data folder
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Create json files if missing
    files = {
        USERS_FILE: [],
        EVENTS_FILE: [],
        VERSES_FILE: [],
        QUIZ_FILE: [],
    }

    for file, default in files.items():
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=4)


# ---------------- USER MANAGEMENT ---------------- #

def add_user(user_id: int):

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)

    if user_id not in users:
        users.append(user_id)

        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)


# ---------------- COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    add_user(user.id)

    await update.message.reply_text(
        f"🙏 Welcome {user.first_name}!\n\n"
        "Church Youth Bot is ready.\n\n"
        "/verse - Daily verse\n"
        "/quiz - Bible quiz\n"
        "/help - Help"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
📖 Church Youth Bot Commands

/start - Start bot
/verse - Daily verse
/quiz - Bible quiz
/help - Show help
"""

    await update.message.reply_text(text)


# ---------------- VERSE ---------------- #

async def send_verse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    with open(VERSES_FILE, "r", encoding="utf-8") as f:
        verses = json.load(f)

    if not verses:
        await update.message.reply_text("No verses yet.")
        return

    import random
    verse = random.choice(verses)

    await update.message.reply_text(f"📖 {verse}")


# ---------------- QUIZ ---------------- #

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await send_quiz(update, context)


# ---------------- BROADCAST ---------------- #

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/broadcast Your message"
        )
        return

    message = " ".join(context.args)

    await broadcast_message(context.bot, message)

    await update.message.reply_text("✅ Broadcast sent.")


# ---------------- MAIN ---------------- #

async def main():

    # Init folders & json files
    init_storage()

    # Build bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("verse", send_verse))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Start scheduler
    asyncio.create_task(start_scheduler(app))

    print("✅ Church Youth Bot is running...")

    # Start bot
    await app.run_polling()


# ---------------- ENTRY ---------------- #

if __name__ == "__main__":
    asyncio.run(main())
