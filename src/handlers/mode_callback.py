"""Mode selection callback handler."""

import re
from aiogram import Router
from aiogram.types import CallbackQuery, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger

from src.ai.analyzer import analyze_conversation
from src.ai.voiceclone import text_to_speech
from src.config import FREE_ANALYSES_LIMIT
from src.db.database import AsyncSessionLocal
from src.db.crud import get_or_create_user, increment_usage, decrement_credits, create_analysis
from src.modes import MODES

router = Router()

# last analysis text per user for voice reply
_last_analysis: dict[int, str] = {}

MAX_TEXT_LENGTH = 1500  # символов

_pending: dict[int, dict] = {}


def store_pending(user_id: int, text: str, content_type: str, msg_id: int):
    _pending[user_id] = {"text": text, "type": content_type, "msg_id": msg_id}


def pop_pending(user_id: int) -> dict | None:
    return _pending.pop(user_id, None)


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_analysis_html(text: str) -> str:
    """
    Конвертирует plain-text анализ в HTML для Telegram.
    Варианты ответа (строки вида '1. "..."') оборачивает в <code> для копирования по нажатию.
    """
    lines = text.split("\n")
    result = []
    for line in lines:
        # Нумерованный вариант: '1. "текст"' или '1. текст'
        m = re.match(r'^(\d+)\.\s*"?(.+?)"?\s*$', line)
        if m:
            num = m.group(1)
            content = _escape_html(m.group(2))
            result.append(f"{num}. <code>{content}</code>")
        else:
            result.append(_escape_html(line))
    return "\n".join(result)


def _extract_variants(analysis: str) -> list[str]:
    """Извлекает чистые тексты вариантов ответа из анализа."""
    variants = []
    for line in analysis.splitlines():
        m = re.match(r'^\d+\.\s*"?(.+?)"?\s*$', line.strip())
        if m:
            variants.append(m.group(1).strip())
    return variants


def _build_voice_keyboard(n_variants: int) -> InlineKeyboardMarkup:
    """Клавиатура: одна строка с кнопкой на каждый вариант."""
    buttons = [
        InlineKeyboardButton(text=f"🎤 {i}", callback_data=f"voice:v:{i}")
        for i in range(1, n_variants + 1)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


@router.callback_query(lambda c: c.data and c.data.startswith("mode:"))
async def on_mode_selected(callback: CallbackQuery):
    mode_key = callback.data.split(":", 1)[1]
    mode = MODES.get(mode_key)
    if not mode:
        await callback.answer("Неизвестный режим")
        return

    pending = pop_pending(callback.from_user.id)
    if not pending:
        await callback.answer("Сессия истекла, отправь сообщение заново")
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    await callback.answer(f"Режим: {mode['label']}")
    await callback.message.edit_text(f"🔍 Анализирую [{mode['label']}]...")

    try:
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(
                session,
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
            )

            within_free = user.free_analyses_used < FREE_ANALYSES_LIMIT
            has_credits = user.credits > 0

            # Определяем доступ и тип списания
            if within_free:
                billing = "free"
            elif has_credits:
                billing = "credits"
            else:
                await callback.message.edit_text(
                    "🔒 Анализы закончились\n\n"
                    "Купи пакет анализов:\n"
                    "👉 /buy"
                )
                return

            text = pending["text"]
            # Обрезаем до лимита
            was_truncated = len(text) > MAX_TEXT_LENGTH
            text = text[:MAX_TEXT_LENGTH]

            analysis_result = await analyze_conversation(
                text,
                mode_prompt=mode["prompt_addon"],
                variant_instructions=mode.get("variants", ""),
            )

            await create_analysis(
                session,
                user=user,
                analysis_type=pending["type"],
                input_text=text[:500],
            )

            # Списываем в зависимости от типа
            if billing == "free":
                await increment_usage(session, user)
                remaining_free = FREE_ANALYSES_LIMIT - user.free_analyses_used
                if remaining_free > 0:
                    footer = f"\n\n📊 Осталось бесплатных: {remaining_free}"
                else:
                    footer = "\n\n⚠️ Бесплатные закончились. Купи пакет: /buy"
            else:  # credits
                await decrement_credits(session, user)
                footer = f"\n\n💳 Осталось анализов: {user.credits}"

            if was_truncated:
                footer = f"\n\n✂️ Текст обрезан до {MAX_TEXT_LENGTH} символов" + footer

            # Сохраняем для возможного голосового ответа
            _last_analysis[callback.from_user.id] = analysis_result

            formatted = format_analysis_html(analysis_result + footer)

            # Если у юзера есть голос — кнопки для каждого варианта
            voice_kb = None
            if user.elevenlabs_voice_id:
                variants = _extract_variants(analysis_result)
                if variants:
                    voice_kb = _build_voice_keyboard(len(variants))

            await callback.message.edit_text(formatted, parse_mode="HTML", reply_markup=voice_kb)

    except Exception as e:
        logger.error(f"Ошибка при анализе с режимом {mode_key}: {e}")
        await callback.message.edit_text("Что-то пошло не так 🔄")


@router.callback_query(lambda c: c.data and c.data.startswith("voice:v:"))
async def on_voice_variant(callback: CallbackQuery):
    """Генерирует TTS конкретного варианта ответа."""
    user_id = callback.from_user.id
    try:
        variant_num = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer("Неверный вариант", show_alert=True)
        return

    analysis = _last_analysis.get(user_id)
    if not analysis:
        await callback.answer("Сессия истекла, сделай анализ заново", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, telegram_id=user_id, username=callback.from_user.username)
        voice_id = user.elevenlabs_voice_id

    if not voice_id:
        await callback.answer("Нет голоса. Используй /voice", show_alert=True)
        return

    variants = _extract_variants(analysis)
    if variant_num < 1 or variant_num > len(variants):
        await callback.answer("Вариант не найден", show_alert=True)
        return

    clean_text = variants[variant_num - 1][:500]
    await callback.answer(f"🎤 Генерирую вариант {variant_num}...")

    try:
        audio_bytes = await text_to_speech(clean_text, voice_id)
        await callback.message.answer_voice(
            BufferedInputFile(audio_bytes, filename=f"variant_{variant_num}.mp3"),
            caption=f"🎤 Вариант {variant_num}"
        )
    except Exception as e:
        logger.error(f"TTS failed for {user_id} variant {variant_num}: {e}")
        await callback.message.answer(f"❌ Ошибка генерации: {str(e)[:150]}")
