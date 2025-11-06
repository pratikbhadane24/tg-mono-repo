"""
Seller routes - Authentication, dashboard, and management endpoints.

Provides APIs for seller registration, login, channel management, and dashboard operations.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.auth import Token, create_access_token, create_refresh_token, decode_token, verify_api_key
from app.response_models import StandardResponse
from app.seller_models import Seller
from app.seller_service import SellerService
from config import get_telegram_config

logger = logging.getLogger(__name__)

# Module-level service instance (set by app on startup)
_seller_service: SellerService | None = None


def _get_cookie_settings() -> dict[str, Any]:
    """Get cookie settings based on environment."""
    config = get_telegram_config()
    return {
        "httponly": True,
        "secure": config.is_production,  # True in production, False in development
        "samesite": "lax",
    }


def set_seller_service(service: SellerService):
    """Set the global seller service instance."""
    global _seller_service
    _seller_service = service


def get_seller_service() -> SellerService:
    """Dependency: Get the seller service instance."""
    if _seller_service is None:
        raise HTTPException(status_code=503, detail="Seller service not initialized")
    return _seller_service


async def get_current_seller(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
    access_token: Annotated[str | None, Cookie()] = None,
    service: SellerService = Depends(get_seller_service),
) -> Seller:
    """Dependency: Get current authenticated seller from token or API key."""

    # Try API key first
    if x_api_key:
        if not verify_api_key(x_api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format",
            )

        seller = await service.get_seller_by_api_key(x_api_key)
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        return seller

    # Try cookie token
    token_to_verify = None
    if access_token:
        token_to_verify = access_token
    # Try Bearer token
    elif authorization and authorization.startswith("Bearer "):
        token_to_verify = authorization.replace("Bearer ", "")

    if token_to_verify:
        payload = decode_token(token_to_verify)

        if not payload or payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        seller_id = payload.get("sub")
        if not seller_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        seller = await service.get_seller(seller_id)
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Seller not found",
            )

        if not seller.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        return seller

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Request/Response models
class RegisterRequest(BaseModel):
    """Seller registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    company_name: str | None = None


class LoginRequest(BaseModel):
    """Seller login request."""

    email: EmailStr
    password: str


class SellerResponse(BaseModel):
    """Seller information response."""

    id: str
    email: str
    company_name: str | None
    is_active: bool
    is_verified: bool
    subscription_status: str | None
    created_at: str
    last_login: str | None


class CreateChannelRequest(BaseModel):
    """Create channel request."""

    chat_id: int = Field(..., description="Telegram chat ID")
    name: str = Field(..., description="Channel name")
    description: str | None = None
    price_per_month: int | None = Field(None, description="Price in cents per month")


class UpdateStripeKeysRequest(BaseModel):
    """Update seller's Stripe keys."""

    publishable_key: str
    secret_key: str


class CreateWebhookRequest(BaseModel):
    """Create webhook configuration."""

    url: str = Field(..., description="Webhook URL")
    events: list[str] | None = Field(None, description="Events to subscribe to")


class ForceRemoveMemberRequest(BaseModel):
    """Force remove a member from channel."""

    ext_user_id: str = Field(..., description="External user ID")
    chat_id: int = Field(..., description="Channel chat ID")
    reason: str | None = Field(None, description="Reason for removal")


def get_seller_router() -> APIRouter:
    """Create and return the seller router."""
    router = APIRouter(prefix="/api/sellers", tags=["Sellers"])

    @router.post("/register", response_model=StandardResponse[dict[str, Any]])
    async def register(
        request: RegisterRequest,
        response: Response,
        service: SellerService = Depends(get_seller_service),
    ):
        """
        Register a new seller account.

        Creates a new seller account with email and password. Returns API key for programmatic access.
        Also sets authentication cookies for immediate login.
        """
        try:
            seller = await service.create_seller(
                email=request.email,
                password=request.password,
                company_name=request.company_name,
            )

            # Generate tokens for immediate login after registration
            access_token = create_access_token(data={"sub": str(seller.id), "email": seller.email})
            refresh_token = create_refresh_token(
                data={"sub": str(seller.id), "email": seller.email}
            )

            # Get environment-aware cookie settings
            cookie_settings = _get_cookie_settings()
            config = get_telegram_config()

            # Set httpOnly cookies
            response.set_cookie(
                key="access_token",
                value=access_token,
                max_age=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                **cookie_settings,
            )

            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                max_age=config.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                **cookie_settings,
            )

            return StandardResponse.success_response(
                message="Seller registered successfully",
                data={
                    "seller_id": str(seller.id),
                    "email": seller.email,
                    "api_key": seller.api_key,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
            )
        except ValueError as e:
            return StandardResponse.error_response(
                message=str(e),
                error_code="REGISTRATION_FAILED",
                error_description=str(e),
            )

    @router.post("/login", response_model=StandardResponse[Token])
    async def login(
        request: LoginRequest,
        response: Response,
        service: SellerService = Depends(get_seller_service),
    ):
        """
        Authenticate a seller and get access tokens.

        Returns JWT access and refresh tokens for authenticated requests.
        Also sets secure httpOnly cookies for enhanced security.
        """
        try:
            result = await service.authenticate_seller(request.email, request.password)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            seller, tokens = result

            # Get environment-aware cookie settings
            cookie_settings = _get_cookie_settings()
            config = get_telegram_config()

            # Set httpOnly cookies for enhanced security
            response.set_cookie(
                key="access_token",
                value=tokens["access_token"],
                max_age=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                **cookie_settings,
            )

            response.set_cookie(
                key="refresh_token",
                value=tokens["refresh_token"],
                max_age=config.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                **cookie_settings,
            )

            return StandardResponse.success_response(
                message="Login successful",
                data=Token(
                    access_token=tokens["access_token"],
                    refresh_token=tokens["refresh_token"],
                    token_type="bearer",
                ),
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            ) from e

    @router.get("/me", response_model=StandardResponse[SellerResponse])
    async def get_current_seller_info(
        seller: Seller = Depends(get_current_seller),
    ):
        """
        Get current seller information.

        Returns the authenticated seller's profile information.
        """
        return StandardResponse.success_response(
            message="Seller information retrieved",
            data=SellerResponse(
                id=str(seller.id),
                email=seller.email,
                company_name=seller.company_name,
                is_active=seller.is_active,
                is_verified=seller.is_verified,
                subscription_status=seller.subscription_status,
                created_at=seller.created_at.isoformat(),
                last_login=seller.last_login.isoformat() if seller.last_login else None,
            ),
        )

    @router.post("/logout")
    async def logout(response: Response):
        """
        Logout the current user by clearing authentication cookies.
        """
        cookie_settings = _get_cookie_settings()
        response.delete_cookie(key="access_token", **cookie_settings)
        response.delete_cookie(key="refresh_token", **cookie_settings)
        return StandardResponse.success_response(
            message="Logged out successfully",
            data=None,
        )

    @router.post("/stripe-keys", response_model=StandardResponse[dict[str, str]])
    async def update_stripe_keys(
        request: UpdateStripeKeysRequest,
        seller: Seller = Depends(get_current_seller),
        service: SellerService = Depends(get_seller_service),
    ):
        """
        Update seller's own Stripe API keys.

        Allows sellers to use their own Stripe account for customer payments.
        """
        success = await service.update_seller_stripe_keys(
            seller.id,
            request.publishable_key,
            request.secret_key,
        )

        if success:
            return StandardResponse.success_response(
                message="Stripe keys updated successfully",
                data={"status": "updated"},
            )
        else:
            return StandardResponse.error_response(
                message="Failed to update Stripe keys",
                error_code="UPDATE_FAILED",
            )

    @router.post("/channels", response_model=StandardResponse[dict[str, Any]])
    async def create_channel(
        request: CreateChannelRequest,
        seller: Seller = Depends(get_current_seller),
        service: SellerService = Depends(get_seller_service),
    ):
        """
        Create a new channel for the seller.

        Registers a Telegram channel under the seller's account.
        """
        try:
            channel = await service.create_seller_channel(
                seller_id=seller.id,
                chat_id=request.chat_id,
                name=request.name,
                description=request.description,
                price_per_month=request.price_per_month,
            )

            return StandardResponse.success_response(
                message="Channel created successfully",
                data={
                    "channel_id": str(channel.id),
                    "chat_id": channel.chat_id,
                    "name": channel.name,
                },
            )
        except ValueError as e:
            return StandardResponse.error_response(
                message=str(e),
                error_code="CHANNEL_CREATION_FAILED",
                error_description=str(e),
            )

    @router.get("/channels", response_model=StandardResponse[list[dict[str, Any]]])
    async def list_channels(
        seller: Seller = Depends(get_current_seller),
        service: SellerService = Depends(get_seller_service),
    ):
        """
        List all channels for the seller.

        Returns all Telegram channels registered under the seller's account.
        """
        channels = await service.get_seller_channels(seller.id)

        return StandardResponse.success_response(
            message=f"Found {len(channels)} channel(s)",
            data=[
                {
                    "id": str(c.id),
                    "chat_id": c.chat_id,
                    "name": c.name,
                    "description": c.description,
                    "price_per_month": c.price_per_month,
                    "total_members": c.total_members,
                    "active_members": c.active_members,
                    "is_active": c.is_active,
                }
                for c in channels
            ],
        )

    @router.get("/members", response_model=StandardResponse[list[dict[str, Any]]])
    async def list_members(
        chat_id: int | None = None,
        status: str | None = None,
        seller: Seller = Depends(get_current_seller),
        service: SellerService = Depends(get_seller_service),
    ):
        """
        List members across seller's channels.

        Returns members with optional filtering by channel and status.
        """
        members = await service.get_seller_members(
            seller_id=seller.id,
            chat_id=chat_id,
            status=status,
        )

        return StandardResponse.success_response(
            message=f"Found {len(members)} member(s)",
            data=members,
        )

    @router.get("/stats", response_model=StandardResponse[dict[str, Any]])
    async def get_stats(
        seller: Seller = Depends(get_current_seller),
        service: SellerService = Depends(get_seller_service),
    ):
        """
        Get dashboard statistics for the seller.

        Returns overview statistics including channels, members, and revenue.
        """
        stats = await service.get_seller_stats(seller.id)

        return StandardResponse.success_response(
            message="Statistics retrieved successfully",
            data=stats,
        )

    @router.post("/webhooks", response_model=StandardResponse[dict[str, Any]])
    async def create_webhook(
        request: CreateWebhookRequest,
        seller: Seller = Depends(get_current_seller),
        service: SellerService = Depends(get_seller_service),
    ):
        """
        Create a webhook configuration.

        Register a webhook URL to receive events about members and payments.
        """
        webhook = await service.create_webhook_config(
            seller_id=seller.id,
            url=request.url,
            events=request.events,
        )

        return StandardResponse.success_response(
            message="Webhook created successfully",
            data={
                "webhook_id": str(webhook.id),
                "url": webhook.url,
                "secret": webhook.secret,
                "events": webhook.events,
            },
        )

    @router.get("/webhooks", response_model=StandardResponse[list[dict[str, Any]]])
    async def list_webhooks(
        seller: Seller = Depends(get_current_seller),
        service: SellerService = Depends(get_seller_service),
    ):
        """
        List all webhook configurations.

        Returns all registered webhooks for the seller.
        """
        webhooks = await service.get_seller_webhooks(seller.id)

        return StandardResponse.success_response(
            message=f"Found {len(webhooks)} webhook(s)",
            data=[
                {
                    "id": str(w.id),
                    "url": w.url,
                    "events": w.events,
                    "is_active": w.is_active,
                    "last_triggered": w.last_triggered.isoformat() if w.last_triggered else None,
                }
                for w in webhooks
            ],
        )

    @router.get("/payments", response_model=StandardResponse[list[dict[str, Any]]])
    async def list_payments(
        limit: int = 100,
        seller: Seller = Depends(get_current_seller),
        service: SellerService = Depends(get_seller_service),
    ):
        """
        List payment history for the seller.

        Returns recent payments received through the platform.
        """
        payments = await service.get_seller_payments(seller.id, limit)

        return StandardResponse.success_response(
            message=f"Found {len(payments)} payment(s)",
            data=[
                {
                    "id": str(p.id),
                    "amount": p.amount,
                    "currency": p.currency,
                    "status": p.status,
                    "stripe_payment_intent_id": p.stripe_payment_intent_id,
                    "used_seller_stripe": p.used_seller_stripe,
                    "created_at": p.created_at.isoformat(),
                }
                for p in payments
            ],
        )

    return router
