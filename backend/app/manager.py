"""
Telegram Manager - Central coordination point for all Telegram services.

This class provides a clean, modular interface for initializing and managing
all Telegram-related functionality without using global variables.
"""

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase

    from config.settings import TelegramConfig

logger = logging.getLogger(__name__)


class TelegramManager:
    """
    Central manager for all Telegram services.

    This provides a clean entry point for initializing and accessing
    all Telegram functionality.

    Usage:
        # Create manager instance
        manager = TelegramManager(db, config)

        # Initialize all services
        await manager.initialize()

        # Access services
        service = manager.get_service()
        bot = manager.get_bot()

        # Shutdown
        await manager.shutdown()
    """

    def __init__(self, db: "AsyncIOMotorDatabase", config: Optional["TelegramConfig"] = None):
        """
        Initialize the Telegram manager.

        Args:
            db: MongoDB database instance
            config: Optional Telegram configuration (will use env vars if not provided)
        """
        self.db = db

        # Lazy import config
        if config is None:
            from config.settings import get_telegram_config

            config = get_telegram_config()
        self.config = config

        # Service instances
        self._bot_api = None
        self._service = None
        self._scheduler = None
        self._initialized = False

    async def initialize(self, skip_webhook: bool = False, skip_scheduler: bool = False):
        """
        Initialize all Telegram services.

        Args:
            skip_webhook: If True, skip webhook registration (useful for testing)
            skip_scheduler: If True, skip starting the scheduler (useful for testing)
        """
        if self._initialized:
            logger.warning("Telegram manager already initialized")
            return

        try:
            logger.info("Initializing Telegram services...")

            # Lazy imports
            from app.bot_api import TelegramBotAPI
            from app.database import create_telegram_indexes
            from app.scheduler import MembershipScheduler
            from app.service import TelegramMembershipService

            # Create database indexes
            await create_telegram_indexes(self.db)
            logger.info("✓ Database indexes created")

            # Initialize bot API
            self._bot_api = TelegramBotAPI(self.config.TELEGRAM_BOT_TOKEN)
            logger.info("✓ Bot API initialized")

            # Initialize membership service
            self._service = TelegramMembershipService(self.db, self._bot_api)
            logger.info("✓ Membership service initialized")

            # Setup webhook
            if not skip_webhook:
                await self._setup_webhook()
                logger.info("✓ Webhook registered")

            # Start scheduler
            if not skip_scheduler:
                self._scheduler = MembershipScheduler(self.db, self._bot_api)
                await self._scheduler.start()
                logger.info("✓ Scheduler started")

            self._initialized = True
            logger.info("Telegram services initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing Telegram services: {e}")
            raise

    async def shutdown(self):
        """Shutdown all Telegram services."""
        if not self._initialized:
            return

        try:
            logger.info("Shutting down Telegram services...")

            # Stop scheduler
            if self._scheduler:
                await self._scheduler.stop()
                logger.info("✓ Scheduler stopped")

            # Close bot API
            if self._bot_api:
                await self._bot_api.close()
                logger.info("✓ Bot API closed")

            self._initialized = False
            logger.info("Telegram services shut down successfully")

        except Exception as e:
            logger.error(f"Error shutting down Telegram services: {e}")

    async def _setup_webhook(self):
        """Setup Telegram webhook."""
        try:
            # Get bot info
            bot_info = await self._bot_api.get_me()
            logger.debug(f"Bot info: {bot_info}")

            # Setup webhook URL
            webhook_url = (
                f"{self.config.BASE_URL}/webhooks/telegram/"
                f"{self.config.TELEGRAM_WEBHOOK_SECRET_PATH}"
            )
            # Telegram requires HTTPS for webhooks
            if not str(self.config.BASE_URL).lower().startswith("https://"):
                logger.warning(
                    "BASE_URL is not HTTPS; skipping webhook registration for local/dev environment"
                )
                return

            logger.info(f"Setting webhook to: {webhook_url}")
            await self._bot_api.set_webhook(webhook_url)

            # Verify webhook
            webhook_info = await self._bot_api.get_webhook_info()
            logger.debug(f"Webhook info: {webhook_info}")

        except Exception as e:
            logger.error(f"Error setting up webhook: {e}")
            # Don't raise - allow app to start even if webhook setup fails

    def get_bot(self):
        """Get the bot API instance."""
        if not self._initialized or self._bot_api is None:
            raise RuntimeError("Telegram manager not initialized. Call initialize() first.")
        return self._bot_api

    def get_service(self):
        """Get the membership service instance."""
        if not self._initialized or self._service is None:
            raise RuntimeError("Telegram manager not initialized. Call initialize() first.")
        return self._service

    def get_scheduler(self):
        """Get the scheduler instance (may be None if disabled)."""
        return self._scheduler

    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized
