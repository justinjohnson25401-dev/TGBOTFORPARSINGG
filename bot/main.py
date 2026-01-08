"""
Main entry point for the 2GIS Database Sales Bot
"""
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from bot.config import BOT_TOKEN, WEBHOOK_HOST, WEBHOOK_PATH, TEMP_FILES_DIR
from bot.database.db import init_db, close_db
from bot.handlers import setup_routers
from bot.handlers.webhook import setup_webhook_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Startup tasks"""
    logger.info("Starting bot...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Create temp directory
    os.makedirs(TEMP_FILES_DIR, exist_ok=True)

    # Set webhook if configured
    if WEBHOOK_HOST:
        webhook_url = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook set: {webhook_url}")

    logger.info("Bot started successfully")


async def on_shutdown(bot: Bot):
    """Shutdown tasks"""
    logger.info("Shutting down bot...")

    # Close database
    await close_db()

    # Delete webhook
    if WEBHOOK_HOST:
        await bot.delete_webhook()

    logger.info("Bot stopped")


async def run_polling():
    """Run bot with polling (for development)"""
    # Create bot
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Create dispatcher
    dp = Dispatcher()

    # Setup routers
    dp.include_router(setup_routers())

    # Register startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    logger.info("Starting polling...")
    await dp.start_polling(bot)


async def run_webhook():
    """Run bot with webhook (for production)"""
    # Create bot
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Create dispatcher
    dp = Dispatcher()

    # Setup routers
    dp.include_router(setup_routers())

    # Create aiohttp app
    app = web.Application()
    app["bot"] = bot

    # Setup webhook routes
    setup_webhook_routes(app)

    # Setup bot webhook handling
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_requests_handler.register(app, path="/webhook/bot")
    setup_application(app, dp, bot=bot)

    # Register startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Run app
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)

    logger.info(f"Starting webhook server on port {port}...")
    await site.start()

    # Keep running
    await asyncio.Event().wait()


def main():
    """Main function"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)

    # Determine run mode
    use_webhook = bool(WEBHOOK_HOST) or os.getenv("USE_WEBHOOK", "").lower() == "true"

    if use_webhook:
        logger.info("Running in webhook mode")
        asyncio.run(run_webhook())
    else:
        logger.info("Running in polling mode")
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
