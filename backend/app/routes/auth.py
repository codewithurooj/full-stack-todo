"""Authentication API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlmodel import Session, select
from datetime import datetime, timedelta
import jwt
import uuid

from app.database import get_session
from app.models.user import User, UserCreate, UserLogin, UserRead, UserResponse
from app.config import settings
from app.middleware.auth import get_current_user_id
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def create_jwt_token(user_id: str) -> str:
    """
    Create a JWT token for authenticated user

    Args:
        user_id: User's unique identifier

    Returns:
        str: Encoded JWT token
    """
    payload = {
        "sub": user_id,  # Subject (user ID)
        "iat": datetime.utcnow(),  # Issued at
        "exp": datetime.utcnow() + timedelta(days=7)  # Expires in 7 days
    }
    return jwt.encode(payload, settings.BETTER_AUTH_SECRET, algorithm="HS256")


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    response: Response,
    session: Session = Depends(get_session)
):
    """
    Register a new user account

    Args:
        user_data: User registration data (email, password, name)
        response: FastAPI Response object for setting cookies
        session: Database session

    Returns:
        UserResponse: JWT token and user data

    Raises:
        HTTPException: If email is already registered or validation fails
    """
    # Check if user already exists
    existing_user = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength (minimum 6 characters)
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create new user
    db_user = User(
        id=str(uuid.uuid4()),  # Generate unique ID
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    # Generate JWT token
    token = create_jwt_token(db_user.id)

    # Set httpOnly cookie for Better Auth compatibility
    # secure=True and samesite="none" required for cross-origin cookies (Vercel + Render)
    response.set_cookie(
        key="better-auth.session_token",
        value=token,
        httponly=True,  # Prevent JavaScript access
        secure=True,  # Required for samesite=none and HTTPS
        samesite="none",  # Allow cross-origin cookies
        max_age=7 * 24 * 60 * 60  # 7 days in seconds
    )

    # Return token and user data
    return UserResponse(
        token=token,
        user=UserRead(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )
    )


@router.post("/signin", response_model=UserResponse)
async def signin(
    credentials: UserLogin,
    response: Response,
    session: Session = Depends(get_session)
):
    """
    Authenticate user and generate session token

    Args:
        credentials: User login credentials (email, password)
        response: FastAPI Response object for setting cookies
        session: Database session

    Returns:
        UserResponse: JWT token and user data

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = session.exec(
        select(User).where(User.email == credentials.email)
    ).first()

    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Generate JWT token
    token = create_jwt_token(user.id)

    # Set httpOnly cookie for Better Auth compatibility
    # secure=True and samesite="none" required for cross-origin cookies (Vercel + Render)
    response.set_cookie(
        key="better-auth.session_token",
        value=token,
        httponly=True,  # Prevent JavaScript access
        secure=True,  # Required for samesite=none and HTTPS
        samesite="none",  # Allow cross-origin cookies
        max_age=7 * 24 * 60 * 60  # 7 days in seconds
    )

    # Return token and user data
    return UserResponse(
        token=token,
        user=UserRead(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post("/signout")
async def signout(response: Response):
    """
    Sign out user by clearing session cookie

    Args:
        response: FastAPI Response object for clearing cookies

    Returns:
        dict: Success message
    """
    # Clear the session cookie
    response.delete_cookie(
        key="better-auth.session_token",
        httponly=True,
        secure=True,
        samesite="none"
    )

    return {"message": "Successfully signed out"}


@router.get("/me", response_model=UserRead)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Get current authenticated user's profile

    Args:
        user_id: Current user's ID from JWT token
        session: Database session

    Returns:
        UserRead: Current user's data

    Raises:
        HTTPException: If user not found
    """
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
