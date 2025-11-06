"""
Tests for seller authentication and management.
"""

import pytest
from datetime import datetime

from app.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    get_password_hash,
    verify_api_key,
    verify_password,
)
from app.seller_models import Seller, SellerChannel, Payment, WebhookConfig


class TestAuth:
    """Test authentication utilities."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_access_token_creation(self):
        """Test JWT access token creation and decoding."""
        data = {"sub": "seller123", "email": "test@example.com"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "seller123"
        assert decoded["email"] == "test@example.com"
        assert decoded["type"] == "access"

    def test_refresh_token_creation(self):
        """Test JWT refresh token creation."""
        data = {"sub": "seller123", "email": "test@example.com"}
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["type"] == "refresh"

    def test_invalid_token_decoding(self):
        """Test decoding of invalid token."""
        invalid_token = "invalid.token.here"
        decoded = decode_token(invalid_token)
        
        assert decoded is None

    def test_api_key_generation(self):
        """Test API key generation."""
        api_key = generate_api_key()
        
        assert api_key is not None
        assert api_key.startswith("sk_")
        assert len(api_key) > 10
        assert verify_api_key(api_key) is True

    def test_api_key_verification(self):
        """Test API key verification."""
        valid_key = "sk_abc123xyz"
        invalid_key = "invalid_key"
        
        assert verify_api_key(valid_key) is True
        assert verify_api_key(invalid_key) is False


class TestSellerModels:
    """Test seller-related models."""

    def test_seller_model_creation(self):
        """Test Seller model creation."""
        seller = Seller(
            email="test@example.com",
            hashed_password="hashed_password",
            company_name="Test Company",
            api_key="sk_test123",
        )
        
        assert seller.email == "test@example.com"
        assert seller.company_name == "Test Company"
        assert seller.is_active is True
        assert seller.is_verified is False
        assert seller.use_own_stripe is False

    def test_seller_channel_model(self):
        """Test SellerChannel model creation."""
        from bson import ObjectId
        
        channel = SellerChannel(
            seller_id=ObjectId(),
            chat_id=-1001234567890,
            name="Premium Channel",
            description="Test channel",
            price_per_month=4900,
        )
        
        assert channel.chat_id == -1001234567890
        assert channel.name == "Premium Channel"
        assert channel.price_per_month == 4900
        assert channel.total_members == 0
        assert channel.is_active is True

    def test_payment_model(self):
        """Test Payment model creation."""
        from bson import ObjectId
        
        payment = Payment(
            seller_id=ObjectId(),
            customer_id=ObjectId(),
            amount=4900,
            currency="usd",
            status="succeeded",
            stripe_payment_intent_id="pi_test123",
        )
        
        assert payment.amount == 4900
        assert payment.currency == "usd"
        assert payment.status == "succeeded"
        assert payment.used_seller_stripe is False

    def test_webhook_config_model(self):
        """Test WebhookConfig model creation."""
        from bson import ObjectId
        
        webhook = WebhookConfig(
            seller_id=ObjectId(),
            url="https://example.com/webhook",
            secret="whsec_test123",
        )
        
        assert webhook.url == "https://example.com/webhook"
        assert webhook.secret == "whsec_test123"
        assert webhook.is_active is True
        assert "member.joined" in webhook.events
        assert "payment.succeeded" in webhook.events
