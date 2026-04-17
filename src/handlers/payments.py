"""Payment handlers — credit packs via Telegram Stars"""

from aiogram import Router, Bot
from aiogram.types import Message, PreCheckoutQuery
from loguru import logger

from src.db.database import AsyncSessionLocal
from src.db.crud import get_or_create_user, add_credits

router = Router()

# Пакеты: payload → (кол-во анализов, Stars)
CREDIT_PACKS = {
    "pack_10": {"credits": 10, "stars": 50,  "label": "10 анализов"},
    "pack_30": {"credits": 30, "stars": 100, "label": "30 анализов"},
    "pack_100": {"credits": 100, "stars": 250, "label": "100 анализов"},
}


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    logger.info(f"Pre-checkout от {pre_checkout_query.from_user.id}, payload: {pre_checkout_query.invoice_payload}")


@router.message(lambda m: m.successful_payment)
async def process_successful_payment(message: Message):
    payment = message.successful_payment
    payload = payment.invoice_payload
    user_id = message.from_user.id

    logger.info(f"Оплата от {user_id}: {payment.total_amount} XTR, payload={payload}")

    pack = CREDIT_PACKS.get(payload)
    if not pack:
        logger.error(f"Неизвестный payload: {payload}")
        await message.answer("Ошибка активации. Напиши @acoustic")
        return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, telegram_id=user_id, username=message.from_user.username)
        await add_credits(session, user, pack["credits"])

        await message.answer(
            f"✅ Куплено {pack['credits']} анализов!\n\n"
            f"Осталось анализов: {user.credits}\n\n"
            f"Отправь переписку и выбери режим."
        )
