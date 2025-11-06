"""
Telegram Service - Standalone FastAPI application for Telegram bot functionality.

This is a separate service from ra-backend that handles all Telegram bot operations,
including channel access management, webhook handling, and membership scheduling.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8001
    granian --interface asgi main:app --host 0.0.0.0 --port 8001
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from app import TelegramManager
from app.response_models import StandardResponse
from app.seller_service import SellerService
from app.stripe_service import StripeService
from config import get_telegram_config
from routers import get_telegram_router, set_telegram_manager
from routers.payments import get_payments_router, set_stripe_service
from routers.sellers import get_seller_router, set_seller_service
from routers.telegram import set_seller_service_for_telegram

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Global instances
_telegram_manager = None
_seller_service = None
_stripe_service = None

# Configure CORS middleware
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
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
    global _telegram_manager, _seller_service, _stripe_service

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
        set_telegram_manager(_telegram_manager)

        # Initialize seller service
        _seller_service = SellerService(db)
        set_seller_service(_seller_service)
        set_seller_service_for_telegram(_seller_service)  # Also set for telegram router
        logging.info("Seller service initialized successfully")

        # Initialize Stripe service (if configured)
        if config.STRIPE_SECRET_KEY:
            _stripe_service = StripeService(db, config.STRIPE_SECRET_KEY)
            set_stripe_service(_stripe_service)
            logging.info("Stripe service initialized successfully")
        else:
            logging.warning("Stripe not configured - payment features will be unavailable")

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
    title="Telegram Paid Subscriber Service",
    description="Multi-user SaaS platform for Telegram channel access management",
    version="2.0.0",
    middleware=middleware,
    lifespan=lifespan,
)

# Include routers
app.include_router(get_telegram_router(), tags=["Telegram"])
app.include_router(get_seller_router(), tags=["Sellers"])
app.include_router(get_payments_router(), tags=["Payments"])


@app.get("/health", response_model=StandardResponse[dict[str, str]])
def health():
    """
    Health check endpoint for Telegram service.

    Returns the service health status. Used by load balancers
    and monitoring systems to verify the service is running.

    Returns:
        StandardResponse: Status information with "status": "UP"
    """
    return StandardResponse.success_response(
        message="Service is healthy", data={"status": "UP", "service": "telegram"}
    )


@app.get("/", response_model=StandardResponse[dict[str, str]])
def root():
    """
    Root endpoint providing service information.

    Returns:
        StandardResponse: Service name and version information
    """
    return StandardResponse.success_response(
        message="Telegram Paid Subscriber Service",
        data={
            "service": "Telegram Paid Subscriber Service",
            "version": "2.0.0",
            "description": "Multi-user SaaS platform for Telegram channel access management",
            "docs": "/docs",
        },
    )
