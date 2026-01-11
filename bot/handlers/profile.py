"""
Profile and purchase history handlers
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from bot.database.models import (
    get_user,
    get_user_purchases,
    get_user_total_contacts,
    get_user_total_spent,
    get_purchase_by_id
)
from bot.keyboards.inline import get_purchases_keyboard, get_main_menu_keyboard
from bot.keyboards.reply import get_main_reply_keyboard
from bot.services.file_generator import generate_pack_file
from bot.utils.helpers import (
    format_price,
    format_date,
    get_city_name,
    get_category_name,
    parse_callback_data,
    safe_int
)

router = Router()


def get_purchases_text(
        username: str,
        created_at: datetime,
        total_contacts: int,
        total_spent: int,
        purchases: list
) -> str:
    """Generate purchases history text"""

    # Format registration date
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    reg_date = format_date(created_at)

    # Build history list
    history_lines = []
    for p in purchases[:10]:  # Limit to 10 recent
        order_id = p.get("order_id", "N/A")
        order_short = order_id[-4:] if order_id and len(order_id) >= 4 else order_id

        purchased_at = p.get("purchased_at")
        if isinstance(purchased_at, str):
            purchased_at = datetime.fromisoformat(purchased_at)

        if purchased_at:
            months_short = ["", "янв", "фев", "мар", "апр", "май", "июн",
                           "июл", "авг", "сен", "окт", "ноя", "дек"]
            date_str = f"{purchased_at.day} {months_short[purchased_at.month]}"
        else:
            date_str = "—"

        city = get_city_name(p["city"])
        category = get_category_name(p["category"])
        # Shorten category name
        cat_short = category.split()[0] if category else "—"
        city_short = city[:6] if len(city) > 6 else city

        contacts = p["contacts_count"]
        price = format_price(p["price"])

        history_lines.append(
            f"#{order_short} | {date_str} | {cat_short} {city_short} | {contacts} шт | {price}₽"
        )

    history_text = "\n".join(history_lines) if history_lines else "Пока нет покупок"

    text = f"""📊 ВАШИ ПОКУПКИ

👤 @{username if username else 'user'}
📅 В системе с: {reg_date}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 СТАТИСТИКА:

Всего: {format_price(total_contacts)} контактов
Потрачено: {format_price(total_spent)}₽
Заказов: {len(purchases)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 ИСТОРИЯ:

{history_text}"""

    return text


@router.message(F.text == "📊 Покупки")
async def btn_purchases(message: Message):
    """Handle purchases button"""
    user_id = message.from_user.id

    # Get user info
    user = await get_user(user_id)
    if not user:
        await message.answer(
            "Вы ещё не зарегистрированы. Нажмите /start",
            reply_markup=get_main_reply_keyboard()
        )
        return

    # Get purchases
    purchases = await get_user_purchases(user_id)
    total_contacts = await get_user_total_contacts(user_id)
    total_spent = await get_user_total_spent(user_id)

    text = get_purchases_text(
        username=user.get("username"),
        created_at=user.get("created_at", datetime.now()),
        total_contacts=total_contacts,
        total_spent=total_spent,
        purchases=purchases
    )

    keyboard = get_purchases_keyboard(purchases)

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("download:"))
async def callback_download(callback: CallbackQuery):
    """Handle file download request"""
    parts = parse_callback_data(callback.data, 2)
    if not parts:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    purchase_id = safe_int(parts[1])
    if purchase_id <= 0:
        await callback.answer("Неверный ID покупки", show_alert=True)
        return

    # Get purchase
    purchase = await get_purchase_by_id(purchase_id)
    if not purchase:
        await callback.answer("Покупка не найдена", show_alert=True)
        return

    # Check if user owns this purchase
    if purchase["user_id"] != callback.from_user.id:
        await callback.answer("Это не ваша покупка", show_alert=True)
        return

    await callback.answer("Подготавливаем файл...")

    # If we have file_id, resend from Telegram cache
    file_id = purchase.get("file_id")
    if file_id:
        try:
            order_id = purchase.get("order_id", "N/A")
            await callback.message.answer_document(
                file_id,
                caption=f"📥 Ваша база данных\n\n📦 Заказ #{order_id}"
            )
            return
        except Exception:
            pass  # Fall through to regenerate

    # Need to regenerate file
    from bot.database.models import get_base, update_purchase_file_id

    base = await get_base(purchase["city"], purchase["category"])
    if not base:
        await callback.message.answer(
            "⚠️ Не удалось найти базу данных. Обратитесь в поддержку."
        )
        return

    result = await generate_pack_file(
        gdrive_file_id=base["gdrive_file_id"],
        pack_number=purchase["pack_number"],
        pack_size=purchase["contacts_count"],
        city=purchase["city"],
        category=purchase["category"]
    )

    if not result:
        await callback.message.answer(
            "⚠️ Ошибка генерации файла. Обратитесь в поддержку."
        )
        return

    filename, file_bytes = result
    document = BufferedInputFile(file_bytes, filename=filename)

    order_id = purchase.get("order_id", "N/A")
    sent = await callback.message.answer_document(
        document,
        caption=f"📥 Ваша база данных\n\n📦 Заказ #{order_id}"
    )

    # Update file_id for future downloads
    if sent.document:
        await update_purchase_file_id(purchase_id, sent.document.file_id)
