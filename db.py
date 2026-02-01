import sqlite3
from pathlib import Path

DB_PATH = Path("data/church_bot.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            language TEXT DEFAULT 'en'
        )
    ''')
    # Prayers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS prayers (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            text TEXT,
            time TEXT,
            prayed INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Events table
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            name TEXT,
            time TEXT
        )
    ''')
    # Quizzes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY,
            question TEXT,
            answer TEXT
        )
    ''')
    # Verses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS verses (
            id INTEGER PRIMARY KEY,
            text TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()
