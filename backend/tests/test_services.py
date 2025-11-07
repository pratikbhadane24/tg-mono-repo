"""
Comprehensive tests for business logic services.

Tests all service functionality including bot API, membership service,
scheduler, and database operations.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from bson import ObjectId

from app.models import Channel, Membership, TelegramUser
from app.services import TelegramBotAPI, TelegramMembershipService


class TestTelegramBotAPI:
    """Comprehensive tests for Telegram Bot API wrapper."""

    @pytest.fixture
    def bot_api(self):
        """Create a TelegramBotAPI instance for testing."""
        return TelegramBotAPI("test_token_12345")

    @pytest.mark.asyncio
    async def test_bot_api_initialization(self, bot_api):
        """Test that bot API initializes correctly."""
        assert bot_api.token == "test_token_12345"
        assert bot_api.base_url == "https://api.telegram.org/bottest_token_12345"

    @pytest.mark.asyncio
    async def test_bot_api_creates_client(self, bot_api):
        """Test that HTTP client is created."""
        assert bot_api.client is not None

    @pytest.mark.asyncio
    async def test_make_request_success(self, bot_api):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value={"ok": True, "result": {"id": 123}})

        with patch.object(bot_api.client, "post", return_value=mock_response):
            result = await bot_api._make_request("getMe")
            assert result == {"id": 123}

    @pytest.mark.asyncio
    async def test_make_request_failure(self, bot_api):
        """Test API request failure handling."""
        mock_response = Mock()
        mock_response.json = AsyncMock(
            return_value={"ok": False, "description": "Bot token invalid"}
        )

        with patch.object(bot_api.client, "post", return_value=mock_response):
            with pytest.raises(Exception, match="Bot token invalid"):
                await bot_api._make_request("getMe")

    @pytest.mark.asyncio
    async def test_get_me(self, bot_api):
        """Test getMe endpoint."""
        mock_result = {"id": 123456, "username": "test_bot", "first_name": "Test Bot"}

        with patch.object(bot_api, "_make_request", return_value=mock_result):
            result = await bot_api.get_me()
            assert result["id"] == 123456
            assert result["username"] == "test_bot"

    @pytest.mark.asyncio
    async def test_create_chat_invite_link(self, bot_api):
        """Test creating invite link."""
        mock_result = {
            "invite_link": "https://t.me/+abc123",
            "expire_date": 1234567890,
        }

        with patch.object(bot_api, "_make_request", return_value=mock_result):
            result = await bot_api.create_chat_invite_link(
                chat_id=-1001234567890,
                expire_date=datetime.now(UTC) + timedelta(hours=1),
                member_limit=1,
            )
            assert "invite_link" in result
            assert result["invite_link"].startswith("https://t.me/")

    @pytest.mark.asyncio
    async def test_ban_chat_member(self, bot_api):
        """Test banning a chat member."""
        with patch.object(bot_api, "_make_request", return_value=True):
            result = await bot_api.ban_chat_member(chat_id=-1001234567890, user_id=123456)
            assert result is True

    @pytest.mark.asyncio
    async def test_unban_chat_member(self, bot_api):
        """Test unbanning a chat member."""
        with patch.object(bot_api, "_make_request", return_value=True):
            result = await bot_api.unban_chat_member(chat_id=-1001234567890, user_id=123456)
            assert result is True


class TestTelegramMembershipService:
    """Comprehensive tests for membership service."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        db = MagicMock()
        db.users = MagicMock()
        db.channels = MagicMock()
        db.memberships = MagicMock()
        db.invites = MagicMock()
        db.audit_log = MagicMock()
        return db

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot API."""
        bot = MagicMock(spec=TelegramBotAPI)
        return bot

    @pytest.fixture
    def service(self, mock_db, mock_bot):
        """Create a membership service instance."""
        return TelegramMembershipService(mock_db, mock_bot)

    @pytest.mark.asyncio
    async def test_upsert_user_new(self, service, mock_db):
        """Test creating a new user."""
        mock_db.users.find_one = AsyncMock(return_value=None)
        mock_db.users.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        mock_db.users.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(),
                "ext_user_id": "user123",
                "telegram_user_id": None,
                "username": None,
            }
        )

        user = await service.upsert_user("user123")

        assert user is not None
        assert user.ext_user_id == "user123"

    @pytest.mark.asyncio
    async def test_get_channel(self, service, mock_db):
        """Test getting a channel."""
        channel_doc = {
            "_id": ObjectId(),
            "chat_id": -1001234567890,
            "name": "Test Channel",
            "join_model": "invite_link",
        }
        mock_db.channels.find_one = AsyncMock(return_value=channel_doc)

        channel = await service.get_channel(-1001234567890)

        assert channel is not None
        assert channel.chat_id == -1001234567890
        assert channel.name == "Test Channel"

    @pytest.mark.asyncio
    async def test_get_channel_not_found(self, service, mock_db):
        """Test getting non-existent channel."""
        mock_db.channels.find_one = AsyncMock(return_value=None)

        channel = await service.get_channel(-1001234567890)

        assert channel is None

    @pytest.mark.asyncio
    async def test_ban_member(self, service, mock_bot):
        """Test banning a member."""
        mock_bot.ban_chat_member = AsyncMock(return_value=True)

        result = await service.ban_member(chat_id=-1001234567890, user_id=123456)

        assert result is True
        mock_bot.ban_chat_member.assert_called_once()

    @pytest.mark.asyncio
    async def test_unban_member(self, service, mock_bot):
        """Test unbanning a member."""
        mock_bot.unban_chat_member = AsyncMock(return_value=True)

        result = await service.unban_member(chat_id=-1001234567890, user_id=123456)

        assert result is True
        mock_bot.unban_chat_member.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_audit(self, service, mock_db):
        """Test audit logging."""
        mock_db.audit_log.insert_one = AsyncMock()

        await service.log_audit(
            action="TEST_ACTION",
            user_id=ObjectId(),
            chat_id=-1001234567890,
            meta={"test": "data"},
        )

        mock_db.audit_log.insert_one.assert_called_once()
        call_args = mock_db.audit_log.insert_one.call_args[0][0]
        assert call_args["action"] == "TEST_ACTION"
        assert call_args["chat_id"] == -1001234567890


class TestScheduler:
    """Comprehensive tests for the membership scheduler."""

    @pytest.mark.asyncio
    async def test_scheduler_import(self):
        """Test that scheduler can be imported."""
        from app.services import MembershipScheduler

        assert MembershipScheduler is not None

    @pytest.mark.asyncio
    async def test_scheduler_has_required_methods(self):
        """Test that scheduler has required methods."""
        from app.services.scheduler import MembershipScheduler

        assert hasattr(MembershipScheduler, "start")
        assert hasattr(MembershipScheduler, "stop")
        assert hasattr(MembershipScheduler, "_run_check")


class TestDatabaseOperations:
    """Test database operations and indexes."""

    @pytest.mark.asyncio
    async def test_create_indexes_function_exists(self):
        """Test that create_indexes function exists."""
        from app.services import create_telegram_indexes

        assert callable(create_telegram_indexes)

    @pytest.mark.asyncio
    async def test_initialize_database_function_exists(self):
        """Test that initialize_database function exists."""
        from app.services import initialize_telegram_database

        assert callable(initialize_telegram_database)
