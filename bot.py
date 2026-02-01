import random, logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from db import get_conn
import config, translations
import asyncio, os

logger = logging.getLogger(__name__)

def get_user_language(telegram_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT language FROM users WHERE telegram_id=?", (telegram_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return row["language"]
    return config.DEFAULT_LANGUAGE

def is_admin(telegram_id):
    return telegram_id in config.ADMIN_IDS

# ---------------- Commands ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (telegram_id,))
    conn.commit()
    conn.close()
    lang = get_user_language(telegram_id)
    await update.message.reply_text(translations.TEXTS[lang]["welcome"])

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_language(update.effective_user.id)
    await update.message.reply_text(translations.TEXTS[lang]["help"])

async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT text FROM verses")
    verses = [row["text"] for row in c.fetchall()]
    conn.close()
    lang = get_user_language(update.effective_user.id)
    if not verses:
        await update.message.reply_text(translations.TEXTS[lang]["no_verses"])
        return
    await update.message.reply_text(f"📖 {random.choice(verses)}")

async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /prayer <your prayer>")
        return
    text = " ".join(context.args)
    telegram_id = update.effective_user.id
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
    user = c.fetchone()
    if user:
        c.execute("INSERT INTO prayers (user_id, text, time) VALUES (?, ?, ?)", (user["id"], text, datetime.now().isoformat()))
        conn.commit()
    conn.close()
    lang = get_user_language(telegram_id)
    await update.message.reply_text(translations.TEXTS[lang]["prayer_recorded"])

# ---------------- Quiz ----------------
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM quizzes")
    quizzes = c.fetchall()
    conn.close()
    if not quizzes:
        await update.message.reply_text("No quizzes available.")
        return
    q = random.choice(quizzes)
    context.user_data["quiz_answer"] = q["answer"]
    lang = get_user_language(update.effective_user.id)
    await update.message.reply_text(translations.TEXTS[lang]["quiz_start"].format(q=q["question"]))

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "quiz_answer" not in context.user_data:
        await update.message.reply_text("Start quiz first with /quiz")
        return
    if not context.args:
        await update.message.reply_text("Usage: /answer <your answer>")
        return
    user_answer = " ".join(context.args).strip()
    correct_answer = context.user_data.get("quiz_answer", "").strip()
    lang = get_user_language(update.effective_user.id)
    if user_answer.lower() == correct_answer.lower():
        await update.message.reply_text(translations.TEXTS[lang]["quiz_correct"])
    else:
        await update.message.reply_text(translations.TEXTS[lang]["quiz_wrong"].format(a=correct_answer))

# ---------------- Daily inspiration ----------------
async def daily_inspiration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    samples = [
        "🌟 Keep your faith strong!",
        "🙏 God is always with you.",
        "✨ Small acts of love change the world.",
        "🕊️ Peace be with you today."
    ]
    await update.message.reply_text(random.choice(samples))

# ---------------- Admin ----------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <text>")
        return
    text = " ".join(context.args)
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users")
    users = [row["telegram_id"] for row in c.fetchall()]
    conn.close()
    sent = failed = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 {text}")
            sent += 1
        except:
            failed += 1
    await update.message.reply_text(f"Sent: {sent}, Failed: {failed}")

# ---------------- Admin media ----------------
async def send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /send_pdf <filename>")
        return
    filename = context.args[0]
    path = f"media/pdfs/{filename}"
    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found.")
        return
    await update.message.reply_document(open(path, "rb"))

async def send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /send_audio <filename>")
        return
    filename = context.args[0]
    path = f"media/audio/{filename}"
    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found.")
        return
    await update.message.reply_audio(open(path, "rb"))

async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /send_image <filename>")
        return
    filename = context.args[0]
    path = f"media/images/{filename}"
    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found.")
        return
    await update.message.reply_photo(open(path, "rb"))
