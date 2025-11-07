"""
Service layer for seller management and operations.

Handles seller registration, authentication, channel management, and dashboard operations.
"""

import logging
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    generate_api_key,
    get_password_hash,
    verify_password,
)
from app.models.telegram import Audit, utcnow
from app.models.seller import PaymentRecord, Seller, SellerChannel, WebhookConfig

logger = logging.getLogger(__name__)


class SellerService:
    """Service for managing sellers and their operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create_seller(
        self, email: str, password: str, company_name: str | None = None
    ) -> Seller:
        """Create a new seller account."""
        # Check if seller already exists
        existing = await self.db.sellers.find_one({"email": email})
        if existing:
            raise ValueError("Email already registered")

        # Hash password
        hashed_password = get_password_hash(password)

        # Generate API key
        api_key = generate_api_key()

        # Create seller
        seller = Seller(
            email=email,
            hashed_password=hashed_password,
            company_name=company_name,
            api_key=api_key,
            created_at=utcnow(),
            updated_at=utcnow(),
        )

        result = await self.db.sellers.insert_one(seller.model_dump(by_alias=True, exclude={"id"}))
        seller.id = result.inserted_id

        # Log audit
        await self._log_audit("SELLER_CREATED", seller_id=seller.id, meta={"email": email})

        return seller

    async def authenticate_seller(
        self, email: str, password: str
    ) -> tuple[Seller, dict[str, str]] | None:
        """Authenticate a seller and return seller + tokens."""
        seller_doc = await self.db.sellers.find_one({"email": email})
        if not seller_doc:
            return None

        seller = Seller(**seller_doc)

        # Verify password
        if not verify_password(password, seller.hashed_password):
            return None

        # Check if active
        if not seller.is_active:
            raise ValueError("Account is deactivated")

        # Create tokens
        access_token = create_access_token(data={"sub": str(seller.id), "email": seller.email})
        refresh_token = create_refresh_token(data={"sub": str(seller.id), "email": seller.email})

        # Update last login
        await self.db.sellers.update_one({"_id": seller.id}, {"$set": {"last_login": utcnow()}})

        # Log audit
        await self._log_audit("SELLER_LOGIN", seller_id=seller.id, meta={"email": email})

        return seller, {"access_token": access_token, "refresh_token": refresh_token}

    async def get_seller(self, seller_id: ObjectId | str) -> Seller | None:
        """Get seller by ID."""
        if isinstance(seller_id, str):
            seller_id = ObjectId(seller_id)

        seller_doc = await self.db.sellers.find_one({"_id": seller_id})
        if not seller_doc:
            return None

        return Seller(**seller_doc)

    async def get_seller_by_api_key(self, api_key: str) -> Seller | None:
        """Get seller by API key."""
        seller_doc = await self.db.sellers.find_one({"api_key": api_key, "is_active": True})
        if not seller_doc:
            return None

        return Seller(**seller_doc)

    async def get_seller_by_email(self, email: str) -> Seller | None:
        """Get seller by email."""
        seller_doc = await self.db.sellers.find_one({"email": email})
        if not seller_doc:
            return None

        return Seller(**seller_doc)

    async def update_seller_stripe_keys(
        self, seller_id: ObjectId, publishable_key: str, secret_key: str
    ) -> bool:
        """Update seller's own Stripe keys."""
        # In production, encrypt the secret_key before storing
        result = await self.db.sellers.update_one(
            {"_id": seller_id},
            {
                "$set": {
                    "own_stripe_publishable_key": publishable_key,
                    "own_stripe_secret_key": secret_key,  # Should be encrypted
                    "use_own_stripe": True,
                    "updated_at": utcnow(),
                }
            },
        )

        await self._log_audit("SELLER_STRIPE_KEYS_UPDATED", seller_id=seller_id)
        return result.modified_count > 0

    async def create_seller_channel(
        self,
        seller_id: ObjectId,
        chat_id: int,
        name: str,
        description: str | None = None,
        price_per_month: int | None = None,
    ) -> SellerChannel:
        """Create a channel for a seller."""
        # Check if channel already exists for this seller
        existing = await self.db.seller_channels.find_one(
            {"seller_id": seller_id, "chat_id": chat_id}
        )
        if existing:
            raise ValueError("Channel already exists for this seller")

        channel = SellerChannel(
            seller_id=seller_id,
            chat_id=chat_id,
            name=name,
            description=description,
            price_per_month=price_per_month,
            created_at=utcnow(),
            updated_at=utcnow(),
        )

        result = await self.db.seller_channels.insert_one(
            channel.model_dump(by_alias=True, exclude={"id"})
        )
        channel.id = result.inserted_id

        await self._log_audit(
            "SELLER_CHANNEL_CREATED", seller_id=seller_id, meta={"chat_id": chat_id, "name": name}
        )

        return channel

    async def get_seller_channels(self, seller_id: ObjectId) -> list[SellerChannel]:
        """Get all channels for a seller."""
        channels = []
        async for doc in self.db.seller_channels.find({"seller_id": seller_id, "is_active": True}):
            channels.append(SellerChannel(**doc))
        return channels

    async def get_seller_channel(self, seller_id: ObjectId, chat_id: int) -> SellerChannel | None:
        """Get a specific channel for a seller."""
        doc = await self.db.seller_channels.find_one({"seller_id": seller_id, "chat_id": chat_id})
        if not doc:
            return None
        return SellerChannel(**doc)

    async def get_seller_members(
        self, seller_id: ObjectId, chat_id: int | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        """Get members for seller's channels."""
        # Build query
        channel_query = {"seller_id": seller_id}
        if chat_id:
            channel_query["chat_id"] = chat_id

        # Get seller's channels
        channel_ids = []
        async for channel_doc in self.db.seller_channels.find(channel_query):
            channel_ids.append(channel_doc["chat_id"])

        if not channel_ids:
            return []

        # Get memberships for these channels
        membership_query: dict[str, Any] = {"chat_id": {"$in": channel_ids}}
        if status:
            membership_query["status"] = status

        members = []
        async for membership_doc in self.db.memberships.find(membership_query):
            # Get user info
            user_doc = await self.db.users.find_one({"_id": membership_doc["user_id"]})
            if user_doc:
                member_info = {
                    "membership": membership_doc,
                    "user": user_doc,
                }
                members.append(member_info)

        return members

    async def get_seller_stats(self, seller_id: ObjectId) -> dict[str, Any]:
        """Get dashboard statistics for a seller."""
        # Get channels
        channels = await self.get_seller_channels(seller_id)
        channel_ids = [c.chat_id for c in channels]

        # Count active members
        active_members = await self.db.memberships.count_documents(
            {"chat_id": {"$in": channel_ids}, "status": "active"}
        )

        # Count total members (all time)
        total_members = await self.db.memberships.count_documents({"chat_id": {"$in": channel_ids}})

        # Get payment stats (if using platform payment)
        total_revenue = 0
        payment_cursor = self.db.payments.find({"seller_id": seller_id, "status": "succeeded"})
        async for payment_doc in payment_cursor:
            total_revenue += payment_doc.get("amount", 0)

        return {
            "total_channels": len(channels),
            "active_members": active_members,
            "total_members": total_members,
            "total_revenue_cents": total_revenue,
            "total_revenue_dollars": total_revenue / 100,
        }

    async def create_webhook_config(
        self, seller_id: ObjectId, url: str, events: list[str] | None = None
    ) -> WebhookConfig:
        """Create webhook configuration for a seller."""
        import secrets

        webhook = WebhookConfig(
            seller_id=seller_id,
            url=url,
            secret=secrets.token_urlsafe(32),
            events=events
            or ["member.joined", "member.left", "payment.succeeded", "subscription.expired"],
            created_at=utcnow(),
            updated_at=utcnow(),
        )

        result = await self.db.webhook_configs.insert_one(
            webhook.model_dump(by_alias=True, exclude={"id"})
        )
        webhook.id = result.inserted_id

        await self._log_audit(
            "WEBHOOK_CONFIG_CREATED", seller_id=seller_id, meta={"url": url, "events": events}
        )

        return webhook

    async def get_seller_webhooks(self, seller_id: ObjectId) -> list[WebhookConfig]:
        """Get all webhook configurations for a seller."""
        webhooks = []
        async for doc in self.db.webhook_configs.find({"seller_id": seller_id}):
            webhooks.append(WebhookConfig(**doc))
        return webhooks

    async def record_payment(
        self,
        seller_id: ObjectId | None,
        customer_id: ObjectId | None,
        amount: int,
        currency: str,
        status: str,
        stripe_payment_intent_id: str | None = None,
        used_seller_stripe: bool = False,
        metadata: dict | None = None,
    ) -> Payment:
        """Record a payment transaction."""
        payment = PaymentRecord(
            seller_id=seller_id,
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            status=status,
            stripe_payment_intent_id=stripe_payment_intent_id,
            used_seller_stripe=used_seller_stripe,
            metadata=metadata or {},
            created_at=utcnow(),
            updated_at=utcnow(),
        )

        result = await self.db.payments.insert_one(
            payment.model_dump(by_alias=True, exclude={"id"})
        )
        payment.id = result.inserted_id

        return payment

    async def get_seller_payments(self, seller_id: ObjectId, limit: int = 100) -> list[Payment]:
        """Get payment history for a seller."""
        payments = []
        async for doc in (
            self.db.payments.find({"seller_id": seller_id}).sort("created_at", -1).limit(limit)
        ):
            payments.append(PaymentRecord(**doc))
        return payments

    async def _log_audit(
        self,
        action: str,
        seller_id: ObjectId | None = None,
        user_id: ObjectId | None = None,
        meta: dict | None = None,
    ):
        """Log an audit entry for seller operations."""
        audit = Audit(
            action=action,
            user_id=user_id,
            meta={**(meta or {}), "seller_id": str(seller_id) if seller_id else None},
        )
        await self.db.audits.insert_one(audit.model_dump(by_alias=True, exclude={"id"}))
