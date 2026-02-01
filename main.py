# main.py
import os
import json
import asyncio
import random
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from functools import wraps

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from flask import Flask, render_template, request, redirect, url_for, session

import config  # BOT_TOKEN, ADMIN_IDS, LANG default

# -----------------------
# Logging
# -----------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# -----------------------
# Paths
# -----------------------
DB_FILE = "data/bot.db"
MEDIA_PDFS = "media/pdfs"
MEDIA_AUDIO = "media/audio"
MEDIA_IMAGES = "media/images"

# -----------------------
# Ensure folders exist
# -----------------------
Path("data").mkdir(exist_ok=True)
Path(MEDIA_PDFS).mkdir(parents=True, exist_ok=True)
Path(MEDIA_AUDIO).mkdir(parents=True, exist_ok=True)
Path(MEDIA_IMAGES).mkdir(parents=True, exist_ok=True)

# -----------------------
# SQLite DB helpers
# -----------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Users
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        points INTEGER DEFAULT 0,
        lang TEXT DEFAULT 'en'
    )""")
    # Prayers
    c.execute("""CREATE TABLE IF NOT EXISTS prayers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        time TEXT
    )""")
    # Events
    c.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        time TEXT
    )""")
    # Verses
    c.execute("""CREATE TABLE IF NOT EXISTS verses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT
    )""")
    # Quizzes
    c.execute("""CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT
    )""")
    conn.commit()
    conn.close()

def db_connection():
    return sqlite3.connect(DB_FILE)

init_db()

# -----------------------
# Utilities
# -----------------------
def add_user(user_id: int, username: str, lang="en"):
    conn = db_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users(id, username, lang) VALUES (?, ?, ?)",
              (user_id, username, lang))
    conn.commit()
    conn.close()

def get_all_users():
    conn = db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def add_prayer(user_id: int, text: str):
    conn = db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO prayers(user_id, text, time) VALUES (?, ?, ?)",
              (user_id, text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def add_points(user_id: int, points=1):
    conn = db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE id = ?", (points, user_id))
    conn.commit()
    conn.close()

def get_top_users(limit=10):
    conn = db_connection()
    c = conn.cursor()
    c.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT ?", (limit,))
    top = c.fetchall()
    conn.close()
    return top

# -----------------------
# Telegram Handlers
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username or "Anonymous")
    await update.message.reply_text("🙏 Welcome! /help for commands")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start\n/help\n/verse\n/prayer <text>\n/events\n/quiz\n/answer <text>\n"
        "/daily_inspiration\n/leaderboard\n"
        "(Admin) /broadcast /send_pdf /send_audio /send_image"
    )
    await update.message.reply_text(text)

async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_connection()
    c = conn.cursor()
    c.execute("SELECT text FROM verses")
    verses = [row[0] for row in c.fetchall()]
    conn.close()
    if not verses:
        await update.message.reply_text("No verses configured.")
        return
    await update.message.reply_text(f"📖 {random.choice(verses)}")

async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /prayer <text>")
        return
    text = " ".join(context.args)
    user_id = update.effective_user.id
    add_prayer(user_id, text)
    await update.message.reply_text("🙏 Prayer recorded. God bless!")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = get_top_users()
    if not top:
        await update.message.reply_text("No leaderboard data yet.")
        return
    lines = ["🏆 Leaderboard:"]
    for i, (username, points) in enumerate(top, 1):
        lines.append(f"{i}. {username} — {points} points")
    await update.message.reply_text("\n".join(lines))

# -----------------------
# Admin check
# -----------------------
def is_admin(user_id):
    return user_id in getattr(config, "ADMIN_IDS", [])

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <text>")
        return
    msg = " ".join(context.args)
    sent = 0
    for uid in get_all_users():
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 {msg}")
            sent += 1
        except:
            continue
    await update.message.reply_text(f"Broadcast sent to {sent} users.")

# -----------------------
# Scheduler Tasks
# -----------------------
async def daily_verse_reminder(bot):
    conn = db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = [row[0] for row in c.fetchall()]
    c.execute("SELECT text FROM verses")
    verses = [row[0] for row in c.fetchall()]
    conn.close()
    if not verses:
        return
    verse = random.choice(verses)
    for uid in users:
        try:
            await bot.send_message(chat_id=uid, text=f"📖 Daily Verse:\n{verse}")
        except:
            continue

async def event_reminder(bot):
    conn = db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = [row[0] for row in c.fetchall()]
    c.execute("SELECT name, time FROM events")
    events = c.fetchall()
    conn.close()
    now = datetime.now().strftime("%H:%M")
    for name, t in events:
        if t == now:
            for uid in users:
                try:
                    await bot.send_message(chat_id=uid, text=f"⏰ Event Reminder: {name}")
                except:
                    continue

# -----------------------
# Main
# -----------------------
# main.py (fixed asyncio / PTB 20+ loop)
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

import config
from handlers import *  # import all your command handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_scheduler(app):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(daily_verse_reminder(app.bot)), "cron", hour=8, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(event_reminder(app.bot)), "cron", minute="*")
    scheduler.start()
    logger.info("Scheduler started with daily verse and event jobs.")

async def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Add handlers
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

    app.add_error_handler(error_handler)

    # Start scheduler
    await start_scheduler(app)

    logger.info("Church Youth Bot is running...")
    # Use run_polling with asynchronous loop (no asyncio.run)
    await app.run_polling()

if __name__ == "__main__":
    # Detect if there's already a running loop (like Codespaces/Notebook)
    try:
        asyncio.get_running_loop()
        # already running loop -> use create_task
        asyncio.create_task(main())
    except RuntimeError:
        # normal case -> run normally
        asyncio.run(main())
