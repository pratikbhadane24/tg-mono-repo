"""
Stripe payment service for handling seller and customer payments.

Handles platform subscriptions for sellers and customer payments routing.
"""

import logging
from typing import Any

import stripe
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.seller_models import Seller

logger = logging.getLogger(__name__)


class StripeService:
    """Service for managing Stripe payments and subscriptions."""

    def __init__(self, db: AsyncIOMotorDatabase, stripe_secret_key: str):
        self.db = db
        self.platform_stripe_key = stripe_secret_key
        stripe.api_key = stripe_secret_key

    def _get_stripe_client(self, seller: Seller | None = None) -> Any:
        """Get Stripe client, using seller's key if configured."""
        if seller and seller.use_own_stripe and seller.own_stripe_secret_key:
            # In production, decrypt the secret_key
            return stripe
        return stripe

    async def create_customer(self, email: str, name: str | None = None) -> str:
        """Create a Stripe customer."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
            )
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise

    async def create_checkout_session(
        self,
        customer_email: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: dict | None = None,
        seller: Seller | None = None,
    ) -> dict[str, Any]:
        """Create a Stripe checkout session."""
        try:
            # Use seller's Stripe if configured
            if seller and seller.use_own_stripe and seller.own_stripe_secret_key:
                # Initialize Stripe with seller's key (decrypted in production)
                import stripe as seller_stripe

                seller_stripe.api_key = (
                    seller.own_stripe_secret_key
                )  # Should decrypt first in production

                session = seller_stripe.checkout.Session.create(
                    customer_email=customer_email,
                    line_items=[
                        {
                            "price": price_id,
                            "quantity": 1,
                        }
                    ],
                    mode="subscription",
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata=metadata or {},
                )
            else:
                # Use platform Stripe
                session = stripe.checkout.Session.create(
                    customer_email=customer_email,
                    line_items=[
                        {
                            "price": price_id,
                            "quantity": 1,
                        }
                    ],
                    mode="subscription",
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata=metadata or {},
                )

            return {
                "session_id": session.id,
                "url": session.url,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise

    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: str | None = None,
        metadata: dict | None = None,
        seller: Seller | None = None,
    ) -> dict[str, Any]:
        """Create a Stripe payment intent."""
        try:
            # Use seller's Stripe if configured
            if seller and seller.use_own_stripe and seller.own_stripe_secret_key:
                # Initialize Stripe with seller's key (decrypted in production)
                import stripe as seller_stripe

                seller_stripe.api_key = (
                    seller.own_stripe_secret_key
                )  # Should decrypt first in production

                intent = seller_stripe.PaymentIntent.create(
                    amount=amount,
                    currency=currency,
                    customer=customer_id,
                    metadata=metadata or {},
                )
            else:
                # Use platform Stripe
                intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency=currency,
                    customer=customer_id,
                    metadata=metadata or {},
                )

            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise

    async def get_subscription(self, subscription_id: str) -> dict[str, Any] | None:
        """Get subscription details from Stripe."""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get subscription: {e}")
            return None

    async def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> bool:
        """Cancel a Stripe subscription."""
        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                stripe.Subscription.delete(subscription_id)
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False

    async def construct_webhook_event(
        self, payload: bytes, sig_header: str, webhook_secret: str
    ) -> Any:
        """Construct and verify a Stripe webhook event."""
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            return event
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise

    async def handle_webhook_event(self, event: dict[str, Any]) -> bool:
        """Handle Stripe webhook events."""
        event_type = event["type"]
        data = event["data"]["object"]

        logger.info(f"Handling Stripe webhook event: {event_type}")

        try:
            if event_type == "checkout.session.completed":
                await self._handle_checkout_completed(data)
            elif event_type == "customer.subscription.created":
                await self._handle_subscription_created(data)
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(data)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(data)
            elif event_type == "invoice.paid":
                await self._handle_invoice_paid(data)
            elif event_type == "invoice.payment_failed":
                await self._handle_invoice_payment_failed(data)
            elif event_type == "payment_intent.succeeded":
                await self._handle_payment_succeeded(data)
            elif event_type == "payment_intent.payment_failed":
                await self._handle_payment_failed(data)
            else:
                logger.info(f"Unhandled event type: {event_type}")

            return True
        except Exception as e:
            logger.error(f"Error handling webhook event {event_type}: {e}")
            return False

    async def _handle_checkout_completed(self, session: dict[str, Any]):
        """Handle successful checkout session."""
        logger.info(f"Checkout completed: {session['id']}")
        # Update seller subscription or customer payment based on metadata

    async def _handle_subscription_created(self, subscription: dict[str, Any]):
        """Handle subscription created."""
        logger.info(f"Subscription created: {subscription['id']}")
        # Update seller subscription status

    async def _handle_subscription_updated(self, subscription: dict[str, Any]):
        """Handle subscription updated."""
        logger.info(f"Subscription updated: {subscription['id']}")
        # Update seller subscription status

    async def _handle_subscription_deleted(self, subscription: dict[str, Any]):
        """Handle subscription deleted."""
        logger.info(f"Subscription deleted: {subscription['id']}")
        # Update seller subscription status to canceled

    async def _handle_invoice_paid(self, invoice: dict[str, Any]):
        """Handle successful invoice payment."""
        logger.info(f"Invoice paid: {invoice['id']}")
        # Record payment

    async def _handle_invoice_payment_failed(self, invoice: dict[str, Any]):
        """Handle failed invoice payment."""
        logger.info(f"Invoice payment failed: {invoice['id']}")
        # Update subscription status

    async def _handle_payment_succeeded(self, payment_intent: dict[str, Any]):
        """Handle successful payment intent."""
        logger.info(f"Payment succeeded: {payment_intent['id']}")
        # Record payment and grant access

    async def _handle_payment_failed(self, payment_intent: dict[str, Any]):
        """Handle failed payment intent."""
        logger.info(f"Payment failed: {payment_intent['id']}")
        # Handle payment failure
