"""Conversation analysis module"""

from anthropic import AsyncAnthropic
from loguru import logger

from src.config import ANTHROPIC_API_KEY

client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты опытный психолог и эксперт по межличностной коммуникации.
Твоя задача — анализировать текстовые переписки и помогать пользователю понять:
- эмоциональный тон собеседника
- скрытые намерения и подтекст
- подходящие варианты ответа

Отвечай структурированно, по делу, без лишних объяснений.
Предлагай 5 вариантов ответа с разными подходами."""

USER_PROMPT_TEMPLATE = """Проанализируй эту переписку:

{text}

Дай структурированный анализ в таком формате:

📊 Тон: [один из: нейтральный / позитивный / агрессивный / обиженный / флиртующий / холодный]
💡 Что имел в виду: [2-3 предложения краткого объяснения]

💬 Варианты ответа:

1. [вариант — спокойный/нейтральный]
2. [вариант — тёплый/сближающий]
3. [вариант — прямой/честный]
4. [вариант — с юмором или альтернативный подход]
5. [вариант — уточняющий вопрос]

Формат должен быть точно таким."""


async def analyze_conversation(conversation_text: str) -> str:
    """
    Анализирует текст переписки через Claude API.

    Args:
        conversation_text: Текст переписки для анализа

    Returns:
        str: Отформатированный текст анализа с эмодзи

    Raises:
        Exception: При ошибках API или обработки
    """
    try:
        logger.info("Анализ переписки через Claude Haiku...")

        message = await client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(text=conversation_text)
                }
            ]
        )

        response_text = message.content[0].text.strip()

        logger.info(
            f"Анализ завершён, токены: input={message.usage.input_tokens}, "
            f"output={message.usage.output_tokens}"
        )

        # Форматируем ответ с заголовком
        formatted_response = f"🧠 Анализ переписки\n\n{response_text}"

        return formatted_response

    except Exception as e:
        logger.error(f"Ошибка при анализе переписки: {e}")
        raise
