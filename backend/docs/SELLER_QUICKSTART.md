# Seller Quick Start Guide

Get started with the Telegram Paid Subscriber Service platform as a seller.

## Overview

As a **SELLER**, you can:
- Manage your own Telegram channels
- Accept payments from your customers
- Use your own Stripe account or the platform's
- Track members and revenue
- Receive real-time event notifications via webhooks

## Quick Start

### 1. Register Your Account

**Using the API:**
```bash
curl -X POST https://api.example.com/api/sellers/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "password": "SecurePassword123!",
    "company_name": "Your Company Name"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Seller registered successfully",
  "data": {
    "seller_id": "507f1f77bcf86cd799439011",
    "email": "you@example.com",
    "api_key": "sk_abc123xyz..."
  }
}
```

**⚠️ Important:** Save your `api_key` - you'll need it for server-to-server integration!

### 2. Login and Get Access Token

```bash
curl -X POST https://api.example.com/api/sellers/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer"
  }
}
```

### 3. Register Your Telegram Channel

First, make sure:
- You have a Telegram channel
- Your bot is added as administrator with required permissions
- You have the chat ID (use [@getidsbot](https://t.me/getidsbot) to get it)

```bash
curl -X POST https://api.example.com/api/sellers/channels \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": -1001234567890,
    "name": "Premium Crypto Signals",
    "description": "Daily trading signals and analysis",
    "price_per_month": 4900
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Channel created successfully",
  "data": {
    "channel_id": "507f1f77bcf86cd799439012",
    "chat_id": -1001234567890,
    "name": "Premium Crypto Signals"
  }
}
```

### 4. Set Up Payments

You have two options:

#### Option A: Use Your Own Stripe Account

```bash
curl -X POST https://api.example.com/api/sellers/stripe-keys \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "publishable_key": "pk_live_...",
    "secret_key": "sk_live_..."
  }'
```

**Benefits:**
- Direct deposits to your Stripe account
- You control the payment flow
- Lower platform fees

#### Option B: Use Platform Payments

No setup required - the platform handles everything!

**Benefits:**
- No Stripe account needed
- Faster setup
- Platform handles compliance and disputes

### 5. Create Your First Checkout

```bash
curl -X POST https://api.example.com/api/payments/checkout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price_id": "price_1234567890",
    "success_url": "https://yoursite.com/success",
    "cancel_url": "https://yoursite.com/cancel",
    "customer_email": "customer@example.com",
    "metadata": {
      "channel_id": "507f1f77bcf86cd799439012"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "cs_test_...",
    "url": "https://checkout.stripe.com/c/pay/cs_test_..."
  }
}
```

Redirect your customer to the `url` to complete payment.

### 6. Grant Access After Payment

After successful payment, grant the customer access:

```bash
curl -X POST https://api.example.com/api/telegram/grant-access \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "ext_user_id": "customer_12345",
    "chat_ids": [-1001234567890],
    "period_days": 30,
    "ref": "payment_abc123"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Access granted until 2024-02-14 23:59:59 UTC",
  "data": {
    "user_id": "507f1f77bcf86cd799439011",
    "invites": {
      "-1001234567890": "https://t.me/+abc123xyz"
    },
    "period_end": "2024-02-14T23:59:59Z"
  }
}
```

Send the `invite_link` to your customer!

## Dashboard & Monitoring

### View Statistics

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.example.com/api/sellers/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_channels": 3,
    "active_members": 142,
    "total_members": 150,
    "total_revenue_cents": 698600,
    "total_revenue_dollars": 6986.00
  }
}
```

### List Members

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  "https://api.example.com/api/sellers/members?status=active"
```

### View Channels

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.example.com/api/sellers/channels
```

### Payment History

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  "https://api.example.com/api/sellers/payments?limit=50"
```

## Webhooks

Get real-time notifications when events happen.

### Create Webhook

```bash
curl -X POST https://api.example.com/api/sellers/webhooks \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://yoursite.com/webhooks/telegram",
    "events": [
      "member.joined",
      "member.left",
      "payment.succeeded",
      "subscription.expired"
    ]
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "webhook_id": "507f1f77bcf86cd799439014",
    "url": "https://yoursite.com/webhooks/telegram",
    "secret": "whsec_abc123...",
    "events": ["member.joined", "member.left", "payment.succeeded", "subscription.expired"]
  }
}
```

**⚠️ Important:** Save your `secret` - use it to verify webhook signatures!

### Handle Webhook Events

**Python Example:**
```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()
WEBHOOK_SECRET = "whsec_abc123..."

@app.post("/webhooks/telegram")
async def handle_webhook(request: Request):
    # Get signature
    signature = request.headers.get("X-Webhook-Signature")
    payload = await request.body()
    
    # Verify signature
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process event
    event = await request.json()
    
    if event["event"] == "member.joined":
        # Send welcome email
        await send_welcome_email(event["data"]["ext_user_id"])
    elif event["event"] == "payment.succeeded":
        # Update your records
        await update_payment_records(event["data"])
    
    return {"status": "ok"}
```

### Available Events

- `member.joined` - User joined a channel
- `member.left` - User left or was removed
- `payment.succeeded` - Payment completed successfully
- `subscription.expired` - Subscription period ended

## Best Practices

### Security

1. **Never expose API keys in client-side code**
2. **Use HTTPS only** for production
3. **Verify webhook signatures** always
4. **Rotate API keys periodically**
5. **Store secrets in environment variables**

### Error Handling

```python
import httpx

async def grant_access_with_retry(api_key: str, user_id: str, chat_id: int):
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.example.com/api/telegram/grant-access",
                    headers={"X-API-Key": api_key},
                    json={
                        "ext_user_id": user_id,
                        "chat_ids": [chat_id],
                        "period_days": 30
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Rate Limiting

Implement rate limiting in your application:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/checkout")
@limiter.limit("10/minute")
async def create_checkout(request: Request):
    # Your code here
    pass
```

## Integration Examples

### Complete Payment Flow

```python
import httpx
from typing import Optional

class TelegramSubscriptionService:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    async def create_subscription(
        self,
        customer_email: str,
        chat_id: int,
        price_id: str
    ) -> dict:
        """Create Stripe checkout and return URL."""
        async with httpx.AsyncClient() as client:
            # Create checkout session
            response = await client.post(
                f"{self.base_url}/api/payments/checkout",
                headers={"X-API-Key": self.api_key},
                json={
                    "price_id": price_id,
                    "success_url": "https://myapp.com/success",
                    "cancel_url": "https://myapp.com/cancel",
                    "customer_email": customer_email,
                    "metadata": {"chat_id": str(chat_id)}
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def grant_access(
        self,
        customer_id: str,
        chat_id: int,
        payment_ref: str
    ) -> dict:
        """Grant customer access to channel."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/telegram/grant-access",
                headers={"X-API-Key": self.api_key},
                json={
                    "ext_user_id": customer_id,
                    "chat_ids": [chat_id],
                    "period_days": 30,
                    "ref": payment_ref
                }
            )
            response.raise_for_status()
            return response.json()

# Usage
service = TelegramSubscriptionService(
    api_key="sk_...",
    base_url="https://api.example.com"
)

# Create checkout
checkout = await service.create_subscription(
    customer_email="customer@example.com",
    chat_id=-1001234567890,
    price_id="price_123"
)
# Redirect customer to checkout["data"]["url"]

# After payment success (webhook or redirect)
access = await service.grant_access(
    customer_id="customer_123",
    chat_id=-1001234567890,
    payment_ref="payment_xyz"
)
# Send invite_link to customer
```

## Troubleshooting

### Common Issues

**1. "Channel not found" error**
- Make sure bot is added to the channel as admin
- Use the correct chat ID format (-100...)
- Check bot permissions (invite users, manage chat, restrict members)

**2. "Authentication required" error**
- Check if token is expired (get new one with /login)
- Verify Authorization header format: `Bearer {token}`
- For API key: use `X-API-Key` header

**3. "Invalid webhook signature"**
- Verify you're using the correct secret from webhook creation
- Check signature calculation (HMAC-SHA256)
- Ensure payload is used as raw bytes

**4. Customer can't join channel**
- Check if invite link is expired
- Verify membership is active
- Ensure customer is not banned

### Getting Help

1. Check [API Documentation](MULTI_USER_API.md)
2. Review error messages in API responses
3. Enable logging in your application
4. Contact support with:
   - Seller ID
   - Request/response details
   - Timestamp of issue
   - Error messages

## Next Steps

1. **Set up your production environment**
   - Use production Stripe keys
   - Configure HTTPS
   - Set up monitoring

2. **Build your frontend**
   - Use the API documentation
   - Implement authentication
   - Create dashboard UI

3. **Configure webhooks**
   - Set up webhook endpoint
   - Implement signature verification
   - Handle all event types

4. **Test payment flows**
   - Use Stripe test mode
   - Test success and failure cases
   - Verify access granting

5. **Monitor and optimize**
   - Track conversion rates
   - Monitor member churn
   - Analyze revenue trends

## Additional Resources

- [Full API Documentation](MULTI_USER_API.md)
- [Stripe Documentation](https://stripe.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- Platform Support: support@example.com
