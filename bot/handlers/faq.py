"""
FAQ and About handlers
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import (
    get_faq_keyboard,
    get_faq_answer_keyboard,
    get_about_keyboard
)
from bot.keyboards.reply import get_main_reply_keyboard

router = Router()

# FAQ answers
FAQ_ANSWERS = {
    "other_city": """🏙️ МОЖНО ЛИ КУПИТЬ ДРУГОЙ ГОРОД?

Да! Мы можем собрать базу по любому городу РФ.

📍 Доступно 250+ городов
💰 Цена: стандартная + 25%
⏱️ Срок: 1 рабочий день

Нажмите "🎯 Под заказ" в главном меню и напишите какой город вам нужен.""",

    "duplicates": """🔄 БУДУТ ЛИ ДУБЛИ ПРИ ДОКУПКЕ?

Нет! Наша система отслеживает ваши покупки.

✅ Каждый раз вы получаете НОВЫЕ контакты
✅ Без пересечений с предыдущими файлами
✅ Pack 1 → Pack 2 → Pack 3 — всегда уникальные данные

Это работает автоматически для каждой категории.""",

    "telegram": """💬 ПОЧЕМУ У ВСЕХ TELEGRAM?

Мы используем уникальную технологию парсинга!

📱 Собираем только мобильные номера (+79...)
🔍 Проверяем каждый номер через Telegram API
✅ В базу попадают только номера с Telegram

Это значит вы можете писать напрямую в Telegram!""",

    "updates": """🔄 КАК ЧАСТО ОБНОВЛЯЮТСЯ БАЗЫ?

Базы обновляются регулярно:

📅 Новые компании добавляются еженедельно
🆕 Сортировка по дате регистрации
📊 Вы получаете самые свежие контакты

Дата последнего обновления указана на странице категории.""",

    "refund": """💰 МОЖНО ЛИ ВЕРНУТЬ ДЕНЬГИ?

⚠️ Возврат невозможен после скачивания файла.

Это цифровой товар — после получения файла
возврат не предусмотрен.

✅ Но мы гарантируем:
• Замену файла если не открывается
• Техподдержку 24/7
• Качество данных""",

    "format": """📄 В КАКОМ ФОРМАТЕ ФАЙЛ?

Вы получаете Excel-файл (.xlsx)

📊 Колонки:
• Название компании
• Телефон (+79...)
• Telegram username
• VK, WhatsApp, Email (если есть)
• Адрес, координаты
• Рейтинг, отзывы

Открывается в Excel, Google Sheets, Numbers и любых
табличных редакторах.""",

    "legal": """⚖️ ЛЕГАЛЬНО ЛИ ЭТО?

Да, в рамках нормальной коммерческой практики.

✅ Используются только открытые контакты компаний
✅ Данные из общедоступных источников
✅ Никаких украденных или «слитых» персональных данных

По сути, вы покупаете готовый, аккуратно собранный
список того, что и так можно найти вручную —
просто намного быстрее."""
}


@router.message(F.text == "💬 Помощь")
async def btn_help(message: Message):
    """Handle Help button"""
    text = """❓ ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ

Выберите интересующий вопрос:"""

    await message.answer(text, reply_markup=get_faq_keyboard())


@router.callback_query(F.data == "faq")
async def callback_faq(callback: CallbackQuery):
    """Handle FAQ callback"""
    text = """❓ ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ

Выберите интересующий вопрос:"""

    await callback.message.edit_text(text, reply_markup=get_faq_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("faq:"))
async def callback_faq_answer(callback: CallbackQuery):
    """Handle FAQ answer callback"""
    faq_key = callback.data.split(":")[1]

    answer = FAQ_ANSWERS.get(faq_key, "Ответ не найден")

    await callback.message.edit_text(answer, reply_markup=get_faq_answer_keyboard())
    await callback.answer()


@router.message(F.text == "ℹ️ О нас")
async def btn_about(message: Message):
    """Handle About button"""
    text = """ℹ️ О НАС

💎 Сервис продажи готовых баз данных компаний
из открытых справочников и каталогов.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 НАШИ ПРЕИМУЩЕСТВА:

✅ Только мобильные номера (+79...)
✅ Telegram у каждого контакта (100%)
✅ Без дублей при докупке
✅ Моментальная выдача (5 секунд)
✅ Свежие данные (обновление еженедельно)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 СТАТИСТИКА:

🏙️ 250+ городов РФ
📁 50+ категорий бизнеса
👥 1 000 000+ контактов в базе
⭐ 500+ довольных клиентов

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 Поддержка: @support
📧 Email: info@example.com"""

    await message.answer(text, reply_markup=get_about_keyboard())
