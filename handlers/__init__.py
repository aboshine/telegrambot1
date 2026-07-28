"""Telegram update handlers grouped by feature."""

from aiogram import Router

from handlers.challenges import router as challenges_router
from handlers.commands import router as commands_router
from handlers.daily import router as daily_router
from handlers.start import router as start_router
from handlers.top import router as top_router

router = Router(name="root")
router.include_router(start_router)
router.include_router(daily_router)
router.include_router(top_router)
router.include_router(challenges_router)
router.include_router(commands_router)
