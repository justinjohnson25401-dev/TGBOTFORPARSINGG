"""
Helper functions and utilities
"""
import uuid
from datetime import datetime
from typing import Dict, Optional
from bot.config import CATEGORIES, CITIES, PRICES


def generate_order_id() -> str:
    """Generate unique order ID"""
    return str(uuid.uuid4())[:8].upper()


def format_price(price: int) -> str:
    """Format price with spaces as thousand separators"""
    return f"{price:,}".replace(",", " ")


def get_category_name(category_key: str) -> str:
    """Get category display name by key"""
    if category_key in CATEGORIES:
        return CATEGORIES[category_key]["name"]
    return category_key


def get_category_emoji(category_key: str) -> str:
    """Get category emoji by key"""
    if category_key in CATEGORIES:
        return CATEGORIES[category_key]["emoji"]
    return "📁"


def get_city_name(city_key: str) -> str:
    """Get city display name by key"""
    if city_key in CITIES:
        return CITIES[city_key]["name"]
    return city_key


def calculate_price_with_discount(base_price: int, discount_percent: int) -> int:
    """Calculate price after discount"""
    if discount_percent <= 0:
        return base_price
    discount = base_price * discount_percent // 100
    return base_price - discount


def get_prices_with_discount(discount_percent: int) -> Dict[int, int]:
    """Get all pack prices with discount applied"""
    return {
        size: calculate_price_with_discount(price, discount_percent)
        for size, price in PRICES.items()
    }


def format_date(dt: datetime) -> str:
    """Format datetime to Russian date string"""
    months = [
        "", "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{dt.day} {months[dt.month]} {dt.year}"


def format_datetime(dt: datetime) -> str:
    """Format datetime to Russian date and time string"""
    return f"{format_date(dt)}, {dt.strftime('%H:%M')}"


def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Create text progress bar"""
    if total <= 0:
        return "░" * length

    filled = int(length * min(current, total) / total)
    empty = length - filled

    return "█" * filled + "░" * empty


def calculate_progress_percent(current: int, total: int) -> int:
    """Calculate progress percentage"""
    if total <= 0:
        return 0
    return min(100, int(current * 100 / total))


def format_contacts_count(count: int) -> str:
    """Format contacts count for display"""
    if count >= 1000:
        return f"{count:,}".replace(",", " ")
    return str(count)


def get_pack_label(pack_size: int) -> str:
    """Get label for pack size"""
    labels = {
        2000: "💰 ПОПУЛЯРНЫЙ",
        3000: "🔥 ВЫГОДНЫЙ",
        5000: "🎉 МАКСИМУМ"
    }
    return labels.get(pack_size, "")


def is_discount_active(deadline: Optional[str]) -> bool:
    """Check if discount is still active based on deadline"""
    if not deadline:
        return False
    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
        return datetime.now() <= deadline_date
    except ValueError:
        return False


def escape_markdown(text: str) -> str:
    """Escape special characters for Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def transliterate(text: str) -> str:
    """Transliterate Russian text to Latin"""
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        ' ': '_'
    }

    result = ""
    for char in text:
        result += translit_map.get(char, char)
    return result


def generate_filename(city: str, category: str, pack_number: int, contacts_count: int) -> str:
    """Generate filename for the database file"""
    city_name = get_city_name(city)
    category_name = get_category_name(category)

    # Transliterate to Latin
    city_lat = transliterate(city_name)
    category_lat = transliterate(category_name)

    return f"{city_lat}_{category_lat}_pack{pack_number}_{contacts_count}.xlsx"
