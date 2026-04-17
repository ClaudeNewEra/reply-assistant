"""Payment handlers for Telegram Stars subscription"""

from aiogram import Router, Bot
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from loguru import logger

from src.db.database import AsyncSessionLocal
from src.db.crud import get_user_by_telegram_id, set_premium

router = Router()


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    """Обработка pre-checkout запроса перед оплатой"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    logger.info(f"Pre-checkout query от пользователя {pre_checkout_query.from_user.id}")


@router.message(lambda message: message.successful_payment)
async def process_successful_payment(message: Message):
    """Обработка успешной оплаты"""
    payment = message.successful_payment
    user_id = message.from_user.id

    logger.info(
        f"Успешная оплата от пользователя {user_id}: "
        f"{payment.total_amount} {payment.currency}, payload: {payment.invoice_payload}"
    )

    # Активируем премиум на 30 дней
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            await set_premium(session, user, days=30)
            await message.answer(
                "✅ Подписка активирована на 30 дней!\n\n"
                "Теперь ты можешь отправлять неограниченное количество анализов.\n"
                "Спасибо за поддержку! 💎"
            )
            logger.info(f"Премиум активирован для пользователя {user_id}")
        else:
            logger.error(f"Пользователь {user_id} не найден после оплаты")
            await message.answer(
                "❌ Произошла ошибка при активации подписки.\n"
                "Свяжись с @acoustic для решения проблемы."
            )
