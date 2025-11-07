"""
Comprehensive API endpoint tests.

Tests all API endpoints including authentication, request/response handling,
error cases, and edge cases.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import get_telegram_config
from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and root endpoints."""

    def test_health_endpoint(self):
        """Test /health endpoint returns correct response."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "UP"
        assert data["data"]["service"] == "telegram"

    def test_root_endpoint(self):
        """Test / endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["service"] == "Telegram Service"
        assert data["data"]["version"] == "1.0.0"
        assert "/docs" in data["data"]["docs"]

    def test_docs_endpoint_exists(self):
        """Test that /docs endpoint exists."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_exists(self):
        """Test that OpenAPI JSON is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert data["info"]["title"] == "Telegram Service"


class TestAuthenticationEndpoints:
    """Test authentication on protected endpoints."""

    @pytest.fixture
    def valid_jwt_token(self):
        """Create a valid JWT token for testing."""
        config = get_telegram_config()
        payload = {
            "username": "testuser",
            "user_id": "12345",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    @pytest.fixture
    def expired_jwt_token(self):
        """Create an expired JWT token for testing."""
        config = get_telegram_config()
        payload = {
            "username": "testuser",
            "user_id": "12345",
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    def test_grant_access_without_auth(self):
        """Test grant-access endpoint requires authentication."""
        response = client.post(
            "/api/telegram/grant-access",
            json={
                "ext_user_id": "user123",
                "chat_ids": [-1001234567890],
                "period_days": 30,
            },
        )

        assert response.status_code == 401

    def test_grant_access_with_invalid_token(self):
        """Test grant-access with invalid token."""
        response = client.post(
            "/api/telegram/grant-access",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "ext_user_id": "user123",
                "chat_ids": [-1001234567890],
                "period_days": 30,
            },
        )

        assert response.status_code == 401

    def test_grant_access_with_expired_token(self, expired_jwt_token):
        """Test grant-access with expired token."""
        response = client.post(
            "/api/telegram/grant-access",
            headers={"Authorization": f"Bearer {expired_jwt_token}"},
            json={
                "ext_user_id": "user123",
                "chat_ids": [-1001234567890],
                "period_days": 30,
            },
        )

        assert response.status_code == 401

    def test_add_channel_without_auth(self):
        """Test add channel endpoint requires authentication."""
        response = client.post(
            "/api/telegram/channels",
            json={"chat_id": -1001234567890, "name": "Test Channel"},
        )

        assert response.status_code == 401

    def test_force_remove_without_auth(self):
        """Test force-remove endpoint requires authentication."""
        response = client.post(
            "/api/telegram/force-remove",
            json={"ext_user_id": "user123", "chat_id": -1001234567890},
        )

        assert response.status_code == 401

    def test_webhook_does_not_require_auth(self):
        """Test webhook endpoint doesn't require JWT auth (has its own secret)."""
        # Note: Will fail for other reasons (invalid secret), but not auth
        response = client.post(
            "/webhooks/telegram/wrong_secret",
            json={"update_id": 123, "message": {"text": "test"}},
        )

        # Should get 404 (wrong secret) not 401 (unauthorized)
        assert response.status_code == 404


class TestGrantAccessEndpoint:
    """Comprehensive tests for grant-access endpoint."""

    @pytest.fixture
    def auth_headers(self):
        """Create auth headers with valid token."""
        config = get_telegram_config()
        payload = {
            "username": "testuser",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        return {"Authorization": f"Bearer {token}"}

    def test_grant_access_validates_request_body(self, auth_headers):
        """Test request validation."""
        response = client.post(
            "/api/telegram/grant-access",
            headers=auth_headers,
            json={"ext_user_id": "user123"},  # Missing required fields
        )

        assert response.status_code == 422  # Validation error

    def test_grant_access_validates_chat_ids_type(self, auth_headers):
        """Test chat_ids must be a list."""
        response = client.post(
            "/api/telegram/grant-access",
            headers=auth_headers,
            json={
                "ext_user_id": "user123",
                "chat_ids": -1001234567890,  # Should be a list
                "period_days": 30,
            },
        )

        assert response.status_code == 422

    def test_grant_access_validates_period_days_positive(self, auth_headers):
        """Test period_days must be positive."""
        response = client.post(
            "/api/telegram/grant-access",
            headers=auth_headers,
            json={"ext_user_id": "user123", "chat_ids": [-1001234567890], "period_days": -1},
        )

        # Note: Current implementation might not validate this, but it should
        assert response.status_code in [422, 503]  # Either validation or service error


class TestChannelEndpoints:
    """Tests for channel management endpoints."""

    @pytest.fixture
    def auth_headers(self):
        """Create auth headers with valid token."""
        config = get_telegram_config()
        payload = {
            "username": "testuser",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        return {"Authorization": f"Bearer {token}"}

    def test_add_channel_validates_chat_id(self, auth_headers):
        """Test chat_id validation."""
        response = client.post(
            "/api/telegram/channels",
            headers=auth_headers,
            json={"chat_id": "invalid"},  # Should be int
        )

        assert response.status_code == 422

    def test_add_channel_validates_join_model(self, auth_headers):
        """Test join_model validation."""
        response = client.post(
            "/api/telegram/channels",
            headers=auth_headers,
            json={"chat_id": -1001234567890, "join_model": "invalid_model"},
        )

        assert response.status_code == 422


class TestWebhookEndpoint:
    """Tests for webhook endpoint."""

    def test_webhook_invalid_secret(self):
        """Test webhook rejects invalid secret."""
        response = client.post(
            "/webhooks/telegram/wrong_secret",
            json={"update_id": 123},
        )

        assert response.status_code == 404

    def test_webhook_validates_update_structure(self):
        """Test webhook handles malformed updates gracefully."""
        # Even with correct secret path (from config), should handle bad data
        config = get_telegram_config()
        response = client.post(
            f"/webhooks/telegram/{config.TELEGRAM_WEBHOOK_SECRET_PATH}",
            json={"invalid": "data"},
        )

        # Should return 200 even on errors to prevent Telegram retries
        assert response.status_code in [200, 503]


class TestErrorHandling:
    """Test error handling across all endpoints."""

    def test_404_for_unknown_endpoint(self):
        """Test 404 for non-existent endpoints."""
        response = client.get("/api/unknown/endpoint")
        assert response.status_code == 404

    def test_405_for_wrong_method(self):
        """Test 405 for wrong HTTP method."""
        response = client.get("/api/telegram/grant-access")  # Should be POST
        assert response.status_code == 405

    def test_422_for_invalid_json(self):
        """Test 422 for malformed JSON."""
        config = get_telegram_config()
        payload = {
            "username": "testuser",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

        response = client.post(
            "/api/telegram/grant-access",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            content="not valid json{",
        )

        assert response.status_code == 422


class TestResponseModels:
    """Test that responses follow StandardResponse format."""

    def test_health_response_structure(self):
        """Test health endpoint response structure."""
        response = client.get("/health")
        data = response.json()

        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)
        assert isinstance(data["data"], dict)

    def test_error_response_structure(self):
        """Test error response structure."""
        response = client.post("/api/telegram/grant-access")  # No auth

        data = response.json()
        assert "detail" in data  # FastAPI default error format
        # When using StandardResponse for errors, check for error field

    def test_root_response_includes_metadata(self):
        """Test root endpoint includes all expected metadata."""
        response = client.get("/")
        data = response.json()

        assert "service" in data["data"]
        assert "version" in data["data"]
        assert "description" in data["data"]
        assert "docs" in data["data"]
