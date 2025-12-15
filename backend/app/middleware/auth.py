"""JWT authentication middleware"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional

from app.config import settings

# Make HTTPBearer optional so we can also check cookies
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Extract and validate JWT token from either Authorization header or cookies.

    Supports two authentication methods:
    1. Authorization: Bearer <token> header (preferred for API clients)
    2. better-auth.session_token cookie (used by Better Auth in browser)

    Args:
        request: FastAPI Request object to access cookies
        credentials: Optional HTTP Bearer token credentials

    Returns:
        str: User ID from JWT token

    Raises:
        HTTPException: If token is invalid, expired, or missing user_id
    """
    token = None

    # Try to get token from Authorization header first (for API compatibility)
    if credentials:
        token = credentials.credentials
    # If not in header, try to get from Better Auth session cookie
    elif "better-auth.session_token" in request.cookies:
        token = request.cookies.get("better-auth.session_token")

    # No token found in either location
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.BETTER_AUTH_SECRET,
            algorithms=["HS256"]
        )

        # Extract user_id from 'sub' claim
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
