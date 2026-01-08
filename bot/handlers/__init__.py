"""Handlers module"""
from aiogram import Router

from bot.handlers import start, catalog, purchase, profile, faq, custom_order, demo, admin


def setup_routers() -> Router:
    """Setup all routers"""
    router = Router()

    # Include all handler routers
    router.include_router(start.router)
    router.include_router(catalog.router)
    router.include_router(purchase.router)
    router.include_router(profile.router)
    router.include_router(faq.router)
    router.include_router(custom_order.router)
    router.include_router(demo.router)
    router.include_router(admin.router)

    return router
