"""Command handlers for the bot"""

from datetime import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import FREE_ANALYSES_LIMIT
from src.db.database import AsyncSessionLocal
from src.db.crud import get_or_create_user

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Приветствие пользователя"""
    await message.answer(
        "👋 Привет! Я бот-ассистент для анализа переписок.\n\n"
        "Отправь мне скриншот переписки из любого мессенджера, "
        "и я помогу тебе понять контекст и предложу варианты ответов.\n\n"
        "Используй /help, чтобы узнать больше."
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь по командам"""
    await message.answer(
        "📚 Доступные команды:\n\n"
        "/start - начать работу с ботом\n"
        "/help - показать эту справку\n"
        "/status - проверить статус и использование\n"
        "/subscribe - оформить премиум подписку\n\n"
        "📸 **Как использовать:**\n"
        "Просто отправь скриншот переписки из любого мессенджера "
        "(Telegram, WhatsApp, Instagram, VK и т.д.), "
        "и я проанализирую контекст и предложу варианты ответов!"
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
async def cmd_subscribe(message: Message):
    """Информация о подписке"""
    await message.answer(
        "⭐ Премиум подписка\n\n"
        "💎 199 ₽/месяц\n\n"
        "Что входит:\n"
        "✅ Безлимитные анализы переписок\n"
        "✅ Приоритетная обработка\n"
        "✅ Доступ к новым функциям\n\n"
        "🚀 Для оформления подписки свяжись с @acoustic\n\n"
        "После оплаты активация произойдёт автоматически."
    )
