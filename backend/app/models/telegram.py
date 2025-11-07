"""
Data models for Telegram service.

Pydantic models for database documents and API request/response schemas.
"""

from datetime import UTC, datetime
from typing import Literal

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    """Get current UTC time with timezone awareness."""
    return datetime.now(UTC)


class PyObjectId(ObjectId):
    """Custom type for MongoDB ObjectId."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class TelegramUser(BaseModel):
    """Telegram user model."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    ext_user_id: str = Field(..., description="External user ID from main system")
    telegram_user_id: int | None = Field(default=None, description="Telegram user ID")
    telegram_username: str | None = Field(default=None, description="Telegram username")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Channel(BaseModel):
    """Telegram channel/group model."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    chat_id: int = Field(..., description="Telegram chat ID (negative for groups/channels)")
    name: str = Field(..., description="Channel name")
    join_model: Literal["invite_link", "join_request"] = Field(
        default="invite_link", description="How users join: invite_link or join_request"
    )
    # Optional overrides stored per-channel
    invite_ttl_seconds: int | None = Field(
        default=None, description="Optional channel-specific invite TTL in seconds"
    )
    invite_member_limit: int | None = Field(
        default=None, description="Optional channel-specific invite member limit"
    )
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Membership(BaseModel):
    """Telegram membership model."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    user_id: ObjectId = Field(..., description="Reference to TelegramUser")
    chat_id: int = Field(..., description="Telegram chat ID")
    status: Literal["active", "cancelled", "expired"] = Field(
        default="active", description="Membership status"
    )
    current_period_end: datetime = Field(..., description="When current period ends")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Invite(BaseModel):
    """Telegram invite link model."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    user_id: ObjectId = Field(..., description="Reference to TelegramUser")
    chat_id: int = Field(..., description="Telegram chat ID")
    invite_link: str = Field(..., description="Telegram invite link URL")
    expire_at: datetime = Field(..., description="When invite link expires")
    member_limit: int = Field(default=1, description="Max members for this invite")
    # Invite usage / lifecycle fields
    used: bool = Field(default=False, description="Whether the invite was used")
    revoked: bool = Field(default=False, description="Whether the invite was revoked")
    used_by_telegram_user_id: int | None = Field(
        default=None, description="Telegram user ID who used this invite (optional)"
    )
    created_at: datetime = Field(default_factory=utcnow)


class Audit(BaseModel):
    """Audit log model."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    action: str = Field(..., description="Action performed")
    user_id: ObjectId | None = Field(default=None, description="Reference to TelegramUser")
    telegram_user_id: int | None = Field(default=None, description="Telegram user ID")
    chat_id: int | None = Field(default=None, description="Telegram chat ID")
    ref: str | None = Field(default=None, description="External reference ID")
    meta: dict = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=utcnow)
