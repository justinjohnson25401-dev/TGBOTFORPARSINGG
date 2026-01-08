"""
Start handler and main menu
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from bot.database.models import (
    get_or_create_user,
    get_all_bases,
    get_discount_percent,
    get_discount_deadline
)
from bot.keyboards.reply import get_main_reply_keyboard
from bot.keyboards.inline import get_main_menu_keyboard
from bot.config import DEFAULT_CITY, CATEGORIES
from bot.utils.helpers import is_discount_active

router = Router()


def get_main_menu_text(city: str = "moskva", discount_percent: int = 0, discount_deadline: str = None) -> str:
    """Generate main menu text"""

    # Build categories list
    categories_text = ""
    for cat_key, cat_info in CATEGORIES.items():
        emoji = cat_info["emoji"]
        name = cat_info["name"]
        # Padding for alignment
        padding = " " * (20 - len(name))
        categories_text += f"{emoji} {name}{padding}5 000+ контактов\n"

    # Discount line
    discount_line = ""
    if discount_percent > 0 and is_discount_active(discount_deadline):
        # Parse deadline for display
        if discount_deadline:
            parts = discount_deadline.split("-")
            if len(parts) == 3:
                months = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
                          "июля", "августа", "сентября", "октября", "ноября", "декабря"]
                day = int(parts[2])
                month = int(parts[1])
                discount_line = f"\n🔥 АКЦИЯ: -{discount_percent}% до {day} {months[month]}"

    text = f"""💎 Базы 2ГИС — Москва

🆕 Самые свежие компании из 2ГИС

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ ЧТО ВЫ ПОЛУЧАЕТЕ:

📱 Мобильные номера (+79...)
💬 Telegram у каждого (100%)
📲 VK, WhatsApp, Email (если есть)
🆕 Новейшие компании (сортировка по дате)
⚡ Моментальная выдача (5 секунд)
🔄 Без дублей при докупке

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏙️ МОСКВА — ДОСТУПНО:

{categories_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{discount_line}"""

    return text


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    # Create or get user
    await get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    # Get discount settings
    discount_percent = await get_discount_percent()
    discount_deadline = await get_discount_deadline()

    # Send main menu
    text = get_main_menu_text(
        city=DEFAULT_CITY,
        discount_percent=discount_percent,
        discount_deadline=discount_deadline
    )

    await message.answer(
        text,
        reply_markup=get_main_reply_keyboard()
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "🏠 Главная")
async def btn_home(message: Message):
    """Handle Home button"""
    # Get discount settings
    discount_percent = await get_discount_percent()
    discount_deadline = await get_discount_deadline()

    text = get_main_menu_text(
        city=DEFAULT_CITY,
        discount_percent=discount_percent,
        discount_deadline=discount_deadline
    )

    await message.answer(
        text,
        reply_markup=get_main_reply_keyboard()
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery):
    """Handle back to main menu callback"""
    # Get discount settings
    discount_percent = await get_discount_percent()
    discount_deadline = await get_discount_deadline()

    text = get_main_menu_text(
        city=DEFAULT_CITY,
        discount_percent=discount_percent,
        discount_deadline=discount_deadline
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "delete_message")
async def callback_delete_message(callback: CallbackQuery):
    """Delete message on button click"""
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()
