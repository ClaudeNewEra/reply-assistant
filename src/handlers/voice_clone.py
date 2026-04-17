"""Voice selection: /voice → choose preset voice → TTS on demand."""

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
)
from loguru import logger

from src.ai.voiceclone import text_to_speech
from src.db.database import AsyncSessionLocal
from src.db.crud import get_or_create_user, set_voice_id

router = Router()

# Предустановленные голоса ElevenLabs (работают на free tier)
PRESET_VOICES = {
    "roger":    ("CwhRBWXzGAHq8TQ4Fs17", "🎙 Роджер — спокойный мужской"),
    "george":   ("JBFqnCBsd6RMkjVDRZzb", "🎙 Джордж — тёплый мужской"),
    "liam":     ("TX3LPaxmHKxFdv7VOQHJ", "🎙 Лиам — энергичный мужской"),
    "sarah":    ("EXAVITQu4vr4xnSDxMaL", "🎙 Сара — уверенный женский"),
    "jessica":  ("cgSgspJ2msm6clMCkdW9", "🎙 Джессика — игривый женский"),
    "alice":    ("Xb7hH8MSUJpSbSDYk0k2", "🎙 Элис — чёткий женский"),
    "river":    ("SAz9YHcvj6GT2YYXdXww", "🎙 Ривер — нейтральный"),
}


def _voice_selection_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for key, (_, label) in PRESET_VOICES.items():
        rows.append([InlineKeyboardButton(text=label, callback_data=f"setvoice:{key}")])
    rows.append([InlineKeyboardButton(text="❌ Отключить голосовой", callback_data="setvoice:off")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("voice"))
async def cmd_voice(message: Message):
    """Выбор голоса для озвучки ответов."""
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session, telegram_id=message.from_user.id, username=message.from_user.username
        )
        current = user.elevenlabs_voice_id

    # Найти текущий голос в пресетах
    current_name = next(
        (label for key, (vid, label) in PRESET_VOICES.items() if vid == current),
        None
    )

    header = f"Текущий голос: {current_name}\n\n" if current_name else ""
    await message.answer(
        f"🎤 Выбери голос для озвучки ответов\n\n"
        f"{header}"
        "После выбора кнопка «🎤 Отправить голосом» появится после каждого анализа.",
        reply_markup=_voice_selection_keyboard(),
    )


@router.callback_query(F.data.startswith("setvoice:"))
async def on_set_voice(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session, telegram_id=callback.from_user.id, username=callback.from_user.username
        )

        if key == "off":
            await set_voice_id(session, user, None)
            await callback.message.edit_text("Голосовая озвучка отключена.")
            await callback.answer()
            return

        voice_data = PRESET_VOICES.get(key)
        if not voice_data:
            await callback.answer("Неизвестный голос")
            return

        voice_id, label = voice_data
        await set_voice_id(session, user, voice_id)

    await callback.message.edit_text(
        f"✅ Голос выбран: {label}\n\n"
        "Теперь после анализа будет кнопка «🎤 Отправить голосом»."
    )
    await callback.answer()
    logger.info(f"User {callback.from_user.id} selected voice: {key} ({voice_id})")
