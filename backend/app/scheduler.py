"""
Background scheduler for membership expiry and revocation.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models import utcnow
from config.settings import get_telegram_config

from .bot_api import TelegramBotAPI
from .service import TelegramMembershipService

logger = logging.getLogger(__name__)


class MembershipScheduler:
    """Scheduler for processing expired memberships."""

    def __init__(self, db: AsyncIOMotorDatabase, bot: TelegramBotAPI):
        self.db = db
        self.bot = bot
        self.service = TelegramMembershipService(db, bot)
        self.config = get_telegram_config()
        self.running = False
        self.task = None

    async def get_last_run_time(self) -> datetime:
        """Get the last run time from the database."""
        state = await self.db.scheduler_state.find_one({"_id": "membership_expiry_worker"})
        if state and "last_run_at" in state:
            return state["last_run_at"]

        # Default to 1 hour ago if no state exists
        return utcnow() - timedelta(hours=1)

    async def update_last_run_time(self, run_time: datetime):
        """Update the last run time in the database."""
        await self.db.scheduler_state.update_one(
            {"_id": "membership_expiry_worker"}, {"$set": {"last_run_at": run_time}}, upsert=True
        )

    async def process_expired_memberships(self):
        """Process all expired memberships and ban users."""
        now = utcnow()
        last_run = await self.get_last_run_time()

        logger.info(f"Processing expired memberships. Last run: {last_run}, Current: {now}")

        # Find all memberships that expired between last run and now (catch-up window)
        expired_memberships = await self.service.find_expired_memberships(now)

        logger.info(f"Found {len(expired_memberships)} expired memberships")

        for membership_doc in expired_memberships:
            try:
                user_id = membership_doc["user_id"]
                chat_id = membership_doc["chat_id"]
                membership_id = membership_doc["_id"]

                # Get user's telegram_user_id
                user_doc = await self.db.users.find_one({"_id": user_id})
                if not user_doc or not user_doc.get("telegram_user_id"):
                    logger.warning(f"User {user_id} has no telegram_user_id, skipping ban")
                    await self.service.expire_membership(membership_id)
                    continue

                telegram_user_id = user_doc["telegram_user_id"]

                # Ban the user
                logger.info(f"Banning user {telegram_user_id} from chat {chat_id}")
                success = await self.service.ban_member(chat_id, telegram_user_id)

                if success:
                    # Mark membership as expired
                    await self.service.expire_membership(membership_id)
                    logger.info(
                        f"Successfully banned and expired membership for user {telegram_user_id}"
                    )
                else:
                    logger.error(f"Failed to ban user {telegram_user_id}, will retry next run")

            except Exception as e:
                logger.error(
                    f"Error processing expired membership {membership_doc.get('_id')}: {e}"
                )

        # Update last run time
        await self.update_last_run_time(now)

        await self.service.log_audit(
            action="SCHEDULER_RUN",
            meta={
                "processed": len(expired_memberships),
                "last_run": last_run.isoformat(),
                "current_run": now.isoformat(),
            },
        )

    async def run_forever(self):
        """Run the scheduler loop forever."""
        self.running = True
        interval = self.config.SCHEDULER_INTERVAL_SECONDS

        logger.info(f"Starting membership scheduler with interval: {interval}s")

        while self.running:
            try:
                await self.process_expired_memberships()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

            # Wait for next interval
            await asyncio.sleep(interval)

    async def start(self):
        """Start the scheduler as a background task."""
        if self.running:
            logger.warning("Scheduler already running")
            return

        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.run_forever())
            logger.info("Membership scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Membership scheduler stopped")
