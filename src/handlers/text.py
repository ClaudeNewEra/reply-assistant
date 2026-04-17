"""Text message handler for conversation analysis"""

from datetime import datetime
from aiogram import Router
from aiogram.types import Message
from loguru import logger

from src.ai.analyzer import analyze_conversation
from src.config import FREE_ANALYSES_LIMIT
from src.db.database import AsyncSessionLocal
from src.db.crud import get_or_create_user, increment_usage, create_analysis

router = Router()


@router.message(lambda message: message.text and len(message.text) >= 30)
async def handle_text(message: Message):
    """
    Обрабатывает текстовые сообщения для анализа переписки.

    Args:
        message: Текстовое сообщение от пользователя
    """
    try:
        async with AsyncSessionLocal() as session:
            # Получаем или создаём пользователя
            user = await get_or_create_user(
                session,
                telegram_id=message.from_user.id,
                username=message.from_user.username
            )

            # Проверяем актуальность премиум-подписки
            has_active_premium = user.is_premium and user.premium_until and datetime.now() < user.premium_until

            # Проверяем лимит бесплатных анализов
            if not has_active_premium and user.free_analyses_used >= FREE_ANALYSES_LIMIT:
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
            processing_msg = await message.answer("🔍 Анализирую переписку...")

            logger.info(
                f"Начат анализ текста от пользователя {user.telegram_id}, "
                f"использовано анализов: {user.free_analyses_used}/{FREE_ANALYSES_LIMIT}"
            )

            # Анализируем переписку
            analysis_result = await analyze_conversation(message.text)

            # Создаём запись об анализе
            await create_analysis(
                session,
                user=user,
                analysis_type="text",
                input_text=message.text
            )

            # Инкрементируем счётчик использованных анализов (только для не-премиум)
            if not has_active_premium:
                await increment_usage(session, user)

            # Отправляем результат
            remaining = FREE_ANALYSES_LIMIT - user.free_analyses_used - 1
            footer = ""
            if not has_active_premium and remaining > 0:
                footer = f"\n\n📊 Осталось бесплатных анализов: {remaining}"
            elif not has_active_premium and remaining == 0:
                footer = "\n\n⚠️ Это был твой последний бесплатный анализ. Используй /subscribe для продолжения."

            await processing_msg.edit_text(analysis_result + footer)

            logger.info(
                f"Анализ завершён для пользователя {user.telegram_id}, "
                f"осталось анализов: {remaining if remaining >= 0 else 0}"
            )

    except Exception as e:
        logger.error(f"Ошибка при обработке текста: {e}")
        await message.answer(
            "❌ Произошла ошибка при анализе.\n"
            "Попробуйте ещё раз или обратитесь в поддержку."
        )
