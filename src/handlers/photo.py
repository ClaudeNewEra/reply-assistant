"""Photo handler — extract text, cache, show mode selection."""

from aiogram import Router, Bot
from aiogram.types import Message
from loguru import logger

from src.ai.vision import extract_text_from_image
from src.modes import build_mode_keyboard
from src.handlers.mode_callback import store_pending

router = Router()


@router.message(lambda message: message.photo)
async def handle_photo(message: Message, bot: Bot):
    processing_msg = await message.answer("🔍 Читаю скриншот...")

    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        image_bytes = await bot.download_file(file.file_path)
        image_data = image_bytes.read()

        conversation_text = await extract_text_from_image(image_data)

        store_pending(message.from_user.id, conversation_text, "image", message.message_id)

        await processing_msg.edit_text(
            "📸 Переписка распознана. Выбери режим анализа:",
            reply_markup=build_mode_keyboard(),
        )
        logger.info(f"Скриншот от {message.from_user.id} обработан, ожидание режима")

    except ValueError:
        await processing_msg.edit_text(
            "❌ Не вижу переписки на этом фото.\n\n"
            "Отправь скриншот переписки из мессенджера (Telegram, WhatsApp, Instagram и т.д.)"
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}")
        await processing_msg.edit_text("Что-то пошло не так 🔄")
