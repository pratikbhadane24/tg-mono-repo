"""
Core application configuration and settings.
"""

from .config import TelegramConfig, get_telegram_config

__all__ = [
    "TelegramConfig",
    "get_telegram_config",
]
