# API Response Format

All API endpoints in this service return responses in a standardized format for consistency and predictability.

## Standard Response Format

```json
{
  "success": bool,
  "message": str,
  "data": dict | null,
  "error": {
    "code": str,
    "description": str
  } | null
}
```

### Fields

- **success** (boolean, required): Indicates whether the request was successful
- **message** (string, required): Human-readable message describing the result
- **data** (object|null, optional): Response data when successful. Structure varies by endpoint.
- **error** (object|null, optional): Error details when `success` is `false`
  - **code** (string): Machine-readable error code (e.g., "INVALID_REQUEST", "NOT_FOUND")
  - **description** (string): Human-readable error description

## Examples

### Successful Response

```json
{
  "success": true,
  "message": "Access granted until 2024-12-31 23:59:59 UTC",
  "data": {
    "user_id": "507f1f77bcf86cd799439011",
    "invites": {
      "-1001234567890": "https://t.me/+abc123xyz"
    },
    "period_end": "2024-12-31T18:29:59+00:00",
    "period_end": "2024-12-31T23:59:59+05:30",
    "errors": null
  },
  "error": null
}
```

### Error Response

```json
{
  "success": false,
  "message": "Failed to grant access",
  "data": null,
  "error": {
    "code": "CHANNEL_NOT_FOUND",
    "description": "Channel with ID -1001234567890 not found in database"
  }
}
```

### Partial Success Response

Some endpoints may return partial success (e.g., grant access to multiple channels where some fail):

```json
{
  "success": false,
  "message": "Access granted with some errors",
  "data": {
    "user_id": "507f1f77bcf86cd799439011",
    "invites": {
      "-1001234567890": "https://t.me/+abc123xyz"
    },
    "period_end": "2024-12-31T18:29:59+00:00",
    "period_end": "2024-12-31T23:59:59+05:30",
    "errors": {
      "-1009876543210": "channel_not_found"
    }
  },
  "error": {
    "code": "PARTIAL_FAILURE",
    "description": "Failed to grant access to 1 channel(s)"
  }
}
```

## Timezone Handling

All datetime fields are provided in both UTC and UTC:

- **UTC fields**: End with `_utc` (e.g., `period_end`)
- **IST fields**: End with `_ist` (e.g., `period_end`)

**Period End Calculation**: When granting access for N days, the period ends at **23:59:59 UTC** on the Nth day from now.

Example:
- Request: `period_days: 30`
- Today: 2024-01-01
- Period end: 2024-01-30 23:59:59 UTC (2024-01-30 18:29:59 UTC)

## Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_REQUEST` | Request validation failed |
| `NOT_FOUND` | Resource not found |
| `USER_NOT_FOUND` | User with specified ID not found |
| `CHANNEL_NOT_FOUND` | Channel not found in database |
| `NO_TELEGRAM_ID` | User hasn't linked their Telegram account |
| `INSUFFICIENT_PERMISSIONS` | Bot lacks required permissions |
| `PERMISSION_CHECK_FAILED` | Failed to verify bot permissions |
| `GRANT_ACCESS_FAILED` | Failed to grant channel access |
| `PARTIAL_FAILURE` | Some operations succeeded, some failed |
| `REMOVAL_FAILED` | Failed to remove user from channel |
| `CHAT_NOT_FOUND` | Telegram chat/channel not found |

## Endpoint-Specific Data Formats

### Health Check (`GET /health`)

**Success Data:**
```json
{
  "status": "UP",
  "service": "telegram"
}
```

### Root (`GET /`)

**Success Data:**
```json
{
  "service": "Telegram Service",
  "version": "1.0.0",
  "description": "Standalone Telegram bot service for channel access management",
  "docs": "/docs"
}
```

### Grant Access (`POST /api/telegram/grant-access`)

**Request:**
```json
{
  "ext_user_id": "user123",
  "chat_ids": [-1001234567890, -1009876543210],
  "period_days": 30,
  "ref": "payment_abc123"
}
```

**Success Data:**
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "invites": {
    "-1001234567890": "https://t.me/+abc123xyz",
    "-1009876543210": "join_request_model"
  },
  "period_end": "2024-01-30T18:29:59+00:00",
  "period_end": "2024-01-30T23:59:59+05:30",
  "errors": null
}
```

### Add Channel (`POST /api/telegram/channels`)

**Request:**
```json
{
  "chat_id": -1001234567890,
  "name": "Premium Trading Channel",
  "join_model": "invite_link",
  "invite_ttl_seconds": 86400,
  "invite_member_limit": 1
}
```

**Success Data:**
```json
{
  "chat_id": -1001234567890,
  "stored_chat_id": -1001234567890,
  "name": "Premium Trading Channel",
  "join_model": "invite_link",
  "checks": {
    "bot_id": 123456789,
    "chat_found": true,
    "chat_type": "channel",
    "chat_title": "Premium Trading Channel",
    "bot_member_status": "administrator",
    "is_admin": true,
    "permissions": {
      "can_invite_users": true,
      "can_manage_chat": true,
      "can_restrict_members": true
    }
  }
}
```

### Force Remove (`POST /api/telegram/force-remove`)

**Request:**
```json
{
  "ext_user_id": "user123",
  "chat_id": -1001234567890,
  "reason": "Payment refund",
  "dry_run": false
}
```

**Success Data:**
```json
{
  "removed": true,
  "expired_membership": true,
  "details": {
    "telegram_user_id": 987654321,
    "membership_found": true,
    "dry_run": false
  }
}
```

## Webhook Responses

Webhook endpoints (`/webhooks/telegram/{secret_path}`) return simple HTTP status codes:
- `200 OK`: Webhook processed successfully
- `404 Not Found`: Invalid webhook secret path

They do not follow the standard response format to comply with Telegram's webhook requirements.
