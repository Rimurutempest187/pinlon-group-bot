import random, logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from db import get_conn
import config, translations

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

# TODO: Add /events, /quiz, /answer, /daily_inspiration, admin broadcast commands
