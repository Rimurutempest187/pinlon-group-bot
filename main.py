import os
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

from db import init_db, add_user, get_users


# Load env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    add_user(
        telegram_id=user.id,
        username=user.username
    )

    await update.message.reply_text(
        "🙏 Welcome! You are registered."
    )


# /users (test command)
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    rows = get_users()

    text = "👥 Registered Users:\n\n"

    for r in rows:
        text += f"ID: {r[1]} | @{r[2]}\n"

    await update.message.reply_text(text)


def main():

    # Init database
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("users", users))

    print("✅ Bot Running...")

    app.run_polling()


if __name__ == "__main__":
    main()
