# User Guide

Complete guide to using the Telegram Paid Subscriber Service.

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Channel Management](#channel-management)
- [Granting Access](#granting-access)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Introduction

The Telegram Paid Subscriber Service is a standalone FastAPI application that manages paid access to Telegram channels. It provides:

- **Automated access grants**: Programmatically grant users access to channels
- **Time-limited memberships**: Memberships expire automatically after the specified period
- **Invite link generation**: Creates unique, time-limited invite links for each user
- **Join request handling**: Automatically approves join requests for authorized users
- **Scheduled cleanup**: Removes expired members from channels
- **Audit logging**: Tracks all access grants and membership changes

## Prerequisites

Before you begin, ensure you have:

1. **Telegram Bot**
   - Create a bot via [@BotFather](https://t.me/botfather)
   - Save your bot token (format: `123456789:ABC-DEF1234567890`)
   - Add bot as administrator to your channels with these permissions:
     - Invite users via link
     - Ban users (for cleanup)
     - Manage chat

2. **Infrastructure**
   - Python 3.13 or higher
   - MongoDB 5.0 or higher
   - Public HTTPS URL (for webhook, required by Telegram)

3. **System Requirements**
   - 1GB RAM minimum (2GB recommended)
   - 10GB disk space
   - Stable internet connection

## Installation

### Option 1: Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/tg-paid-subscriber-service.git
cd tg-paid-subscriber-service

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Option 2: Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/tg-paid-subscriber-service.git
cd tg-paid-subscriber-service

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Using Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/tg-paid-subscriber-service.git
cd tg-paid-subscriber-service

# Build the image
docker build -t telegram-service .

# Run with docker-compose (includes MongoDB)
docker-compose up -d
```

## Configuration

### 1. Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure the following:

```env
# Required: Your Telegram bot token from @BotFather
TELEGRAM_BOT_TOKEN=123456789:ABC-DEF1234567890

# Required: Secret path for webhook URL (use a random string)
TELEGRAM_WEBHOOK_SECRET_PATH=my_random_secret_12345

# Required: Your public HTTPS URL
BASE_URL=https://telegram.yourdomain.com

# Required: MongoDB connection string
MONGODB_URI=mongodb://localhost:27017/telegram

# Optional: Invite link settings
INVITE_LINK_TTL_SECONDS=900      # 15 minutes
INVITE_LINK_MEMBER_LIMIT=1       # 1 user per link

# Optional: Scheduler settings
SCHEDULER_INTERVAL_SECONDS=60    # Check every minute

# Optional: Default join model
JOIN_MODEL=invite_link           # or 'join_request'
```

### 2. MongoDB Setup

**Local MongoDB:**

```bash
# Install MongoDB
# Ubuntu/Debian:
sudo apt-get install mongodb

# macOS with Homebrew:
brew install mongodb-community

# Start MongoDB
sudo systemctl start mongod
```

**MongoDB Atlas (Cloud):**

1. Create a free account at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster
3. Get connection string
4. Update `MONGODB_URI` in `.env`

### 3. Channel Configuration

Add your Telegram channels to the database using the CLI:

```bash
# Add a channel (get chat_id from @userinfobot)
python -m app.cli add -1001234567890 "Premium Channel"

# Add channel with custom join model
python -m app.cli add -1001234567890 "Premium Channel" --join-model=join_request

# List all configured channels
python -m app.cli list

# Update channel settings
python -m app.cli update -1001234567890 --name="VIP Channel"

# Remove a channel
python -m app.cli remove -1001234567890
```

**Finding your chat ID:**

1. Add [@userinfobot](https://t.me/userinfobot) to your channel
2. Forward a message from the channel to the bot
3. The bot will reply with the chat ID (negative number)

## Channel Management

### Join Models

The service supports two join models:

#### 1. Invite Link Model (Default)

- Creates unique invite links for each user
- Links expire after a configurable time (default: 15 minutes)
- Limited to 1 user per link
- User clicks link to join
- Best for: Public or semi-public channels

**Configuration:**

```bash
python -m app.cli add -1001234567890 "Channel" --join-model=invite_link
```

#### 2. Join Request Model

- User requests to join
- Bot automatically approves authorized users
- No invite links needed
- Best for: Private channels with controlled access

**Configuration:**

```bash
python -m app.cli add -1001234567890 "Channel" --join-model=join_request
```

**Note:** For join request model, enable "Approve New Members" in your Telegram channel settings.

### Channel Permissions

Ensure your bot has these permissions in each channel:

1. Open Telegram channel
2. Go to channel settings
3. Add bot as administrator
4. Enable these permissions:
   - ✅ Manage chat
   - ✅ Delete messages
   - ✅ Ban users
   - ✅ Invite users via link
   - ✅ Add new admins

## Granting Access

### Programmatic Access

Grant access via API call:

```python
import httpx

async def grant_channel_access(user_id: str, channel_ids: list[int], days: int):
    """Grant user access to channels."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/telegram/grant-access",
            json={
                "ext_user_id": user_id,
                "chat_ids": channel_ids,
                "period_days": days,
                "ref": f"payment_{user_id}"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["invites"]
        else:
            raise Exception(f"Failed to grant access: {response.text}")

# Usage
invites = await grant_channel_access(
    user_id="user123",
    channel_ids=[-1001234567890],
    days=30
)

# Send invite link to user
invite_link = invites[0]["invite_link"]
print(f"Join here: {invite_link}")
```

### Typical Integration Flow

1. **User completes payment**
2. **Your payment handler calls grant_access API**
3. **Service returns invite links**
4. **You send invite links to user** (email, SMS, or in-app)
5. **User joins channels via links**
6. **Service tracks membership**
7. **Service auto-removes user after expiration**

## Monitoring

### Health Checks

Monitor service health:

```bash
# Check if service is up
curl http://localhost:8001/health

# Expected response:
# {"status":"UP","service":"telegram"}
```

### Logs

View application logs:

```bash
# If running with uvicorn/granian
tail -f logs/app.log

# If running with Docker
docker logs -f telegram-service

# If running with systemd
journalctl -u telegram-service -f
```

### Key Metrics to Monitor

1. **Service uptime**: Health endpoint availability
2. **Webhook delivery**: Check Telegram webhook info regularly
3. **Membership counts**: Active vs expired
4. **API response times**: Grant access endpoint latency
5. **Error rates**: Failed access grants or webhook processing

### Database Queries

Check membership status:

```javascript
// MongoDB shell
use telegram

// Count active memberships
db.memberships.count({status: "active"})

// Find expiring soon (next 24 hours)
db.memberships.find({
  status: "active",
  current_period_end: {
    $lte: new Date(Date.now() + 86400000)
  }
})

// Audit logs for a user
db.audits.find({ext_user_id: "user123"}).sort({created_at: -1})
```

## Troubleshooting

### Service Won't Start

**Problem:** Service fails to start

**Solutions:**

1. Check all required env vars are set:
   ```bash
   cat .env | grep -E "TELEGRAM_BOT_TOKEN|BASE_URL|MONGODB_URI"
   ```

2. Verify MongoDB is running:
   ```bash
   mongosh --eval "db.adminCommand('ping')"
   ```

3. Test bot token:
   ```bash
   curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
   ```

4. Check logs for specific errors:
   ```bash
   tail -50 logs/app.log
   ```

### Webhook Not Working

**Problem:** Telegram updates not received

**Solutions:**

1. Verify BASE_URL is HTTPS and publicly accessible
2. Check webhook registration:
   ```bash
   curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
   ```

3. Expected webhook URL format:
   ```
   https://your-domain.com/api/telegram/webhook/your_secret_path
   ```

4. Test webhook manually:
   ```bash
   curl -X POST https://your-domain.com/api/telegram/webhook/your_secret_path \
     -H "Content-Type: application/json" \
     -d '{"update_id":1,"message":{"text":"test"}}'
   ```

### Access Grant Fails

**Problem:** grant-access API call fails

**Solutions:**

1. Verify bot is admin in the channel
2. Check channel is in database:
   ```bash
   python -m app.cli list
   ```

3. Test with simple curl:
   ```bash
   curl -X POST http://localhost:8001/api/telegram/grant-access \
     -H "Content-Type: application/json" \
     -d '{
       "ext_user_id":"test123",
       "chat_ids":[-1001234567890],
       "period_days":30
     }'
   ```

4. Check service logs for errors

### Members Not Removed

**Problem:** Expired members still in channel

**Solutions:**

1. Check scheduler is running (logs show periodic runs)
2. Verify memberships in database:
   ```javascript
   db.memberships.find({status: "expired"})
   ```

3. Manually trigger cleanup (in Python):
   ```python
   from app.scheduler import MembershipScheduler
   scheduler = MembershipScheduler(service)
   await scheduler.cleanup_expired_memberships()
   ```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Telegram services not initialized" | Manager not started | Restart service |
| "Bot is not admin" | Missing permissions | Add bot as admin with correct permissions |
| "Chat not found" | Invalid chat_id | Verify chat_id is correct and negative |
| "Invalid bot token" | Wrong token | Check TELEGRAM_BOT_TOKEN in .env |
| "Webhook already set" | Webhook conflict | Delete old webhook via Bot API |

### Getting Help

If you're still experiencing issues:

1. Check the [API Documentation](api.md)
2. Review [Setup Guide](setup.md)
3. Search existing GitHub issues
4. Create a new issue with:
   - Service version
   - Environment details (OS, Python version)
   - Complete error messages
   - Steps to reproduce
   - Relevant log excerpts

## Best Practices

1. **Security**
   - Keep bot token secret
   - Use strong webhook secret path
   - Enable HTTPS only
   - Implement API authentication

2. **Reliability**
   - Monitor health endpoint
   - Set up log aggregation
   - Configure alerts for errors
   - Regular database backups

3. **Performance**
   - Use MongoDB indexes (auto-created by service)
   - Monitor database query performance
   - Scale horizontally if needed
   - Use connection pooling

4. **Maintenance**
   - Review audit logs regularly
   - Clean up old invite links
   - Monitor membership trends
   - Update dependencies regularly
