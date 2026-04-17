"""Photo handler for analyzing conversation screenshots"""

from aiogram import Router, Bot
from aiogram.types import Message
from loguru import logger

from src.ai.vision import extract_text_from_image
from src.ai.analyzer import analyze_conversation

router = Router()


@router.message(lambda message: message.photo)
async def handle_photo(message: Message, bot: Bot):
    """
    Обрабатывает фото со скриншотами переписки.

    Args:
        message: Сообщение с фото
        bot: Инстанс бота для скачивания файла
    """
    try:
        # Отправляем сообщение о начале обработки
        processing_msg = await message.answer("🔍 Анализирую скриншот...")

        # Получаем самое большое фото (лучшее качество)
        photo = message.photo[-1]

        logger.info(f"Получено фото от пользователя {message.from_user.id}, file_id: {photo.file_id}")

        # Скачиваем файл
        file = await bot.get_file(photo.file_id)
        image_bytes = await bot.download_file(file.file_path)

        # Читаем байты из BytesIO объекта
        image_data = image_bytes.read()

        logger.info(f"Фото скачано, размер: {len(image_data)} байт")

        # Извлекаем текст из изображения
        try:
            conversation_text = await extract_text_from_image(image_data)
        except ValueError as e:
            # Это не скриншот переписки
            await processing_msg.edit_text(
                "❌ Не вижу переписки на этом фото.\n\n"
                "Пожалуйста, отправь скриншот переписки из мессенджера "
                "(Telegram, WhatsApp, Instagram, VK и т.д.)"
            )
            return

        logger.info("Текст успешно извлечён, отправляем на анализ")

        # Анализируем переписку
        analysis_result = await analyze_conversation(conversation_text)

        # Формируем ответ
        response = (
            "✅ Анализ завершён!\n\n"
            f"📊 **Контекст:**\n{analysis_result['analysis']}\n\n"
            f"🎭 **Рекомендуемый тон:** {analysis_result['tone']}\n\n"
            "💬 **Варианты ответов:**\n\n"
        )

        for i, suggestion in enumerate(analysis_result['suggestions'], 1):
            response += f"{i}. {suggestion}\n\n"

        await processing_msg.edit_text(response, parse_mode="Markdown")
        logger.info(f"Анализ отправлен пользователю {message.from_user.id}")

    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке изображения.\n"
            "Попробуй ещё раз или обратись в поддержку."
        )
