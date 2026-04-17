"""Command handlers for the bot"""

from datetime import datetime
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, LabeledPrice

from src.config import FREE_ANALYSES_LIMIT
from src.db.database import AsyncSessionLocal
from src.db.crud import get_or_create_user

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Приветствие пользователя"""
    await message.answer(
        "👋 Привет! Я помогу разобраться в любой переписке.\n\n"
        "Отправь мне:\n"
        "📝 Текст переписки — просто скопируй диалог\n"
        "📸 Скриншот — сделай скрин чата\n\n"
        "Я скажу:\n"
        "• Что человек имел в виду\n"
        "• Какой у него тон и настроение\n"
        "• Как лучше ответить (5 вариантов)\n\n"
        "3 анализа бесплатно. Поехали! 🚀"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь по командам"""
    await message.answer(
        "📖 Как пользоваться ботом\n\n"
        "Есть два способа:\n\n"
        "1️⃣ **Скопируй текст переписки**\n"
        "Выдели сообщения в чате, нажми «Копировать» и отправь мне.\n"
        "Пример:\n"
        "```\n"
        "Аня: Привет, как дела?\n"
        "Я: Нормально\n"
        "Аня: Ты чего такой?\n"
        "```\n\n"
        "2️⃣ **Отправь скриншот**\n"
        "Сделай скрин переписки из любого мессенджера (Telegram, WhatsApp, VK) и пришли мне.\n\n"
        "💡 Я проанализирую тон, объясню что человек имел в виду и предложу 5 вариантов ответа.\n\n"
        "⚙️ Команды:\n"
        "/status — сколько анализов осталось\n"
        "/subscribe — безлимитный доступ"
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Проверка статуса и использования анализов"""
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )

        # Формируем информацию об использовании
        usage_info = f"Использовано {user.free_analyses_used} из {FREE_ANALYSES_LIMIT} бесплатных анализов"

        # Формируем информацию о подписке
        if user.is_premium and user.premium_until:
            # Проверяем актуальность подписки
            if user.premium_until > datetime.now():
                premium_date = user.premium_until.strftime("%d.%m.%Y")
                subscription_info = f"Подписка активна до {premium_date}"
            else:
                subscription_info = "Подписка не активна"
        else:
            subscription_info = "Подписка не активна"

        await message.answer(
            f"📊 Твой статус\n\n"
            f"🔹 {usage_info}\n"
            f"🔹 {subscription_info}\n\n"
            f"{'✅ Всё готово к работе!' if user.is_premium or user.free_analyses_used < FREE_ANALYSES_LIMIT else '⚠️ Лимит исчерпан. Используй /subscribe'}"
        )


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message, bot: Bot):
    """Оформление подписки через Telegram Stars"""
    await bot.send_invoice(
        chat_id=message.chat.id,
        title='Подписка Reply Assistant',
        description='Безлимитные AI-анализы переписки на 30 дней',
        payload='premium_30d',
        currency='XTR',  # Telegram Stars
        prices=[LabeledPrice(label='30 дней', amount=100)]  # 100 Stars
    )
