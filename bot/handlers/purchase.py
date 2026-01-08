"""
Purchase handlers - order confirmation, payment, success
"""
import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from bot.database.models import (
    get_or_create_user,
    get_base,
    get_next_pack_number,
    get_user_total_contacts,
    get_user_total_spent,
    get_user_packs,
    get_discount_percent,
    get_discount_deadline,
    create_pending_order,
    get_pending_order,
    complete_pending_order,
    cancel_pending_order,
    add_purchase,
    get_purchase_by_id,
    update_purchase_file_id
)
from bot.keyboards.inline import (
    get_order_confirmation_keyboard,
    get_payment_keyboard,
    get_success_payment_keyboard
)
from bot.services.prodamus import create_payment_link
from bot.services.file_generator import generate_pack_file
from bot.config import PRICES
from bot.utils.helpers import (
    generate_order_id,
    get_category_name,
    get_category_emoji,
    get_city_name,
    get_prices_with_discount,
    calculate_price_with_discount,
    format_price,
    format_datetime,
    create_progress_bar,
    calculate_progress_percent,
    is_discount_active
)

router = Router()
logger = logging.getLogger(__name__)


def get_order_confirmation_text(
        city: str,
        category: str,
        pack_size: int,
        base_price: int,
        final_price: int,
        discount_percent: int = 0
) -> str:
    """Generate order confirmation text"""

    city_name = get_city_name(city)
    cat_name = get_category_name(category)
    emoji = get_category_emoji(category)

    # Price section
    if discount_percent > 0 and final_price < base_price:
        discount_amount = base_price - final_price
        price_section = f"""💰 СТОИМОСТЬ:

Обычная цена:    {format_price(base_price)}₽
Скидка (-{discount_percent}%):   -{format_price(discount_amount)}₽
──────────────────────
ИТОГО:           {format_price(final_price)}₽"""
    else:
        price_section = f"""💰 СТОИМОСТЬ:

ИТОГО: {format_price(final_price)}₽"""

    text = f"""✅ ПОДТВЕРЖДЕНИЕ ЗАКАЗА

📦 Ваш заказ:

🏙️ Город: {city_name}
{emoji} Категория: {cat_name}
📊 Количество: {format_price(pack_size)} контактов

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{price_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 ВЫ ПОЛУЧИТЕ:

✅ Excel-файл с {format_price(pack_size)} контактами
✅ Telegram у каждого (100%)
✅ Мобильные номера (+79...)
✅ Выдача за 5 секунд после оплаты

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ ГАРАНТИИ:

✅ Замена если файл не откроется
✅ Техподдержка 24/7
⚠️ Возврат невозможен после скачивания"""

    return text


def get_payment_text(city: str, category: str, pack_size: int, price: int) -> str:
    """Generate payment page text"""

    city_name = get_city_name(city)
    cat_name = get_category_name(category)

    return f"""💳 ОПЛАТА ЗАКАЗА

📦 {city_name} — {cat_name} ({pack_size} шт)
💰 Сумма: {format_price(price)}₽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Нажмите кнопку для оплаты

Принимаем: Visa, MasterCard, Mir, СБП
🔒 Безопасная оплата через Prodamus"""


def get_success_payment_text(
        order_id: str,
        city: str,
        category: str,
        pack_number: int,
        pack_size: int,
        total_contacts: int,
        total_spent: int,
        total_available: int
) -> str:
    """Generate successful payment text"""

    city_name = get_city_name(city)
    cat_name = get_category_name(category)

    now = format_datetime(datetime.now())

    progress_bar = create_progress_bar(total_contacts, total_available)
    progress_percent = calculate_progress_percent(total_contacts, total_available)
    remaining = max(0, total_available - total_contacts)

    text = f"""🎉 ОПЛАТА ПРОШЛА УСПЕШНО!

✅ Заказ #{order_id}
📅 {now}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 ВАША БАЗА:

📄 Файл отправлен выше ⬆️

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 СТАТИСТИКА:

Всего куплено: {format_price(total_contacts)} контактов
Потрачено: {format_price(total_spent)}₽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 ПРОГРЕСС:

[{progress_bar}] {format_price(total_contacts)} / {format_price(total_available)}+ ({progress_percent}%)
📦 Доступно: {format_price(remaining)}+ новых

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 Докупите со скидкой:
+1000 шт → 8 000₽
+2000 шт → 15 000₽"""

    return text


@router.callback_query(F.data.startswith("pack:"))
async def callback_select_pack(callback: CallbackQuery):
    """Handle pack selection - show order confirmation"""
    parts = callback.data.split(":")
    city = parts[1]
    category = parts[2]
    pack_size = int(parts[3])

    user_id = callback.from_user.id

    # Get discount
    discount_percent = await get_discount_percent()
    discount_deadline = await get_discount_deadline()

    if not is_discount_active(discount_deadline):
        discount_percent = 0

    # Calculate price
    base_price = PRICES.get(pack_size, 10000)
    final_price = calculate_price_with_discount(base_price, discount_percent)

    # Generate order ID
    order_id = generate_order_id()

    # Get next pack number for this user
    pack_number = await get_next_pack_number(user_id, city, category)

    # Create pending order
    await create_pending_order(
        order_id=order_id,
        user_id=user_id,
        city=city,
        category=category,
        pack_number=pack_number,
        contacts_count=pack_size,
        price=final_price
    )

    text = get_order_confirmation_text(
        city=city,
        category=category,
        pack_size=pack_size,
        base_price=base_price,
        final_price=final_price,
        discount_percent=discount_percent
    )

    keyboard = get_order_confirmation_keyboard(
        city=city,
        category=category,
        pack_size=pack_size,
        price=final_price,
        order_id=order_id
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("pay:"))
async def callback_pay(callback: CallbackQuery):
    """Handle pay button - show payment page"""
    order_id = callback.data.split(":")[1]

    # Get pending order
    order = await get_pending_order(order_id)
    if not order:
        await callback.answer("Заказ не найден или истёк", show_alert=True)
        return

    city = order["city"]
    category = order["category"]
    pack_size = order["contacts_count"]
    price = order["price"]

    # Create payment link
    description = f"{get_city_name(city)} - {get_category_name(category)} ({pack_size} шт)"
    payment_url = create_payment_link(
        order_id=order_id,
        amount=price,
        description=description
    )

    text = get_payment_text(city, category, pack_size, price)
    keyboard = get_payment_keyboard(payment_url, order_id)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_order:"))
async def callback_cancel_order(callback: CallbackQuery):
    """Handle order cancellation"""
    order_id = callback.data.split(":")[1]

    await cancel_pending_order(order_id)

    await callback.answer("Заказ отменён", show_alert=True)

    # Return to main menu
    from bot.handlers.start import get_main_menu_text
    from bot.keyboards.inline import get_main_menu_keyboard
    from bot.config import DEFAULT_CITY

    discount_percent = await get_discount_percent()
    discount_deadline = await get_discount_deadline()

    text = get_main_menu_text(DEFAULT_CITY, discount_percent, discount_deadline)

    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())


async def process_successful_payment(bot: Bot, order_id: str):
    """
    Process successful payment - generate and send file

    Called from webhook handler
    """
    logger.info(f"Processing successful payment for order {order_id}")

    # Get pending order
    order = await get_pending_order(order_id)
    if not order:
        logger.error(f"Order {order_id} not found")
        return False

    user_id = order["user_id"]
    city = order["city"]
    category = order["category"]
    pack_number = order["pack_number"]
    pack_size = order["contacts_count"]
    price = order["price"]

    # Get base info for file generation
    base = await get_base(city, category)
    if not base:
        logger.error(f"Base not found for {city}/{category}")
        # Still mark order as completed but notify admin
        await complete_pending_order(order_id)
        await bot.send_message(
            user_id,
            "⚠️ Оплата получена, но возникла техническая ошибка. "
            "Наш менеджер свяжется с вами в ближайшее время."
        )
        return False

    gdrive_file_id = base["gdrive_file_id"]

    # Generate pack file
    result = await generate_pack_file(
        gdrive_file_id=gdrive_file_id,
        pack_number=pack_number,
        pack_size=pack_size,
        city=city,
        category=category
    )

    if not result:
        logger.error(f"Failed to generate file for order {order_id}")
        await complete_pending_order(order_id)
        await bot.send_message(
            user_id,
            "⚠️ Оплата получена, но возникла ошибка при генерации файла. "
            "Наш менеджер свяжется с вами в ближайшее время."
        )
        return False

    filename, file_bytes = result

    # Send file to user
    document = BufferedInputFile(file_bytes, filename=filename)
    sent_message = await bot.send_document(
        user_id,
        document,
        caption=f"📥 Ваша база данных\n\n📦 Заказ #{order_id}"
    )

    # Get file_id from sent message
    file_id = sent_message.document.file_id if sent_message.document else None

    # Save purchase record
    purchase_id = await add_purchase(
        user_id=user_id,
        city=city,
        category=category,
        pack_number=pack_number,
        contacts_count=pack_size,
        price=price,
        order_id=order_id,
        file_id=file_id
    )

    # Mark pending order as completed
    await complete_pending_order(order_id)

    # Get updated stats
    total_contacts = await get_user_total_contacts(user_id, city, category)
    total_spent = await get_user_total_spent(user_id)
    total_available = base["total_contacts"]

    # Send success message
    text = get_success_payment_text(
        order_id=order_id,
        city=city,
        category=category,
        pack_number=pack_number,
        pack_size=pack_size,
        total_contacts=total_contacts,
        total_spent=total_spent,
        total_available=total_available
    )

    keyboard = get_success_payment_keyboard(city, category)

    await bot.send_message(user_id, text, reply_markup=keyboard)

    logger.info(f"Successfully processed payment for order {order_id}")
    return True


# For testing without real payment
@router.callback_query(F.data.startswith("test_pay:"))
async def callback_test_pay(callback: CallbackQuery):
    """Test payment simulation (for development)"""
    order_id = callback.data.split(":")[1]

    await callback.answer("Симуляция оплаты...", show_alert=True)

    # Process as successful payment
    await process_successful_payment(callback.bot, order_id)
