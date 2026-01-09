"""
Webhook handlers for production deployment
"""
import logging
from aiohttp import web

logger = logging.getLogger(__name__)


async def health_check_handler(request: web.Request) -> web.Response:
    """Health check endpoint for Railway deployment"""
    return web.Response(status=200, text="OK")


async def root_handler(request: web.Request) -> web.Response:
    """Root endpoint"""
    return web.Response(
        status=200,
        text="2GIS Database Sales Bot is running",
        content_type="text/plain"
    )


def setup_webhook_routes(app: web.Application):
    """Setup webhook routes"""
    app.router.add_get("/", root_handler)
    app.router.add_get("/health", health_check_handler)
