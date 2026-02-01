import asyncio
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from config import BOT_TOKEN, USERS_FILE
from reminders import send_daily_verse, event_reminder
from broadcast import broadcast
from games import get_random_quiz

# ---------- User management ----------
def add_user(user_id: int):
    import os
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    users[str(user_id)] = True
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def get_all_users():
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    return list(users.keys())

# ---------- Bot Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.message.from_user.id)
    await update.message.reply_text("Welcome to Church Youth Bot! ✅")

async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    from config import VERSES_FILE
    with open(VERSES_FILE, "r") as f:
        verses = json.load(f)
    await update.message.reply_text(f"📖 Daily Verse:\n{random.choice(verses)}")

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quiz = get_random_quiz()
    context.user_data['quiz_answer'] = quiz['Answer']
    await update.message.reply_text(f"❓ Quiz:\n{quiz['Question']}")

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text.strip()
    correct = context.user_data.get('quiz_answer', '')
    if user_answer.lower() == correct.lower():
        await update.message.reply_text("✅ Correct!")
    else:
        await update.message.reply_text(f"❌ Wrong! Correct answer: {correct}")

# ---------- Scheduler ----------
async def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.run(send_daily_verse(app.bot)), 'cron', hour=8, minute=0)
    scheduler.add_job(lambda: asyncio.run(event_reminder(app.bot)), 'cron', minute='*')
    scheduler.start()

# ---------- Main ----------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verse", verse))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("answer", answer))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("Church Youth Bot (multimedia version) is running...")

    # Start scheduler
    asyncio.get_event_loop().create_task(start_scheduler(app))
    app.run_polling()
