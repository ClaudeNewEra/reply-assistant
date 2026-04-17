"""ElevenLabs voice cloning and TTS."""

import io
import aiohttp
from loguru import logger

from src.config import ELEVENLABS_API_KEY

BASE_URL = "https://api.elevenlabs.io/v1"
HEADERS = {"xi-api-key": ELEVENLABS_API_KEY}


async def create_voice_clone(user_id: int, audio_files: list[bytes], filenames: list[str]) -> str:
    """
    Создаёт голосовой клон на ElevenLabs из нескольких аудиофайлов.
    Возвращает voice_id.
    """
    data = aiohttp.FormData()
    data.add_field("name", f"user_{user_id}")
    data.add_field("description", f"Voice clone for Telegram user {user_id}")

    for i, (audio, fname) in enumerate(zip(audio_files, filenames)):
        data.add_field(
            "files",
            audio,
            filename=fname,
            content_type="audio/ogg",
        )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/voices/add",
            headers=HEADERS,
            data=data,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as resp:
            result = await resp.json()

    if "voice_id" not in result:
        raise Exception(f"ElevenLabs clone error: {result}")

    voice_id = result["voice_id"]
    logger.info(f"Voice clone created for user {user_id}: {voice_id}")
    return voice_id


async def delete_voice(voice_id: str) -> None:
    """Удаляет голос с ElevenLabs (при сбросе)."""
    async with aiohttp.ClientSession() as session:
        await session.delete(
            f"{BASE_URL}/voices/{voice_id}",
            headers=HEADERS,
        )


async def text_to_speech(text: str, voice_id: str) -> bytes:
    """
    Генерирует речь в голосе пользователя.
    Возвращает байты mp3.
    """
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/text-to-speech/{voice_id}",
            headers={**HEADERS, "Content-Type": "application/json"},
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"ElevenLabs TTS error {resp.status}: {error[:200]}")
            audio_bytes = await resp.read()

    logger.info(f"TTS generated: {len(audio_bytes)} bytes, voice_id={voice_id}")
    return audio_bytes
