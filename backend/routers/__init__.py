"""
API routers for Telegram Paid Subscriber Service.
"""

from .telegram import get_telegram_router, set_telegram_manager

__all__ = [
    "get_telegram_router",
    "set_telegram_manager",
]
