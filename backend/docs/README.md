# Documentation

Complete documentation for the Telegram Paid Subscriber Service.

## Table of Contents

1. [Setup Guide](setup.md) - Installation and initial configuration
2. [User Guide](user-guide.md) - Daily operations and usage
3. [API Documentation](api.md) - Complete API reference

## Quick Links

### For New Users

Start here:
1. [Setup Guide](setup.md) - Get the service running
2. [User Guide](user-guide.md#granting-access) - Learn how to grant access

### For Developers

- [API Documentation](api.md) - REST API reference
- [Repository Structure](../README.md#directory-structure) - Code organization
- [Agent Instructions](../.github/agents/instructions.md) - Development guidelines

### For Operations

- [Monitoring](user-guide.md#monitoring) - Health checks and metrics
- [Troubleshooting](user-guide.md#troubleshooting) - Common issues and solutions

## Documentation Overview

### [Setup Guide](setup.md)

Complete installation and configuration guide:

- Creating a Telegram bot
- Installing dependencies
- Configuring environment variables
- Setting up MongoDB
- Deploying with Docker
- Production checklist

**Start here if**: You're setting up the service for the first time.

### [User Guide](user-guide.md)

Daily operations and usage guide:

- Managing channels
- Granting user access
- Monitoring the service
- Integration examples
- Troubleshooting common issues
- Best practices

**Start here if**: You have the service running and want to use it.

### [API Documentation](api.md)

Complete REST API reference:

- Endpoint descriptions
- Request/response formats
- Authentication (when implemented)
- Error handling
- Code examples (curl, Python)
- Best practices

**Start here if**: You're integrating the service with your application.

## Architecture

The service follows a clean architecture pattern:

```
HTTP Request → Router → Service → Bot API → Telegram
                ↓         ↓
              Validation  Database
```

### Key Components

- **FastAPI App** (`main.py`): Entry point, lifespan management
- **Routers** (`routers/`): HTTP endpoint handlers
- **Services** (`app/service.py`): Business logic
- **Bot API** (`app/bot_api.py`): Telegram API wrapper
- **Models** (`app/models.py`): Data structures
- **Config** (`config/`): Environment management
- **Database** (`app/database.py`): MongoDB operations

## Common Use Cases

### Use Case 1: Paid Channel Access

**Scenario**: Grant users access to premium Telegram channels after payment.

**Implementation**:
1. User completes payment in your system
2. Your payment webhook calls `POST /api/telegram/grant-access`
3. Service creates invite link and membership
4. You send invite link to user
5. User joins channel
6. Service auto-removes user after expiration

**Documentation**: [API Documentation](api.md#grant-access)

### Use Case 2: Subscription Management

**Scenario**: Manage recurring subscriptions with automatic renewal.

**Implementation**:
1. User subscribes (monthly/yearly)
2. On each billing cycle, call grant-access with period_days
3. Service extends membership automatically
4. If payment fails, membership expires naturally
5. Service removes user from channel

**Documentation**: [User Guide](user-guide.md#granting-access)

### Use Case 3: Multi-Tier Access

**Scenario**: Different subscription tiers with different channel access.

**Implementation**:
1. Define tier → channel mapping in your application
2. On subscription, grant access to tier-specific channels
3. Use different period_days for different tiers
4. Upgrade: grant access to additional channels
5. Downgrade: let old memberships expire naturally

**Code Example**:
```python
tier_channels = {
    'basic': [-1001234567890],
    'premium': [-1001234567890, -1009876543210],
    'vip': [-1001234567890, -1009876543210, -1001111111111]
}

async def grant_tier_access(user_id: str, tier: str, days: int):
    chat_ids = tier_channels.get(tier, [])
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_SERVICE_URL}/api/telegram/grant-access",
            json={
                "ext_user_id": user_id,
                "chat_ids": chat_ids,
                "period_days": days,
                "ref": f"subscription_{tier}_{user_id}"
            }
        )
    
    return response.json()
```

## Integration Patterns

### Pattern 1: Direct Integration

Your backend calls the service directly:

```python
# Your payment handler
async def handle_payment_success(payment):
    result = await telegram_service.grant_access(
        user_id=payment.user_id,
        chat_ids=get_channels_for_plan(payment.plan),
        period_days=payment.period
    )
    
    # Send invite links to user
    await send_email_with_invites(payment.user_id, result['invites'])
```

### Pattern 2: Queue-Based Integration

Use a message queue for reliability:

```python
# Payment handler enqueues task
async def handle_payment_success(payment):
    await queue.enqueue('grant_telegram_access', {
        'user_id': payment.user_id,
        'plan': payment.plan,
        'period': payment.period
    })

# Worker processes queue
async def process_grant_access(task):
    result = await telegram_service.grant_access(**task)
    # Handle result
```

### Pattern 3: Webhook Integration

Service sends webhooks for membership events (requires implementation):

```python
# In your webhook handler
@app.post("/webhooks/telegram")
async def telegram_webhook(event: TelegramEvent):
    if event.type == "membership.expired":
        # Update user in your database
        await update_user_access(event.user_id, expired=True)
    
    return {"ok": True}
```

## Error Handling

The service uses standard HTTP status codes:

- **2xx**: Success
- **4xx**: Client error (bad request, validation failure)
- **5xx**: Server error (service unavailable, internal error)

Always check the response status:

```python
response = await client.post(url, json=data)

if response.status_code == 200:
    result = response.json()
    # Process success
elif response.status_code == 422:
    errors = response.json()['detail']
    # Handle validation errors
else:
    # Handle error
    logger.error(f"Grant access failed: {response.text}")
```

## Security Considerations

1. **API Authentication**: Currently not implemented. **Add this for production.**
2. **HTTPS Only**: Required by Telegram and recommended for all traffic
3. **Rate Limiting**: Not implemented. **Add this for production.**
4. **Input Validation**: Handled by Pydantic models
5. **Secret Management**: Use environment variables, never commit secrets

## Performance Tips

1. **Batch Operations**: Grant access to multiple channels in one call
2. **Async Operations**: Use async/await for all I/O operations
3. **Connection Pooling**: Motor (MongoDB driver) handles this automatically
4. **Caching**: Consider caching channel configurations
5. **Monitoring**: Track API response times and error rates

## Testing

The service includes a comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov=routers --cov=config

# Run specific test file
pytest tests/test_api.py -v

# Run by marker
pytest -m unit
pytest -m integration
```

## Contributing

1. Read [Agent Instructions](../.github/agents/instructions.md)
2. Follow the existing code structure
3. Add tests for new features
4. Update documentation
5. Run pre-push validation before committing

## Support

- **Setup Issues**: Check [Setup Guide](setup.md) and [Troubleshooting](user-guide.md#troubleshooting)
- **Usage Questions**: See [User Guide](user-guide.md)
- **API Questions**: See [API Documentation](api.md)
- **Bugs**: Open a GitHub issue with reproduction steps
- **Feature Requests**: Open a GitHub issue with use case description

## Version History

See [CHANGELOG](../logs/CHANGELOG.md) for version history and migration guides.

## License

[Add your license information here]
