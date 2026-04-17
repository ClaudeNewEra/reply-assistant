"""Vision: extract conversation text from screenshots via claude CLI"""

import asyncio
import subprocess
import tempfile
import os
from loguru import logger


async def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Извлекает текст переписки из скриншота через claude CLI.

    Args:
        image_bytes: Байты изображения

    Returns:
        Извлечённый текст в формате "Имя: текст"

    Raises:
        ValueError: Если на изображении нет переписки
    """
    # Определяем расширение по сигнатуре
    if image_bytes[:4] == b'\x89PNG':
        ext = '.png'
    elif image_bytes[:2] == b'\xff\xd8':
        ext = '.jpg'
    elif b'WEBP' in image_bytes[:12]:
        ext = '.webp'
    else:
        ext = '.jpg'

    # Сохраняем во временный файл
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    logger.info(f"Отправка изображения в claude CLI ({len(image_bytes)} байт, {tmp_path})")

    try:
        prompt = (
            f"Прочитай файл {tmp_path} — это скриншот переписки из мессенджера. "
            "Извлеки весь диалог в формате:\n"
            "Имя1: текст сообщения\n"
            "Имя2: текст сообщения\n\n"
            "Если это не скриншот переписки — верни слово NONE. "
            "Верни только диалог, без пояснений."
        )

        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ['claude', '-p', prompt, '--output-format', 'text',
                     '--dangerously-skip-permissions'],
                    capture_output=True, text=True, timeout=60
                )
            ),
            timeout=65.0
        )

        if result.returncode != 0:
            logger.error(f"claude CLI error: {result.stderr[:200]}")
            raise Exception(f"claude CLI failed: {result.stderr[:200]}")

        extracted = result.stdout.strip()
        logger.info(f"Извлечённый текст: {extracted[:100]}...")

        if extracted.upper() == "NONE" or not extracted:
            raise ValueError("На изображении не обнаружена переписка")

        return extracted

    except asyncio.TimeoutError:
        raise Exception("Timeout: claude CLI не ответил вовремя")
    except Exception as e:
        logger.error(f"Ошибка извлечения текста: {e}")
        raise
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
