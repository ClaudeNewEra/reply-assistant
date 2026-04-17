"""Bot handlers"""

from aiogram import Router

from .commands import router as commands_router
from .photo import router as photo_router

main_router = Router()
main_router.include_router(commands_router)
main_router.include_router(photo_router)

__all__ = ["main_router"]
