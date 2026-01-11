"""
Catalog handlers - category selection and product pages
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.database.models import (
    get_or_create_user,
    get_base,
    get_all_bases,
    get_user_packs,
    get_user_total_contacts,
    get_discount_percent,
    get_discount_deadline,
    get_next_pack_number
)
from bot.keyboards.inline import (
    get_categories_keyboard,
    get_category_page_keyboard
)
from bot.config import DEFAULT_CITY, CATEGORIES, PRICES
from bot.utils.helpers import (
    get_category_name,
    get_category_emoji,
    get_city_name,
    get_prices_with_discount,
    create_progress_bar,
    calculate_progress_percent,
    format_price,
    format_date,
    is_discount_active,
    parse_callback_data
)

router = Router()


def get_categories_text(city: str) -> str:
    """Generate categories selection text"""
    city_name = get_city_name(city)
    return f"""📍 {city_name.upper()} — ВЫБЕРИТЕ

Выберите категорию компаний:"""


def get_category_page_text(
        city: str,
        category: str,
        total_contacts: int,
        updated_at: datetime,
        user_purchased_contacts: int,
        purchased_packs: list,
        discount_percent: int = 0,
        discount_deadline: str = None
) -> str:
    """Generate category page text"""

    emoji = get_category_emoji(category)
    cat_name = get_category_name(category).upper()
    city_name = get_city_name(city).upper()

    # Format update date
    if updated_at:
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        update_str = format_date(updated_at)
    else:
        update_str = format_date(datetime.now())

    # Build prices section
    prices_with_discount = get_prices_with_discount(discount_percent) if discount_percent > 0 else PRICES
    prices_text = ""

    for pack_size in [1000, 2000, 3000, 5000]:
        price = prices_with_discount.get(pack_size, PRICES[pack_size])
        base_price = PRICES[pack_size]
        price_str = format_price(price)

        label = ""
        if pack_size == 2000:
            label = " 💰 ПОПУЛЯРНЫЙ"
        elif pack_size == 3000:
            label = " 🔥 ВЫГОДНЫЙ"
        elif pack_size == 5000:
            label = " 🎉 МАКСИМУМ"

        if discount_percent > 0 and price < base_price:
            base_price_str = format_price(base_price)
            prices_text += f"{pack_size} шт - {price_str}₽ (было {base_price_str}₽){label}\n"
        else:
            prices_text += f"{pack_size} шт - {price_str}₽{label}\n"

    # Progress section
    progress_bar = create_progress_bar(user_purchased_contacts, total_contacts)
    progress_percent = calculate_progress_percent(user_purchased_contacts, total_contacts)
    remaining = max(0, total_contacts - user_purchased_contacts)

    packs_str = ", ".join(str(p) for p in purchased_packs) if purchased_packs else "—"

    text = f"""{emoji} {cat_name} — {city_name}

📊 В наличии: {format_price(total_contacts)}+ контактов
🆕 Обновлено: {update_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ ЧТО В БАЗЕ:

📋 Основное:
  • Название компании
  • Мобильный телефон +79...
  • Telegram username (100%)

📲 Дополнительно (если есть):
  • VK, WhatsApp, Email, Сайт

📍 Информация:
  • Адрес + координаты
  • Рейтинг, отзывы, график работы

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 ПАКЕТЫ:

{prices_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ВАШ ПРОГРЕСС:

[{progress_bar}] {format_price(user_purchased_contacts)} / {format_price(total_contacts)}+ ({progress_percent}%)
✅ Куплено: pack {packs_str}
📦 Доступно: {format_price(remaining)}+ новых контактов"""

    return text


@router.callback_query(F.data == "catalog")
async def callback_catalog(callback: CallbackQuery):
    """Handle catalog button - show categories"""
    city = DEFAULT_CITY

    text = get_categories_text(city)
    keyboard = get_categories_keyboard(city)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        # Can't edit file/photo messages, send new message instead
        await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("catalog:"))
async def callback_catalog_city(callback: CallbackQuery):
    """Handle catalog with specific city"""
    parts = parse_callback_data(callback.data, 2)
    if not parts:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    city = parts[1]

    text = get_categories_text(city)
    keyboard = get_categories_keyboard(city)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def callback_category(callback: CallbackQuery):
    """Handle category selection - show category page"""
    parts = parse_callback_data(callback.data, 3)
    if not parts:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    city = parts[1]
    category = parts[2]

    user_id = callback.from_user.id

    # Ensure user exists
    await get_or_create_user(
        user_id=user_id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name
    )

    # Get base info
    base = await get_base(city, category)
    total_contacts = base["total_contacts"] if base else 5000
    updated_at = base["updated_at"] if base else datetime.now()

    # Get user's purchase history for this category
    purchased_packs = await get_user_packs(user_id, city, category)
    user_purchased_contacts = await get_user_total_contacts(user_id, city, category)

    # Get discount
    discount_percent = await get_discount_percent()
    discount_deadline = await get_discount_deadline()

    if not is_discount_active(discount_deadline):
        discount_percent = 0

    # Generate page
    text = get_category_page_text(
        city=city,
        category=category,
        total_contacts=total_contacts,
        updated_at=updated_at,
        user_purchased_contacts=user_purchased_contacts,
        purchased_packs=purchased_packs,
        discount_percent=discount_percent,
        discount_deadline=discount_deadline
    )

    prices_with_discount = get_prices_with_discount(discount_percent) if discount_percent > 0 else PRICES

    keyboard = get_category_page_keyboard(
        city=city,
        category=category,
        available_packs=[],
        prices_with_discount=prices_with_discount,
        discount_percent=discount_percent
    )

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()
