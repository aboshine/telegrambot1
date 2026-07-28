"""Minimal HTTP server for platform health checks (Render, Railway, etc.)."""

import logging
import os

from aiohttp import web

logger = logging.getLogger(__name__)


async def _health(_request: web.Request) -> web.Response:
    return web.Response(text="OK", status=200)


async def start_health_server() -> web.AppRunner:
    port = int(os.getenv("PORT", "8080"))
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logger.info("Health server listening on http://0.0.0.0:%s", port)
    return runner
