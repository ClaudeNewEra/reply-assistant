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


def is_question_to_bot(text: str) -> bool:
    """
    Определяет, является ли текст вопросом к боту, а не перепиской.

    Args:
        text: Текст сообщения

    Returns:
        True если это вопрос к боту
    """
    question_indicators = [
        "как тебя зовут",
        "что ты умеешь",
        "кто ты",
        "что делать",
        "помоги",
        "как работа",
        "объясни",
        "расскажи",
        "?",  # Одиночные вопросы без переписки
    ]

    # Если текст короткий и содержит вопросительный знак
    if len(text) < 100 and "?" in text:
        return True

    # Если текст не содержит признаков переписки (двоеточия, имен)
    if ":" not in text and len(text) < 150:
        for indicator in question_indicators:
            if indicator in text.lower():
                return True

    return False


@router.message(lambda message: message.text and len(message.text) < 30)
async def handle_short_text(message: Message):
    """Обработка слишком коротких сообщений"""
    await message.answer(
        "Пришли больше текста, мне нужен контекст 🤔\n\n"
        "Скопируй несколько сообщений из переписки или отправь скриншот."
    )


@router.message(lambda message: message.text and len(message.text) >= 30)
async def handle_text(message: Message):
    """
    Обрабатывает текстовые сообщения для анализа переписки.

    Args:
        message: Текстовое сообщение от пользователя
    """
    try:
        # Проверяем, не является ли это вопросом к боту
        if is_question_to_bot(message.text):
            await message.answer(
                "Я анализирую переписки, а не отвечаю на вопросы 😊\n\n"
                "Отправь мне текст диалога или скриншот чата, и я помогу разобраться в ситуации.\n\n"
                "Используй /help, чтобы узнать как работать со мной."
            )
            return

        # Обрезаем слишком длинный текст
        original_text = message.text
        was_truncated = False
        if len(original_text) > 4000:
            original_text = original_text[:4000]
            was_truncated = True

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
            status_text = "🔍 Анализирую переписку..."
            if was_truncated:
                status_text += "\n\n⚠️ Текст слишком длинный, анализирую первые 4000 символов"
            processing_msg = await message.answer(status_text)

            logger.info(
                f"Начат анализ текста от пользователя {user.telegram_id}, "
                f"использовано анализов: {user.free_analyses_used}/{FREE_ANALYSES_LIMIT}"
            )

            # Анализируем переписку
            analysis_result = await analyze_conversation(original_text)

            # Создаём запись об анализе
            await create_analysis(
                session,
                user=user,
                analysis_type="text",
                input_text=original_text[:500]  # Сохраняем только первые 500 символов
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

        # Определяем тип ошибки для более информативного сообщения
        error_message = "Что-то пошло не так, попробуй ещё раз 🔄"

        # Проверяем тип ошибки
        error_str = str(e).lower()
        if "timeout" in error_str or "timed out" in error_str:
            error_message = "⏱️ Превышено время ожидания. Попробуй ещё раз или отправь более короткий текст."
        elif "rate limit" in error_str or "429" in error_str:
            error_message = "⚠️ Слишком много запросов. Подожди минуту и попробуй снова."
        elif "api" in error_str or "connection" in error_str:
            error_message = "🔌 Проблема с подключением. Попробуй через минуту."

        await message.answer(error_message)
