import json
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import reminders, games, broadcast
import config

USERS_FILE = "data/users.json"
VERSES_FILE = "data/verses.json"

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

# -------------------------
# Command Handlers
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.message.from_user.id)
    await update.message.reply_text("🙏 Welcome to Church Youth Bot! Use /help to see commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
/verse - Daily inspirational verse
/prayer <text> - Submit prayer request
/events - Show upcoming events from Google Calendar
/quiz - Bible knowledge quiz
/answer <text> - Answer quiz
/broadcast <text> - Admin broadcast
/daily_inspiration - Get motivational quote
"""
    await update.message.reply_text(text)

async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    with open(VERSES_FILE, "r") as f:
        verses = json.load(f)
    await update.message.reply_text(f"📖 Daily Verse:\n{random.choice(verses)}")

async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if len(context.args) == 0:
        await update.message.reply_text("Please provide your prayer request after /prayer command.")
        return
    text = " ".join(context.args)
    add_user(user_id)
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    users[user_id]["prayer_requests"].append(text)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)
    await update.message.reply_text("🙏 Your prayer request has been recorded!")

async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = reminders.google_calendar.get_upcoming_events()
    if not events:
        await update.message.reply_text("No upcoming events found.")
        return
    msg = "🗓 Upcoming Events:\n"
    for e in events:
        start = e['start'].get('dateTime', e['start'].get('date'))
        msg += f"{e['summary']} at {start}\n"
    await update.message.reply_text(msg)

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = games.get_random_quiz()
    context.user_data["current_quiz"] = q
    await update.message.reply_text(f"❓ Quiz: {q['question']}")

async def answer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "current_quiz" not in context.user_data:
        await update.message.reply_text("Please start a quiz with /quiz first.")
        return
    user_answer = " ".join(context.args)
    correct_answer = context.user_data["current_quiz"]["answer"]
    if user_answer.lower() == correct_answer.lower():
        await update.message.reply_text("✅ Correct!")
    else:
        await update.message.reply_text(f"❌ Wrong! Correct answer: {correct_answer}")

async def daily_inspiration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    inspirations = [
        "🌟 Keep your faith strong today!",
        "🙏 God is always with you.",
        "✨ Your small acts matter."
    ]
    await update.message.reply_text(random.choice(inspirations))

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to broadcast.")
        return
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a message to broadcast.")
        return
    text = " ".join(context.args)
    await broadcast.broadcast_message(context.bot, USERS_FILE, text)
    await update.message.reply_text("✅ Broadcast sent!")

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("verse", verse))
    app.add_handler(CommandHandler("prayer", prayer))
    app.add_handler(CommandHandler("events", events_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("answer", answer_command))
    app.add_handler(CommandHandler("daily_inspiration", daily_inspiration))
    app.add_handler(CommandHandler("broadcast", broadcast_command))

    # Scheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.run(reminders.send_daily_verse(app.bot, USERS_FILE, VERSES_FILE)),
                      'cron', hour=8, minute=0)
    scheduler.add_job(lambda: asyncio.run(reminders.send_event_reminders(app.bot, USERS_FILE)),
                      'cron', minute='*/1')
    scheduler.start()

    print("Church Youth Bot is running with Google Calendar integration...")
    app.run_polling()
