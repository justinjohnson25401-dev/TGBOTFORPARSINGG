"""
Demo file handler
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from bot.services.file_generator import get_demo_file
from bot.keyboards.inline import get_demo_keyboard
from bot.keyboards.reply import get_main_reply_keyboard

router = Router()

DEMO_TEXT = """📊 ПРИМЕР БАЗЫ ДАННЫХ

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ В демо: телефоны скрыты (+79999999999)

✅ В полной версии — все данные настоящие"""


@router.message(F.text == "👁️ Демо")
async def btn_demo(message: Message):
    """Handle Demo button"""
    # Get or generate demo file
    result = get_demo_file()

    if result:
        filename, file_bytes = result
        document = BufferedInputFile(file_bytes, filename=filename)

        await message.answer_document(
            document,
            caption=DEMO_TEXT,
            reply_markup=get_demo_keyboard()
        )
    else:
        await message.answer(
            "⚠️ Не удалось загрузить демо-файл. Попробуйте позже.",
            reply_markup=get_main_reply_keyboard()
        )


@router.callback_query(F.data == "demo")
async def callback_demo(callback: CallbackQuery):
    """Handle demo callback from inline button"""
    result = get_demo_file()

    if result:
        filename, file_bytes = result
        document = BufferedInputFile(file_bytes, filename=filename)

        # Send as new message (can't edit to document)
        await callback.message.answer_document(
            document,
            caption=DEMO_TEXT,
            reply_markup=get_demo_keyboard()
        )
        await callback.answer()
    else:
        await callback.answer("Не удалось загрузить демо-файл", show_alert=True)


@router.callback_query(F.data.startswith("demo:"))
async def callback_demo_from_category(callback: CallbackQuery):
    """Handle demo callback from category page"""
    parts = callback.data.split(":")
    city = parts[1] if len(parts) > 1 else None
    category = parts[2] if len(parts) > 2 else None

    result = get_demo_file()

    if result:
        filename, file_bytes = result
        document = BufferedInputFile(file_bytes, filename=filename)

        await callback.message.answer_document(
            document,
            caption=DEMO_TEXT,
            reply_markup=get_demo_keyboard(city, category)
        )
        await callback.answer()
    else:
        await callback.answer("Не удалось загрузить демо-файл", show_alert=True)
