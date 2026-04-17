"""Conversation analysis via claude CLI (no API key required)"""

import asyncio
import subprocess
from loguru import logger

SYSTEM_PROMPT = """Ты опытный психолог и эксперт по межличностной коммуникации.
Анализируй переписки: тон, подтекст, варианты ответа.
Отвечай структурированно, по делу.
ВАЖНО: не используй markdown-форматирование. Никаких звёздочек (**), подчёркиваний (_), решёток (#). Только чистый текст и эмодзи."""

USER_PROMPT_TEMPLATE = """Проанализируй эту переписку:

{text}

Дай анализ строго в таком формате (без звёздочек и markdown):

📊 Тон: нейтральный / позитивный / агрессивный / обиженный / флиртующий / холодный
💡 Что имел в виду: 2-3 предложения объяснения

💬 Варианты ответа:
{variant_instructions}

Каждый вариант — готовая фраза в кавычках. Без заголовков в квадратных скобках."""


DEFAULT_VARIANTS = (
    "1. Спокойный, нейтральный\n"
    "2. Тёплый, сближающий\n"
    "3. Прямой, честный\n"
    "4. С лёгким юмором\n"
    "5. Уточняющий вопрос"
)


async def analyze_conversation(
    conversation_text: str,
    mode_prompt: str = "",
    variant_instructions: str = "",
) -> str:
    """Анализирует текст переписки через claude CLI."""
    mode_section = f"\n\n{mode_prompt}" if mode_prompt else ""
    variants = variant_instructions or DEFAULT_VARIANTS
    prompt = USER_PROMPT_TEMPLATE.format(
        text=conversation_text,
        variant_instructions=variants,
    )
    full_prompt = f"{SYSTEM_PROMPT}{mode_section}\n\n{prompt}"

    logger.info("Анализ переписки через claude CLI...")

    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ['claude', '-p', full_prompt, '--output-format', 'text',
                     '--dangerously-skip-permissions'],
                    capture_output=True, text=True, timeout=60
                )
            ),
            timeout=65.0
        )

        if result.returncode != 0:
            logger.error(f"claude CLI error: {result.stderr[:200]}")
            raise Exception(f"claude CLI failed: {result.stderr[:200]}")

        response = result.stdout.strip()
        logger.info(f"Анализ завершён ({len(response)} символов)")

        return f"🧠 Анализ переписки\n\n{response}"

    except asyncio.TimeoutError:
        raise Exception("Timeout: claude CLI не ответил вовремя")
    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        raise
