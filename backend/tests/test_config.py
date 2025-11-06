"""
Unit tests for configuration module.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from config.settings import TelegramConfig


class TestTelegramConfig:
    """Test TelegramConfig class."""

    @pytest.fixture
    def test_env(self):
        """Fixture for test environment variables."""
        return {
            "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF1234567890",
            "TELEGRAM_WEBHOOK_SECRET_PATH": "test_secret_path",
            "BASE_URL": "https://test.example.com",
            "MONGODB_URI": "mongodb://localhost:27017/test_db",
        }

    def test_config_loads_from_env(self, test_env):
        """Test that config loads correctly from environment variables."""
        with patch.dict(os.environ, test_env, clear=True):
            config = TelegramConfig()

            assert config.TELEGRAM_BOT_TOKEN == test_env["TELEGRAM_BOT_TOKEN"]
            assert config.TELEGRAM_WEBHOOK_SECRET_PATH == test_env["TELEGRAM_WEBHOOK_SECRET_PATH"]
            assert config.BASE_URL == test_env["BASE_URL"]
            assert config.MONGODB_URI == test_env["MONGODB_URI"]

    def test_config_defaults(self, test_env):
        """Test that config uses proper defaults."""
        with patch.dict(os.environ, test_env, clear=True):
            config = TelegramConfig()

            assert config.INVITE_LINK_TTL_SECONDS == 900
            assert config.INVITE_LINK_MEMBER_LIMIT == 1
            assert config.SCHEDULER_INTERVAL_SECONDS == 60
            assert config.JOIN_MODEL == "invite_link"

    def test_config_custom_values(self, test_env):
        """Test that config accepts custom values."""
        test_env.update(
            {
                "INVITE_LINK_TTL_SECONDS": "1800",
                "INVITE_LINK_MEMBER_LIMIT": "5",
                "SCHEDULER_INTERVAL_SECONDS": "120",
                "JOIN_MODEL": "join_request",
            }
        )

        with patch.dict(os.environ, test_env, clear=True):
            config = TelegramConfig()

            assert config.INVITE_LINK_TTL_SECONDS == 1800
            assert config.INVITE_LINK_MEMBER_LIMIT == 5
            assert config.SCHEDULER_INTERVAL_SECONDS == 120
            assert config.JOIN_MODEL == "join_request"

    def test_get_database_name_from_uri(self, test_env):
        """Test extracting database name from URI."""
        with patch.dict(os.environ, test_env, clear=True):
            config = TelegramConfig()

            assert config.get_database_name() == "test_db"

    def test_get_database_name_default(self, test_env):
        """Test default database name when not in URI."""
        test_env["MONGODB_URI"] = "mongodb://localhost:27017"

        with patch.dict(os.environ, test_env, clear=True):
            config = TelegramConfig()

            assert config.get_database_name() == "telegram"

    def test_get_database_name_explicit(self, test_env):
        """Test explicit database name overrides URI."""
        test_env["MONGODB_DATABASE"] = "custom_db"

        with patch.dict(os.environ, test_env, clear=True):
            config = TelegramConfig()

            assert config.get_database_name() == "custom_db"

    def test_config_missing_required_fields(self):
        """Test that config raises error when required fields are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                TelegramConfig()
