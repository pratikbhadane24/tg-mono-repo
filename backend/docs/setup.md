# Setup Guide

Step-by-step guide to set up the Telegram Paid Subscriber Service.

## Quick Start

For the impatient, here's the fastest way to get started:

```bash
# 1. Clone and install
git clone https://github.com/yourusername/tg-paid-subscriber-service.git
cd tg-paid-subscriber-service
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your bot token, webhook secret, and MongoDB URI

# 3. Add a channel
python -m app.cli add -1001234567890 "My Channel"

# 4. Run
uvicorn main:app --reload --port 8001
```

## Detailed Setup

### Step 1: Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Start a chat and send `/newbot`
3. Follow the prompts:
   - Choose a name (e.g., "My Paid Access Bot")
   - Choose a username (e.g., "my_paid_access_bot")
4. Save the bot token (format: `123456789:ABC-DEF1234567890`)

**Important:** Keep this token secret! Anyone with this token can control your bot.

### Step 2: Configure Your Channel

1. Create or open your Telegram channel
2. Add your bot as administrator:
   - Go to channel info → Administrators → Add Administrator
   - Search for your bot by username
   - Grant these permissions:
     - ✅ Manage chat
     - ✅ Delete messages
     - ✅ Ban users
     - ✅ Invite users via link
     - ✅ Add new admins

3. Get your channel's chat ID:
   - Add [@userinfobot](https://t.me/userinfobot) to your channel
   - Forward any message from the channel to @userinfobot
   - The bot replies with the chat ID (negative number like `-1001234567890`)
   - Remove @userinfobot from your channel

### Step 3: Install MongoDB

#### Option A: Local MongoDB

**Ubuntu/Debian:**
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify it's running
mongosh --eval "db.adminCommand('ping')"
```

**macOS:**
```bash
# Install with Homebrew
brew tap mongodb/brew
brew install mongodb-community@7.0

# Start MongoDB
brew services start mongodb-community@7.0

# Verify it's running
mongosh --eval "db.adminCommand('ping')"
```

**Windows:**
1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Run the installer
3. Follow the setup wizard
4. MongoDB Compass (GUI) is included

#### Option B: MongoDB Atlas (Cloud)

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free account
3. Create a new cluster (free tier available)
4. Wait for cluster creation (2-5 minutes)
5. Create a database user:
   - Database Access → Add New Database User
   - Choose password authentication
   - Save username and password
6. Whitelist your IP:
   - Network Access → Add IP Address
   - Choose "Allow access from anywhere" for testing
   - For production, whitelist specific IPs
7. Get connection string:
   - Clusters → Connect → Connect your application
   - Copy the connection string
   - Replace `<password>` with your database user password

### Step 4: Set Up HTTPS

Telegram requires HTTPS for webhooks. You have several options:

#### Option A: Self-hosted with Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot

# Get certificate (standalone mode)
sudo certbot certonly --standalone -d telegram.yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/telegram.yourdomain.com/
```

#### Option B: Reverse Proxy (Recommended)

Use NGINX or Caddy as a reverse proxy:

**NGINX Configuration:**

```nginx
server {
    listen 443 ssl http2;
    server_name telegram.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/telegram.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/telegram.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Caddy Configuration (automatic HTTPS):**

```
telegram.yourdomain.com {
    reverse_proxy localhost:8001
}
```

#### Option C: Cloud Platform

Deploy to a platform with automatic HTTPS:

- **Fly.io**: `fly launch`
- **Railway**: Connect GitHub repo
- **Render**: Connect GitHub repo
- **DigitalOcean App Platform**: Connect GitHub repo

### Step 5: Install the Service

```bash
# Clone repository
git clone https://github.com/yourusername/tg-paid-subscriber-service.git
cd tg-paid-subscriber-service

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### Step 6: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env  # or vim, code, etc.
```

Required configuration:

```env
# Bot token from @BotFather
TELEGRAM_BOT_TOKEN=123456789:ABC-DEF1234567890

# Random secret string (generate with: openssl rand -hex 32)
TELEGRAM_WEBHOOK_SECRET_PATH=your_random_secret_here

# Your public HTTPS URL
BASE_URL=https://telegram.yourdomain.com

# MongoDB connection string
MONGODB_URI=mongodb://localhost:27017/telegram
# Or for Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/telegram
```

Optional configuration:

```env
# Invite link expires after 15 minutes (900 seconds)
INVITE_LINK_TTL_SECONDS=900

# Each invite link can be used by 1 person
INVITE_LINK_MEMBER_LIMIT=1

# Check for expired memberships every minute
SCHEDULER_INTERVAL_SECONDS=60

# Default method for users to join
JOIN_MODEL=invite_link
```

### Step 7: Add Channels

Add your channels to the database:

```bash
# Add a channel
python -m app.cli add -1001234567890 "Premium Channel"

# Add multiple channels
python -m app.cli add -1001234567890 "Premium Channel"
python -m app.cli add -1009876543210 "VIP Channel"
python -m app.cli add -1001111111111 "Elite Channel"

# List all channels
python -m app.cli list

# Expected output:
# Configured Channels:
# ================================================================================
# Chat ID: -1001234567890
# Name: Premium Channel
# Join Model: invite_link
# Created: 2024-01-01 00:00:00
# --------------------------------------------------------------------------------
```

### Step 8: Run the Service

#### Development Mode

```bash
# Run with auto-reload (for development)
uvicorn main:app --reload --port 8001

# Or with more logging
uvicorn main:app --reload --port 8001 --log-level debug
```

#### Production Mode

**Option 1: Using Granian (Recommended)**

```bash
granian --interface asgi main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --workers 4 \
    --log-level info
```

**Option 2: Using Uvicorn**

```bash
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --workers 4 \
    --log-level info
```

**Option 3: Using systemd**

Create `/etc/systemd/system/telegram-service.service`:

```ini
[Unit]
Description=Telegram Paid Subscriber Service
After=network.target mongod.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/telegram-service
Environment="PATH=/opt/telegram-service/.venv/bin"
ExecStart=/opt/telegram-service/.venv/bin/granian --interface asgi main:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-service
sudo systemctl start telegram-service
sudo systemctl status telegram-service
```

### Step 9: Verify Installation

1. **Check service health:**
   ```bash
   curl http://localhost:8001/health
   # Expected: {"status":"UP","service":"telegram"}
   ```

2. **Check webhook registration:**
   ```bash
   curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
   # Should show your webhook URL
   ```

3. **Test access grant:**
   ```bash
   curl -X POST http://localhost:8001/api/telegram/grant-access \
     -H "Content-Type: application/json" \
     -d '{
       "ext_user_id":"test_user_001",
       "chat_ids":[-1001234567890],
       "period_days":1
     }'
   # Should return invite links
   ```

4. **Check API documentation:**
   Open browser: `http://localhost:8001/docs`

### Step 10: Integration

Integrate with your application:

```python
# Example: Django payment webhook
import httpx
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
async def payment_webhook(request):
    """Handle payment completion."""
    # Verify payment (your logic here)
    user_id = request.POST.get('user_id')
    plan = request.POST.get('plan')
    
    # Map plan to channel IDs
    channel_mapping = {
        'basic': [-1001234567890],
        'premium': [-1001234567890, -1009876543210],
        'vip': [-1001234567890, -1009876543210, -1001111111111],
    }
    
    chat_ids = channel_mapping.get(plan, [])
    
    # Grant Telegram access
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://telegram-service:8001/api/telegram/grant-access',
            json={
                'ext_user_id': user_id,
                'chat_ids': chat_ids,
                'period_days': 30,
                'ref': f'payment_{payment_id}'
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            # Send invite links to user
            send_email_with_invites(user_id, result['invites'])
            
    return JsonResponse({'status': 'success'})
```

## Docker Setup

### Using Docker Compose (Easiest)

```bash
# Start services (MongoDB + Telegram Service)
docker-compose up -d

# View logs
docker-compose logs -f telegram-service

# Add a channel
docker-compose exec telegram-service python -m app.cli add -1001234567890 "Channel"

# Stop services
docker-compose down
```

### Building Docker Image

```bash
# Build image with uv (optimized)
docker build -t telegram-service .

# Run container
docker run -d \
    --name telegram-service \
    -p 8001:8001 \
    --env-file .env \
    telegram-service
```

## Troubleshooting Setup

### Issue: "ModuleNotFoundError"

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
uv pip install -r requirements.txt
```

### Issue: "Can't connect to MongoDB"

**Solutions:**
1. Check MongoDB is running: `systemctl status mongod`
2. Test connection: `mongosh --eval "db.adminCommand('ping')"`
3. Verify MONGODB_URI in .env
4. Check firewall rules

### Issue: "Webhook registration failed"

**Solutions:**
1. Verify BASE_URL is HTTPS
2. Test URL is publicly accessible
3. Check webhook secret path is correct
4. Ensure port 8001 is accessible

### Issue: "Bot not admin in channel"

**Solution:**
1. Go to channel → Administrators
2. Ensure bot is listed with correct permissions
3. Try removing and re-adding the bot

## Next Steps

1. Read the [User Guide](user-guide.md) for daily operations
2. Check [API Documentation](api.md) for integration details
3. Set up monitoring and alerts
4. Configure backups for MongoDB
5. Implement authentication for API endpoints
6. Set up logging aggregation

## Production Checklist

Before going to production:

- [ ] Use strong bot token (never exposed publicly)
- [ ] Generate random webhook secret path
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set up MongoDB with authentication
- [ ] Configure MongoDB backups
- [ ] Implement API authentication
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Test failover scenarios
- [ ] Document your deployment
- [ ] Set up CI/CD pipeline
- [ ] Configure rate limiting
- [ ] Enable firewall rules
- [ ] Set up health check monitoring

## Support

Need help? 

1. Check the [User Guide](user-guide.md)
2. Review the [API Documentation](api.md)
3. Search GitHub issues
4. Create a new issue with details
