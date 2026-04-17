"""Vision module for extracting text from conversation screenshots"""

import base64
import anthropic
from loguru import logger

from src.config import ANTHROPIC_API_KEY


async def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Извлекает текст переписки из скриншота.

    Args:
        image_bytes: Байты изображения

    Returns:
        Извлечённый текст в формате "Имя: текст" или пустая строка, если переписка не найдена

    Raises:
        ValueError: Если на изображении нет переписки
    """
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Кодируем изображение в base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        # Определяем тип изображения (простая эвристика по первым байтам)
        if image_bytes.startswith(b'\x89PNG'):
            media_type = "image/png"
        elif image_bytes.startswith(b'\xff\xd8\xff'):
            media_type = "image/jpeg"
        elif image_bytes.startswith(b'WEBP'):
            media_type = "image/webp"
        else:
            # По умолчанию предполагаем JPEG
            media_type = "image/jpeg"

        logger.info(f"Отправка изображения в Claude Vision (размер: {len(image_bytes)} байт)")

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Извлеки текст переписки из этого скриншота. "
                                "Верни только диалог в формате:\n"
                                "Имя1: текст сообщения\n"
                                "Имя2: текст сообщения\n\n"
                                "Если это не скриншот переписки (мессенджера), верни слово NONE."
                            )
                        }
                    ],
                }
            ],
        )

        extracted_text = message.content[0].text.strip()

        logger.info(f"Извлечённый текст: {extracted_text[:100]}...")

        # Проверяем, является ли это скриншотом переписки
        if extracted_text == "NONE" or not extracted_text:
            raise ValueError("На изображении не обнаружена переписка")

        return extracted_text

    except anthropic.APIError as e:
        logger.error(f"Ошибка API Claude: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при извлечении текста из изображения: {e}")
        raise
