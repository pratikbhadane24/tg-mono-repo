"""
Data models for multi-user seller system.

Models for sellers, subscriptions, payments, and API keys.
"""

from datetime import datetime
from typing import Literal

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import utcnow


class Seller(BaseModel):
    """Seller/Customer model for multi-user platform."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    email: EmailStr = Field(..., description="Seller's email address")
    hashed_password: str = Field(..., description="Bcrypt hashed password")
    company_name: str | None = Field(default=None, description="Company name")
    is_active: bool = Field(default=True, description="Whether account is active")
    is_verified: bool = Field(default=False, description="Whether email is verified")

    # Stripe integration
    stripe_customer_id: str | None = Field(default=None, description="Stripe customer ID")
    subscription_status: (
        Literal["trialing", "active", "past_due", "canceled", "incomplete"] | None
    ) = Field(default=None, description="Current subscription status")
    subscription_id: str | None = Field(default=None, description="Stripe subscription ID")
    current_period_end: datetime | None = Field(
        default=None, description="Current billing period end"
    )

    # Seller's own Stripe keys (optional)
    own_stripe_publishable_key: str | None = Field(
        default=None, description="Seller's Stripe publishable key"
    )
    own_stripe_secret_key: str | None = Field(
        default=None, description="Seller's Stripe secret key (encrypted)"
    )
    use_own_stripe: bool = Field(default=False, description="Whether to use own Stripe account")

    # API access
    api_key: str | None = Field(default=None, description="API key for programmatic access")

    # Metadata
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    last_login: datetime | None = Field(default=None, description="Last login timestamp")


class SellerSubscription(BaseModel):
    """Subscription plan for sellers."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    seller_id: ObjectId = Field(..., description="Reference to Seller")

    # Stripe details
    stripe_subscription_id: str = Field(..., description="Stripe subscription ID")
    stripe_customer_id: str = Field(..., description="Stripe customer ID")
    stripe_price_id: str = Field(..., description="Stripe price ID")

    # Subscription info
    status: Literal["trialing", "active", "past_due", "canceled", "incomplete", "unpaid"] = Field(
        ..., description="Subscription status"
    )
    current_period_start: datetime = Field(..., description="Current period start")
    current_period_end: datetime = Field(..., description="Current period end")
    cancel_at_period_end: bool = Field(default=False, description="Whether to cancel at period end")

    # Metadata
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Payment(BaseModel):
    """Payment transaction record."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    seller_id: ObjectId | None = Field(
        default=None, description="Seller who received payment (if using platform)"
    )
    customer_id: ObjectId | None = Field(
        default=None, description="Reference to TelegramUser (customer)"
    )

    # Payment details
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    status: Literal["pending", "succeeded", "failed", "refunded"] = Field(
        ..., description="Payment status"
    )

    # Stripe details
    stripe_payment_intent_id: str | None = Field(
        default=None, description="Stripe payment intent ID"
    )
    stripe_charge_id: str | None = Field(default=None, description="Stripe charge ID")

    # Metadata
    description: str | None = Field(default=None, description="Payment description")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    used_seller_stripe: bool = Field(default=False, description="Whether seller's Stripe was used")

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class SellerChannel(BaseModel):
    """Seller-owned channel mapping."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    seller_id: ObjectId = Field(..., description="Reference to Seller")
    chat_id: int = Field(..., description="Telegram chat ID")
    name: str = Field(..., description="Channel name")
    description: str | None = Field(default=None, description="Channel description")

    # Pricing
    price_per_month: int | None = Field(default=None, description="Price in cents per month")

    # Stats
    total_members: int = Field(default=0, description="Total members count")
    active_members: int = Field(default=0, description="Active members count")

    is_active: bool = Field(default=True, description="Whether channel is active")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class WebhookConfig(BaseModel):
    """Webhook configuration for seller to receive updates."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    seller_id: ObjectId = Field(..., description="Reference to Seller")

    # Webhook settings
    url: str = Field(..., description="Webhook URL to send events to")
    secret: str = Field(..., description="Secret for signature verification")
    events: list[str] = Field(
        default_factory=lambda: [
            "member.joined",
            "member.left",
            "payment.succeeded",
            "subscription.expired",
        ],
        description="Events to send to this webhook",
    )

    is_active: bool = Field(default=True, description="Whether webhook is active")
    last_triggered: datetime | None = Field(default=None, description="Last trigger timestamp")

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
