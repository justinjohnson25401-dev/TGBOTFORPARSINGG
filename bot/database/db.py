"""
Database connection and initialization module
"""
import os
import aiosqlite
from bot.config import DATABASE_PATH

# Global database connection
_db_connection = None


async def get_db() -> aiosqlite.Connection:
    """Get database connection (singleton)"""
    global _db_connection
    if _db_connection is None:
        # Create directory if not exists
        db_dir = os.path.dirname(DATABASE_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        _db_connection = await aiosqlite.connect(DATABASE_PATH)
        _db_connection.row_factory = aiosqlite.Row
    return _db_connection


async def close_db():
    """Close database connection"""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None


async def init_db():
    """Initialize database tables"""
    db = await get_db()

    # Users table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notifications_enabled BOOLEAN DEFAULT TRUE,
            is_blocked BOOLEAN DEFAULT FALSE
        )
    """)

    # User purchases table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            city TEXT,
            category TEXT,
            pack_number INTEGER,
            contacts_count INTEGER,
            price INTEGER,
            order_id TEXT,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_id TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Bases table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS bases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            category TEXT,
            total_contacts INTEGER,
            pack_size INTEGER DEFAULT 1000,
            gdrive_file_id TEXT,
            updated_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)

    # Prices table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_size INTEGER,
            base_price INTEGER,
            discount_percent INTEGER DEFAULT 0
        )
    """)

    # Custom requests table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS custom_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            request_text TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            admin_response TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Settings table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Pending orders (for payment tracking)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS pending_orders (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER,
            city TEXT,
            category TEXT,
            pack_number INTEGER,
            contacts_count INTEGER,
            price INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    await db.commit()

    # Initialize default settings
    await init_default_settings()


async def init_default_settings():
    """Initialize default settings if not exist"""
    from bot.config import DEFAULT_DISCOUNT_PERCENT, DEFAULT_DISCOUNT_DEADLINE

    db = await get_db()

    # Check if settings exist
    cursor = await db.execute("SELECT COUNT(*) FROM settings")
    row = await cursor.fetchone()

    if row[0] == 0:
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("discount_percent", str(DEFAULT_DISCOUNT_PERCENT))
        )
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("discount_deadline", DEFAULT_DISCOUNT_DEADLINE)
        )
        await db.commit()
