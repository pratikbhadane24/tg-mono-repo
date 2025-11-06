# Multi-User Platform API Documentation

Complete API reference for the Telegram Paid Subscriber Service - Multi-User SaaS Platform.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Authentication](#authentication)
- [Seller APIs](#seller-apis)
- [Payment APIs](#payment-apis)
- [Customer APIs](#customer-apis)
- [Webhook System](#webhook-system)
- [Data Models](#data-models)
- [Integration Guide](#integration-guide)

## Overview

The Telegram Paid Subscriber Service now operates as a multi-user SaaS platform where:

- **SELLERS** (your customers) register and manage their own Telegram channels
- **END-USERS** (seller's customers) purchase access to channels
- **Platform** handles payments, authentication, and infrastructure

### Key Features

1. **Seller Management** - Registration, authentication, and profile management
2. **Payment Routing** - Sellers can use their own Stripe account or the platform's
3. **Channel Management** - Each seller manages their own channels
4. **Dashboard APIs** - Statistics, member management, and analytics
5. **Webhook System** - Real-time event notifications to sellers
6. **Multi-tenancy** - Complete data isolation between sellers

## Architecture

### Database Structure

The platform uses a multi-tenant architecture with the following collections:

```
sellers               # Seller accounts
seller_channels       # Channels owned by sellers
seller_subscriptions  # Platform subscriptions for sellers
payments              # Payment transactions
webhook_configs       # Webhook configurations
users                 # End-user accounts (linked to telegram_user_id)
memberships           # User memberships to channels
channels              # Global channel registry
audits                # Audit logs
```

### Data Isolation

All seller data is isolated using `seller_id` field:
- Sellers can only access their own channels
- Sellers can only see their own customers/members
- Payment records are tracked per seller

## Authentication

### Methods

The platform supports two authentication methods:

#### 1. JWT Bearer Token

Used for web applications and interactive sessions.

**Login Flow:**
```bash
POST /api/sellers/login
{
  "email": "seller@example.com",
  "password": "securepassword"
}

Response:
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

**Using the token:**
```bash
curl -H "Authorization: Bearer eyJ..." https://api.example.com/api/sellers/me
```

#### 2. API Key

Used for server-to-server integration and automation.

**Obtain API Key:**
API key is provided during registration or available in seller dashboard.

**Using the API key:**
```bash
curl -H "X-API-Key: sk_..." https://api.example.com/api/sellers/stats
```

### Security Best Practices

- Store JWT tokens securely (httpOnly cookies for web)
- Never expose API keys in client-side code
- Rotate API keys periodically
- Use HTTPS only in production
- Implement rate limiting

## Seller APIs

### Registration

Register a new seller account.

**Endpoint:** `POST /api/sellers/register`

**Request:**
```json
{
  "email": "seller@example.com",
  "password": "SecurePassword123!",
  "company_name": "My Awesome Company"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Seller registered successfully",
  "data": {
    "seller_id": "507f1f77bcf86cd799439011",
    "email": "seller@example.com",
    "api_key": "sk_abc123xyz..."
  }
}
```

### Login

Authenticate and get access tokens.

**Endpoint:** `POST /api/sellers/login`

**Request:**
```json
{
  "email": "seller@example.com",
  "password": "SecurePassword123!"
}
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

### Get Profile

Get current seller information.

**Endpoint:** `GET /api/sellers/me`

**Headers:** `Authorization: Bearer {token}` or `X-API-Key: {api_key}`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "email": "seller@example.com",
    "company_name": "My Awesome Company",
    "is_active": true,
    "is_verified": true,
    "subscription_status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

### Update Stripe Keys

Configure seller's own Stripe account for payments.

**Endpoint:** `POST /api/sellers/stripe-keys`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "publishable_key": "pk_live_...",
  "secret_key": "sk_live_..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Stripe keys updated successfully",
  "data": {
    "status": "updated"
  }
}
```

### Create Channel

Register a new Telegram channel.

**Endpoint:** `POST /api/sellers/channels`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "chat_id": -1001234567890,
  "name": "Premium Crypto Signals",
  "description": "Daily crypto trading signals",
  "price_per_month": 4900
}
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

### List Channels

Get all channels for the seller.

**Endpoint:** `GET /api/sellers/channels`

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "success": true,
  "message": "Found 3 channel(s)",
  "data": [
    {
      "id": "507f1f77bcf86cd799439012",
      "chat_id": -1001234567890,
      "name": "Premium Crypto Signals",
      "description": "Daily crypto trading signals",
      "price_per_month": 4900,
      "total_members": 150,
      "active_members": 142,
      "is_active": true
    }
  ]
}
```

### List Members

Get members across seller's channels.

**Endpoint:** `GET /api/sellers/members?chat_id={chat_id}&status={status}`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `chat_id` (optional): Filter by specific channel
- `status` (optional): Filter by status (active, cancelled, expired)

**Response:**
```json
{
  "success": true,
  "message": "Found 142 member(s)",
  "data": [
    {
      "membership": {
        "_id": "507f1f77bcf86cd799439013",
        "user_id": "507f1f77bcf86cd799439011",
        "chat_id": -1001234567890,
        "status": "active",
        "current_period_end": "2024-02-01T00:00:00Z"
      },
      "user": {
        "_id": "507f1f77bcf86cd799439011",
        "ext_user_id": "user123",
        "telegram_user_id": 123456789,
        "telegram_username": "johndoe"
      }
    }
  ]
}
```

### Get Statistics

Get dashboard statistics.

**Endpoint:** `GET /api/sellers/stats`

**Headers:** `Authorization: Bearer {token}`

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

### Create Webhook

Register a webhook to receive events.

**Endpoint:** `POST /api/sellers/webhooks`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "url": "https://myapp.com/webhooks/telegram",
  "events": [
    "member.joined",
    "member.left",
    "payment.succeeded",
    "subscription.expired"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Webhook created successfully",
  "data": {
    "webhook_id": "507f1f77bcf86cd799439014",
    "url": "https://myapp.com/webhooks/telegram",
    "secret": "whsec_abc123...",
    "events": ["member.joined", "member.left", "payment.succeeded", "subscription.expired"]
  }
}
```

### List Webhooks

Get all webhook configurations.

**Endpoint:** `GET /api/sellers/webhooks`

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "success": true,
  "message": "Found 1 webhook(s)",
  "data": [
    {
      "id": "507f1f77bcf86cd799439014",
      "url": "https://myapp.com/webhooks/telegram",
      "events": ["member.joined", "member.left"],
      "is_active": true,
      "last_triggered": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Payment APIs

### Create Checkout Session

Create a Stripe checkout session for subscriptions.

**Endpoint:** `POST /api/payments/checkout`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "price_id": "price_1234567890",
  "success_url": "https://myapp.com/success",
  "cancel_url": "https://myapp.com/cancel",
  "customer_email": "customer@example.com",
  "metadata": {
    "channel_id": "507f1f77bcf86cd799439012",
    "plan": "monthly"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Checkout session created",
  "data": {
    "session_id": "cs_test_...",
    "url": "https://checkout.stripe.com/c/pay/cs_test_..."
  }
}
```

### Create Payment Intent

Create a payment intent for custom payment flows.

**Endpoint:** `POST /api/payments/payment-intent`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "amount": 4900,
  "currency": "usd",
  "customer_email": "customer@example.com",
  "metadata": {
    "channel_id": "507f1f77bcf86cd799439012"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Payment intent created",
  "data": {
    "client_secret": "pi_..._secret_...",
    "payment_intent_id": "pi_..."
  }
}
```

### Get Subscription

Get subscription details.

**Endpoint:** `GET /api/payments/subscription/{subscription_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "sub_...",
    "status": "active",
    "current_period_start": 1704067200,
    "current_period_end": 1706745600,
    "cancel_at_period_end": false
  }
}
```

### List Payments

Get payment history.

**Endpoint:** `GET /api/sellers/payments?limit=100`

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "success": true,
  "message": "Found 15 payment(s)",
  "data": [
    {
      "id": "507f1f77bcf86cd799439015",
      "amount": 4900,
      "currency": "usd",
      "status": "succeeded",
      "stripe_payment_intent_id": "pi_...",
      "used_seller_stripe": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Customer APIs

### Grant Access (Existing API)

Grant a customer access to channels after payment.

**Endpoint:** `POST /api/telegram/grant-access`

**Headers:** `Authorization: Bearer {token}` or `X-API-Key: {api_key}`

**Request:**
```json
{
  "ext_user_id": "customer_12345",
  "chat_ids": [-1001234567890],
  "period_days": 30,
  "ref": "payment_abc123"
}
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

### Force Remove Member

Forcefully remove a member from a channel.

**Endpoint:** `POST /api/telegram/force-remove`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "ext_user_id": "customer_12345",
  "chat_id": -1001234567890,
  "reason": "Policy violation",
  "dry_run": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "User removed from chat. Membership expired: true",
  "data": {
    "removed": true,
    "expired_membership": true,
    "details": {
      "telegram_user_id": 123456789,
      "membership_found": true
    }
  }
}
```

## Webhook System

### Webhook Events

The platform sends webhooks to sellers for the following events:

#### member.joined
Sent when a user joins a channel.

```json
{
  "event": "member.joined",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "chat_id": -1001234567890,
    "user_id": "507f1f77bcf86cd799439011",
    "ext_user_id": "customer_12345",
    "telegram_user_id": 123456789,
    "telegram_username": "johndoe"
  }
}
```

#### member.left
Sent when a user leaves or is removed from a channel.

```json
{
  "event": "member.left",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "chat_id": -1001234567890,
    "user_id": "507f1f77bcf86cd799439011",
    "telegram_user_id": 123456789,
    "reason": "left|kicked|expired"
  }
}
```

#### payment.succeeded
Sent when a payment is successful.

```json
{
  "event": "payment.succeeded",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "payment_id": "507f1f77bcf86cd799439015",
    "amount": 4900,
    "currency": "usd",
    "customer_id": "507f1f77bcf86cd799439011",
    "ext_user_id": "customer_12345",
    "stripe_payment_intent_id": "pi_..."
  }
}
```

#### subscription.expired
Sent when a subscription expires.

```json
{
  "event": "subscription.expired",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "membership_id": "507f1f77bcf86cd799439013",
    "user_id": "507f1f77bcf86cd799439011",
    "ext_user_id": "customer_12345",
    "chat_id": -1001234567890
  }
}
```

### Webhook Signature Verification

All webhooks are signed with HMAC-SHA256. Verify signatures to ensure authenticity.

**Python Example:**
```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

# Usage
@app.post("/webhooks/telegram")
async def handle_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Webhook-Signature")
    secret = "whsec_abc123..."  # From webhook creation
    
    if not verify_webhook_signature(payload, signature, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook...
```

## Integration Guide

### Complete Integration Flow

#### 1. Seller Onboarding

```python
import httpx

# Step 1: Register seller
async def register_seller(email: str, password: str, company_name: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/api/sellers/register",
            json={
                "email": email,
                "password": password,
                "company_name": company_name
            }
        )
        return response.json()

# Step 2: Login and get tokens
async def login_seller(email: str, password: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/api/sellers/login",
            json={"email": email, "password": password}
        )
        return response.json()
```

#### 2. Channel Setup

```python
# Step 3: Create channel
async def create_channel(token: str, chat_id: int, name: str, price: int):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/api/sellers/channels",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "chat_id": chat_id,
                "name": name,
                "price_per_month": price
            }
        )
        return response.json()
```

#### 3. Payment Setup

```python
# Step 4: Configure Stripe (optional - use own keys)
async def setup_stripe(token: str, publishable: str, secret: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/api/sellers/stripe-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "publishable_key": publishable,
                "secret_key": secret
            }
        )
        return response.json()
```

#### 4. Customer Payment Flow

```python
# Step 5: Create checkout for customer
async def create_checkout(token: str, price_id: str, customer_email: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/api/payments/checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "price_id": price_id,
                "success_url": "https://myapp.com/success",
                "cancel_url": "https://myapp.com/cancel",
                "customer_email": customer_email
            }
        )
        return response.json()

# Step 6: After payment success, grant access
async def grant_channel_access(api_key: str, ext_user_id: str, chat_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/api/telegram/grant-access",
            headers={"X-API-Key": api_key},
            json={
                "ext_user_id": ext_user_id,
                "chat_ids": [chat_id],
                "period_days": 30,
                "ref": "payment_xyz"
            }
        )
        return response.json()
```

#### 5. Webhook Integration

```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()

WEBHOOK_SECRET = "whsec_abc123..."

@app.post("/webhooks/telegram")
async def handle_telegram_webhook(request: Request):
    # Verify signature
    payload = await request.body()
    signature = request.headers.get("X-Webhook-Signature")
    
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
        # Handle new member
        await handle_member_joined(event["data"])
    elif event["event"] == "payment.succeeded":
        # Handle successful payment
        await handle_payment_succeeded(event["data"])
    
    return {"status": "ok"}
```

### Best Practices

1. **Security**
   - Always use HTTPS in production
   - Verify webhook signatures
   - Store API keys securely (environment variables, secrets manager)
   - Rotate API keys periodically
   - Implement rate limiting

2. **Error Handling**
   - Implement retry logic for API calls
   - Handle webhook failures gracefully
   - Log all errors for debugging
   - Use idempotency keys for critical operations

3. **Performance**
   - Cache seller data when appropriate
   - Use pagination for large result sets
   - Implement webhook queuing for high volume
   - Monitor API rate limits

4. **Testing**
   - Test with Stripe test mode keys
   - Verify webhook deliveries
   - Test payment flows end-to-end
   - Validate error scenarios

## Support

For issues or questions:

1. Check this documentation
2. Review API examples
3. Check application logs
4. Contact support with:
   - Request/response details
   - Error messages
   - Timestamp of issue
   - Seller ID or email
