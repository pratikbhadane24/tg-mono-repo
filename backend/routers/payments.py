"""
Payment routes - Stripe integration and payment handling.

Provides APIs for creating payment sessions, handling webhooks, and managing subscriptions.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.response_models import StandardResponse
from app.seller_models import Seller
from app.stripe_service import StripeService
from routers.sellers import get_current_seller, get_seller_service

logger = logging.getLogger(__name__)

# Module-level service instance (set by app on startup)
_stripe_service: StripeService | None = None


def set_stripe_service(service: StripeService):
    """Set the global stripe service instance."""
    global _stripe_service
    _stripe_service = service


def get_stripe_service() -> StripeService:
    """Dependency: Get the stripe service instance."""
    if _stripe_service is None:
        raise HTTPException(status_code=503, detail="Payment service not initialized")
    return _stripe_service


# Request/Response models
class CreateCheckoutRequest(BaseModel):
    """Create checkout session request."""

    price_id: str = Field(..., description="Stripe price ID")
    success_url: str = Field(..., description="URL to redirect after successful payment")
    cancel_url: str = Field(..., description="URL to redirect after canceled payment")
    customer_email: str | None = Field(None, description="Customer email")
    metadata: dict[str, str] | None = Field(None, description="Additional metadata")


class CreatePaymentIntentRequest(BaseModel):
    """Create payment intent request."""

    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    customer_email: str | None = Field(None, description="Customer email")
    metadata: dict[str, str] | None = Field(None, description="Additional metadata")


def get_payments_router() -> APIRouter:
    """Create and return the payments router."""
    router = APIRouter(prefix="/api/payments", tags=["Payments"])

    @router.post("/checkout", response_model=StandardResponse[dict[str, str]])
    async def create_checkout_session(
        request: CreateCheckoutRequest,
        seller: Seller = Depends(get_current_seller),
        stripe_service: StripeService = Depends(get_stripe_service),
    ):
        """
        Create a Stripe checkout session.

        Creates a hosted checkout page for subscriptions or one-time payments.
        """
        try:
            # Add seller_id to metadata
            metadata = request.metadata or {}
            metadata["seller_id"] = str(seller.id)

            session = await stripe_service.create_checkout_session(
                customer_email=request.customer_email or seller.email,
                price_id=request.price_id,
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                metadata=metadata,
                seller=seller,
            )

            return StandardResponse.success_response(
                message="Checkout session created",
                data=session,
            )
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            return StandardResponse.error_response(
                message="Failed to create checkout session",
                error_code="CHECKOUT_FAILED",
                error_description=str(e),
            )

    @router.post("/payment-intent", response_model=StandardResponse[dict[str, str]])
    async def create_payment_intent(
        request: CreatePaymentIntentRequest,
        seller: Seller = Depends(get_current_seller),
        stripe_service: StripeService = Depends(get_stripe_service),
    ):
        """
        Create a Stripe payment intent.

        Creates a payment intent for custom payment flows.
        """
        try:
            # Create or get customer
            customer_id = seller.stripe_customer_id
            if not customer_id and request.customer_email:
                customer_id = await stripe_service.create_customer(
                    email=request.customer_email,
                    name=seller.company_name,
                )
                # Update seller with customer_id
                seller_svc = get_seller_service()
                await seller_svc.db.sellers.update_one(
                    {"_id": seller.id}, {"$set": {"stripe_customer_id": customer_id}}
                )

            # Add seller_id to metadata
            metadata = request.metadata or {}
            metadata["seller_id"] = str(seller.id)

            intent = await stripe_service.create_payment_intent(
                amount=request.amount,
                currency=request.currency,
                customer_id=customer_id,
                metadata=metadata,
                seller=seller,
            )

            return StandardResponse.success_response(
                message="Payment intent created",
                data=intent,
            )
        except Exception as e:
            logger.error(f"Failed to create payment intent: {e}")
            return StandardResponse.error_response(
                message="Failed to create payment intent",
                error_code="PAYMENT_INTENT_FAILED",
                error_description=str(e),
            )

    @router.post("/webhook")
    async def stripe_webhook(
        request: Request,
        stripe_signature: str = Header(None, alias="stripe-signature"),
        stripe_service: StripeService = Depends(get_stripe_service),
    ):
        """
        Handle Stripe webhook events.

        Receives and processes events from Stripe (subscriptions, payments, etc.).
        """
        # Get webhook secret from configuration
        from config.settings import get_telegram_config

        config = get_telegram_config()
        webhook_secret = config.STRIPE_WEBHOOK_SECRET

        if not webhook_secret:
            logger.error("Stripe webhook secret not configured")
            raise HTTPException(status_code=500, detail="Webhook secret not configured")

        try:
            payload = await request.body()

            # Verify webhook signature
            event = await stripe_service.construct_webhook_event(
                payload,
                stripe_signature,
                webhook_secret,
            )

            # Handle the event
            success = await stripe_service.handle_webhook_event(event)

            if success:
                return {"status": "success"}
            else:
                raise HTTPException(status_code=400, detail="Event handling failed")

        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload") from e
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            raise HTTPException(status_code=400, detail=str(e)) from e

    @router.get("/subscription/{subscription_id}", response_model=StandardResponse[dict[str, Any]])
    async def get_subscription(
        subscription_id: str,
        seller: Seller = Depends(get_current_seller),
        stripe_service: StripeService = Depends(get_stripe_service),
    ):
        """
        Get subscription details.

        Retrieves current subscription status and billing information.
        """
        subscription = await stripe_service.get_subscription(subscription_id)

        if not subscription:
            return StandardResponse.error_response(
                message="Subscription not found",
                error_code="SUBSCRIPTION_NOT_FOUND",
            )

        return StandardResponse.success_response(
            message="Subscription retrieved",
            data=subscription,
        )

    @router.post(
        "/subscription/{subscription_id}/cancel", response_model=StandardResponse[dict[str, str]]
    )
    async def cancel_subscription(
        subscription_id: str,
        at_period_end: bool = True,
        seller: Seller = Depends(get_current_seller),
        stripe_service: StripeService = Depends(get_stripe_service),
    ):
        """
        Cancel a subscription.

        Cancels subscription either immediately or at the end of the billing period.
        """
        success = await stripe_service.cancel_subscription(
            subscription_id,
            at_period_end=at_period_end,
        )

        if success:
            return StandardResponse.success_response(
                message="Subscription canceled",
                data={"status": "canceled"},
            )
        else:
            return StandardResponse.error_response(
                message="Failed to cancel subscription",
                error_code="CANCEL_FAILED",
            )

    return router
