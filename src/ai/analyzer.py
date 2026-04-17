"""Conversation analysis module"""

import anthropic
from loguru import logger

from src.config import ANTHROPIC_API_KEY


async def analyze_conversation(conversation_text: str) -> dict:
    """
    Анализирует текст переписки и предлагает варианты ответов.

    Args:
        conversation_text: Текст переписки в формате "Имя: текст"

    Returns:
        dict с ключами:
            - analysis: str - анализ контекста и тона
            - suggestions: list[str] - 3 варианта ответов
            - tone: str - рекомендуемый тон общения
    """
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        logger.info("Анализ переписки через Claude...")

        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Проанализируй эту переписку и предложи 3 варианта ответа.\n\n"
                        f"Переписка:\n{conversation_text}\n\n"
                        f"Верни ответ в формате JSON:\n"
                        f"{{\n"
                        f'  "analysis": "краткий анализ контекста и отношений",\n'
                        f'  "tone": "рекомендуемый тон (формальный/дружеский/нейтральный)",\n'
                        f'  "suggestions": [\n'
                        f'    "вариант ответа 1",\n'
                        f'    "вариант ответа 2",\n'
                        f'    "вариант ответа 3"\n'
                        f'  ]\n'
                        f"}}"
                    )
                }
            ],
        )

        response_text = message.content[0].text.strip()
        logger.info(f"Получен анализ: {response_text[:100]}...")

        # Парсим JSON из ответа
        import json

        # Ищем JSON в ответе (может быть обёрнут в markdown)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        result = json.loads(response_text)

        return result

    except anthropic.APIError as e:
        logger.error(f"Ошибка API Claude: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON ответа: {e}")
        raise ValueError("Не удалось разобрать ответ от AI")
    except Exception as e:
        logger.error(f"Ошибка при анализе переписки: {e}")
        raise
