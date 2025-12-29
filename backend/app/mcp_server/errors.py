"""Custom exception classes for MCP server"""
from typing import Any, Dict, Optional


class MCPError(Exception):
    """Base exception class for MCP server errors"""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to JSON-serializable dictionary"""
        return {
            "error": {
                "message": self.message,
                "code": self.code,
                "details": self.details
            }
        }


class ValidationError(MCPError):
    """Raised when input validation fails"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class AuthorizationError(MCPError):
    """Raised when user is not authorized to perform action"""

    def __init__(self, message: str = "Unauthorized access", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )


class NotFoundError(MCPError):
    """Raised when requested resource is not found"""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details
        )


class DatabaseError(MCPError):
    """Raised when database operation fails"""

    def __init__(self, message: str = "Database error occurred", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details=details
        )
