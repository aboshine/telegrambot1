"""Telegram update handlers grouped by feature."""

from aiogram import Router

from handlers.commands import router as commands_router

router = Router(name="root")
router.include_router(commands_router)
