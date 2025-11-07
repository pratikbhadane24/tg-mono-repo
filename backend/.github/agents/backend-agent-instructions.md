# Backend Agent Instructions (FastAPI/Python)

## Must-Have Requirements

### 1. Project Structure (MANDATORY)

**ALL FastAPI Python applications MUST follow this exact handler-backend pattern:**

```
project-name/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints/          # API route handlers
│   │       ├── __init__.py
│   │       ├── health.py       # Health check (REQUIRED)
│   │       └── [domain].py     # Domain-specific endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Environment configuration (REQUIRED)
│   │   ├── auth.py             # Authentication/authorization (if auth needed)
│   │   └── security.py         # Security utilities
│   ├── models/
│   │   ├── __init__.py
│   │   ├── [domain].py         # Pydantic models for domain
│   │   └── responses.py        # Standard response models (REQUIRED)
│   ├── services/
│   │   ├── __init__.py
│   │   └── [service].py        # Business logic services
│   └── database/               # Database layer (if needed)
│       ├── __init__.py
│       ├── models.py           # ORM/ODM models
│       └── database.py         # Database connection/operations
│   └── utils/  
│       ├── __init__.py
│       └── [utility].py        # Utility functions
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures (REQUIRED)
│   ├── test_integration.py     # Integration tests (REQUIRED)
│   ├── test_endpoints.py       # API endpoint tests (REQUIRED)
│   ├── test_services.py        # Service tests (REQUIRED)
│   └── test_[module].py        # Module-specific tests
├── docs/
│   ├── api.md                  # API documentation (REQUIRED)
│   └── setup.md                # Setup guide (REQUIRED)
├── .env.example                # Environment template (REQUIRED)
├── requirements.txt            # Dependencies (REQUIRED)
├── pyproject.toml              # Project config (REQUIRED)
├── Dockerfile                  # Docker build (REQUIRED)
├── .dockerignore
└── README.md                   # Project documentation (REQUIRED)
```

**If structure is missing or incorrect, STOP and create it first.**

### 2. Configuration (REQUIRED)

**ALL applications MUST have:**

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # REQUIRED fields
    APP_NAME: str = Field(..., description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="App version")

    # Database (if used)
    DATABASE_URL: str | None = Field(None, description="Database URL")

    # Authentication (if used)
    JWT_SECRET_KEY: str = Field(..., description="JWT secret")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")

    # API
    API_PREFIX: str = Field(default="/api", description="API prefix")


_config = None


def get_settings() -> Settings:
    """Get singleton config instance."""
    global _config
    if _config is None:
        _config = Settings()
    return _config
```

**.env.example MUST include ALL required variables with examples.**

### 3. Authentication (REQUIRED if app has protected endpoints)

**If authentication is needed, MUST implement:**

```python
# app/core/auth.py
from fastapi import HTTPException, Request, status
from jose import jwt
from app.core.config import get_settings


async def get_current_user(request: Request) -> dict:
    """Extract and validate JWT token from request.
    
    Token can be in:
    1. Authorization header: Bearer <token>
    2. Cookie: access_token
    3. Custom header: x-access-token
    
    Raises HTTPException(401) if invalid/missing.
    """
    token = None

    # Check Authorization header
    if auth := request.headers.get("Authorization"):
        if auth.startswith("Bearer "):
            token = auth[7:].strip()

    # Check cookie
    if not token:
        token = request.cookies.get("access_token")

    # Check custom header
    if not token:
        token = request.headers.get("x-access-token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        config = get_settings()
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )
        if not payload.get("username"):
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

**Protect endpoints using dependency injection:**

```python
from fastapi import Depends
from app.core.auth import get_current_user


@router.post("/protected",
             openapi_extra={
                 "parameters": [
                     {
                         "name": "Authorization",
                         "in": "header",
                         "required": True,
                         "schema": {"type": "string"},
                         "description": "Bearer token, e.g. 'Bearer your_token_here'"
                     },
                 ]
             },
             )
async def protected_endpoint(
        current_user: dict = Depends(get_current_user),
):
    # current_user is guaranteed valid here
    return {"user": current_user["username"]}
```

All endpoints requiring authentication MUST use this dependency. And have defined openapi_extra for docs.

### 4. Standard Response Model (REQUIRED)

**ALL API responses MUST use a standard format:**

```python
# app/models/responses.py
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail model."""
    code: str = Field(..., description="Error code")
    description: str = Field(..., description="Error description")


class StandardResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Human-readable message")
    data: T | None = Field(None, description="Response data")
    error: ErrorDetail | None = Field(None, description="Error details if failed")

    @classmethod
    def success_response(cls, message: str, data: T = None):
        """Create success response."""
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_response(cls, message: str, error_code: str, error_description: str):
        """Create error response."""
        return cls(
            success=False,
            message=message,
            error=ErrorDetail(code=error_code, description=error_description)
        )
```

- These models MUST return 'dict' response but should have responses defined in the route.
- Example

```python
@router.get(
    "/enhanced-external-data",
    responses={200: {"model": EnhancedExternalDataResponse}},
    tags=["enhanced-example"],
)
async def get_enhanced_external_data() -> Dict[str, Any]:
    """Example endpoint using enhanced HTTP client.
    
    This demonstrates the use of the enhanced HTTP client with
    standardized responses and comprehensive error handling.
    
    Returns:
        Standardized response with data from external API
    """
    # Make request using enhanced HTTP client
    response = await enhanced_http_client.get(
        "https://jsonplaceholder.typicode.com/todos/1"
    )
    # Return dict directly
    return response.to_dict()
```

### 5. Health Check (REQUIRED)

**EVERY application MUST have a health endpoint:**

```python
# app/api/endpoints/health.py
from fastapi import APIRouter
from app.models.responses import StandardResponse

router = APIRouter()


@router.get("/health", response_model=StandardResponse[dict])
def health():
    """Health check endpoint."""
    return StandardResponse.success_response(
        message="Service is healthy",
        data={"status": "UP"}
    )
```

### 6. Testing (CRITICAL - NON-NEGOTIABLE)

**Testing is MANDATORY. If tests are missing or inadequate, STOP and fix immediately.**

#### Required Test Structure:

```
tests/
├── conftest.py              # Shared fixtures
├── test_integration.py      # Structure & import validation
├── test_endpoints.py        # API tests with auth
├── test_services.py         # Business logic tests
├── test_auth.py             # Authentication tests
└── test_[module].py         # Module-specific tests
```

#### Test Coverage Requirements:

1. **Integration Tests (test_integration.py)** - REQUIRED

```python
"""Validate application structure and imports."""


class TestApplicationStructure:
    def test_all_modules_importable(self):
        """Test ALL modules import without errors."""
        modules = [
            "app.main",
            "app.core.config",
            "app.core.auth",  # if auth exists
            "app.models",
            "app.services",
            "app.api.endpoints.health",
        ]
        failed = []
        for mod in modules:
            try:
                importlib.import_module(mod)
            except Exception as e:
                failed.append((mod, str(e)))
        assert not failed, f"Failed imports: {failed}"

    def test_no_circular_imports(self):
        """Detect circular import issues."""
        # Test imports fresh
        pass

    def test_config_loads(self):
        """Config loads with required fields."""
        from app.core.config import get_settings
        config = get_settings()
        assert config.APP_NAME is not None
```

2. **Endpoint Tests (test_endpoints.py)** - REQUIRED

```python
"""Test ALL API endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "UP"


class TestAuthenticationEndpoints:
    def test_protected_endpoint_requires_auth(self):
        """Protected endpoints return 401 without auth."""
        response = client.post("/api/protected")
        assert response.status_code == 401

    def test_protected_endpoint_accepts_valid_token(self, valid_token):
        """Protected endpoints work with valid token."""
        response = client.post(
            "/api/protected",
            headers={"Authorization": f"******}
        )
        assert response.status_code == 200


class TestRequestValidation:
    def test_invalid_request_returns_422(self):
        """Invalid requests return validation errors."""
        response = client.post(
            "/api/endpoint",
            json={"invalid": "data"}
        )
        assert response.status_code == 422
```

3. **Service Tests (test_services.py)** - REQUIRED

```python
"""Test business logic services."""
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestMyService:
    @pytest.fixture
    def mock_dependencies(self):
        """Mock external dependencies."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_service_method(self, mock_dependencies):
        """Test service methods with mocks."""
        service = MyService(mock_dependencies)
        result = await service.do_something()
        assert result is not None
```

4. **Authentication Tests (test_auth.py)** - REQUIRED if auth used

```python
"""Test authentication flows."""
import pytest
from jose import jwt
from datetime import datetime, timedelta, UTC


class TestAuthentication:
    @pytest.fixture
    def valid_token(self):
        """Create valid JWT token."""
        from app.core.config import get_settings
        config = get_settings()
        payload = {
            "username": "test",
            "exp": datetime.now(UTC) + timedelta(hours=1)
        }
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    def test_token_validation_success(self, valid_token):
        """Valid token passes validation."""
        # Test implementation
        pass

    def test_token_validation_expired(self):
        """Expired token fails validation."""
        # Test implementation
        pass
```

#### Test Execution Requirements:

```toml
# pyproject.toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = [
    "-ra",
    "-q",
    "--strict-markers",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
]
testpaths = ["tests"]

[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/__pycache__/*"]
```

**Minimum Requirements:**

- ✅ 80%+ code coverage
- ✅ ALL endpoints tested
- ✅ ALL authentication paths tested
- ✅ ALL service methods tested
- ✅ Integration tests for imports
- ✅ Error cases tested
- ✅ Edge cases tested

**If coverage < 80% or critical paths untested, tests are INADEQUATE.**

### 7. Error Handling (REQUIRED)

**ALL endpoints MUST handle errors properly:**

```python
from fastapi import HTTPException
from app.models.responses import StandardResponse


@router.post("/endpoint")
async def endpoint():
    try:
        # Business logic
        return StandardResponse.success_response("Success", data=result)
    except ValueError as e:
        return StandardResponse.error_response(
            message="Invalid input",
            error_code="VALIDATION_ERROR",
            error_description=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return StandardResponse.error_response(
            message="Internal server error",
            error_code="INTERNAL_ERROR",
            error_description="An unexpected error occurred"
        )
```

### 8. Code Quality (REQUIRED)

**ALL code MUST pass:**

```bash
# Linting
ruff check app tests

# Formatting
black app tests

# Type checking (recommended)
mypy app
```

**Configuration:**

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501"]

[tool.black]
line-length = 100
target-version = ['py311']
```

### 9. Documentation (REQUIRED)

**MUST have:**

1. **API Documentation (docs/api.md)**
    - All endpoints documented
    - Request/response examples
    - Authentication requirements
    - Error codes

2. **Setup Guide (docs/setup.md)**
    - Installation steps
    - Environment configuration
    - Database setup (if applicable)
    - Running the application

3. **README.md**
    - Project overview
    - Quick start
    - Directory structure
    - Testing instructions

### 10. Docker (REQUIRED)

```dockerfile
# Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ ./app/
COPY main.py .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Checklist for Every Backend Task

Before considering a task complete, verify:

- [ ] Handler-backend structure implemented correctly
- [ ] Configuration with .env.example
- [ ] Authentication if needed (with tests)
- [ ] StandardResponse for all endpoints
- [ ] Health endpoint exists and works
- [ ] **Comprehensive tests (80%+ coverage)**
- [ ] **ALL endpoints have tests**
- [ ] **ALL authentication paths tested**
- [ ] **Integration tests for structure**
- [ ] Error handling on all endpoints
- [ ] Linting passes (ruff)
- [ ] Formatting passes (black)
- [ ] Documentation complete
- [ ] Dockerfile present
- [ ] No import errors
- [ ] No circular imports

## Common Mistakes to Avoid

❌ **NEVER:**

- Use flat app structure (app/*.py all in one folder)
- Mix business logic in endpoints
- Return raw exceptions to users
- Skip authentication tests
- Have <80% test coverage
- Leave endpoints untested
- Use undefined config variables
- Have circular imports
- Skip error handling

✅ **ALWAYS:**

- Use handler-backend pattern
- Separate concerns (API/Services/Models)
- Use StandardResponse
- Test EVERYTHING thoroughly
- Handle all errors gracefully
- Validate all inputs
- Document all endpoints
- Use type hints

## If Something is Missing

**STOP IMMEDIATELY and:**

1. Identify what's missing from requirements
2. Inform the user clearly
3. Add the missing component
4. Test the addition
5. Update documentation
6. Verify checklist again

**Quality over speed. Complete implementation over partial.**
