import os
import logging
from datetime import datetime

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

import db


# Load token
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# --------------------
# Commands
# --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    db.add_user(user.id, user.username)

    await update.message.reply_text(
        "🙏 Welcome to Church Bot!\nYou are registered."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
📌 Commands:

/start - Register
/prayer <text> - Send prayer
/users - Show members
/help - Help
"""

    await update.message.reply_text(text)


async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "Usage: /prayer <your request>"
        )
        return

    user = update.effective_user
    text = " ".join(context.args)

    db.add_prayer(
        user.id,
        text,
        datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    await update.message.reply_text(
        "🙏 Prayer saved. God bless you."
    )


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = db.get_users()

    if not data:
        await update.message.reply_text("No users yet.")
        return

    text = "👥 Members:\n\n"

    for u in data:
        name = u[1] if u[1] else "NoUsername"
        text += f"• {name}\n"

    await update.message.reply_text(text)


# --------------------
# Main
# --------------------

def main():

    # Init database
    db.init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("prayer", prayer))
    app.add_handler(CommandHandler("users", users))

    print("✅ Church Bot Started")

    # Run (NO asyncio.run → No loop error)
    app.run_polling()


if __name__ == "__main__":
    main()
