"""Text message handler — cache content, show mode selection."""

from aiogram import Router
from aiogram.types import Message
from loguru import logger

from src.modes import build_mode_keyboard
from src.handlers.mode_callback import store_pending, MAX_TEXT_LENGTH

router = Router()


@router.message(lambda message: message.text and len(message.text) < 30)
async def handle_short_text(message: Message):
    await message.answer(
        "Пришли больше текста, мне нужен контекст 🤔\n\n"
        "Скопируй несколько сообщений из переписки или отправь скриншот."
    )


@router.message(lambda message: message.text and len(message.text) >= 30)
async def handle_text(message: Message):
    text = message.text

    if len(text) > MAX_TEXT_LENGTH:
        await message.answer(
            f"✂️ Текст слишком длинный ({len(text)} символов).\n\n"
            f"Максимум — {MAX_TEXT_LENGTH} символов. Скопируй самую важную часть переписки."
        )
        return

    store_pending(message.from_user.id, text, "text", message.message_id)

    msg = await message.answer(
        "Выбери режим анализа:",
        reply_markup=build_mode_keyboard(),
    )
    logger.info(f"Текст от {message.from_user.id} закеширован, ожидание выбора режима")
