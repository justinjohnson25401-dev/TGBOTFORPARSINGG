"""
Custom order handlers
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database.models import (
    get_or_create_user,
    create_custom_request,
    get_user
)
from bot.keyboards.inline import (
    get_custom_order_keyboard,
    get_custom_order_sent_keyboard
)
from bot.keyboards.reply import get_main_reply_keyboard
from bot.config import ADMIN_IDS

router = Router()
logger = logging.getLogger(__name__)


class CustomOrderStates(StatesGroup):
    """States for custom order flow"""
    waiting_for_request = State()


CUSTOM_ORDER_TEXT = """🎯 БАЗЫ ПОД ЗАКАЗ

Соберём базу по вашим параметрам!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏙️ Любой город РФ (250+ городов)
🎨 Любая категория из 2ГИС

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Условия:
Цена: обычная + 25%
Срок: 1 рабочий день
Минимум: 500 контактов

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Напишите что нужно:

Пример: "Стоматологии Казань, 1500 шт\""""


@router.message(F.text == "🎯 Под заказ")
async def btn_custom_order(message: Message, state: FSMContext):
    """Handle custom order button"""
    await state.set_state(CustomOrderStates.waiting_for_request)

    await message.answer(CUSTOM_ORDER_TEXT, reply_markup=get_custom_order_keyboard())


@router.callback_query(F.data == "custom_order")
async def callback_custom_order(callback: CallbackQuery, state: FSMContext):
    """Handle custom order callback"""
    await state.set_state(CustomOrderStates.waiting_for_request)

    await callback.message.edit_text(
        CUSTOM_ORDER_TEXT,
        reply_markup=get_custom_order_keyboard()
    )
    await callback.answer()


@router.message(CustomOrderStates.waiting_for_request)
async def process_custom_order(message: Message, state: FSMContext, bot: Bot):
    """Process custom order request"""
    user_id = message.from_user.id
    request_text = message.text

    # Skip if it's a menu button
    if request_text in ["🏠 Главная", "👁️ Демо", "📊 Покупки",
                        "💬 Помощь", "ℹ️ О нас", "🎯 Под заказ"]:
        await state.clear()
        return

    # Ensure user exists
    await get_or_create_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    # Save request
    request_id = await create_custom_request(user_id, request_text)

    # Clear state
    await state.clear()

    # Notify user
    success_text = f"""✅ ЗАЯВКА ПРИНЯТА!

📝 Ваш запрос:
{request_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️ Мы свяжемся с вами в течение часа
📱 Ответим в этот чат

Номер заявки: #{request_id}"""

    await message.answer(success_text, reply_markup=get_custom_order_sent_keyboard())

    # Notify admins
    user = await get_user(user_id)
    username = user.get("username", "—") if user else "—"
    first_name = user.get("first_name", "—") if user else "—"

    admin_text = f"""🆕 НОВАЯ ЗАЯВКА #{request_id}

👤 Пользователь: {first_name} (@{username})
🆔 ID: {user_id}

📝 Запрос:
{request_text}"""

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
