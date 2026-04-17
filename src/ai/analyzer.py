"""Conversation analysis via claude CLI (no API key required)"""

import asyncio
import subprocess
from loguru import logger

SYSTEM_PROMPT = """Ты опытный психолог и эксперт по межличностной коммуникации.
Анализируй переписки: тон, подтекст, варианты ответа.
Отвечай структурированно, по делу."""

USER_PROMPT_TEMPLATE = """Проанализируй эту переписку:

{text}

Дай анализ строго в таком формате:

📊 Тон: [нейтральный / позитивный / агрессивный / обиженный / флиртующий / холодный]
💡 Что имел в виду: [2-3 предложения]

💬 Варианты ответа:

1. [спокойный/нейтральный]
2. [тёплый/сближающий]
3. [прямой/честный]
4. [с юмором или альтернативный]
5. [уточняющий вопрос]"""


async def analyze_conversation(conversation_text: str) -> str:
    """Анализирует текст переписки через claude CLI."""
    prompt = USER_PROMPT_TEMPLATE.format(text=conversation_text)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"

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
