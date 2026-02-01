import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS").split(",")]

# File paths
USERS_FILE = "data/users.json"
QUIZZES_FILE = "data/quizzes.json"
EVENTS_FILE = "data/events.json"
VERSES_FILE = "data/verses.json"
