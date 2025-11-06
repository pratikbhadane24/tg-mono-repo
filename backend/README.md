# Telegram Paid Subscriber Service

**Multi-User SaaS Platform** for managing paid access to Telegram channels with automated membership management.

## 🎯 What's New - Multi-User Platform!

This service now operates as a complete **SaaS platform** where:

- 🏢 **SELLERS** register and manage their own Telegram channels
- 💳 **Payment Flexibility**: Use your own Stripe account or the platform's
- 📊 **Dashboard APIs**: Complete member management and analytics
- 🔔 **Webhooks**: Real-time event notifications
- 🔐 **Secure**: JWT authentication and API key support
- 🏗️ **Multi-Tenant**: Complete data isolation between sellers

### For Sellers

Get started in minutes:
1. Register your account → Get API key
2. Add your Telegram channels
3. Configure payments (your Stripe or ours)
4. Start selling access!

**→ [Seller Quick Start Guide](docs/SELLER_QUICKSTART.md)**

**→ [Complete API Documentation](docs/MULTI_USER_API.md)**

## Overview

This platform provides comprehensive Telegram channel access management for **SaaS businesses**:

### Core Features

- 🔐 **Seller Management**: Registration, authentication, and profile management
- 💰 **Payment Processing**: Stripe integration with dual-mode (platform or seller's account)
- 📈 **Dashboard APIs**: Statistics, member management, and analytics
- 🔗 **Automated Access Control**: Time-limited channel access with invite links
- ⏰ **Scheduled Cleanup**: Automatic member removal on expiration
- 🔔 **Webhook System**: Event notifications for member and payment events
- 📊 **Audit Logging**: Complete tracking of all operations

### API Endpoints

#### Seller Management
- `POST /api/sellers/register` - Register new seller
- `POST /api/sellers/login` - Authentication
- `GET /api/sellers/me` - Get profile
- `GET /api/sellers/stats` - Dashboard statistics
- `GET /api/sellers/channels` - List channels
- `GET /api/sellers/members` - List members
- `POST /api/sellers/webhooks` - Configure webhooks

#### Payments
- `POST /api/payments/checkout` - Create Stripe checkout
- `POST /api/payments/payment-intent` - Create payment intent
- `GET /api/payments/subscription/{id}` - Get subscription
- `POST /api/payments/webhook` - Stripe webhook handler

#### Customer Access
- `POST /api/telegram/grant-access` - Grant channel access
- `POST /api/telegram/force-remove` - Remove member
- `POST /api/telegram/channels` - Register channel

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/pratikbhadane24/tg-paid-subscriber-service.git
cd tg-paid-subscriber-service

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

### Configuration

Create `.env` file:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_SECRET_PATH=secret_path
BASE_URL=https://your-domain.com

# Database
MONGODB_URI=mongodb://localhost:27017/telegram

# Stripe (Platform)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# JWT
JWT_SECRET_KEY=your-very-secure-secret
```

### Run the Service

```bash
# Development
uvicorn main:app --reload --port 8001

# Production
granian --interface asgi main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Docker

```bash
docker-compose up -d
```

## Architecture

### Multi-Tenant Design

```
sellers              # Seller accounts with auth
  ├── seller_channels    # Channels owned by sellers
  ├── payments           # Payment transactions
  └── webhook_configs    # Webhook configurations

users                # End-user accounts
  ├── memberships        # Channel memberships
  └── invites            # Invite links

channels             # Global channel registry
audits              # Complete audit trail
```

### Data Isolation

- Each seller can only access their own data
- Automatic filtering by `seller_id`
- Secure authentication (JWT + API keys)
- Webhook signature verification

## Documentation

- 📚 **[Multi-User API Documentation](docs/MULTI_USER_API.md)** - Complete API reference
- 🚀 **[Seller Quick Start](docs/SELLER_QUICKSTART.md)** - Get started as a seller
- 📖 **[User Guide](docs/user-guide.md)** - Daily operations
- 🔌 **[Original API](docs/api.md)** - Telegram bot API reference
- 🛠️ **[Setup Guide](docs/setup.md)** - Installation and configuration

## Directory Structure

```
tg-paid-subscriber-service/
├── app/                    # Core application logic
│   ├── bot_api.py         # Telegram Bot API wrapper
│   ├── service.py         # Business logic layer
│   ├── manager.py         # Service coordinator
│   ├── models.py          # Pydantic data models
│   ├── scheduler.py       # Background task scheduler
│   ├── database.py        # Database operations
│   └── cli.py             # Channel management CLI
├── routers/                # FastAPI route handlers
├── config/                 # Configuration management
├── tests/                  # Comprehensive test suite
├── docs/                   # Complete documentation
├── scripts/                # Utility scripts
├── logs/                   # Change logs
└── .github/agents/         # Development guidelines
```

## Installation

### Using pip

```bash
git clone https://github.com/yourusername/tg-paid-subscriber-service.git
cd tg-paid-subscriber-service
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Using uv (Recommended)

```bash
git clone https://github.com/yourusername/tg-paid-subscriber-service.git
cd tg-paid-subscriber-service
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Using Docker

```bash
docker-compose up -d
```

## Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

Required environment variables:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_SECRET_PATH=random_secret_path
BASE_URL=https://your-domain.com
MONGODB_URI=mongodb://localhost:27017/telegram
```

See [Setup Guide](docs/setup.md) for complete configuration details.

## Usage

### Add Channels

```bash
python -m app.cli add -1001234567890 "Premium Channel"
python -m app.cli list
```

### Start Service

Development:
```bash
uvicorn main:app --reload --port 8001
```

Production:
```bash
granian --interface asgi main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Grant Access via API

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8001/api/telegram/grant-access",
        json={
            "ext_user_id": "user123",
            "chat_ids": [-1001234567890],
            "period_days": 30,
            "ref": "payment_abc123"
        }
    )
    result = response.json()
    invite_link = result["invites"][0]["invite_link"]
```

## API Endpoints

### Health Check
```
GET /health
```

### Grant Access
```
POST /api/telegram/grant-access
```

### Webhook (Internal)
```
POST /api/telegram/webhook/{secret_path}
```

See [API Documentation](docs/api.md) for complete details.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov=routers --cov=config --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py -v

# Run by marker
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
```

## Development

### Pre-Push Validation

Automatically runs before each push:
- Code linting (ruff)
- Code formatting (black)
- Full test suite
- Coverage reporting

Results logged to `logs/` folder.

### Code Quality

```bash
# Lint code
ruff check app routers config tests main.py

# Format code
black app routers config tests main.py

# Run validation manually
python scripts/pre_push_check.py
```

## Deployment

### Docker

```bash
# Build image
docker build -t telegram-service .

# Run container
docker run -d -p 8001:8001 --env-file .env telegram-service
```

### Docker Compose

```bash
# Start all services (app + MongoDB)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Systemd Service

See [Setup Guide](docs/setup.md#step-8-run-the-service) for systemd configuration.

## Monitoring

- Health endpoint: `GET /health`
- Application logs: Check service logs
- Database metrics: Monitor MongoDB
- Webhook status: Check Telegram API webhook info

## Troubleshooting

See [User Guide - Troubleshooting](docs/user-guide.md#troubleshooting) for common issues and solutions.

## Contributing

1. Read [Agent Instructions](.github/agents/instructions.md)
2. Create a feature branch
3. Make changes with tests
4. Run pre-push validation
5. Submit pull request

## Security

- ⚠️ Never commit secrets or tokens
- ✅ Use environment variables
- ✅ Enable HTTPS for webhooks
- ⚠️ Implement API authentication for production
- ⚠️ Configure rate limiting for production
- ✅ Use strong webhook secret paths

## License

[Add your license here]

## Support

- **Documentation**: Check [docs/](docs/) folder
- **Issues**: Open a GitHub issue
- **Questions**: See [User Guide](docs/user-guide.md)

## Changelog

See [CHANGELOG.md](logs/CHANGELOG.md) for version history.

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Motor](https://motor.readthedocs.io/)
- [Pydantic](https://docs.pydantic.dev/)
- [Granian](https://github.com/emmett-framework/granian)
