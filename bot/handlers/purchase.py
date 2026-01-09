"""
Purchase handlers - order confirmation, payment via YooMoney, success
"""
import logging
from datetime import datetime
from typing import List
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
    get_payment_check_keyboard,
    get_success_payment_keyboard
)
from bot.services.yoomoney import get_yoomoney_service
from bot.services.file_generator import (
    download_pack_file,
    get_pack_files_for_order,
    get_pack_count_for_contacts
)
from bot.config import PRICES, SUPPORT_USERNAME, PAYMENT_CHECK_MINUTES, PAYMENT_TOLERANCE, YOOMONEY_WALLET
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
✅ Выдача сразу после оплаты

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ ГАРАНТИИ:

✅ Замена если файл не откроется
✅ Техподдержка 24/7
⚠️ Возврат невозможен после скачивания"""

    return text


def get_payment_text(city: str, category: str, pack_size: int, price: int) -> str:
    """Generate payment page text with YooMoney instructions"""

    city_name = get_city_name(city)
    cat_name = get_category_name(category)

    return f"""💳 ОПЛАТА ЗАКАЗА

📦 {city_name} — {cat_name} ({pack_size} шт)
💰 Сумма: {format_price(price)}₽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 ИНСТРУКЦИЯ:

1️⃣ Нажмите "Перейти к оплате"
2️⃣ Введите сумму: {format_price(price)}₽
3️⃣ Оплатите картой (без регистрации)
4️⃣ Вернитесь сюда и нажмите "Проверить оплату"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ ВАЖНО: Оплатите ТОЧНО {format_price(price)}₽
Иначе система не найдёт ваш платёж!"""


def get_success_payment_text(
        order_id: str,
        city: str,
        category: str,
        pack_numbers: List[int],
        pack_size: int,
        total_contacts: int,
        total_spent: int,
        total_available: int
) -> str:
    """Generate successful payment text"""

    now = format_datetime(datetime.now())

    progress_bar = create_progress_bar(total_contacts, total_available)
    progress_percent = calculate_progress_percent(total_contacts, total_available)
    remaining = max(0, total_available - total_contacts)

    packs_str = ", ".join(str(p) for p in pack_numbers) if pack_numbers else "—"

    text = f"""🎉 ОПЛАТА ПРОШЛА УСПЕШНО!

✅ Заказ #{order_id}
📅 {now}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 ВАШИ ФАЙЛЫ:

Файлы отправлены выше ⬆️
Паки: {packs_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 СТАТИСТИКА:

Всего куплено: {format_price(total_contacts)} контактов
Потрачено: {format_price(total_spent)}₽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 ПРОГРЕСС:

[{progress_bar}] {format_price(total_contacts)} / {format_price(total_available)}+ ({progress_percent}%)
📦 Доступно ещё: {format_price(remaining)}+ контактов"""

    return text


def get_payment_not_found_text(price: int) -> str:
    """Generate payment not found text"""
    return f"""❌ ОПЛАТА НЕ НАЙДЕНА

Мы не нашли платёж на сумму {format_price(price)}₽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Возможные причины:

• Платёж ещё обрабатывается (подождите 1-2 минуты)
• Оплачена другая сумма
• Платёж не прошёл

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Что делать:

1. Подождите 1-2 минуты
2. Нажмите "Проверить ещё раз"
3. Если не помогло — напишите в поддержку"""


def get_underpaid_text(expected: int, received: int) -> str:
    """Generate underpaid text"""
    diff = expected - received
    return f"""⚠️ ПОЛУЧЕНА НЕПОЛНАЯ СУММА

Ожидалось: {format_price(expected)}₽
Получено: {format_price(received)}₽
Не хватает: {format_price(diff)}₽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Что делать:

Доплатите {format_price(diff)}₽ и нажмите "Проверить ещё раз"

Или напишите в поддержку для решения вопроса."""


def get_overpaid_text(expected: int, received: int) -> str:
    """Generate overpaid text (large overpayment)"""
    diff = received - expected
    return f"""✅ ОПЛАТА ПОЛУЧЕНА

Вы оплатили больше чем нужно:
Сумма заказа: {format_price(expected)}₽
Получено: {format_price(received)}₽
Переплата: {format_price(diff)}₽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ваш заказ будет выполнен.
По вопросу возврата переплаты — напишите в поддержку @{SUPPORT_USERNAME}"""


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

    # Calculate pack count
    pack_count = get_pack_count_for_contacts(pack_size)

    # Create pending order
    await create_pending_order(
        order_id=order_id,
        user_id=user_id,
        city=city,
        category=category,
        pack_number=pack_count,  # Number of packs to buy
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
    """Handle pay button - show payment page with YooMoney link"""
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

    # Create YooMoney payment URL
    yoomoney = get_yoomoney_service()
    if yoomoney:
        payment_url = yoomoney.get_payment_url(price)
    else:
        # Fallback to direct link
        payment_url = f"https://yoomoney.ru/to/{YOOMONEY_WALLET}?sum={price}"

    text = get_payment_text(city, category, pack_size, price)
    keyboard = get_payment_keyboard(payment_url, order_id)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("check_payment:"))
async def callback_check_payment(callback: CallbackQuery):
    """Handle payment check - verify payment via YooMoney API"""
    order_id = callback.data.split(":")[1]

    # Get pending order
    order = await get_pending_order(order_id)
    if not order:
        await callback.answer("Заказ не найден или истёк", show_alert=True)
        return

    user_id = order["user_id"]
    city = order["city"]
    category = order["category"]
    pack_count = order["pack_number"]
    pack_size = order["contacts_count"]
    price = order["price"]

    await callback.answer("🔍 Проверяем оплату...")

    # Check payment via YooMoney API
    yoomoney = get_yoomoney_service()
    if not yoomoney:
        await callback.message.edit_text(
            "⚠️ Сервис проверки оплаты временно недоступен.\n\n"
            f"Напишите в поддержку @{SUPPORT_USERNAME} с номером заказа #{order_id}",
            reply_markup=get_payment_check_keyboard(order_id)
        )
        return

    # Find payment
    payment_result = await yoomoney.find_payment(
        amount=price,
        minutes_ago=PAYMENT_CHECK_MINUTES,
        tolerance=PAYMENT_TOLERANCE
    )

    if not payment_result["found"]:
        # Check if partial payment
        if payment_result.get("partial"):
            text = get_underpaid_text(price, int(payment_result["actual_amount"]))
        else:
            text = get_payment_not_found_text(price)

        await callback.message.edit_text(
            text,
            reply_markup=get_payment_check_keyboard(order_id)
        )
        return

    # Payment found!
    operation_id = payment_result["operation_id"]
    actual_amount = int(payment_result["actual_amount"])

    # Check for large overpayment
    if payment_result.get("large_overpay"):
        # Notify about overpayment but still process
        await callback.message.answer(get_overpaid_text(price, actual_amount))

    # Get already purchased packs
    already_purchased = await get_user_packs(user_id, city, category)

    # Download pack files
    files = await get_pack_files_for_order(
        city=city,
        category=category,
        pack_count=pack_count,
        already_purchased_packs=already_purchased
    )

    if not files:
        await callback.message.edit_text(
            "⚠️ Оплата получена, но возникла ошибка при получении файлов.\n\n"
            f"Напишите в поддержку @{SUPPORT_USERNAME} с номером заказа #{order_id}",
            reply_markup=get_payment_check_keyboard(order_id)
        )
        return

    # Send files to user
    pack_numbers = []
    for filename, file_bytes in files:
        # Parse pack number from filename
        try:
            parts = filename.split("_PACK_")
            if len(parts) > 1:
                pack_num = int(parts[1].replace(".xlsx", "").replace(".XLSX", ""))
                pack_numbers.append(pack_num)
            else:
                pack_num = len(pack_numbers) + 1
                pack_numbers.append(pack_num)
        except:
            pack_num = len(pack_numbers) + 1
            pack_numbers.append(pack_num)

        document = BufferedInputFile(file_bytes, filename=filename)
        sent = await callback.message.answer_document(
            document,
            caption=f"📥 {filename}"
        )

        # Save purchase for each pack
        file_id = sent.document.file_id if sent.document else None
        await add_purchase(
            user_id=user_id,
            city=city,
            category=category,
            pack_number=pack_num,
            contacts_count=1000,  # Each pack is 1000 contacts
            price=price // len(files) if files else price,
            order_id=order_id,
            file_id=file_id
        )

    # Mark order as completed
    await complete_pending_order(order_id)

    # Get updated stats
    total_contacts = await get_user_total_contacts(user_id, city, category)
    total_spent = await get_user_total_spent(user_id)

    # Get total available (assume 5000+ for now)
    total_available = 5000

    # Send success message
    text = get_success_payment_text(
        order_id=order_id,
        city=city,
        category=category,
        pack_numbers=pack_numbers,
        pack_size=pack_size,
        total_contacts=total_contacts,
        total_spent=total_spent,
        total_available=total_available
    )

    keyboard = get_success_payment_keyboard(city, category)

    await callback.message.answer(text, reply_markup=keyboard)

    logger.info(f"Successfully processed payment for order {order_id}, user {user_id}")


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
