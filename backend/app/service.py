"""
Service layer for Telegram membership management.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.bot_api import TelegramBotAPI
from app.models import Audit, Channel, Invite, Membership, TelegramUser, utcnow
from config.settings import get_telegram_config

logger = logging.getLogger(__name__)


class TelegramMembershipService:
    """Service for managing Telegram memberships and access."""

    def __init__(self, db: AsyncIOMotorDatabase, bot: TelegramBotAPI):
        self.db = db
        self.bot = bot
        self.config = get_telegram_config()

    async def log_audit(
        self,
        action: str,
        user_id: ObjectId | None = None,
        telegram_user_id: int | None = None,
        chat_id: int | None = None,
        ref: str | None = None,
        meta: dict | None = None,
    ):
        """Log an audit entry."""
        audit = Audit(
            action=action,
            user_id=user_id,
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            ref=ref,
            meta=meta or {},
        )
        await self.db.audits.insert_one(audit.model_dump(by_alias=True, exclude={"id"}))

    async def upsert_user(self, ext_user_id: str) -> TelegramUser:
        """Create or update a user by external user ID."""
        now = utcnow()

        # Try to find existing user
        user_doc = await self.db.users.find_one({"ext_user_id": ext_user_id})

        if user_doc:
            # Update timestamp
            await self.db.users.update_one({"_id": user_doc["_id"]}, {"$set": {"updated_at": now}})
            user_doc["updated_at"] = now
            return TelegramUser(**user_doc)

        # Create new user
        user = TelegramUser(ext_user_id=ext_user_id, created_at=now, updated_at=now)
        result = await self.db.users.insert_one(user.model_dump(by_alias=True, exclude={"id"}))
        user.id = result.inserted_id

        await self.log_audit(
            action="CREATE_USER", user_id=user.id, meta={"ext_user_id": ext_user_id}
        )

        return user

    async def link_telegram_user(
        self, ext_user_id: str, telegram_user_id: int, telegram_username: str | None = None
    ) -> TelegramUser | None:
        """Link a Telegram user ID to an internal user."""
        now = utcnow()

        # Find user by external ID
        user_doc = await self.db.users.find_one({"ext_user_id": ext_user_id})
        if not user_doc:
            logger.warning(f"User not found for ext_user_id: {ext_user_id}")
            return None

        # Update telegram info
        update_data = {"telegram_user_id": telegram_user_id, "updated_at": now}
        if telegram_username:
            update_data["telegram_username"] = telegram_username

        await self.db.users.update_one({"_id": user_doc["_id"]}, {"$set": update_data})

        user_doc.update(update_data)

        await self.log_audit(
            action="LINK_TELEGRAM_USER",
            user_id=user_doc["_id"],
            telegram_user_id=telegram_user_id,
            meta={"telegram_username": telegram_username},
        )

        return TelegramUser(**user_doc)

    async def get_user_by_telegram_id(self, telegram_user_id: int) -> TelegramUser | None:
        """Get user by Telegram user ID."""
        user_doc = await self.db.users.find_one({"telegram_user_id": telegram_user_id})
        if user_doc:
            return TelegramUser(**user_doc)
        return None

    async def get_channel(self, chat_id: int) -> Channel | None:
        """Get channel configuration."""
        channel_doc = await self.db.channels.find_one({"chat_id": chat_id})
        if channel_doc:
            return Channel(**channel_doc)
        return None

    async def get_all_channels(self) -> list[Channel]:
        """Get all configured channels."""
        channels = []
        async for channel_doc in self.db.channels.find():
            channels.append(Channel(**channel_doc))
        return channels

    async def upsert_membership(
        self, user_id: ObjectId, chat_id: int, period_end: datetime, status: str = "active"
    ) -> Membership:
        """Create or update a membership."""
        now = utcnow()

        # Check if membership exists
        membership_doc = await self.db.memberships.find_one(
            {"user_id": user_id, "chat_id": chat_id}
        )

        if membership_doc:
            # Update existing membership
            await self.db.memberships.update_one(
                {"_id": membership_doc["_id"]},
                {"$set": {"status": status, "current_period_end": period_end, "updated_at": now}},
            )
            membership_doc["status"] = status
            membership_doc["current_period_end"] = period_end
            membership_doc["updated_at"] = now

            await self.log_audit(
                action="UPDATE_MEMBERSHIP",
                user_id=user_id,
                chat_id=chat_id,
                meta={"status": status, "period_end": period_end.isoformat()},
            )

            return Membership(**membership_doc)

        # Create new membership
        membership = Membership(
            user_id=user_id,
            chat_id=chat_id,
            status=status,
            current_period_end=period_end,
            created_at=now,
            updated_at=now,
        )
        result = await self.db.memberships.insert_one(
            membership.model_dump(by_alias=True, exclude={"id"})
        )
        membership.id = result.inserted_id

        await self.log_audit(
            action="CREATE_MEMBERSHIP",
            user_id=user_id,
            chat_id=chat_id,
            meta={"status": status, "period_end": period_end.isoformat()},
        )

        return membership

    async def create_invite_link(
        self, user_id: ObjectId, chat_id: int, channel: Channel | None = None
    ) -> Invite | None:
        """Create an invite link for a user and channel."""
        if not channel:
            channel = await self.get_channel(chat_id)

        if not channel:
            logger.error(f"Channel not found for chat_id: {chat_id}")
            return None

        # Use channel-specific overrides or config defaults
        ttl_seconds = channel.invite_ttl_seconds or self.config.INVITE_LINK_TTL_SECONDS
        member_limit = channel.invite_member_limit or self.config.INVITE_LINK_MEMBER_LIMIT

        # Use timezone-aware UTC to avoid invalid UNIX timestamps
        expire_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)

        try:
            # Create invite link via Telegram API
            result = await self.bot.create_chat_invite_link(
                chat_id=chat_id, expire_date=expire_at, member_limit=member_limit
            )

            invite_link = result.get("invite_link")
            if not invite_link:
                logger.error("No invite link returned from Telegram API")
                return None

            # Save invite to database
            invite = Invite(
                user_id=user_id,
                chat_id=chat_id,
                invite_link=invite_link,
                expire_at=expire_at,
                member_limit=member_limit,
            )
            result = await self.db.invites.insert_one(
                invite.model_dump(by_alias=True, exclude={"id"})
            )
            invite.id = result.inserted_id

            await self.log_audit(
                action="CREATE_INVITE",
                user_id=user_id,
                chat_id=chat_id,
                meta={
                    "invite_link": invite_link,
                    "expire_at": expire_at.isoformat(),
                    "member_limit": member_limit,
                },
            )

            return invite

        except Exception as e:
            logger.error(f"Error creating invite link: {e}")
            await self.log_audit(
                action="CREATE_INVITE_ERROR",
                user_id=user_id,
                chat_id=chat_id,
                meta={"error": str(e)},
            )
            return None

    async def revoke_invite_link(self, invite_link: str, chat_id: int):
        """Revoke an invite link."""
        try:
            await self.bot.revoke_chat_invite_link(chat_id, invite_link)

            # Mark as revoked in database (update_one will update the first matching invite; invite_link is not unique per chat)
            await self.db.invites.update_one(
                {"invite_link": invite_link, "chat_id": chat_id},
                {"$set": {"revoked": True, "updated_at": utcnow()}},
            )

            await self.log_audit(
                action="REVOKE_INVITE", chat_id=chat_id, meta={"invite_link": invite_link}
            )

        except Exception as e:
            logger.error(f"Error revoking invite link: {e}")

    async def mark_invite_used(self, invite_link: str, chat_id: int, telegram_user_id: int):
        """Mark an invite as used."""
        await self.db.invites.update_one(
            {"invite_link": invite_link, "chat_id": chat_id},
            {"$set": {"used": True, "updated_at": utcnow()}},
        )

        await self.log_audit(
            action="INVITE_USED",
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            meta={"invite_link": invite_link},
        )

    async def ban_member(self, chat_id: int, telegram_user_id: int):
        """Ban a member from a channel."""
        try:
            await self.bot.ban_chat_member(
                chat_id=chat_id, user_id=telegram_user_id, revoke_messages=False
            )

            await self.log_audit(
                action="BAN_MEMBER", telegram_user_id=telegram_user_id, chat_id=chat_id
            )

            return True

        except Exception as e:
            logger.error(f"Error banning member {telegram_user_id} from {chat_id}: {e}")
            await self.log_audit(
                action="BAN_MEMBER_ERROR",
                telegram_user_id=telegram_user_id,
                chat_id=chat_id,
                meta={"error": str(e)},
            )
            return False

    async def unban_member(self, chat_id: int, telegram_user_id: int) -> bool:
        """Unban a member from a channel so they can rejoin."""
        try:
            ok = await self.bot.unban_chat_member(
                chat_id=chat_id,
                user_id=telegram_user_id,
                only_if_banned=True,
            )
            await self.log_audit(
                action="UNBAN_MEMBER",
                telegram_user_id=telegram_user_id,
                chat_id=chat_id,
                meta={"ok": ok},
            )
            return bool(ok)
        except Exception as e:
            logger.error(f"Error unbanning member {telegram_user_id} from {chat_id}: {e}")
            await self.log_audit(
                action="UNBAN_MEMBER_ERROR",
                telegram_user_id=telegram_user_id,
                chat_id=chat_id,
                meta={"error": str(e)},
            )
            return False

    async def get_active_membership(self, user_id: ObjectId, chat_id: int) -> Membership | None:
        """Get active membership for a user and channel."""
        membership_doc = await self.db.memberships.find_one(
            {"user_id": user_id, "chat_id": chat_id, "status": "active"}
        )

        if membership_doc:
            return Membership(**membership_doc)
        return None

    async def find_expired_memberships(self, cutoff_time: datetime) -> list[dict[str, Any]]:
        """Find all memberships that have expired."""
        expired = []
        async for membership_doc in self.db.memberships.find(
            {"status": "active", "current_period_end": {"$lte": cutoff_time}}
        ):
            expired.append(membership_doc)
        return expired

    async def expire_membership(self, membership_id: ObjectId):
        """Mark a membership as expired."""
        await self.db.memberships.update_one(
            {"_id": membership_id}, {"$set": {"status": "expired", "updated_at": utcnow()}}
        )
