"""
Unit tests for authentication module.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request
from jose import jwt

from app.core.auth import get_current_user, verify_user_token
from app.core.config import get_telegram_config


class TestAuthentication:
    """Test authentication utilities."""

    @pytest.fixture
    def test_user_payload(self):
        """Fixture for test user payload."""
        return {
            "username": "test_user",
            "user_id": "12345",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }

    @pytest.fixture
    def valid_token(self, test_user_payload):
        """Fixture for a valid JWT token."""
        config = get_telegram_config()
        return jwt.encode(
            test_user_payload,
            config.JWT_SECRET_KEY,
            algorithm=config.JWT_ALGORITHM,
        )

    @pytest.fixture
    def expired_token(self):
        """Fixture for an expired JWT token."""
        config = get_telegram_config()
        payload = {
            "username": "test_user",
            "user_id": "12345",
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    def test_verify_user_token_valid(self, valid_token, test_user_payload):
        """Test that verify_user_token succeeds with valid token."""
        payload = verify_user_token(valid_token)

        assert payload is not None
        assert payload["username"] == test_user_payload["username"]
        assert payload["user_id"] == test_user_payload["user_id"]

    def test_verify_user_token_expired(self, expired_token):
        """Test that verify_user_token raises error for expired token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_user_token(expired_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_verify_user_token_invalid(self):
        """Test that verify_user_token raises error for invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_user_token("invalid_token")

        assert exc_info.value.status_code == 401

    def test_verify_user_token_no_username(self):
        """Test that verify_user_token raises error when username is missing."""
        config = get_telegram_config()
        payload = {
            "user_id": "12345",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_user_token(token)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_from_bearer(self, valid_token):
        """Test get_current_user extracts token from Authorization header."""
        request = MagicMock(spec=Request)
        request.headers.get = MagicMock(
            side_effect=lambda key: f"Bearer {valid_token}" if key == "Authorization" else None
        )
        request.cookies.get = MagicMock(return_value=None)

        user = await get_current_user(request)

        assert user is not None
        assert user["username"] == "test_user"

    @pytest.mark.asyncio
    async def test_get_current_user_from_cookie(self, valid_token):
        """Test get_current_user extracts token from cookie."""
        request = MagicMock(spec=Request)
        request.headers.get = MagicMock(return_value=None)
        request.cookies.get = MagicMock(
            side_effect=lambda key: valid_token if key == "access_token" else None
        )

        user = await get_current_user(request)

        assert user is not None
        assert user["username"] == "test_user"

    @pytest.mark.asyncio
    async def test_get_current_user_from_x_access_token(self, valid_token):
        """Test get_current_user extracts token from x-access-token header."""
        request = MagicMock(spec=Request)
        request.headers.get = MagicMock(
            side_effect=lambda key: valid_token if key == "x-access-token" else None
        )
        request.cookies.get = MagicMock(return_value=None)

        user = await get_current_user(request)

        assert user is not None
        assert user["username"] == "test_user"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self):
        """Test get_current_user raises error when no token is provided."""
        request = MagicMock(spec=Request)
        request.headers.get = MagicMock(return_value=None)
        request.cookies.get = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user raises error for invalid token."""
        request = MagicMock(spec=Request)
        request.headers.get = MagicMock(
            side_effect=lambda key: "Bearer invalid_token" if key == "Authorization" else None
        )
        request.cookies.get = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == 401
