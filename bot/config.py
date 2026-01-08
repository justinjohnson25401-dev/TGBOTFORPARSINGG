"""
Configuration file for the 2GIS Database Sales Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# Prodamus settings
PRODAMUS_SECRET = os.getenv("PRODAMUS_SECRET", "")
PRODAMUS_SHOP_ID = os.getenv("PRODAMUS_SHOP_ID", "")
PRODAMUS_BASE_URL = "https://payform.ru"

# Google Drive settings
GDRIVE_CREDENTIALS_FILE = os.getenv("GDRIVE_CREDENTIALS_FILE", "credentials.json")
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot/data/database.db")

# Prices (base prices without discount)
PRICES = {
    1000: 10000,
    2000: 20000,
    3000: 30000,
    5000: 50000
}

# Pack sizes available
PACK_SIZES = [1000, 2000, 3000, 5000]

# Default discount settings
DEFAULT_DISCOUNT_PERCENT = 20
DEFAULT_DISCOUNT_DEADLINE = "2026-01-31"

# Categories configuration
CATEGORIES = {
    "salony": {"name": "Салоны красоты", "emoji": "💅"},
    "auto": {"name": "Автосервисы", "emoji": "🚗"},
    "medicina": {"name": "Медицина", "emoji": "🏥"},
    "restorany": {"name": "Рестораны", "emoji": "🍽️"}
}

# Cities configuration
CITIES = {
    "moskva": {"name": "Москва"},
    "spb": {"name": "Санкт-Петербург"}
}

# Default city
DEFAULT_CITY = "moskva"

# Webhook settings (for Prodamus)
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH = "/webhook/prodamus"

# File settings
DEMO_FILE_PATH = "bot/data/demo.xlsx"
TEMP_FILES_DIR = "bot/data/temp"
