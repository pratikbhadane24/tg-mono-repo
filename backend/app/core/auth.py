"""Token verification and user authentication utilities.

This module provides functions for JWT token verification and user authentication
from HTTP requests. It supports extracting tokens from both cookies and headers.

Also includes password hashing, JWT token creation, and API key generation for
the seller management system.
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_telegram_config

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token payload data."""

    seller_id: str | None = None
    email: str | None = None


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    config = get_telegram_config()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    config = get_telegram_config()
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=config.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT token."""
    config = get_telegram_config()
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return f"sk_{secrets.token_urlsafe(32)}"


def verify_api_key(api_key: str) -> bool:
    """Verify API key format (basic validation)."""
    return api_key.startswith("sk_") and len(api_key) > 10


async def get_current_user(request: Request):
    """Get the current authenticated user from the JWT token.

    This function extracts and verifies a JWT token from the request.

    The token is extracted from (in order of precedence):
    1. Authorization header with Bearer token
    2. Cookie named "access_token"
    3. Header named "x-access-token"

    Args:
        request: The FastAPI Request object containing headers and cookies

    Returns:
        dict: The decoded JWT payload containing user information

    Raises:
        HTTPException: With status 401 if no token is found or authentication fails

    Example:
        # >>> @router.post("/endpoint")
        # >>> async def endpoint(user: dict = Depends(get_current_user)):
        # ...     # user is guaranteed to be valid here
        # ...     return {"username": user["username"]}
    """
    if request.headers.get("Authorization"):
        access_token = request.headers.get("Authorization")
        if access_token.startswith("Bearer "):
            access_token = access_token[len("Bearer ") :].strip()
        else:
            access_token = None
    else:
        access_token = request.cookies.get("access_token") or request.headers.get("x-access-token")

    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_user_token(access_token)


def verify_user_token(token):
    """Verify and decode a JWT token.

    This function validates a JWT token's signature and expiration, then extracts
    the user information from the payload. It uses the secret key and algorithm
    configured in application settings.

    Args:
        token: The JWT token string to verify

    Returns:
        dict: The decoded JWT payload containing user information (including username)

    Raises:
        HTTPException: With status 401 if:
            - Token signature is invalid
            - Token has expired
            - Token is malformed
            - Username is missing from payload

    Example:
        # >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        # >>> payload = verify_user_token(token)
        # >>> print(payload["username"])  # "john_doe"
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        config = get_telegram_config()
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception from None
    return payload
