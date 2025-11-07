"""
Unit tests for data models.
"""

from datetime import datetime, timedelta

import pytest
from bson import ObjectId
from pydantic import ValidationError

from app.models import Audit, Channel, Invite, Membership, PyObjectId, TelegramUser, utcnow


class TestPyObjectId:
    """Test PyObjectId validation."""

    def test_valid_objectid(self):
        """Test that valid ObjectId strings are accepted."""
        oid = ObjectId()
        result = PyObjectId.validate(str(oid))
        assert isinstance(result, ObjectId)

    def test_invalid_objectid(self):
        """Test that invalid ObjectId strings are rejected."""
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            PyObjectId.validate("invalid_id")


class TestTelegramUser:
    """Test TelegramUser model."""

    def test_create_user_minimal(self):
        """Test creating user with minimal required fields."""
        user = TelegramUser(ext_user_id="user123")

        assert user.ext_user_id == "user123"
        assert user.telegram_user_id is None
        assert user.telegram_username is None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_create_user_complete(self):
        """Test creating user with all fields."""
        now = utcnow()
        user = TelegramUser(
            ext_user_id="user123",
            telegram_user_id=123456789,
            telegram_username="testuser",
            created_at=now,
            updated_at=now,
        )

        assert user.ext_user_id == "user123"
        assert user.telegram_user_id == 123456789
        assert user.telegram_username == "testuser"
        assert user.created_at == now
        assert user.updated_at == now

    def test_user_model_dump(self):
        """Test model serialization."""
        user = TelegramUser(
            ext_user_id="user123",
            telegram_user_id=123456789,
        )

        data = user.model_dump(by_alias=True, exclude={"id"})

        assert "ext_user_id" in data
        assert "telegram_user_id" in data
        assert "created_at" in data
        assert "_id" not in data


class TestChannel:
    """Test Channel model."""

    def test_create_channel_minimal(self):
        """Test creating channel with minimal required fields."""
        channel = Channel(
            chat_id=-1001234567890,
            name="Test Channel",
        )

        assert channel.chat_id == -1001234567890
        assert channel.name == "Test Channel"
        assert channel.join_model == "invite_link"
        # New optional invite-related fields should default to None
        assert channel.invite_ttl_seconds is None
        assert channel.invite_member_limit is None
        assert isinstance(channel.created_at, datetime)

    def test_create_channel_with_join_request(self):
        """Test creating channel with join_request model."""
        channel = Channel(
            chat_id=-1001234567890,
            name="Test Channel",
            join_model="join_request",
        )

        assert channel.join_model == "join_request"

    def test_channel_invalid_join_model(self):
        """Test that invalid join_model is rejected."""
        with pytest.raises(ValidationError):
            Channel(
                chat_id=-1001234567890,
                name="Test Channel",
                join_model="invalid_model",
            )


class TestMembership:
    """Test Membership model."""

    def test_create_membership(self):
        """Test creating membership."""
        user_id = ObjectId()
        period_end = utcnow() + timedelta(days=30)

        membership = Membership(
            user_id=user_id,
            chat_id=-1001234567890,
            status="active",
            current_period_end=period_end,
        )

        assert membership.user_id == user_id
        assert membership.chat_id == -1001234567890
        assert membership.status == "active"
        assert membership.current_period_end == period_end

    def test_membership_statuses(self):
        """Test different membership statuses."""
        user_id = ObjectId()
        period_end = utcnow() + timedelta(days=30)

        for status in ["active", "cancelled", "expired"]:
            membership = Membership(
                user_id=user_id,
                chat_id=-1001234567890,
                status=status,
                current_period_end=period_end,
            )
            assert membership.status == status

    def test_membership_invalid_status(self):
        """Test that invalid status is rejected."""
        user_id = ObjectId()
        period_end = utcnow() + timedelta(days=30)

        with pytest.raises(ValidationError):
            Membership(
                user_id=user_id,
                chat_id=-1001234567890,
                status="invalid_status",
                current_period_end=period_end,
            )


class TestInvite:
    """Test Invite model."""

    def test_create_invite(self):
        """Test creating invite."""
        user_id = ObjectId()
        expire_at = utcnow() + timedelta(hours=1)

        invite = Invite(
            user_id=user_id,
            chat_id=-1001234567890,
            invite_link="https://t.me/+abc123xyz",
            expire_at=expire_at,
        )

        assert invite.user_id == user_id
        assert invite.chat_id == -1001234567890
        assert invite.invite_link == "https://t.me/+abc123xyz"
        assert invite.expire_at == expire_at
        assert invite.member_limit == 1

    def test_invite_custom_member_limit(self):
        """Test creating invite with custom member limit."""
        user_id = ObjectId()
        expire_at = utcnow() + timedelta(hours=1)

        invite = Invite(
            user_id=user_id,
            chat_id=-1001234567890,
            invite_link="https://t.me/+abc123xyz",
            expire_at=expire_at,
            member_limit=5,
        )

        assert invite.member_limit == 5


class TestAudit:
    """Test Audit model."""

    def test_create_audit_minimal(self):
        """Test creating audit with minimal fields."""
        audit = Audit(action="TEST_ACTION")

        assert audit.action == "TEST_ACTION"
        assert audit.user_id is None
        assert audit.telegram_user_id is None
        assert audit.chat_id is None
        assert audit.ref is None
        assert audit.meta == {}
        assert isinstance(audit.created_at, datetime)

    def test_create_audit_complete(self):
        """Test creating audit with all fields."""
        user_id = ObjectId()
        meta = {"key": "value", "count": 123}

        audit = Audit(
            action="GRANT_ACCESS",
            user_id=user_id,
            telegram_user_id=123456789,
            chat_id=-1001234567890,
            ref="payment_abc123",
            meta=meta,
        )

        assert audit.action == "GRANT_ACCESS"
        assert audit.user_id == user_id
        assert audit.telegram_user_id == 123456789
        assert audit.chat_id == -1001234567890
        assert audit.ref == "payment_abc123"
        assert audit.meta == meta
