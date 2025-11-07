# Telegram Paid Subscriber Service

Production-grade FastAPI service for managing paid access to Telegram channels with automated membership management.

## Overview

This standalone service provides comprehensive Telegram channel access management:

- 🔐 **Automated Access Control**: Grant time-limited access to Telegram channels
- 🔗 **Invite Link Generation**: Create unique, expiring invite links for each user
- ✅ **Join Request Handling**: Automatically approve authorized join requests
- ⏰ **Scheduled Cleanup**: Remove expired members automatically
- 🔗 **Account Linking**: Connect your system users with Telegram accounts
- 📊 **Audit Logging**: Track all access grants and membership changes

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your bot token and MongoDB URI

# Add a channel
python -m app.cli add -1001234567890 "My Channel"

# Start the service
uvicorn main:app --reload --port 8001
```

## Documentation

- 📚 **[Setup Guide](docs/setup.md)**: Complete installation and configuration
- 📖 **[User Guide](docs/user-guide.md)**: Daily operations and usage
- 🔌 **[API Documentation](docs/api.md)**: Complete REST API reference
- 🏗️ **[Agent Instructions](.github/agents/instructions.md)**: Development guidelines

## Features

### Core Functionality

- **Grant Access API**: RESTful endpoint to grant users channel access
- **Webhook Handler**: Process Telegram updates (join requests, member events)
- **Background Scheduler**: Automatically clean up expired memberships
- **CLI Tool**: Manage channel configurations
- **Audit Logs**: Complete tracking of all operations

### Architecture

- **FastAPI**: Modern async web framework
- **MongoDB**: Document storage for users, memberships, and audit logs
- **Motor**: Async MongoDB driver
- **Pydantic**: Data validation and settings management
- **Granian/Uvicorn**: High-performance ASGI servers

### Production Ready

- ✅ Comprehensive test suite with pytest
- ✅ Pre-push validation (linting, formatting, tests)
- ✅ Docker support with optimized multi-stage build
- ✅ Complete API documentation
- ✅ Structured logging
- ✅ Health check endpoint
- ✅ MongoDB indexes for performance

## Directory Structure

```
ra-tg-service/
├── app/                      # Main application package
│   ├── api/                  # API layer
│   │   └── endpoints/        # API endpoints
│   │       ├── health.py     # Health check endpoints
│   │       └── telegram.py   # Telegram API endpoints
│   ├── core/                 # Core utilities
│   │   ├── auth.py           # Authentication utilities
│   │   └── config.py         # Configuration management
│   ├── models/               # Data models
│   │   ├── telegram.py       # Telegram domain models
│   │   └── responses.py      # API response models
│   ├── services/             # Business logic services
│   │   ├── bot_api.py        # Telegram Bot API wrapper
│   │   ├── telegram_service.py  # Membership service
│   │   ├── scheduler.py      # Background scheduler
│   │   └── database.py       # Database operations
│   ├── main.py               # FastAPI application
│   ├── manager.py            # Service coordinator
│   ├── cli.py                # Channel management CLI
│   └── timezone_utils.py     # Timezone utilities
├── tests/                    # Comprehensive test suite
├── docs/                     # Complete documentation
├── scripts/                  # Utility scripts
├── main.py                   # Entry point (imports app.main)
└── .github/agents/           # Development guidelines
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
JWT_SECRET_KEY=your_secret_key_here_change_this_in_production
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
# Using backward-compatible entry point
uvicorn main:app --reload --port 8001

# Or using new structure directly
uvicorn app.main:app --reload --port 8001
```

Production:
```bash
# Using backward-compatible entry point
granian --interface asgi main:app --host 0.0.0.0 --port 8001 --workers 4

# Or using new structure directly
granian --interface asgi app.main:app --host 0.0.0.0 --port 8001 --workers 4
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
- ✅ Use environment variables for all secrets (JWT_SECRET_KEY, TELEGRAM_BOT_TOKEN, etc.)
- ✅ Enable HTTPS for webhooks
- ✅ JWT authentication is implemented for API endpoints (grant-access, channels, force-remove)
- ✅ Use strong, random JWT_SECRET_KEY in production
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
