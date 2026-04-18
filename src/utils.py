"""Shared utilities."""

import traceback
from aiogram import Bot
from loguru import logger

from src.config import ADMIN_CHAT_ID


async def notify_admin_error(bot: Bot, context: str, error: Exception, user_id: int | None = None) -> None:
    """Send error details to admin silently."""
    if not ADMIN_CHAT_ID:
        return
    user_info = f"user_id={user_id}" if user_id else "user unknown"
    tb = traceback.format_exc()
    msg = (
        f"🔴 Ошибка бота\n"
        f"Контекст: {context}\n"
        f"{user_info}\n\n"
        f"<code>{str(error)[:300]}</code>\n\n"
        f"<code>{tb[-600:]}</code>"
    )
    try:
        await bot.send_message(ADMIN_CHAT_ID, msg, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
