"""
Database models and helper functions
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from bot.database.db import get_db


# ==================== USERS ====================

async def get_or_create_user(user_id: int, username: str = None, first_name: str = None) -> Dict:
    """Get existing user or create new one"""
    db = await get_db()

    cursor = await db.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )
    user = await cursor.fetchone()

    if user:
        # Update username if changed
        if username and user["username"] != username:
            await db.execute(
                "UPDATE users SET username = ? WHERE user_id = ?",
                (username, user_id)
            )
            await db.commit()
        return dict(user)

    # Create new user
    await db.execute(
        "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name)
    )
    await db.commit()

    cursor = await db.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )
    user = await cursor.fetchone()
    return dict(user)


async def get_user(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )
    user = await cursor.fetchone()
    return dict(user) if user else None


async def get_all_users(include_blocked: bool = False) -> List[Dict]:
    """Get all users"""
    db = await get_db()
    if include_blocked:
        cursor = await db.execute("SELECT * FROM users")
    else:
        cursor = await db.execute("SELECT * FROM users WHERE is_blocked = FALSE")
    users = await cursor.fetchall()
    return [dict(u) for u in users]


async def get_recent_users(limit: int = 20) -> List[Dict]:
    """Get recent registered users"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM users ORDER BY created_at DESC LIMIT ?""",
        (limit,)
    )
    users = await cursor.fetchall()
    return [dict(u) for u in users]


async def get_users_with_notifications() -> List[Dict]:
    """Get users with notifications enabled"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM users WHERE notifications_enabled = TRUE AND is_blocked = FALSE"
    )
    users = await cursor.fetchall()
    return [dict(u) for u in users]


async def update_user_blocked(user_id: int, is_blocked: bool):
    """Update user blocked status"""
    db = await get_db()
    await db.execute(
        "UPDATE users SET is_blocked = ? WHERE user_id = ?",
        (is_blocked, user_id)
    )
    await db.commit()


# ==================== PURCHASES ====================

async def get_user_purchases(user_id: int, city: str = None, category: str = None) -> List[Dict]:
    """Get user purchases, optionally filtered by city and category"""
    db = await get_db()

    query = "SELECT * FROM user_purchases WHERE user_id = ?"
    params = [user_id]

    if city:
        query += " AND city = ?"
        params.append(city)

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY purchased_at DESC"

    cursor = await db.execute(query, params)
    purchases = await cursor.fetchall()
    return [dict(p) for p in purchases]


async def get_user_packs(user_id: int, city: str, category: str) -> List[int]:
    """Get list of pack numbers user has purchased for city+category"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT pack_number FROM user_purchases
           WHERE user_id = ? AND city = ? AND category = ?
           ORDER BY pack_number""",
        (user_id, city, category)
    )
    rows = await cursor.fetchall()
    return [r["pack_number"] for r in rows]


async def get_next_pack_number(user_id: int, city: str, category: str) -> int:
    """Get next pack number for user (avoiding duplicates)"""
    purchased_packs = await get_user_packs(user_id, city, category)
    if not purchased_packs:
        return 1
    # Find first missing pack number
    for i in range(1, max(purchased_packs) + 2):
        if i not in purchased_packs:
            return i
    return max(purchased_packs) + 1


async def get_user_total_contacts(user_id: int, city: str = None, category: str = None) -> int:
    """Get total contacts purchased by user"""
    db = await get_db()

    query = "SELECT COALESCE(SUM(contacts_count), 0) as total FROM user_purchases WHERE user_id = ?"
    params = [user_id]

    if city:
        query += " AND city = ?"
        params.append(city)

    if category:
        query += " AND category = ?"
        params.append(category)

    cursor = await db.execute(query, params)
    row = await cursor.fetchone()
    return row["total"] if row else 0


async def get_user_total_spent(user_id: int) -> int:
    """Get total amount spent by user"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT COALESCE(SUM(price), 0) as total FROM user_purchases WHERE user_id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()
    return row["total"] if row else 0


async def add_purchase(
        user_id: int,
        city: str,
        category: str,
        pack_number: int,
        contacts_count: int,
        price: int,
        order_id: str,
        file_id: str = None
) -> int:
    """Add new purchase record"""
    db = await get_db()
    cursor = await db.execute(
        """INSERT INTO user_purchases
           (user_id, city, category, pack_number, contacts_count, price, order_id, file_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, city, category, pack_number, contacts_count, price, order_id, file_id)
    )
    await db.commit()
    return cursor.lastrowid


async def get_purchase_by_order_id(order_id: str) -> Optional[Dict]:
    """Get purchase by order ID"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM user_purchases WHERE order_id = ?",
        (order_id,)
    )
    purchase = await cursor.fetchone()
    return dict(purchase) if purchase else None


async def get_purchase_by_id(purchase_id: int) -> Optional[Dict]:
    """Get purchase by ID"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM user_purchases WHERE id = ?",
        (purchase_id,)
    )
    purchase = await cursor.fetchone()
    return dict(purchase) if purchase else None


async def update_purchase_file_id(purchase_id: int, file_id: str):
    """Update file_id for purchase"""
    db = await get_db()
    await db.execute(
        "UPDATE user_purchases SET file_id = ? WHERE id = ?",
        (file_id, purchase_id)
    )
    await db.commit()


# ==================== BASES ====================

async def get_base(city: str, category: str) -> Optional[Dict]:
    """Get base info by city and category"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM bases WHERE city = ? AND category = ? AND is_active = TRUE",
        (city, category)
    )
    base = await cursor.fetchone()
    return dict(base) if base else None


async def get_all_bases(city: str = None) -> List[Dict]:
    """Get all active bases, optionally filtered by city"""
    db = await get_db()

    if city:
        cursor = await db.execute(
            "SELECT * FROM bases WHERE city = ? AND is_active = TRUE",
            (city,)
        )
    else:
        cursor = await db.execute("SELECT * FROM bases WHERE is_active = TRUE")

    bases = await cursor.fetchall()
    return [dict(b) for b in bases]


async def add_base(
        city: str,
        category: str,
        total_contacts: int,
        gdrive_file_id: str,
        pack_size: int = 1000
) -> int:
    """Add new base"""
    db = await get_db()
    cursor = await db.execute(
        """INSERT INTO bases (city, category, total_contacts, gdrive_file_id, pack_size, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (city, category, total_contacts, gdrive_file_id, pack_size, datetime.now())
    )
    await db.commit()
    return cursor.lastrowid


async def update_base(base_id: int, **kwargs):
    """Update base fields (whitelist approach to prevent SQL injection)"""
    # Whitelist of allowed fields
    ALLOWED_FIELDS = {"city", "category", "total_contacts", "pack_size", "gdrive_file_id", "updated_at", "is_active"}

    db = await get_db()
    fields = []
    values = []

    for key, value in kwargs.items():
        if key not in ALLOWED_FIELDS:
            raise ValueError(f"Invalid field name: {key}")
        fields.append(f"{key} = ?")
        values.append(value)

    if not fields:
        return

    values.append(base_id)

    await db.execute(
        f"UPDATE bases SET {', '.join(fields)} WHERE id = ?",
        values
    )
    await db.commit()


# ==================== PENDING ORDERS ====================

async def create_pending_order(
        order_id: str,
        user_id: int,
        city: str,
        category: str,
        pack_number: int,
        contacts_count: int,
        price: int
):
    """Create pending order for payment tracking"""
    db = await get_db()
    await db.execute(
        """INSERT INTO pending_orders
           (order_id, user_id, city, category, pack_number, contacts_count, price)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (order_id, user_id, city, category, pack_number, contacts_count, price)
    )
    await db.commit()


async def get_pending_order(order_id: str, include_processing: bool = False) -> Optional[Dict]:
    """Get pending order by ID"""
    db = await get_db()
    if include_processing:
        cursor = await db.execute(
            "SELECT * FROM pending_orders WHERE order_id = ? AND status IN ('pending', 'processing')",
            (order_id,)
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM pending_orders WHERE order_id = ? AND status = 'pending'",
            (order_id,)
        )
    order = await cursor.fetchone()
    return dict(order) if order else None


async def complete_pending_order(order_id: str):
    """Mark pending order as completed (works with pending or processing status)"""
    db = await get_db()
    await db.execute(
        "UPDATE pending_orders SET status = 'completed' WHERE order_id = ? AND status IN ('pending', 'processing')",
        (order_id,)
    )
    await db.commit()


async def update_pending_order_price(order_id: str, new_price: int, promo_code_id: int = None):
    """Update pending order price (when promo code applied)"""
    db = await get_db()
    await db.execute(
        "UPDATE pending_orders SET price = ?, promo_code_id = ? WHERE order_id = ? AND status = 'pending'",
        (new_price, promo_code_id, order_id)
    )
    await db.commit()


async def set_pending_order_processing(order_id: str) -> bool:
    """
    Set pending order status to 'processing' to prevent race condition.
    Returns True if successfully set, False if already processing/completed.
    """
    db = await get_db()
    cursor = await db.execute(
        "UPDATE pending_orders SET status = 'processing' WHERE order_id = ? AND status = 'pending'",
        (order_id,)
    )
    await db.commit()
    return cursor.rowcount > 0


async def reset_pending_order_to_pending(order_id: str):
    """Reset order back to pending (if processing failed)"""
    db = await get_db()
    await db.execute(
        "UPDATE pending_orders SET status = 'pending' WHERE order_id = ? AND status = 'processing'",
        (order_id,)
    )
    await db.commit()


async def cancel_pending_order(order_id: str):
    """Mark pending order as cancelled"""
    db = await get_db()
    await db.execute(
        "UPDATE pending_orders SET status = 'cancelled' WHERE order_id = ?",
        (order_id,)
    )
    await db.commit()


# ==================== CUSTOM REQUESTS ====================

async def create_custom_request(user_id: int, request_text: str) -> int:
    """Create custom order request"""
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO custom_requests (user_id, request_text) VALUES (?, ?)",
        (user_id, request_text)
    )
    await db.commit()
    return cursor.lastrowid


async def get_pending_requests() -> List[Dict]:
    """Get all pending custom requests"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT cr.*, u.username, u.first_name
           FROM custom_requests cr
           JOIN users u ON cr.user_id = u.user_id
           WHERE cr.status = 'pending'
           ORDER BY cr.created_at DESC"""
    )
    requests = await cursor.fetchall()
    return [dict(r) for r in requests]


async def update_request_status(request_id: int, status: str, admin_response: str = None):
    """Update custom request status"""
    db = await get_db()
    if admin_response:
        await db.execute(
            "UPDATE custom_requests SET status = ?, admin_response = ? WHERE id = ?",
            (status, admin_response, request_id)
        )
    else:
        await db.execute(
            "UPDATE custom_requests SET status = ? WHERE id = ?",
            (status, request_id)
        )
    await db.commit()


# ==================== SETTINGS ====================

async def get_setting(key: str) -> Optional[str]:
    """Get setting value by key"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT value FROM settings WHERE key = ?",
        (key,)
    )
    row = await cursor.fetchone()
    return row["value"] if row else None


async def set_setting(key: str, value: str):
    """Set setting value"""
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    await db.commit()


async def get_discount_percent() -> int:
    """Get current discount percent"""
    value = await get_setting("discount_percent")
    return int(value) if value else 0


async def get_discount_deadline() -> Optional[str]:
    """Get discount deadline"""
    return await get_setting("discount_deadline")


# ==================== STATISTICS ====================

async def get_stats_today() -> Dict:
    """Get today's statistics"""
    db = await get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    cursor = await db.execute(
        """SELECT COUNT(*) as orders, COALESCE(SUM(price), 0) as revenue
           FROM user_purchases WHERE DATE(purchased_at) = ?""",
        (today,)
    )
    row = await cursor.fetchone()
    return {"orders": row["orders"], "revenue": row["revenue"]}


async def get_stats_month() -> Dict:
    """Get current month statistics"""
    db = await get_db()
    month_start = datetime.now().strftime("%Y-%m-01")

    cursor = await db.execute(
        """SELECT COUNT(*) as orders, COALESCE(SUM(price), 0) as revenue
           FROM user_purchases WHERE DATE(purchased_at) >= ?""",
        (month_start,)
    )
    row = await cursor.fetchone()
    return {"orders": row["orders"], "revenue": row["revenue"]}


async def get_stats_total() -> Dict:
    """Get total statistics"""
    db = await get_db()

    cursor = await db.execute(
        "SELECT COUNT(*) as orders, COALESCE(SUM(price), 0) as revenue FROM user_purchases"
    )
    row = await cursor.fetchone()
    return {"orders": row["orders"], "revenue": row["revenue"]}


async def get_users_count() -> Dict:
    """Get users count statistics"""
    db = await get_db()

    cursor = await db.execute("SELECT COUNT(*) as total FROM users")
    total = (await cursor.fetchone())["total"]

    # Active users (made purchase in last 30 days)
    cursor = await db.execute(
        """SELECT COUNT(DISTINCT user_id) as active
           FROM user_purchases
           WHERE purchased_at >= datetime('now', '-30 days')"""
    )
    active = (await cursor.fetchone())["active"]

    return {"total": total, "active": active}


async def get_recent_orders(limit: int = 10) -> List[Dict]:
    """Get recent orders"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT up.*, u.username, u.first_name
           FROM user_purchases up
           JOIN users u ON up.user_id = u.user_id
           ORDER BY up.purchased_at DESC
           LIMIT ?""",
        (limit,)
    )
    orders = await cursor.fetchall()
    return [dict(o) for o in orders]


# ==================== PROMO CODES ====================

async def create_promo_code(
        code: str,
        discount_percent: int,
        created_by: int,
        max_uses: int = None,
        expires_at: str = None
) -> int:
    """Create new promo code"""
    db = await get_db()
    cursor = await db.execute(
        """INSERT INTO promo_codes (code, discount_percent, max_uses, created_by, expires_at)
           VALUES (?, ?, ?, ?, ?)""",
        (code.upper(), discount_percent, max_uses, created_by, expires_at)
    )
    await db.commit()
    return cursor.lastrowid


async def get_promo_code(code: str) -> Optional[Dict]:
    """Get promo code by code string"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM promo_codes WHERE code = ? AND is_active = TRUE",
        (code.upper(),)
    )
    promo = await cursor.fetchone()
    return dict(promo) if promo else None


async def validate_promo_code(code: str, user_id: int) -> Dict:
    """
    Validate promo code for user.
    Returns: {"valid": bool, "discount": int, "error": str or None, "promo_id": int or None}
    """
    promo = await get_promo_code(code)

    if not promo:
        return {"valid": False, "discount": 0, "error": "Промокод не найден", "promo_id": None}

    # Check if expired
    if promo.get("expires_at"):
        expires = datetime.fromisoformat(promo["expires_at"])
        if datetime.now() > expires:
            return {"valid": False, "discount": 0, "error": "Промокод истёк", "promo_id": None}

    # Check max uses
    if promo.get("max_uses") and promo["used_count"] >= promo["max_uses"]:
        return {"valid": False, "discount": 0, "error": "Промокод больше не действует", "promo_id": None}

    # Check if user already used this code
    db = await get_db()
    cursor = await db.execute(
        "SELECT id FROM promo_code_uses WHERE promo_code_id = ? AND user_id = ?",
        (promo["id"], user_id)
    )
    if await cursor.fetchone():
        return {"valid": False, "discount": 0, "error": "Вы уже использовали этот промокод", "promo_id": None}

    return {
        "valid": True,
        "discount": promo["discount_percent"],
        "error": None,
        "promo_id": promo["id"]
    }


async def use_promo_code(promo_code_id: int, user_id: int, order_id: str, discount_amount: int):
    """Record promo code usage"""
    db = await get_db()

    # Add usage record
    await db.execute(
        """INSERT INTO promo_code_uses (promo_code_id, user_id, order_id, discount_amount)
           VALUES (?, ?, ?, ?)""",
        (promo_code_id, user_id, order_id, discount_amount)
    )

    # Increment used_count
    await db.execute(
        "UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?",
        (promo_code_id,)
    )

    await db.commit()


async def get_all_promo_codes() -> List[Dict]:
    """Get all promo codes for admin"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM promo_codes ORDER BY created_at DESC"
    )
    codes = await cursor.fetchall()
    return [dict(c) for c in codes]


async def deactivate_promo_code(promo_id: int):
    """Deactivate promo code"""
    db = await get_db()
    await db.execute(
        "UPDATE promo_codes SET is_active = FALSE WHERE id = ?",
        (promo_id,)
    )
    await db.commit()


async def get_promo_code_stats(promo_id: int) -> Dict:
    """Get promo code usage statistics"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT
               COUNT(*) as total_uses,
               COALESCE(SUM(discount_amount), 0) as total_discount
           FROM promo_code_uses WHERE promo_code_id = ?""",
        (promo_id,)
    )
    row = await cursor.fetchone()
    return {"total_uses": row["total_uses"], "total_discount": row["total_discount"]}
