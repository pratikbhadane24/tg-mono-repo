"""
Channel management CLI for Telegram paid access.

Usage:
    python -m telegram.cli add <chat_id> <name> [--join-model=invite_link]
    python -m telegram.cli list
    python -m telegram.cli remove <chat_id>
    python -m telegram.cli update <chat_id> --name=<name> [--join-model=<model>]

Alternative usage:
    python telegram/cli.py [command] [args]
"""

import asyncio
import sys

from motor.motor_asyncio import AsyncIOMotorClient

from app.models import utcnow
from config.settings import get_telegram_config


async def add_channel(
    chat_id: int,
    name: str,
    join_model: str = "invite_link",
    invite_ttl: int = None,
    member_limit: int = None,
):
    """Add a new channel to the database."""
    config = get_telegram_config()
    client = AsyncIOMotorClient(config.MONGODB_URI)
    db = client.get_database(config.get_database_name())

    # Check if channel already exists
    existing = await db.channels.find_one({"chat_id": chat_id})
    if existing:
        print(f"❌ Channel with chat_id {chat_id} already exists!")
        client.close()
        return

    # Insert channel
    channel_data = {
        "chat_id": chat_id,
        "name": name,
        "join_model": join_model,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }

    if invite_ttl:
        channel_data["invite_ttl_seconds"] = invite_ttl
    if member_limit:
        channel_data["invite_member_limit"] = member_limit

    result = await db.channels.insert_one(channel_data)
    print("✅ Channel added successfully!")
    print(f"   ID: {result.inserted_id}")
    print(f"   Chat ID: {chat_id}")
    print(f"   Name: {name}")
    print(f"   Join Model: {join_model}")

    client.close()


async def list_channels():
    """List all channels in the database."""
    config = get_telegram_config()
    client = AsyncIOMotorClient(config.MONGODB_URI)
    db = client.get_database(config.get_database_name())

    print("\n📋 Configured Channels:")
    print("-" * 80)

    count = 0
    async for channel in db.channels.find():
        count += 1
        print(f"\n{count}. {channel['name']}")
        print(f"   Chat ID: {channel['chat_id']}")
        print(f"   Join Model: {channel['join_model']}")
        if channel.get("invite_ttl_seconds"):
            print(f"   Invite TTL: {channel['invite_ttl_seconds']}s")
        if channel.get("invite_member_limit"):
            print(f"   Member Limit: {channel['invite_member_limit']}")
        print(f"   Created: {channel['created_at']}")

    if count == 0:
        print("\n   No channels configured yet.")

    print()
    client.close()


async def remove_channel(chat_id: int):
    """Remove a channel from the database."""
    config = get_telegram_config()
    client = AsyncIOMotorClient(config.MONGODB_URI)
    db = client.get_database(config.get_database_name())

    # Check if channel exists
    channel = await db.channels.find_one({"chat_id": chat_id})
    if not channel:
        print(f"❌ Channel with chat_id {chat_id} not found!")
        client.close()
        return

    # Confirm deletion
    print(f"⚠️  About to delete channel: {channel['name']} (chat_id: {chat_id})")
    print("   This will NOT delete memberships or invites.")
    confirm = input("   Type 'yes' to confirm: ")

    if confirm.lower() != "yes":
        print("❌ Deletion cancelled.")
        client.close()
        return

    # Delete channel
    await db.channels.delete_one({"chat_id": chat_id})
    print("✅ Channel deleted successfully!")

    client.close()


async def update_channel(
    chat_id: int,
    name: str = None,
    join_model: str = None,
    invite_ttl: int = None,
    member_limit: int = None,
):
    """Update a channel's configuration."""
    config = get_telegram_config()
    client = AsyncIOMotorClient(config.MONGODB_URI)
    db = client.get_database(config.get_database_name())

    # Check if channel exists
    channel = await db.channels.find_one({"chat_id": chat_id})
    if not channel:
        print(f"❌ Channel with chat_id {chat_id} not found!")
        client.close()
        return

    # Build update document
    update_data = {"updated_at": utcnow()}
    if name:
        update_data["name"] = name
    if join_model:
        update_data["join_model"] = join_model
    if invite_ttl is not None:
        update_data["invite_ttl_seconds"] = invite_ttl
    if member_limit is not None:
        update_data["invite_member_limit"] = member_limit

    # Update channel
    await db.channels.update_one({"chat_id": chat_id}, {"$set": update_data})

    print("✅ Channel updated successfully!")
    print(f"   Chat ID: {chat_id}")
    for key, value in update_data.items():
        if key != "updated_at":
            print(f"   {key.replace('_', ' ').title()}: {value}")

    client.close()


def print_usage():
    """Print usage information."""
    print(__doc__)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 4:
            print("Usage: python -m telegram add <chat_id> <name> [--join-model=invite_link]")
            sys.exit(1)

        chat_id = int(sys.argv[2])
        name = sys.argv[3]
        join_model = "invite_link"

        # Parse optional arguments
        for arg in sys.argv[4:]:
            if arg.startswith("--join-model="):
                join_model = arg.split("=", 1)[1]

        asyncio.run(add_channel(chat_id, name, join_model))

    elif command == "list":
        asyncio.run(list_channels())

    elif command == "remove":
        if len(sys.argv) < 3:
            print("Usage: python -m telegram remove <chat_id>")
            sys.exit(1)

        chat_id = int(sys.argv[2])
        asyncio.run(remove_channel(chat_id))

    elif command == "update":
        if len(sys.argv) < 3:
            print("Usage: python -m telegram update <chat_id> --name=<name> [--join-model=<model>]")
            sys.exit(1)

        chat_id = int(sys.argv[2])
        name = None
        join_model = None

        # Parse optional arguments
        for arg in sys.argv[3:]:
            if arg.startswith("--name="):
                name = arg.split("=", 1)[1]
            elif arg.startswith("--join-model="):
                join_model = arg.split("=", 1)[1]

        asyncio.run(update_channel(chat_id, name, join_model))

    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
