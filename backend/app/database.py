"""
Database initialization and index management for Telegram system.
"""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

logger = logging.getLogger(__name__)


async def create_telegram_indexes(db: AsyncIOMotorDatabase):
    """Create all required indexes for Telegram collections."""

    # Users collection indexes
    await db.users.create_indexes(
        [
            IndexModel([("ext_user_id", ASCENDING)], unique=True, name="ext_user_id_unique"),
            IndexModel(
                [("telegram_user_id", ASCENDING)],
                unique=True,
                sparse=True,
                name="telegram_user_id_unique",
            ),
            IndexModel([("updated_at", DESCENDING)], name="updated_at_desc"),
        ]
    )
    logger.info("Created indexes for users collection")

    # Channels collection indexes
    await db.channels.create_indexes(
        [
            IndexModel([("chat_id", ASCENDING)], unique=True, name="chat_id_unique"),
        ]
    )
    logger.info("Created indexes for channels collection")

    # Memberships collection indexes
    await db.memberships.create_indexes(
        [
            IndexModel(
                [("user_id", ASCENDING), ("chat_id", ASCENDING)],
                unique=True,
                name="user_chat_unique",
            ),
            IndexModel(
                [("status", ASCENDING), ("current_period_end", ASCENDING)], name="status_period_end"
            ),
            IndexModel(
                [("chat_id", ASCENDING), ("current_period_end", ASCENDING)], name="chat_period_end"
            ),
        ]
    )
    logger.info("Created indexes for memberships collection")

    # Invites collection indexes
    await db.invites.create_indexes(
        [
            IndexModel(
                [
                    ("user_id", ASCENDING),
                    ("chat_id", ASCENDING),
                    ("used", ASCENDING),
                    ("revoked", ASCENDING),
                    ("expire_at", ASCENDING),
                ],
                name="invite_lookup",
            ),
        ]
    )
    logger.info("Created indexes for invites collection")

    # Audits collection indexes
    await db.audits.create_indexes(
        [
            IndexModel([("created_at", DESCENDING)], name="created_at_desc"),
            IndexModel([("action", ASCENDING), ("created_at", DESCENDING)], name="action_created"),
        ]
    )
    logger.info("Created indexes for audits collection")

    # Scheduler state collection indexes
    # Note: MongoDB automatically creates a unique index on _id.
    # Creating a manual index on _id with options is invalid and causes error 197.
    # No index creation needed here; the collection will be created on first write.
    logger.info("Skipped indexes for scheduler_state collection (using default _id index)")

    # Jobs collection indexes
    await db.jobs.create_indexes(
        [
            IndexModel([("status", ASCENDING), ("run_at", ASCENDING)], name="status_run_at"),
        ]
    )
    logger.info("Created indexes for jobs collection")

    # Sellers collection indexes
    await db.sellers.create_indexes(
        [
            IndexModel([("email", ASCENDING)], unique=True, name="email_unique"),
            IndexModel([("api_key", ASCENDING)], unique=True, sparse=True, name="api_key_unique"),
            IndexModel([("stripe_customer_id", ASCENDING)], sparse=True, name="stripe_customer_id"),
            IndexModel([("created_at", DESCENDING)], name="created_at_desc"),
        ]
    )
    logger.info("Created indexes for sellers collection")

    # Seller channels collection indexes
    await db.seller_channels.create_indexes(
        [
            IndexModel(
                [("seller_id", ASCENDING), ("chat_id", ASCENDING)],
                unique=True,
                name="seller_chat_unique",
            ),
            IndexModel([("seller_id", ASCENDING), ("is_active", ASCENDING)], name="seller_active"),
        ]
    )
    logger.info("Created indexes for seller_channels collection")

    # Payments collection indexes
    await db.payments.create_indexes(
        [
            IndexModel(
                [("seller_id", ASCENDING), ("created_at", DESCENDING)], name="seller_payments"
            ),
            IndexModel(
                [("customer_id", ASCENDING), ("created_at", DESCENDING)], name="customer_payments"
            ),
            IndexModel(
                [("stripe_payment_intent_id", ASCENDING)], sparse=True, name="stripe_intent"
            ),
            IndexModel([("status", ASCENDING), ("created_at", DESCENDING)], name="status_created"),
        ]
    )
    logger.info("Created indexes for payments collection")

    # Seller subscriptions collection indexes
    await db.seller_subscriptions.create_indexes(
        [
            IndexModel([("seller_id", ASCENDING)], name="seller_subscription"),
            IndexModel(
                [("stripe_subscription_id", ASCENDING)], unique=True, name="stripe_sub_unique"
            ),
            IndexModel(
                [("status", ASCENDING), ("current_period_end", ASCENDING)], name="status_period"
            ),
        ]
    )
    logger.info("Created indexes for seller_subscriptions collection")

    # Webhook configs collection indexes
    await db.webhook_configs.create_indexes(
        [
            IndexModel(
                [("seller_id", ASCENDING), ("is_active", ASCENDING)], name="seller_webhooks"
            ),
        ]
    )
    logger.info("Created indexes for webhook_configs collection")


async def initialize_telegram_database(mongodb_uri: str, database_name: str = "telegram"):
    """Initialize the database and create indexes."""
    client = AsyncIOMotorClient(mongodb_uri)
    db = client[database_name]

    try:
        await create_telegram_indexes(db)
        logger.info("Successfully initialized Telegram database indexes")
    except Exception as e:
        logger.error(f"Error initializing Telegram database: {e}")
        raise
    finally:
        client.close()
