"""
Pytest configuration and fixtures.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def test_env():
    """Set up test environment variables for all tests."""
    test_env_vars = {
        "TELEGRAM_BOT_TOKEN": "123456789:test_token_for_testing_only",
        "TELEGRAM_WEBHOOK_SECRET_PATH": "test_secret_path",
        "BASE_URL": "https://test.example.com",
        "MONGODB_URI": "mongodb://localhost:27017/test_telegram",
        "JWT_SECRET_KEY": "test_jwt_secret_key_for_testing_only_change_in_production",
    }

    with patch.dict(os.environ, test_env_vars):
        yield


@pytest.fixture(scope="function", autouse=True)
def mock_telegram_manager():
    """Mock the Telegram manager for all endpoint tests."""
    from app.api.endpoints import telegram
    from app.services import TelegramBotAPI, TelegramMembershipService
    
    # Create mock manager
    mock_manager = MagicMock()
    
    # Create mock service and bot
    mock_service = MagicMock(spec=TelegramMembershipService)
    mock_bot = MagicMock(spec=TelegramBotAPI)
    
    # Configure manager to return mocks
    mock_manager.get_service.return_value = mock_service
    mock_manager.get_bot.return_value = mock_bot
    
    # Set the manager in the telegram endpoints module
    telegram.set_telegram_manager(mock_manager)
    
    yield mock_manager
    
    # Clean up
    telegram.set_telegram_manager(None)
