"""Photo handler for analyzing conversation screenshots"""

from aiogram import Router, Bot
from aiogram.types import Message
from loguru import logger

from src.ai.vision import extract_text_from_image
from src.ai.analyzer import analyze_conversation
from src.config import FREE_ANALYSES_LIMIT
from src.db.database import AsyncSessionLocal
from src.db.crud import get_or_create_user, increment_usage, create_analysis

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
        async with AsyncSessionLocal() as session:
            # Получаем или создаём пользователя
            user = await get_or_create_user(
                session,
                telegram_id=message.from_user.id,
                username=message.from_user.username
            )

            # Проверяем лимит бесплатных анализов
            if not user.is_premium and user.free_analyses_used >= FREE_ANALYSES_LIMIT:
                await message.answer(
                    "🔒 Бесплатные анализы закончились\n\n"
                    f"Ты использовал(а) {FREE_ANALYSES_LIMIT} бесплатных анализа.\n\n"
                    "Чтобы продолжить — оформи подписку:\n"
                    "⭐ 199 ₽/месяц — безлимитные анализы\n\n"
                    "👉 /subscribe — оформить подписку"
                )
                logger.info(
                    f"Пользователь {user.telegram_id} исчерпал лимит "
                    f"({user.free_analyses_used}/{FREE_ANALYSES_LIMIT})"
                )
                return

            # Отправляем сообщение о начале обработки
            processing_msg = await message.answer("🔍 Анализирую скриншот...")

            # Получаем самое большое фото (лучшее качество)
            photo = message.photo[-1]

            logger.info(
                f"Получено фото от пользователя {user.telegram_id}, "
                f"использовано анализов: {user.free_analyses_used}/{FREE_ANALYSES_LIMIT}"
            )

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

            # Создаём запись об анализе
            await create_analysis(
                session,
                user=user,
                analysis_type="image",
                input_text="[фото переписки]"
            )

            # Инкрементируем счётчик использованных анализов
            await increment_usage(session, user)

            # Отправляем результат
            remaining = FREE_ANALYSES_LIMIT - user.free_analyses_used - 1
            footer = ""
            if not user.is_premium and remaining > 0:
                footer = f"\n\n📊 Осталось бесплатных анализов: {remaining}"
            elif not user.is_premium and remaining == 0:
                footer = "\n\n⚠️ Это был твой последний бесплатный анализ. Используй /subscribe для продолжения."

            await processing_msg.edit_text(analysis_result + footer)

            logger.info(
                f"Анализ завершён для пользователя {user.telegram_id}, "
                f"осталось анализов: {remaining if remaining >= 0 else 0}"
            )

    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке изображения.\n"
            "Попробуй ещё раз или обратись в поддержку."
        )
