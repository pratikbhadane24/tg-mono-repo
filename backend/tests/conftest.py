"""
Pytest configuration and fixtures.
"""

import os
from unittest.mock import patch

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
