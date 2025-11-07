"""
Telegram Service - Standalone FastAPI application for Telegram bot functionality.

This is a separate service from ra-backend that handles all Telegram bot operations,
including channel access management, webhook handling, and membership scheduling.

Usage:
    uvicorn app.main:app --host 0.0.0.0 --port 8001
    granian --interface asgi app.main:app --host 0.0.0.0 --port 8001
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from app.api.endpoints import health, sellers, telegram
from app.core.config import get_telegram_config
from app.manager import TelegramManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Global Telegram manager instance
_telegram_manager = None

# Configure CORS middleware
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://cirrus.trade",
    "https://web.cirrus.trade",
    "https://analyst.cirrus.trade",
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for Telegram service."""
    global _telegram_manager

    # Startup
    try:
        logging.info("Starting Telegram service...")

        # Load Telegram configuration
        try:
            config = get_telegram_config()
            logging.info("Telegram configuration loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load Telegram configuration: {e}")
            raise

        # Connect to MongoDB
        mongodb_uri = config.MONGODB_URI
        if not mongodb_uri:
            raise ValueError("MONGODB_URI is required for Telegram service")

        client = AsyncIOMotorClient(mongodb_uri)
        db = client.get_database(config.get_database_name())

        # Create and initialize Telegram manager
        _telegram_manager = TelegramManager(db)
        await _telegram_manager.initialize()

        # Set manager for routes to use
        telegram.set_telegram_manager(_telegram_manager)

        # Initialize seller service
        from app.api.endpoints import sellers
        from app.services import SellerService

        seller_service = SellerService(db)
        sellers.set_seller_service(seller_service)

        logging.info("Telegram service started successfully")
    except Exception as e:
        logging.error(f"Error starting Telegram service: {e}")
        raise

    yield

    # Shutdown
    if _telegram_manager:
        try:
            logging.info("Shutting down Telegram service...")
            await _telegram_manager.shutdown()
            logging.info("Telegram service shut down successfully")
        except Exception as e:
            logging.error(f"Error shutting down Telegram service: {e}")


# Create FastAPI application
app = FastAPI(
    title="Telegram Service",
    description="Standalone service for Telegram bot channel access management",
    version="1.0.0",
    middleware=middleware,
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(telegram.get_telegram_router(), tags=["Telegram"])
app.include_router(sellers.router, tags=["Sellers"])
