"""Token verification and user authentication utilities.

This module provides functions for JWT token verification and user authentication
from HTTP requests. It supports extracting tokens from both cookies and headers.
"""

from fastapi import HTTPException, Request, status
from jose import jwt

from app.core.config import get_telegram_config


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
