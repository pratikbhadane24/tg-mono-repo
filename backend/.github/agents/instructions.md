# Agent Instructions for Telegram Paid Subscriber Service

This document provides guidance for AI agents working on this repository.

## Repository Structure

```
tg-paid-subscriber-service/
├── app/                    # Core application logic
│   ├── __init__.py
│   ├── __main__.py        # CLI entry point
│   ├── bot_api.py         # Telegram Bot API wrapper
│   ├── cli.py             # Channel management CLI
│   ├── database.py        # Database operations
│   ├── manager.py         # Service coordinator
│   ├── models.py          # Pydantic data models
│   ├── scheduler.py       # Background task scheduler
│   └── service.py         # Business logic layer
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py        # Environment and settings
├── routers/                # FastAPI routes
│   ├── __init__.py
│   └── telegram.py        # API endpoints
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_api.py        # API endpoint tests
│   ├── test_config.py     # Configuration tests
│   ├── test_models.py     # Model validation tests
│   └── test_telegram_service.py  # Legacy tests (deprecated)
├── docs/                   # Documentation
│   ├── api.md             # API documentation
│   ├── setup.md           # Setup guide
│   └── user-guide.md      # User guide
├── scripts/                # Utility scripts
│   └── pre_push_check.py  # Pre-push validation
├── logs/                   # Change logs and validation results
├── .github/
│   └── agents/
│       └── instructions.md # This file
├── main.py                 # FastAPI application entry point
├── Dockerfile              # Docker build (optimized with uv)
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project configuration
├── .env.example            # Environment template
└── README.md               # Main documentation

# Deprecated/Old Structure (DO NOT USE):
└── telegram/               # Old folder - being phased out
    └── ...                 # Do not add new code here
```

## Development Workflow

### Before Making Changes

1. **Understand the structure**: Review the directory layout above
2. **Check existing tests**: Run `pytest tests/` to see what's tested
3. **Read documentation**: Check `docs/` for context
4. **Review logs**: Check `logs/` for recent changes

### Making Changes

1. **Use the new structure**: All new code goes in `app/`, `routers/`, or `config/`
2. **Update imports**: Use absolute imports (`from app.models import ...`)
3. **Add tests**: Every new function should have corresponding tests
4. **Update docs**: Keep `docs/` synchronized with code changes
5. **Log changes**: Major changes should be noted in `logs/CHANGELOG.md`

### Testing Changes

```bash
# Run specific test file
pytest tests/test_models.py -v

# Run all tests with coverage
pytest --cov=app --cov=routers --cov=config --cov-report=term-missing

# Run tests by marker
pytest -m unit  # Unit tests only
pytest -m integration  # Integration tests only
```

### Code Quality

```bash
# Lint code
ruff check app routers config tests main.py

# Format code
black app routers config tests main.py

# Type checking (if mypy is configured)
mypy app routers config

# Run all checks (automatic before push)
python scripts/pre_push_check.py
```

## Key Concepts

### Service Architecture

The service follows a layered architecture:

1. **main.py**: FastAPI application initialization, lifespan management
2. **routers/**: HTTP endpoints, request/response handling
3. **app/service.py**: Business logic, orchestration
4. **app/bot_api.py**: External API calls (Telegram)
5. **app/database.py**: Database operations
6. **app/models.py**: Data structures and validation

### Manager Pattern

The `TelegramManager` coordinates all services:

```python
# Initialization
manager = TelegramManager(db)
await manager.initialize()

# Access services
service = manager.get_service()
bot = manager.get_bot()

# Cleanup
await manager.shutdown()
```

### Configuration

All configuration is managed via environment variables:

```python
from config.settings import get_telegram_config

config = get_telegram_config()
token = config.TELEGRAM_BOT_TOKEN
```

### Database Models

Models use Pydantic v2 with MongoDB ObjectId support:

```python
from app.models import TelegramUser, Channel, Membership

user = TelegramUser(ext_user_id="user123")
data = user.model_dump(by_alias=True, exclude={"id"})
```

## Common Tasks

### Adding a New API Endpoint

1. Define route in `routers/telegram.py`:
   ```python
   @router.post("/new-endpoint")
   async def new_endpoint(
       data: RequestModel,
       service: TelegramMembershipService = Depends(get_telegram_service)
   ):
       result = await service.do_something(data)
       return {"success": True, "result": result}
   ```

2. Implement business logic in `app/service.py`:
   ```python
   async def do_something(self, data):
       # Business logic here
       pass
   ```

3. Add tests in `tests/test_api.py`:
   ```python
   def test_new_endpoint(client, mock_manager):
       response = client.post("/api/telegram/new-endpoint", json={...})
       assert response.status_code == 200
   ```

4. Document in `docs/api.md`

### Adding a New Model

1. Define in `app/models.py`:
   ```python
   class NewModel(BaseModel):
       model_config = ConfigDict(
           populate_by_name=True,
           arbitrary_types_allowed=True,
           json_encoders={ObjectId: str}
       )
       
       id: Optional[ObjectId] = Field(default=None, alias="_id")
       field: str = Field(..., description="Description")
   ```

2. Add tests in `tests/test_models.py`

3. Update database operations in `app/database.py` if needed

### Adding Configuration Options

1. Add to `config/settings.py`:
   ```python
   class TelegramConfig(BaseSettings):
       NEW_OPTION: str = Field(default="default_value", description="Description")
   ```

2. Update `.env.example`

3. Document in `docs/setup.md` and `docs/user-guide.md`

4. Add tests in `tests/test_config.py`

## Testing Guidelines

### Test Organization

- **Unit tests** (`@pytest.mark.unit`): Test individual functions, no external dependencies
- **Integration tests** (`@pytest.mark.integration`): Test with mocked external services
- **Slow tests** (`@pytest.mark.slow`): Tests that take >1 second

### Test Fixtures

Common fixtures in `tests/conftest.py` (create if needed):

```python
@pytest.fixture
def mock_db():
    """Mock MongoDB database."""
    return AsyncMock()

@pytest.fixture
def test_config():
    """Test configuration."""
    with patch.dict(os.environ, {...}):
        yield get_telegram_config()
```

### Mocking External Services

Always mock external APIs:

```python
@patch('app.bot_api.httpx.AsyncClient')
async def test_bot_api(mock_client):
    mock_response = Mock()
    mock_response.json.return_value = {"ok": True}
    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
    
    # Test code here
```

## Documentation Standards

### Code Documentation

- **Modules**: Docstring at top explaining purpose
- **Classes**: Docstring with usage example
- **Methods**: Docstring with Args, Returns, Raises
- **Complex logic**: Inline comments explaining "why"

### API Documentation

When adding/modifying endpoints:

1. Update `docs/api.md` with:
   - Endpoint path and method
   - Request/response examples
   - Status codes
   - Error cases
   - Usage examples (curl + Python)

2. FastAPI will auto-generate OpenAPI docs at `/docs`

### User Documentation

Keep `docs/user-guide.md` and `docs/setup.md` updated with:

- Configuration changes
- New features
- Breaking changes
- Migration guides

## Pre-Push Validation

The pre-push hook automatically runs:

1. **Ruff linting**: Code quality checks
2. **Black formatting**: Code style consistency
3. **Pytest**: All tests must pass

To bypass (only in emergencies):

```bash
git push --no-verify
```

## Debugging Tips

### Local Development

```bash
# Run with debug logging
uvicorn main:app --reload --log-level debug

# Watch for changes
uvicorn main:app --reload
```

### Database Inspection

```bash
# MongoDB shell
mongosh

use telegram
db.users.find({ext_user_id: "user123"})
db.memberships.find({status: "active"}).count()
```

### Testing Webhook

```bash
# Check webhook status
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"

# Send test update
curl -X POST http://localhost:8001/api/telegram/webhook/secret_path \
  -H "Content-Type: application/json" \
  -d '{"update_id":1,"message":{"text":"test"}}'
```

## Performance Considerations

1. **Database queries**: Use indexes (auto-created by `database.py`)
2. **Async operations**: Always use `async/await` for I/O
3. **Connection pooling**: Motor handles this automatically
4. **Rate limiting**: Consider adding for production
5. **Caching**: Consider Redis for frequently accessed data

## Security Best Practices

1. **Never commit secrets**: Use environment variables
2. **Validate all inputs**: Pydantic models handle this
3. **Use HTTPS**: Required for Telegram webhooks
4. **Implement authentication**: Add API key auth for production
5. **Rate limit**: Prevent abuse
6. **Audit logging**: Track all access grants (already implemented)

## Troubleshooting

### Import Errors

If imports fail, check:

1. Virtual environment is activated
2. Dependencies installed: `pip install -r requirements.txt`
3. Using absolute imports: `from app.models import ...`

### Test Failures

1. Check if MongoDB is required (integration tests)
2. Verify mock setup is correct
3. Check for outdated fixtures
4. Run with `-v` for verbose output

### Git Hook Issues

If pre-push hook fails:

1. Check tool installation: `ruff --version`, `black --version`, `pytest --version`
2. Install missing tools: `pip install -r requirements.txt`
3. Run manually: `python scripts/pre_push_check.py`
4. Check logs in `logs/` folder

## Getting Help

1. **Documentation**: Check `docs/` folder first
2. **Tests**: Look at test files for usage examples
3. **Code**: Read existing implementations
4. **Logs**: Check `logs/` for validation results
5. **Issues**: Create GitHub issue with details

## Migration Notes

### Old `telegram/` Folder

The old `telegram/` folder structure is deprecated. When modifying code:

1. ⚠️ **DO NOT add new code to `telegram/` folder**
2. ✅ **Use `app/`, `routers/`, `config/` instead**
3. 📝 **If updating existing `telegram/` files, consider migrating to new structure**

### Import Changes

Old:
```python
from telegram.config import get_telegram_config
from telegram import TelegramManager
```

New:
```python
from config.settings import get_telegram_config
from app import TelegramManager
```

## Changelog Location

All changes should be logged in `logs/CHANGELOG.md` with:

- Date
- Type of change (Feature, Fix, Breaking Change, Documentation)
- Description
- Related issue/PR number

Example:
```markdown
## 2024-11-06

### Restructure
- Reorganized repository into production-grade structure
- Moved code from `telegram/` to `app/`, `routers/`, `config/`
- Added comprehensive documentation
- Implemented pre-push validation
```

---

**Last Updated**: 2024-11-06
**Structure Version**: 2.0
**Deprecated Structure**: telegram/ folder (v1.0)
