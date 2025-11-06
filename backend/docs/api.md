# API Documentation

Complete API reference for the Telegram Paid Subscriber Service.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Grant Access](#grant-access)
  - [Webhook](#webhook)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Overview

The Telegram Paid Subscriber Service provides a REST API for managing paid access to Telegram channels. The service handles:

- User access grants with time-limited memberships
- Automatic invite link generation
- Webhook handling for join request approvals
- Membership expiration and cleanup

## Authentication

Currently, the service does not implement authentication. **In production, you should:**

1. Add API key authentication
2. Use IP whitelisting
3. Deploy behind a reverse proxy with authentication
4. Use HTTPS only

## Base URL

```
Development: http://localhost:8001
Production: https://your-domain.com
```

## Endpoints

### Health Check

Check if the service is running and healthy.

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "UP",
  "service": "telegram"
}
```

**Status Codes:**
- `200 OK`: Service is healthy

**Example:**

```bash
curl http://localhost:8001/health
```

---

### Grant Access

Grant a user access to one or more Telegram channels for a specified period.

**Endpoint:** `POST /api/telegram/grant-access`

**Request Body:**

```json
{
  "ext_user_id": "user123",
  "chat_ids": [-1001234567890, -1009876543210],
  "period_days": 30,
  "ref": "payment_abc123"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ext_user_id` | string | Yes | External user ID from your system |
| `chat_ids` | array[int] | Yes | List of Telegram chat IDs (negative for channels) |
| `period_days` | int | Yes | Number of days to grant access |
| `ref` | string | No | Reference ID (e.g., payment ID) for tracking |

**Response:**

```json
{
  "success": true,
  "invites": [
    {
      "chat_id": -1001234567890,
      "invite_link": "https://t.me/+abc123xyz",
      "expire_at": "2024-01-15T10:30:00Z"
    }
  ],
  "memberships": [
    {
      "chat_id": -1001234567890,
      "status": "active",
      "current_period_end": "2024-02-14T10:30:00Z"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Access granted successfully
- `400 Bad Request`: Invalid request parameters
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Example:**

```bash
curl -X POST http://localhost:8001/api/telegram/grant-access \
  -H "Content-Type: application/json" \
  -d '{
    "ext_user_id": "user123",
    "chat_ids": [-1001234567890],
    "period_days": 30,
    "ref": "payment_abc123"
  }'
```

**Python Example:**

```python
import httpx

async def grant_access(user_id: str, chat_ids: list[int], days: int):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/telegram/grant-access",
            json={
                "ext_user_id": user_id,
                "chat_ids": chat_ids,
                "period_days": days,
                "ref": f"payment_{user_id}"
            }
        )
        return response.json()

# Usage
result = await grant_access("user123", [-1001234567890], 30)
print(result["invites"][0]["invite_link"])
```

---

### Webhook

Receive updates from Telegram Bot API. This endpoint is automatically configured during service startup.

**Endpoint:** `POST /api/telegram/webhook/{secret_path}`

**Note:** This endpoint is for Telegram's use only. Do not call it directly from your application.

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `secret_path` | string | Yes | Secret path configured in `TELEGRAM_WEBHOOK_SECRET_PATH` |

**Request Body:**

Telegram sends update objects as defined in the [Telegram Bot API](https://core.telegram.org/bots/api#update).

**Response:**

```json
{
  "ok": true
}
```

**Status Codes:**
- `200 OK`: Update processed successfully
- `404 Not Found`: Invalid secret path

---

## Data Models

### TelegramUser

Represents a user in the system.

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "ext_user_id": "user123",
  "telegram_user_id": 123456789,
  "telegram_username": "testuser",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Channel

Represents a Telegram channel configuration.

```json
{
  "_id": "507f1f77bcf86cd799439012",
  "chat_id": -1001234567890,
  "name": "Premium Channel",
  "join_model": "invite_link",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Membership

Represents a user's membership to a channel.

```json
{
  "_id": "507f1f77bcf86cd799439013",
  "user_id": "507f1f77bcf86cd799439011",
  "chat_id": -1001234567890,
  "status": "active",
  "current_period_end": "2024-02-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Membership Statuses:**
- `active`: User has active access
- `cancelled`: User cancelled but still has access until period end
- `expired`: Membership has expired

### Invite

Represents a Telegram invite link.

```json
{
  "_id": "507f1f77bcf86cd799439014",
  "user_id": "507f1f77bcf86cd799439011",
  "chat_id": -1001234567890,
  "invite_link": "https://t.me/+abc123xyz",
  "expire_at": "2024-01-01T01:00:00Z",
  "member_limit": 1,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format.

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 400 | Bad Request | Invalid parameters, missing required fields |
| 404 | Not Found | Resource not found, invalid endpoint |
| 422 | Unprocessable Entity | Validation error, invalid data types |
| 500 | Internal Server Error | Server error, database connection issues |
| 503 | Service Unavailable | Service not initialized, dependencies unavailable |

### Error Examples

**Validation Error:**

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "chat_ids"],
      "msg": "Field required",
      "input": {"ext_user_id": "user123", "period_days": 30}
    }
  ]
}
```

**Service Error:**

```json
{
  "detail": "Telegram services not initialized"
}
```

---

## Rate Limiting

The service does not currently implement rate limiting. **For production, consider:**

1. **Application-level rate limiting**: Use middleware like `slowapi`
2. **Reverse proxy rate limiting**: Configure NGINX or similar
3. **API Gateway**: Use cloud provider's API gateway with rate limiting

**Example with slowapi:**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/telegram/grant-access")
@limiter.limit("10/minute")
async def grant_access(request: Request, ...):
    ...
```

---

## Best Practices

1. **Always use HTTPS** in production
2. **Implement authentication** for all endpoints
3. **Validate all inputs** before processing
4. **Handle errors gracefully** and return meaningful messages
5. **Log all access grants** for audit purposes
6. **Monitor webhook delivery** from Telegram
7. **Set up health check monitoring** for uptime tracking
8. **Use idempotency keys** for critical operations
9. **Implement retry logic** for external API calls
10. **Keep secrets secure** and never commit them to version control

---

## Support

For issues or questions:

1. Check the [User Guide](user-guide.md)
2. Review the [Setup Guide](setup.md)
3. Check application logs
4. Open an issue on GitHub with:
   - Request/response details
   - Error messages
   - Environment information
