from dotenv import load_dotenv
import os

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Game settings
COLLECTION_TIMES = {
    "wood": 3600,    # 1 hour in seconds
    "stone": 7200,   # 2 hours
    "water": 1800,   # 30 minutes
    "food": 5400,    # 1.5 hours
}

COLLECTION_AMOUNTS = {
    "wood": 10,
    "stone": 5,
    "water": 20,
    "food": 15,
}