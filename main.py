import json
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import reminders, quiz_updater, broadcast
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
    await update.message.reply_text("🙏 Welcome! Use /help to see commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
/verse - Daily inspirational verse
/prayer <text> - Submit prayer request
/events - Show upcoming Google Calendar events
/quiz - Start a quiz
/answer <text> - Answer quiz (max 10 chars)
/broadcast <text> - Admin broadcast
/daily_inspiration - Motivational quote
"""
    await update.message.reply_text(text)

async def verse(update, context):
    import random
    with open(VERSES_FILE, "r") as f:
        verses = json.load(f)
    await update.message.reply_text(f"📖 Daily Verse:\n{random.choice(verses)}")

async def prayer(update, context):
    user_id = str(update.message.from_user.id)
    if len(context.args) == 0:
        await update.message.reply_text("Provide a prayer request after /prayer")
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
    events = reminders.google_calendar.get_upcoming_events()
    if not events:
        await update.message.reply_text("No upcoming events found.")
        return
    msg = "🗓 Upcoming Events:\n"
    for e in events:
        start = e['start'].get('dateTime', e['start'].get('date'))
        msg += f"{e['summary']} at {start}\n"
    await update.message.reply_text(msg)

async def quiz_command(update, context):
    q = quiz_updater.get_random_quiz()
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
    import random
    inspirations = ["🌟 Keep faith strong!", "🙏 God is always with you", "✨ Your acts matter"]
    await update.message.reply_text(random.choice(inspirations))

async def broadcast_command(update, context):
    user_id = update.message.from_user.id
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized")
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
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.run(reminders.send_daily_verse(app.bot, USERS_FILE, VERSES_FILE)),
                      'cron', hour=8, minute=0)
    scheduler.add_job(lambda: asyncio.run(reminders.send_event_reminders(app.bot, USERS_FILE)),
                      'cron', minute='*/1')
    scheduler.start()

    print("Church Youth Bot is running with Google Calendar & auto-updating quizzes!")
    app.run_polling()
