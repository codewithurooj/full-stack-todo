"""JWT authentication utilities for MCP tools"""
from typing import Optional
import jwt
from app.config import settings
from app.mcp_server.errors import AuthorizationError


def verify_jwt_token(token: str) -> str:
    """
    Verify JWT token and extract user_id.

    Args:
        token: JWT token string (without 'Bearer ' prefix)

    Returns:
        user_id extracted from token

    Raises:
        AuthorizationError: If token is invalid, expired, or missing user_id
    """
    try:
        payload = jwt.decode(
            token,
            settings.BETTER_AUTH_SECRET,
            algorithms=["HS256"]
        )

        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise AuthorizationError(
                message="Invalid token: missing user_id",
                details={"reason": "Token payload missing 'sub' claim"}
            )

        return user_id

    except jwt.ExpiredSignatureError:
        raise AuthorizationError(
            message="Token has expired",
            details={"reason": "ExpiredSignatureError"}
        )
    except jwt.InvalidTokenError as e:
        raise AuthorizationError(
            message="Invalid token",
            details={"reason": str(e)}
        )


def verify_user_authorization(requested_user_id: str, token_user_id: str) -> None:
    """
    Verify that requested user_id matches the authenticated user from JWT.

    Args:
        requested_user_id: User ID from request parameters
        token_user_id: User ID extracted from JWT token

    Raises:
        AuthorizationError: If user IDs don't match
    """
    if requested_user_id != token_user_id:
        raise AuthorizationError(
            message="User ID mismatch: cannot access other user's resources",
            details={
                "requested_user_id": requested_user_id,
                "authenticated_user_id": token_user_id
            }
        )
