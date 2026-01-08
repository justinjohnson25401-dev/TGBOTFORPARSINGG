"""
Reply keyboards for the bot
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Get main reply keyboard (persistent)"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏠 Главная"),
                KeyboardButton(text="👁️ Демо"),
                KeyboardButton(text="📊 Покупки")
            ],
            [
                KeyboardButton(text="💬 Помощь"),
                KeyboardButton(text="ℹ️ О нас"),
                KeyboardButton(text="🎯 Под заказ")
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )
    return keyboard
