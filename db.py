import sqlite3


DB_NAME = "database.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        language TEXT DEFAULT 'mm',
        points INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def add_user(telegram_id, username):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users (telegram_id, username)
    VALUES (?, ?)
    """, (telegram_id, username))

    conn.commit()
    conn.close()


def get_users():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()

    conn.close()
    return rows
