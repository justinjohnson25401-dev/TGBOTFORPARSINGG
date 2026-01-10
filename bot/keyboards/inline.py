"""
Inline keyboards for the bot
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Optional
from bot.config import CATEGORIES, PRICES, SUPPORT_USERNAME


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu inline keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛒 Выбрать базу данных",
            callback_data="catalog"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👁️ Посмотреть пример базы",
            callback_data="demo"
        )
    )
    return builder.as_markup()


def get_categories_keyboard(
        city: str,
        bases_info: Dict[str, Dict] = None
) -> InlineKeyboardMarkup:
    """
    Get categories selection keyboard
    bases_info: dict with category -> {total_contacts, min_price} info
    """
    builder = InlineKeyboardBuilder()

    # Create category buttons - one per row for better visibility
    for cat_key, cat_info in CATEGORIES.items():
        emoji = cat_info["emoji"]
        name = cat_info["name"]

        # Get additional info if available
        if bases_info and cat_key in bases_info:
            contacts = bases_info[cat_key].get("total_contacts", 5000)
            contacts_str = f"{contacts:,}".replace(",", " ")
            min_price = bases_info[cat_key].get("min_price", 6)
            text = f"{emoji} {name}  {contacts_str}+ | от {min_price}₽"
        else:
            text = f"{emoji} {name}  5 000+ | от 6₽"

        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"category:{city}:{cat_key}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🎯 Заказать другой город/категорию",
            callback_data="custom_order"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_main"
        )
    )

    return builder.as_markup()


def get_category_page_keyboard(
        city: str,
        category: str,
        available_packs: List[int],
        prices_with_discount: Dict[int, int],
        discount_percent: int = 0
) -> InlineKeyboardMarkup:
    """
    Get category page keyboard with pack selection
    available_packs: list of pack sizes that can be purchased
    prices_with_discount: dict pack_size -> price after discount
    """
    builder = InlineKeyboardBuilder()

    # Demo button
    builder.row(
        InlineKeyboardButton(
            text="👁️ Посмотреть пример базы",
            callback_data=f"demo:{city}:{category}"
        )
    )

    # Pack size buttons in pairs
    pack_sizes = [1000, 2000, 3000, 5000]

    for i in range(0, len(pack_sizes), 2):
        row_buttons = []
        for j in range(2):
            if i + j < len(pack_sizes):
                pack_size = pack_sizes[i + j]
                price = prices_with_discount.get(pack_size, PRICES.get(pack_size, 0))
                price_str = f"{price:,}".replace(",", " ")

                # Add labels for popular/best value
                label = ""
                if pack_size == 2000:
                    label = " 💰"
                elif pack_size == 3000:
                    label = " 🔥"
                elif pack_size == 5000:
                    label = " 🎉"

                text = f"{pack_size} шт - {price_str}₽{label}"

                row_buttons.append(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=f"pack:{city}:{category}:{pack_size}"
                    )
                )

        if len(row_buttons) == 2:
            builder.row(*row_buttons)
        elif len(row_buttons) == 1:
            builder.row(row_buttons[0])

    # Back button
    builder.row(
        InlineKeyboardButton(
            text="◀️ Другая категория",
            callback_data=f"catalog:{city}"
        )
    )

    return builder.as_markup()


def get_demo_keyboard(city: str = None, category: str = None) -> InlineKeyboardMarkup:
    """Get demo file keyboard"""
    builder = InlineKeyboardBuilder()

    if city and category:
        builder.row(
            InlineKeyboardButton(
                text="💳 Купить полную базу",
                callback_data=f"category:{city}:{category}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="💳 Купить полную базу",
                callback_data="catalog"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="delete_message"
        )
    )

    return builder.as_markup()


def get_order_confirmation_keyboard(
        city: str,
        category: str,
        pack_size: int,
        price: int,
        order_id: str,
        has_promo: bool = False,
        promo_discount: int = 0
) -> InlineKeyboardMarkup:
    """Get order confirmation keyboard"""
    builder = InlineKeyboardBuilder()

    price_str = f"{price:,}".replace(",", " ")

    builder.row(
        InlineKeyboardButton(
            text=f"💳 ОПЛАТИТЬ {price_str}₽",
            callback_data=f"pay:{order_id}"
        )
    )

    # Promo code button
    if has_promo:
        builder.row(
            InlineKeyboardButton(
                text=f"✅ Промокод применён (-{promo_discount}%)",
                callback_data="promo_applied"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="🎁 У меня промокод",
                callback_data=f"promo:{order_id}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="◀️ Изменить пакет",
            callback_data=f"category:{city}:{category}"
        )
    )

    return builder.as_markup()


def get_payment_keyboard(payment_url: str, order_id: str) -> InlineKeyboardMarkup:
    """Get payment keyboard with YooMoney link"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="💳 Перейти к оплате",
            url=payment_url
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✅ Проверить оплату",
            callback_data=f"check_payment:{order_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"cancel_order:{order_id}"
        )
    )

    return builder.as_markup()


def get_payment_check_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Get keyboard for checking payment status"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🔄 Проверить ещё раз",
            callback_data=f"check_payment:{order_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💬 Связаться с поддержкой",
            url=f"https://t.me/{SUPPORT_USERNAME}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"cancel_order:{order_id}"
        )
    )

    return builder.as_markup()


def get_success_payment_keyboard(city: str, category: str) -> InlineKeyboardMarkup:
    """Get keyboard after successful payment"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🛒 Докупить контакты",
            callback_data=f"category:{city}:{category}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📦 Другая категория",
            callback_data=f"catalog:{city}"
        ),
        InlineKeyboardButton(
            text="🏠 Главная",
            callback_data="back_to_main"
        )
    )

    return builder.as_markup()


def get_purchases_keyboard(purchases: List[Dict]) -> InlineKeyboardMarkup:
    """Get purchases history keyboard with download buttons"""
    builder = InlineKeyboardBuilder()

    for purchase in purchases[:10]:  # Limit to 10 most recent
        purchase_id = purchase["id"]
        order_id = purchase.get("order_id", "N/A")

        builder.row(
            InlineKeyboardButton(
                text=f"📥 Скачать #{order_id[-4:] if order_id else purchase_id}",
                callback_data=f"download:{purchase_id}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🏠 Главная",
            callback_data="back_to_main"
        )
    )

    return builder.as_markup()


def get_faq_keyboard() -> InlineKeyboardMarkup:
    """Get FAQ questions keyboard"""
    builder = InlineKeyboardBuilder()

    faq_items = [
        ("🏙️ Нужен другой город или регион?", "faq:other_city"),
        ("📄 Что внутри файла?", "faq:format"),
        ("💬 Зачем у всех Telegram?", "faq:telegram"),
        ("🔄 Будут ли повторы при докупке?", "faq:duplicates"),
        ("🔄 Как часто обновляются базы?", "faq:updates"),
        ("⚖️ Это вообще легально?", "faq:legal"),
        ("💰 Есть ли возврат денег?", "faq:refund"),
        ("🤝 Партнёрство", "faq:partnership"),
    ]

    for text, callback in faq_items:
        builder.row(
            InlineKeyboardButton(text=text, callback_data=callback)
        )

    builder.row(
        InlineKeyboardButton(
            text="💬 Написать в поддержку",
            url=f"https://t.me/{SUPPORT_USERNAME}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_main"
        )
    )

    return builder.as_markup()


def get_faq_answer_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for FAQ answer (back button)"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к FAQ",
            callback_data="faq"
        )
    )
    return builder.as_markup()


def get_about_keyboard() -> InlineKeyboardMarkup:
    """Get about page keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛒 Выбрать базу",
            callback_data="catalog"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_main"
        )
    )
    return builder.as_markup()


def get_custom_order_keyboard() -> InlineKeyboardMarkup:
    """Get custom order page keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_main"
        )
    )
    return builder.as_markup()


def get_custom_order_sent_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard after custom order sent"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛒 Посмотреть готовые базы",
            callback_data="catalog"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏠 Главная",
            callback_data="back_to_main"
        )
    )
    return builder.as_markup()


# ==================== ADMIN KEYBOARDS ====================


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Get admin menu keyboard"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
        InlineKeyboardButton(text="📦 Заказы", callback_data="admin:orders")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:users"),
        InlineKeyboardButton(text="📝 Заявки", callback_data="admin:requests")
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Промокоды", callback_data="admin:promo"),
        InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast")
    )
    builder.row(
        InlineKeyboardButton(text="➕ Добавить базу", callback_data="admin:add_base"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin:settings")
    )

    return builder.as_markup()


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    """Get admin back button"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад в админку",
            callback_data="admin:menu"
        )
    )
    return builder.as_markup()


def get_admin_requests_keyboard(requests: List[Dict]) -> InlineKeyboardMarkup:
    """Get keyboard for custom requests management"""
    builder = InlineKeyboardBuilder()

    for req in requests[:10]:
        req_id = req["id"]
        builder.row(
            InlineKeyboardButton(
                text=f"✅ Выполнено #{req_id}",
                callback_data=f"admin:req_done:{req_id}"
            ),
            InlineKeyboardButton(
                text=f"❌ Отклонить #{req_id}",
                callback_data=f"admin:req_reject:{req_id}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад в админку",
            callback_data="admin:menu"
        )
    )

    return builder.as_markup()


def get_admin_settings_keyboard() -> InlineKeyboardMarkup:
    """Get admin settings keyboard"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="📊 Изменить скидку",
            callback_data="admin:set_discount"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📅 Изменить дедлайн",
            callback_data="admin:set_deadline"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад в админку",
            callback_data="admin:menu"
        )
    )

    return builder.as_markup()


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get broadcast confirmation keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Отправить",
            callback_data="admin:broadcast_confirm"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="admin:broadcast_cancel"
        )
    )
    return builder.as_markup()


def get_promo_cancel_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Get keyboard for promo code input (cancel button)"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="◀️ Отмена",
            callback_data=f"promo_cancel:{order_id}"
        )
    )
    return builder.as_markup()


def get_admin_promo_keyboard() -> InlineKeyboardMarkup:
    """Get admin promo codes management keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Создать промокод",
            callback_data="admin:promo_create"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📋 Список промокодов",
            callback_data="admin:promo_list"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад в админку",
            callback_data="admin:menu"
        )
    )
    return builder.as_markup()


def get_admin_promo_list_keyboard(promo_codes: List[Dict]) -> InlineKeyboardMarkup:
    """Get keyboard with promo codes list for admin"""
    builder = InlineKeyboardBuilder()

    for promo in promo_codes[:10]:
        code = promo["code"]
        discount = promo["discount_percent"]
        used = promo["used_count"]
        max_uses = promo.get("max_uses") or "∞"
        is_active = promo.get("is_active", True)

        status = "✅" if is_active else "❌"
        text = f"{status} {code} (-{discount}%) [{used}/{max_uses}]"

        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"admin:promo_view:{promo['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="➕ Создать промокод",
            callback_data="admin:promo_create"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="admin:promo"
        )
    )

    return builder.as_markup()


def get_admin_promo_view_keyboard(promo_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Get keyboard for viewing single promo code"""
    builder = InlineKeyboardBuilder()

    if is_active:
        builder.row(
            InlineKeyboardButton(
                text="🚫 Деактивировать",
                callback_data=f"admin:promo_deactivate:{promo_id}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к списку",
            callback_data="admin:promo_list"
        )
    )

    return builder.as_markup()
