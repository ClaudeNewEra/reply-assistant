"""Voice handler — transcribe, cache, show mode selection."""

import os
import tempfile
import aiohttp
from aiogram import Router, Bot
from aiogram.types import Message
from loguru import logger

from src.config import GROQ_API_KEY
from src.modes import build_mode_keyboard
from src.handlers.mode_callback import store_pending
from src.utils import notify_admin_error

router = Router()


async def transcribe_voice(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        audio_bytes = f.read()

    filename = os.path.basename(file_path)
    if filename.endswith('.oga'):
        filename = filename.replace('.oga', '.ogg')

    data = aiohttp.FormData()
    data.add_field('model', 'whisper-large-v3')
    data.add_field('file', audio_bytes, filename=filename, content_type='audio/ogg')

    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://api.groq.com/openai/v1/audio/transcriptions',
            headers={'Authorization': f'Bearer {GROQ_API_KEY}'},
            data=data,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            result = await resp.json()

    if 'error' in result:
        raise Exception(f"Groq STT error: {result['error'].get('message', result['error'])}")
    return result.get('text', '').strip()


@router.message(lambda m: m.voice or m.audio)
async def handle_voice(message: Message, bot: Bot):
    processing_msg = await message.answer("🎤 Распознаю голосовое...")

    voice = message.voice or message.audio
    file = await bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await bot.download_file(file.file_path, destination=tmp_path)
        text = await transcribe_voice(tmp_path)
    except Exception as e:
        logger.error(f"Ошибка распознавания голоса {message.from_user.id}: {e}")
        await notify_admin_error(bot, "handle_voice/transcribe", e, message.from_user.id)
        await processing_msg.edit_text("Не удалось распознать речь. Попробуй ещё раз или отправь текст.")
        return
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    if not text:
        await processing_msg.edit_text("Не удалось распознать речь. Попробуй ещё раз или отправь текст.")
        return

    logger.info(f"Голосовое от {message.from_user.id}: {text[:80]}...")
    store_pending(message.from_user.id, text, "voice", message.message_id)

    await processing_msg.edit_text(
        f"🎤 Распознано:\n{text}\n\nВыбери режим анализа:",
        reply_markup=build_mode_keyboard(),
    )
