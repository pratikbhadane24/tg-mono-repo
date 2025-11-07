"""
Example integration: How to grant Telegram access from ra-backend payment handlers.

This example shows how to integrate the separated Telegram service with your
payment processing logic in ra-backend.
"""

import logging

import httpx

# Configure your Telegram service URL
# In production, use environment variable
TELEGRAM_SERVICE_URL = "http://telegram-service:8001"  # Docker Compose
# TELEGRAM_SERVICE_URL = "http://localhost:8001"  # Local development
# TELEGRAM_SERVICE_URL = "https://telegram.your-domain.com"  # Production

logger = logging.getLogger(__name__)


async def grant_telegram_access(
    user_id: str,
    channel_ids: list[int],
    period_days: int = 30,
    reference: str = None
) -> dict:
    """
    Grant a user access to Telegram channels.

    Args:
        user_id: Your internal user ID
        channel_ids: List of Telegram channel chat IDs
        period_days: Access period in days
        reference: Optional reference ID for tracking

    Returns:
        dict: Response from Telegram service with invite links and membership info

    Raises:
        httpx.HTTPError: If the request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_SERVICE_URL}/api/telegram/grant-access",
                json={
                    "ext_user_id": user_id,
                    "chat_ids": channel_ids,
                    "period_days": period_days,
                    "ref": reference or f"access_{user_id}"
                },
                timeout=30.0  # 30 second timeout
            )

            response.raise_for_status()
            return response.json()

    except httpx.HTTPError as e:
        logger.error(f"Failed to grant Telegram access for user {user_id}: {e}")
        raise


# Example 1: Grant access after successful payment
async def handle_payment_success(user_id: str, payment_id: str, plan_id: str):
    """
    Example: Grant Telegram access after a successful payment.

    Call this from your payment webhook handler (Stripe, Razorpay, etc.)
    """
    # Map plan_id to channel IDs (customize based on your plans)
    plan_channels = {
        "basic": [-1001234567890],
        "premium": [-1001234567890, -1001111111111],
        "enterprise": [-1001234567890, -1001111111111, -1002222222222]
    }

    channel_ids = plan_channels.get(plan_id, [])

    if not channel_ids:
        logger.warning(f"No channels configured for plan: {plan_id}")
        return

    try:
        result = await grant_telegram_access(
            user_id=user_id,
            channel_ids=channel_ids,
            period_days=30,
            reference=f"payment_{payment_id}"
        )

        if result.get("success"):
            logger.info(f"Successfully granted Telegram access for user {user_id}")

            # Send invite links to user via email/SMS/notification
            for invite in result.get("invites", []):
                invite_link = invite.get("invite_link")
                chat_id = invite.get("chat_id")
                logger.info(f"Invite link for channel {chat_id}: {invite_link}")

                # TODO: Send invite_link to user via your notification system
                # send_email(user_id, "Your Telegram Access", invite_link)
                # send_sms(user_id, f"Join our channel: {invite_link}")

        else:
            logger.error(f"Failed to grant access: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error granting Telegram access: {e}")


# Example 2: Extend access on subscription renewal
async def handle_subscription_renewal(user_id: str, subscription_id: str):
    """
    Example: Extend Telegram access when subscription is renewed.

    Call this from your subscription renewal webhook handler.
    """
    # Get user's current channels (from your database)
    # For this example, we'll use a fixed set
    channel_ids = [-1001234567890]

    try:
        result = await grant_telegram_access(
            user_id=user_id,
            channel_ids=channel_ids,
            period_days=30,  # Extend by 30 days
            reference=f"renewal_{subscription_id}"
        )

        if result.get("success"):
            logger.info(f"Extended Telegram access for user {user_id}")
        else:
            logger.error(f"Failed to extend access: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error extending Telegram access: {e}")


# Example 3: Check Telegram service health
async def check_telegram_service_health() -> bool:
    """
    Check if the Telegram service is running and healthy.

    Returns:
        bool: True if service is healthy, False otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TELEGRAM_SERVICE_URL}/health",
                timeout=5.0
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "UP"

            return False

    except Exception as e:
        logger.error(f"Telegram service health check failed: {e}")
        return False


# Example 4: Integration with FastAPI router
"""
Add this to your payment router (e.g., routers/payment.py):

from fastapi import APIRouter, HTTPException
from .telegram_integration import grant_telegram_access, check_telegram_service_health

router = APIRouter()

@router.post("/payment/webhook")
async def payment_webhook(payload: dict):
    '''Handle payment webhook and grant Telegram access.'''

    # Parse payment webhook (example with Stripe)
    if payload.get("type") == "checkout.session.completed":
        session = payload["data"]["object"]

        user_id = session["client_reference_id"]
        payment_id = session["id"]
        plan_id = session["metadata"]["plan_id"]

        # Grant Telegram access
        try:
            await handle_payment_success(user_id, payment_id, plan_id)
        except Exception as e:
            logger.error(f"Failed to grant Telegram access: {e}")
            # Don't fail the webhook - payment was successful

    return {"status": "ok"}

@router.get("/system/health")
async def system_health():
    '''Check system health including Telegram service.'''

    telegram_healthy = await check_telegram_service_health()

    return {
        "status": "UP",
        "services": {
            "telegram": "UP" if telegram_healthy else "DOWN"
        }
    }
"""


if __name__ == "__main__":
    # Simple test
    import asyncio

    async def test():
        """Test the integration functions."""
        print("Testing Telegram service health...")
        healthy = await check_telegram_service_health()
        print(f"Telegram service healthy: {healthy}")

        if healthy:
            print("\nAttempting to grant access (will fail without valid config)...")
            try:
                result = await grant_telegram_access(
                    user_id="test_user_123",
                    channel_ids=[-1001234567890],
                    period_days=30,
                    reference="test"
                )
                print(f"Result: {result}")
            except Exception as e:
                print(f"Expected error (no valid config): {e}")

    asyncio.run(test())
