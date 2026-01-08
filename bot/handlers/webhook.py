"""
Webhook handler for Prodamus payments
"""
import logging
from aiohttp import web
from aiogram import Bot

from bot.services.prodamus import (
    verify_webhook_signature,
    parse_webhook_data,
    is_payment_successful,
    get_order_id_from_webhook
)
from bot.handlers.purchase import process_successful_payment

logger = logging.getLogger(__name__)


async def prodamus_webhook_handler(request: web.Request) -> web.Response:
    """Handle Prodamus payment webhooks"""
    try:
        # Get bot from app
        bot: Bot = request.app["bot"]

        # Get raw data
        raw_data = await request.read()
        logger.info(f"Received webhook: {raw_data[:200]}")

        # Parse data
        data = parse_webhook_data(raw_data)
        if not data:
            logger.error("Failed to parse webhook data")
            return web.Response(status=400, text="Bad Request")

        # Verify signature
        signature = request.headers.get("Sign", "") or data.get("signature", "")
        if not verify_webhook_signature(data, signature):
            logger.warning("Invalid webhook signature")
            return web.Response(status=403, text="Forbidden")

        # Check payment status
        if not is_payment_successful(data):
            logger.info(f"Payment not successful: {data.get('payment_status')}")
            return web.Response(status=200, text="OK")

        # Get order ID
        order_id = get_order_id_from_webhook(data)
        if not order_id:
            logger.error("No order_id in webhook data")
            return web.Response(status=400, text="Bad Request")

        logger.info(f"Processing successful payment for order: {order_id}")

        # Process payment
        success = await process_successful_payment(bot, order_id)

        if success:
            return web.Response(status=200, text="OK")
        else:
            return web.Response(status=500, text="Processing Error")

    except Exception as e:
        logger.exception(f"Webhook handler error: {e}")
        return web.Response(status=500, text="Internal Server Error")


def setup_webhook_routes(app: web.Application):
    """Setup webhook routes"""
    app.router.add_post("/webhook/prodamus", prodamus_webhook_handler)
