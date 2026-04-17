from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.db.models import User, Analysis


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None = None) -> User:
    """Получить существующего пользователя или создать нового"""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"Создан новый пользователь: {telegram_id} (@{username})")
    elif username and user.username != username:
        user.username = username
        await session.commit()
        logger.debug(f"Обновлен username для пользователя {telegram_id}: @{username}")

    return user


async def increment_usage(session: AsyncSession, user: User) -> None:
    """Увеличить счетчик использованных бесплатных анализов"""
    user.free_analyses_used += 1
    await session.commit()
    logger.debug(f"Пользователь {user.telegram_id} использовал {user.free_analyses_used} анализов")


async def set_premium(session: AsyncSession, user: User, days: int) -> None:
    """Установить премиум-статус для пользователя на указанное количество дней"""
    premium_until = datetime.now() + timedelta(days=days)
    user.is_premium = True
    user.premium_until = premium_until
    await session.commit()
    logger.info(f"Премиум статус для пользователя {user.telegram_id} активирован на {days} дней (до {premium_until.strftime('%d.%m.%Y')})")


async def create_analysis(
    session: AsyncSession,
    user: User,
    analysis_type: str,
    input_text: str
) -> Analysis:
    """Создать запись об анализе"""
    preview = input_text[:100] if len(input_text) > 100 else input_text
    analysis = Analysis(
        user_id=user.id,
        type=analysis_type,
        input_preview=preview
    )
    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)
    logger.debug(f"Создана запись анализа: тип={analysis_type}, пользователь={user.telegram_id}")
    return analysis


async def get_user_analyses_count(session: AsyncSession, user: User) -> int:
    """Получить количество анализов пользователя"""
    stmt = select(Analysis).where(Analysis.user_id == user.id)
    result = await session.execute(stmt)
    return len(result.scalars().all())


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    """Получить пользователя по telegram_id"""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
