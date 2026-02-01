import sqlite3

DB_NAME = "church.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        points INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prayers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        time TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_user(tg_id, username):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users (telegram_id, username)
    VALUES (?, ?)
    """, (tg_id, username))

    conn.commit()
    conn.close()


def add_prayer(user_id, text, time):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO prayers (user_id, text, time)
    VALUES (?, ?, ?)
    """, (user_id, text, time))

    conn.commit()
    conn.close()


def get_users():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT telegram_id, username FROM users")

    data = cur.fetchall()

    conn.close()
    return data
