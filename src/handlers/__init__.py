"""Bot handlers"""

from aiogram import Router

from .commands import router as commands_router
from .photo import router as photo_router
from .text import router as text_router
from .payments import router as payments_router
from .voice import router as voice_router
from .voice_clone import router as voice_clone_router
from .mode_callback import router as mode_router

main_router = Router()
main_router.include_router(commands_router)
main_router.include_router(payments_router)
main_router.include_router(mode_router)
main_router.include_router(voice_clone_router)  # перед voice чтобы перехватить ГС во время тренировки
main_router.include_router(voice_router)
main_router.include_router(photo_router)
main_router.include_router(text_router)

__all__ = ["main_router"]
