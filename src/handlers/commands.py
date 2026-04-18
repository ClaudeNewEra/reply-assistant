"""Command handlers for the bot"""

from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, LabeledPrice
from loguru import logger

from src.config import FREE_ANALYSES_LIMIT, ADMIN_CHAT_ID
from src.db.database import AsyncSessionLocal
from src.db.crud import get_or_create_user

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        is_new = user.free_analyses_used == 0 and user.credits == 0
        remaining = max(0, FREE_ANALYSES_LIMIT - user.free_analyses_used)
        credits = user.credits

    if is_new and ADMIN_CHAT_ID:
        uname = f"@{message.from_user.username}" if message.from_user.username else "без username"
        name = message.from_user.full_name or "Без имени"
        try:
            await bot.send_message(
                ADMIN_CHAT_ID,
                f"👤 Новый пользователь!\n{name} ({uname})\nID: {message.from_user.id}"
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление: {e}")

    if credits > 0:
        footer = f"У тебя {credits} анализов в запасе."
    elif remaining > 0:
        footer = f"{remaining} анализа бесплатно. Поехали! 🚀"
    else:
        footer = "Бесплатные анализы закончились. /buy — купи пакет."

    await message.answer(
        "🧠 МозгПереписки — AI читает между строк и пишет ответы за тебя.\n\n"
        "Скинь мне:\n"
        "📝 Текст переписки — скопируй диалог\n"
        "📸 Скриншот чата — любой мессенджер\n"
        "🎤 Голосовое — надиктуй\n\n"
        "Получишь:\n"
        "• Что человек реально имел в виду\n"
        "• Его тон и настроение\n"
        "• 5 готовых вариантов ответа — флирт, юмор, дружба, дело\n\n"
        + footer
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🧠 МозгПереписки — как пользоваться\n\n"
        "1. Отправь переписку — текст, скрин или голосовое\n"
        "2. Выбери режим: флирт, юмор, дружба, любовь, деловой\n"
        "3. Получи анализ + 5 готовых ответов\n"
        "4. Нажми на ответ — он скопируется. Или озвучь голосом 🎤\n\n"
        "Команды:\n"
        "/status — сколько анализов осталось\n"
        "/buy — купить пакет анализов\n"
        "/voice — выбрать голос для озвучки"
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
        remaining_free = max(0, FREE_ANALYSES_LIMIT - user.free_analyses_used)
        credits = user.credits
        has_voice = bool(user.elevenlabs_voice_id)

    parts = ["📊 Твой статус\n"]
    if remaining_free > 0:
        parts.append(f"Бесплатных анализов: {remaining_free} из {FREE_ANALYSES_LIMIT}")
    else:
        parts.append("Бесплатные анализы: использованы")
    parts.append(f"Купленных анализов: {credits}")
    parts.append(f"Голос для озвучки: {'✅ выбран (/voice)' if has_voice else '❌ не выбран (/voice)'}")

    if remaining_free == 0 and credits == 0:
        parts.append("\nКупи пакет → /buy")

    await message.answer("\n".join(parts))


@router.message(Command("buy"))
async def cmd_buy(message: Message, bot: Bot):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
        credits = user.credits

    await message.answer(
        f"💳 Купи пакет анализов\n\n"
        f"Сейчас у тебя: {credits} анализов\n\n"
        f"Выбери пакет:"
    )

    packs = [
        ("pack_10",  "10 анализов",  50,  "Попробовать"),
        ("pack_30",  "30 анализов", 100,  "Популярный"),
        ("pack_100", "100 анализов", 250, "Выгодный"),
    ]
    for payload, label, stars, hint in packs:
        await bot.send_invoice(
            chat_id=message.chat.id,
            title=f"{label} — {hint}",
            description="МозгПереписки — AI анализы переписки с выбором режима",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label=label, amount=stars)]
        )


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    await message.answer("/buy — купи пакет анализов")
