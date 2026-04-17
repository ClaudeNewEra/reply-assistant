import asyncio
from aiogram import Bot, Dispatcher
from loguru import logger

from src.config import TELEGRAM_BOT_TOKEN
from src.handlers import main_router
from src.db.database import init_db


async def main():
    """Запуск бота"""
    logger.info("Запуск бота...")

    await init_db()

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(main_router)

    logger.info("Бот запущен. Ожидание сообщений...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
