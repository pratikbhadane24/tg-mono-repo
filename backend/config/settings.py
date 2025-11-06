"""
Configuration for Telegram paid access system.
"""

from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Default database name for Telegram service
DEFAULT_DATABASE_NAME = "telegram"


class TelegramConfig(BaseSettings):
    """Telegram bot configuration using Pydantic BaseSettings."""

    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignore unrelated env vars instead of raising
    )

    # Telegram Bot API
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram Bot API token")
    TELEGRAM_WEBHOOK_SECRET_PATH: str = Field(..., description="Secret path for webhook URL")
    BASE_URL: str = Field(..., description="Public base URL for webhook registration")

    # Invite link configuration
    INVITE_LINK_TTL_SECONDS: int = Field(default=900, description="TTL for invite links in seconds")
    INVITE_LINK_MEMBER_LIMIT: int = Field(default=1, description="Member limit for invite links")

    # Scheduler configuration
    SCHEDULER_INTERVAL_SECONDS: int = Field(
        default=60,
        description="Interval for scheduler runs in seconds",
    )

    # MongoDB (optional here; manager uses global AIO_MONGO_CLIENT)
    # Accept MONGODB_URI or fallback to DATABASE_URL if provided in env
    MONGODB_URI: str | None = Field(
        default=None,
        description="MongoDB connection URI (optional; falls back to DATABASE_URL)",
        validation_alias=AliasChoices("MONGODB_URI", "DATABASE_URL"),
    )

    # Database name (can be extracted from URI or specified separately)
    MONGODB_DATABASE: str = Field(
        default=DEFAULT_DATABASE_NAME,
        description="MongoDB database name to use",
    )

    # Join model
    JOIN_MODEL: Literal["invite_link", "join_request"] = Field(
        default="invite_link",
        description="Default join model for channels",
    )

    # Stripe configuration
    STRIPE_SECRET_KEY: str | None = Field(
        default=None,
        description="Stripe secret key for platform payments",
    )
    STRIPE_PUBLISHABLE_KEY: str | None = Field(
        default=None,
        description="Stripe publishable key for platform payments",
    )
    STRIPE_WEBHOOK_SECRET: str | None = Field(
        default=None,
        description="Stripe webhook signing secret",
    )

    # JWT configuration
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token signing",
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm for JWT token signing",
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes",
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days",
    )

    def get_database_name(self) -> str:
        """
        Get the database name to use.

        Returns the configured MONGODB_DATABASE or extracts it from MONGODB_URI
        if present in the URI path.
        """
        # If explicitly set via environment, use it
        if self.MONGODB_DATABASE and self.MONGODB_DATABASE != DEFAULT_DATABASE_NAME:
            return self.MONGODB_DATABASE

        # Try to extract from URI if present
        if self.MONGODB_URI and "/" in self.MONGODB_URI:
            parts = self.MONGODB_URI.split("/")
            if len(parts) > 3:
                # URI format: mongodb://host:port/database
                db_name = parts[-1].split("?")[0]  # Remove query params if any
                if db_name:
                    return db_name

        # Default to DEFAULT_DATABASE_NAME
        return DEFAULT_DATABASE_NAME


# Global config instance
_config = None


def get_telegram_config() -> TelegramConfig:
    """Get or create the global telegram config instance."""
    global _config
    if _config is None:
        _config = TelegramConfig()
    return _config
