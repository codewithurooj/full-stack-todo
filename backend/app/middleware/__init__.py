"""Authentication and authorization middleware"""
from app.middleware.auth import get_current_user_id

__all__ = ["get_current_user_id"]
