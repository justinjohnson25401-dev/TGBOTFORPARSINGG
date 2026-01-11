"""
Admin panel handlers
"""
import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database.models import (
    get_stats_today,
    get_stats_month,
    get_stats_total,
    get_users_count,
    get_recent_orders,
    get_pending_requests,
    update_request_status,
    get_all_users,
    get_recent_users,
    set_setting,
    get_discount_percent,
    get_discount_deadline,
    add_base,
    create_promo_code,
    get_all_promo_codes,
    get_promo_code,
    deactivate_promo_code,
    get_promo_code_stats
)
from bot.keyboards.inline import (
    get_admin_menu_keyboard,
    get_admin_back_keyboard,
    get_admin_requests_keyboard,
    get_admin_settings_keyboard,
    get_broadcast_confirm_keyboard,
    get_admin_promo_keyboard,
    get_admin_promo_list_keyboard,
    get_admin_promo_view_keyboard
)
from bot.config import ADMIN_IDS
from bot.utils.helpers import (
    format_price, format_datetime, get_city_name, get_category_name,
    parse_callback_data, safe_int, escape_html, truncate_text
)

router = Router()
logger = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    """Admin panel states"""
    waiting_for_discount = State()
    waiting_for_deadline = State()
    waiting_for_broadcast = State()
    broadcast_confirm = State()
    waiting_for_base_file = State()
    waiting_for_base_city = State()
    waiting_for_base_category = State()
    waiting_for_promo_code = State()
    waiting_for_promo_discount = State()
    waiting_for_promo_max_uses = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel entry point"""
    if not is_admin(message.from_user.id):
        return

    text = """👨‍💼 АДМИН-ПАНЕЛЬ

Выберите раздел:"""

    await message.answer(text, reply_markup=get_admin_menu_keyboard())


@router.callback_query(F.data == "admin:menu")
async def callback_admin_menu(callback: CallbackQuery, state: FSMContext):
    """Return to admin menu"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()

    text = """👨‍💼 АДМИН-ПАНЕЛЬ

Выберите раздел:"""

    await callback.message.edit_text(text, reply_markup=get_admin_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def callback_admin_stats(callback: CallbackQuery):
    """Show statistics"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    today = await get_stats_today()
    month = await get_stats_month()
    total = await get_stats_total()
    users = await get_users_count()

    text = f"""📊 СТАТИСТИКА

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 СЕГОДНЯ:
Заказов: {today['orders']}
Выручка: {format_price(today['revenue'])}₽

📆 МЕСЯЦ:
Заказов: {month['orders']}
Выручка: {format_price(month['revenue'])}₽

📈 ВСЕГО:
Заказов: {total['orders']}
Выручка: {format_price(total['revenue'])}₽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 ПОЛЬЗОВАТЕЛИ:
Всего: {users['total']}
Активных (30 дней): {users['active']}"""

    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:orders")
async def callback_admin_orders(callback: CallbackQuery):
    """Show recent orders"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    orders = await get_recent_orders(10)

    if not orders:
        text = "📦 Заказов пока нет"
    else:
        lines = ["📦 ПОСЛЕДНИЕ ЗАКАЗЫ\n"]
        for order in orders:
            order_id = order.get("order_id", "N/A")
            username = order.get("username", "—")
            city = get_city_name(order["city"])[:6]
            category = get_category_name(order["category"]).split()[0]
            contacts = order["contacts_count"]
            price = format_price(order["price"])

            purchased_at = order.get("purchased_at")
            if isinstance(purchased_at, str):
                purchased_at = datetime.fromisoformat(purchased_at)
            date_str = purchased_at.strftime("%d.%m %H:%M") if purchased_at else "—"

            lines.append(
                f"#{order_id[-4:]} | {date_str} | @{username}\n"
                f"   {city} {category} | {contacts} шт | {price}₽\n"
            )

        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:users")
async def callback_admin_users(callback: CallbackQuery):
    """Show users info"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    users_count = await get_users_count()
    recent_users = await get_recent_users(100)

    # Build users list with clickable links
    users_list = ""
    for u in recent_users:
        username = u.get("username")
        first_name = u.get("first_name", "")
        user_id = u["user_id"]
        created_at = u.get("created_at", "")

        if isinstance(created_at, str) and created_at:
            try:
                dt = datetime.fromisoformat(created_at)
                date_str = dt.strftime("%d.%m")
            except:
                date_str = "—"
        else:
            date_str = "—"

        if username:
            users_list += f"• <a href='https://t.me/{username}'>@{username}</a> ({date_str})\n"
        else:
            users_list += f"• <a href='tg://user?id={user_id}'>{first_name or user_id}</a> ({date_str})\n"

    text = f"""👥 ПОЛЬЗОВАТЕЛИ

Всего зарегистрировано: {users_count['total']}
Активных (покупали за 30 дней): {users_count['active']}
Конверсия: {round(users_count['active'] / users_count['total'] * 100, 1) if users_count['total'] > 0 else 0}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Последние 100 пользователей:

{users_list}"""

    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard(), disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "admin:requests")
async def callback_admin_requests(callback: CallbackQuery):
    """Show pending custom requests"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    requests = await get_pending_requests()

    if not requests:
        text = "📝 Нет активных заявок"
        await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    else:
        lines = ["📝 ЗАЯВКИ ПОД ЗАКАЗ\n"]
        for req in requests[:10]:
            req_id = req["id"]
            username = req.get("username", "—")
            first_name = req.get("first_name", "—")
            request_text = req["request_text"][:50]

            created_at = req.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            date_str = created_at.strftime("%d.%m %H:%M") if created_at else "—"

            lines.append(
                f"#{req_id} | {date_str}\n"
                f"👤 {first_name} (@{username})\n"
                f"📝 {request_text}...\n"
            )

        text = "\n".join(lines)
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_requests_keyboard(requests)
        )

    await callback.answer()


@router.callback_query(F.data.startswith("admin:req_done:"))
async def callback_req_done(callback: CallbackQuery):
    """Mark request as done"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = parse_callback_data(callback.data, 3)
    if not parts:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    req_id = safe_int(parts[2])
    if req_id <= 0:
        await callback.answer("Неверный ID заявки", show_alert=True)
        return

    await update_request_status(req_id, "completed")

    await callback.answer(f"Заявка #{req_id} выполнена", show_alert=True)

    # Refresh list
    await callback_admin_requests(callback)


@router.callback_query(F.data.startswith("admin:req_reject:"))
async def callback_req_reject(callback: CallbackQuery):
    """Reject request"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = parse_callback_data(callback.data, 3)
    if not parts:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    req_id = safe_int(parts[2])
    if req_id <= 0:
        await callback.answer("Неверный ID заявки", show_alert=True)
        return

    await update_request_status(req_id, "rejected")

    await callback.answer(f"Заявка #{req_id} отклонена", show_alert=True)

    # Refresh list
    await callback_admin_requests(callback)


@router.callback_query(F.data == "admin:settings")
async def callback_admin_settings(callback: CallbackQuery):
    """Show settings"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    discount = await get_discount_percent()
    deadline = await get_discount_deadline()

    text = f"""⚙️ НАСТРОЙКИ

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Текущая скидка: {discount}%
📅 Действует до: {deadline or '—'}"""

    await callback.message.edit_text(text, reply_markup=get_admin_settings_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:set_discount")
async def callback_set_discount(callback: CallbackQuery, state: FSMContext):
    """Set discount percent"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_discount)

    text = """📊 УСТАНОВКА СКИДКИ

Введите процент скидки (0-100):

Пример: 20
(100 = бесплатно, для тестирования)"""

    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.message(AdminStates.waiting_for_discount)
async def process_discount(message: Message, state: FSMContext):
    """Process discount input"""
    if not is_admin(message.from_user.id):
        return

    try:
        discount = int(message.text)
        if discount < 0 or discount > 100:
            await message.answer("Скидка должна быть от 0 до 100%")
            return

        await set_setting("discount_percent", str(discount))
        await state.clear()

        await message.answer(
            f"✅ Скидка установлена: {discount}%",
            reply_markup=get_admin_menu_keyboard()
        )

    except ValueError:
        await message.answer("Введите число от 0 до 100")


@router.callback_query(F.data == "admin:set_deadline")
async def callback_set_deadline(callback: CallbackQuery, state: FSMContext):
    """Set discount deadline"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_deadline)

    text = """📅 УСТАНОВКА ДЕДЛАЙНА

Введите дату окончания акции:

Формат: ГГГГ-ММ-ДД
Пример: 2026-01-31"""

    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.message(AdminStates.waiting_for_deadline)
async def process_deadline(message: Message, state: FSMContext):
    """Process deadline input"""
    if not is_admin(message.from_user.id):
        return

    try:
        # Validate date format
        datetime.strptime(message.text, "%Y-%m-%d")

        await set_setting("discount_deadline", message.text)
        await state.clear()

        await message.answer(
            f"✅ Дедлайн установлен: {message.text}",
            reply_markup=get_admin_menu_keyboard()
        )

    except ValueError:
        await message.answer("Неверный формат. Используйте ГГГГ-ММ-ДД")


@router.callback_query(F.data == "admin:broadcast")
async def callback_broadcast(callback: CallbackQuery, state: FSMContext):
    """Start broadcast"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_broadcast)

    users = await get_users_count()

    text = f"""📢 РАССЫЛКА

Будет отправлено {users['total']} пользователям.

Введите текст сообщения:"""

    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast_text(message: Message, state: FSMContext):
    """Process broadcast text"""
    if not is_admin(message.from_user.id):
        return

    # Telegram message limit is 4096 characters
    if len(message.text) > 4000:
        await message.answer(
            f"❌ Сообщение слишком длинное ({len(message.text)} символов).\n"
            "Максимум: 4000 символов. Сократите текст."
        )
        return

    await state.update_data(broadcast_text=message.text)
    await state.set_state(AdminStates.broadcast_confirm)

    text = f"""📢 ПОДТВЕРЖДЕНИЕ РАССЫЛКИ

Текст сообщения:
{message.text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Отправить?"""

    await message.answer(text, reply_markup=get_broadcast_confirm_keyboard())


@router.callback_query(F.data == "admin:broadcast_confirm")
async def callback_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Confirm and send broadcast"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    data = await state.get_data()
    broadcast_text = data.get("broadcast_text")

    if not broadcast_text:
        await callback.answer("Текст не найден", show_alert=True)
        await state.clear()
        return

    await state.clear()

    users = await get_all_users(include_blocked=False)

    await callback.message.edit_text("📤 Рассылка началась...")

    sent = 0
    failed = 0

    for user in users:
        try:
            await bot.send_message(user["user_id"], broadcast_text)
            sent += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send to {user['user_id']}: {e}")

    result_text = f"""✅ РАССЫЛКА ЗАВЕРШЕНА

Отправлено: {sent}
Ошибок: {failed}"""

    await callback.message.answer(result_text, reply_markup=get_admin_menu_keyboard())


@router.callback_query(F.data == "admin:broadcast_cancel")
async def callback_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel broadcast"""
    await state.clear()
    await callback.answer("Рассылка отменена")
    await callback_admin_menu(callback, state)


@router.callback_query(F.data == "admin:add_base")
async def callback_add_base(callback: CallbackQuery, state: FSMContext):
    """Start adding new base"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    text = """➕ ДОБАВЛЕНИЕ БАЗЫ

Для добавления базы используйте команду:

/addbase <city> <category> <gdrive_id> <total_contacts>

Пример:
/addbase moskva salony 1abc123def456 5000"""

    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.message(Command("addbase"))
async def cmd_add_base(message: Message):
    """Add new base via command"""
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 5:
        await message.answer(
            "Использование: /addbase <city> <category> <gdrive_id> <total_contacts>"
        )
        return

    city = parts[1]
    category = parts[2]
    gdrive_id = parts[3]
    try:
        total_contacts = int(parts[4])
    except ValueError:
        await message.answer("total_contacts должен быть числом")
        return

    base_id = await add_base(city, category, total_contacts, gdrive_id)

    await message.answer(
        f"✅ База добавлена (ID: {base_id})\n\n"
        f"Город: {city}\n"
        f"Категория: {category}\n"
        f"Контактов: {total_contacts}",
        reply_markup=get_admin_menu_keyboard()
    )


# Command shortcuts for quick stats
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Quick stats command"""
    if not is_admin(message.from_user.id):
        return

    today = await get_stats_today()
    month = await get_stats_month()

    text = f"""📊 Быстрая статистика

Сегодня: {today['orders']} заказов, {format_price(today['revenue'])}₽
Месяц: {month['orders']} заказов, {format_price(month['revenue'])}₽"""

    await message.answer(text)


@router.message(Command("setdiscount"))
async def cmd_set_discount(message: Message):
    """Set discount via command"""
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /setdiscount <percent>")
        return

    try:
        discount = int(parts[1])
        if discount < 0 or discount > 100:
            await message.answer("Скидка должна быть от 0 до 100%")
            return

        await set_setting("discount_percent", str(discount))
        await message.answer(f"✅ Скидка установлена: {discount}%")

    except ValueError:
        await message.answer("Введите число")


@router.message(Command("setdeadline"))
async def cmd_set_deadline(message: Message):
    """Set deadline via command"""
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /setdeadline ГГГГ-ММ-ДД")
        return

    try:
        datetime.strptime(parts[1], "%Y-%m-%d")
        await set_setting("discount_deadline", parts[1])
        await message.answer(f"✅ Дедлайн установлен: {parts[1]}")

    except ValueError:
        await message.answer("Неверный формат. Используйте ГГГГ-ММ-ДД")


# ==================== PROMO CODES ====================

@router.callback_query(F.data == "admin:promo")
async def callback_admin_promo(callback: CallbackQuery):
    """Show promo codes menu"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    text = """🎁 ПРОМОКОДЫ

Управление промокодами для индивидуальных скидок.

Промокоды можно:
• Раздавать партнёрам
• Использовать для тестирования
• Давать за отзыв/рекомендацию"""

    await callback.message.edit_text(text, reply_markup=get_admin_promo_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:promo_list")
async def callback_admin_promo_list(callback: CallbackQuery):
    """Show list of all promo codes"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    promo_codes = await get_all_promo_codes()

    if not promo_codes:
        text = """🎁 СПИСОК ПРОМОКОДОВ

Промокодов пока нет.
Нажмите "Создать промокод" чтобы добавить."""
    else:
        text = f"""🎁 СПИСОК ПРОМОКОДОВ

Всего: {len(promo_codes)}

Нажмите на промокод для просмотра деталей."""

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_promo_list_keyboard(promo_codes)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:promo_create")
async def callback_admin_promo_create(callback: CallbackQuery, state: FSMContext):
    """Start promo code creation"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_promo_code)

    text = """➕ СОЗДАНИЕ ПРОМОКОДА

Шаг 1/3: Введите код промокода

• Только буквы и цифры
• Будет преобразован в ЗАГЛАВНЫЕ
• Пример: PARTNER10, TEST50, VIP"""

    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
    await callback.answer()


@router.message(AdminStates.waiting_for_promo_code)
async def process_promo_code_name(message: Message, state: FSMContext):
    """Process promo code name input"""
    if not is_admin(message.from_user.id):
        return

    code = message.text.strip().upper()

    # Validate code format
    if not code.isalnum():
        await message.answer(
            "❌ Код должен содержать только буквы и цифры.\nПопробуйте снова:"
        )
        return

    if len(code) < 3 or len(code) > 20:
        await message.answer(
            "❌ Код должен быть от 3 до 20 символов.\nПопробуйте снова:"
        )
        return

    # Check if code already exists
    existing = await get_promo_code(code)
    if existing:
        await message.answer(
            f"❌ Промокод {code} уже существует.\nВведите другой код:"
        )
        return

    await state.update_data(promo_code=code)
    await state.set_state(AdminStates.waiting_for_promo_discount)

    await message.answer(
        f"""✅ Код: {code}

Шаг 2/3: Введите процент скидки (1-100)

Пример: 10, 20, 50"""
    )


@router.message(AdminStates.waiting_for_promo_discount)
async def process_promo_discount(message: Message, state: FSMContext):
    """Process promo discount input"""
    if not is_admin(message.from_user.id):
        return

    try:
        discount = int(message.text.strip())
        if discount < 1 or discount > 100:
            await message.answer("❌ Скидка должна быть от 1 до 100%.\nПопробуйте снова:")
            return

        await state.update_data(promo_discount=discount)
        await state.set_state(AdminStates.waiting_for_promo_max_uses)

        await message.answer(
            f"""✅ Скидка: {discount}%

Шаг 3/3: Введите лимит использований

• Введите число (например: 10, 100)
• Или "0" для безлимитного промокода"""
        )

    except ValueError:
        await message.answer("❌ Введите число от 1 до 100:")


@router.message(AdminStates.waiting_for_promo_max_uses)
async def process_promo_max_uses(message: Message, state: FSMContext):
    """Process promo max uses input and create promo code"""
    if not is_admin(message.from_user.id):
        return

    try:
        max_uses = int(message.text.strip())
        if max_uses < 0:
            await message.answer("❌ Введите 0 или положительное число:")
            return

        data = await state.get_data()
        code = data["promo_code"]
        discount = data["promo_discount"]

        # Create promo code
        promo_id = await create_promo_code(
            code=code,
            discount_percent=discount,
            created_by=message.from_user.id,
            max_uses=max_uses if max_uses > 0 else None
        )

        await state.clear()

        max_uses_str = str(max_uses) if max_uses > 0 else "∞ (безлимит)"

        await message.answer(
            f"""✅ ПРОМОКОД СОЗДАН!

🎁 Код: {code}
💰 Скидка: {discount}%
🔢 Лимит: {max_uses_str}

Теперь вы можете раздавать этот промокод клиентам.""",
            reply_markup=get_admin_menu_keyboard()
        )

    except ValueError:
        await message.answer("❌ Введите число:")


@router.callback_query(F.data.startswith("admin:promo_view:"))
async def callback_admin_promo_view(callback: CallbackQuery):
    """View single promo code details"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = parse_callback_data(callback.data, 3)
    if not parts:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    promo_id = safe_int(parts[2])
    if promo_id <= 0:
        await callback.answer("Неверный ID промокода", show_alert=True)
        return

    # Get promo code from all codes (we need to find by id)
    promo_codes = await get_all_promo_codes()
    promo = None
    for p in promo_codes:
        if p["id"] == promo_id:
            promo = p
            break

    if not promo:
        await callback.answer("Промокод не найден", show_alert=True)
        return

    code = promo["code"]
    discount = promo["discount_percent"]
    used_count = promo["used_count"]
    max_uses = promo.get("max_uses") or "∞"
    is_active = promo.get("is_active", True)
    created_at = promo.get("created_at", "—")

    if isinstance(created_at, str) and created_at != "—":
        try:
            dt = datetime.fromisoformat(created_at)
            created_at = dt.strftime("%d.%m.%Y %H:%M")
        except:
            pass

    status = "✅ Активен" if is_active else "❌ Деактивирован"

    # Get usage stats
    stats = await get_promo_code_stats(promo_id)
    total_discount = stats["total_discount"]

    text = f"""🎁 ПРОМОКОД: {code}

Статус: {status}
Скидка: {discount}%
Использований: {used_count}/{max_uses}
Создан: {created_at}

📊 Статистика:
Сэкономлено клиентами: {format_price(total_discount)}₽"""

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_promo_view_keyboard(promo_id, is_active)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:promo_deactivate:"))
async def callback_admin_promo_deactivate(callback: CallbackQuery):
    """Deactivate promo code"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = parse_callback_data(callback.data, 3)
    if not parts:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    promo_id = safe_int(parts[2])
    if promo_id <= 0:
        await callback.answer("Неверный ID промокода", show_alert=True)
        return

    await deactivate_promo_code(promo_id)

    await callback.answer("✅ Промокод деактивирован", show_alert=True)

    # Refresh list
    await callback_admin_promo_list(callback)


@router.message(Command("promo"))
async def cmd_promo(message: Message):
    """Quick command to create promo code"""
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "Использование: /promo <КОД> <СКИДКА%> [ЛИМИТ]\n\n"
            "Примеры:\n"
            "/promo TEST50 50 10\n"
            "/promo VIP20 20"
        )
        return

    code = parts[1].upper()
    try:
        discount = int(parts[2])
        max_uses = int(parts[3]) if len(parts) > 3 else None

        if discount < 1 or discount > 100:
            await message.answer("❌ Скидка должна быть от 1 до 100%")
            return

        # Check if exists
        existing = await get_promo_code(code)
        if existing:
            await message.answer(f"❌ Промокод {code} уже существует")
            return

        promo_id = await create_promo_code(
            code=code,
            discount_percent=discount,
            created_by=message.from_user.id,
            max_uses=max_uses
        )

        max_str = str(max_uses) if max_uses else "∞"
        await message.answer(
            f"✅ Промокод создан!\n\n"
            f"🎁 Код: {code}\n"
            f"💰 Скидка: {discount}%\n"
            f"🔢 Лимит: {max_str}"
        )

    except ValueError:
        await message.answer("❌ Неверный формат. Скидка и лимит должны быть числами.")
