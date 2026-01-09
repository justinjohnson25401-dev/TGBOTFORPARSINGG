"""
Configuration file for the Contact Database Sales Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# Support contact
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "Oroani")

# YooMoney settings
YOOMONEY_ACCESS_TOKEN = os.getenv("YOOMONEY_ACCESS_TOKEN", "")
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET", "4100118480127303")
YOOMONEY_CLIENT_ID = os.getenv("YOOMONEY_CLIENT_ID", "")

# Google Drive settings
GDRIVE_CREDENTIALS_FILE = os.getenv("GDRIVE_CREDENTIALS_FILE", "credentials.json")
GDRIVE_BASE_FOLDER_ID = os.getenv("GDRIVE_BASE_FOLDER_ID", "")  # Folder with base files
GDRIVE_DEMO_FOLDER_ID = os.getenv("GDRIVE_DEMO_FOLDER_ID", "")  # Folder with demo file

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

# Contacts per pack
CONTACTS_PER_PACK = 1000

# Default discount settings
DEFAULT_DISCOUNT_PERCENT = 20
DEFAULT_DISCOUNT_DEADLINE = "2026-01-31"

# Categories configuration
# File naming: {City}_{Category}_PACK_{NN}.xlsx
# Example: Moscow_SalonKrasoty_PACK_01.xlsx
CATEGORIES = {
    "SalonKrasoty": {"name": "Салоны красоты", "emoji": "💅"},
    "Avtoservisy": {"name": "Автосервисы", "emoji": "🚗"},
    "Medicina": {"name": "Медицина", "emoji": "🏥"},
    "Restorany": {"name": "Рестораны", "emoji": "🍽️"}
}

# Cities configuration
CITIES = {
    "Moscow": {"name": "Москва"},
    "SPB": {"name": "Санкт-Петербург"}
}

# Default city
DEFAULT_CITY = "Moscow"

# Webhook settings (for Railway deployment)
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH = "/webhook/bot"

# File settings
DEMO_FILE_PATH = "bot/data/demo.xlsx"
TEMP_FILES_DIR = "bot/data/temp"

# Payment settings
PAYMENT_CHECK_MINUTES = 30  # How far back to search for payments
PAYMENT_TOLERANCE = 100  # Accept overpayment up to this amount without warning
