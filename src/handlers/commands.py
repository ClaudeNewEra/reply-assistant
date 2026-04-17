"""Command handlers for the bot"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

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
        "/status - проверить статус бота\n\n"
        "📸 **Как использовать:**\n"
        "Просто отправь скриншот переписки из любого мессенджера "
        "(Telegram, WhatsApp, Instagram, VK и т.д.), "
        "и я проанализирую контекст и предложу варианты ответов!"
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Проверка статуса бота"""
    await message.answer(
        "✅ Бот работает нормально\n\n"
        "🔹 Статус: активен\n"
        "🔹 AI Vision: доступен\n"
        "🔹 AI Analyzer: доступен\n\n"
        "Всё готово к работе!"
    )
