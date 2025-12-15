"""User model and schemas for authentication"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class UserBase(SQLModel):
    """Base user fields"""
    email: str = Field(unique=True, index=True)
    name: Optional[str] = None


class User(UserBase, table=True):
    """User database model"""
    __tablename__ = "users"

    id: Optional[str] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    """Schema for user registration"""
    email: str
    password: str
    name: Optional[str] = None


class UserLogin(SQLModel):
    """Schema for user login"""
    email: str
    password: str


class UserRead(UserBase):
    """Schema for reading user data (no password)"""
    id: str
    created_at: datetime
    updated_at: datetime


class UserResponse(SQLModel):
    """Schema for authentication responses"""
    token: str
    user: UserRead
