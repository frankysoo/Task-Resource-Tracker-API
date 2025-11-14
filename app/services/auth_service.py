"""Authentication service - handles all the login/signup/token stuff.

This was tricky to get right, especially the JWT tokens and password hashing.
"""

from datetime import timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token
)
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest
from app.schemas.user import UserCreate


class AuthService:
    """Handles all authentication stuff - login, signup, tokens, etc."""

    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """Create a new user. Hashes password so it's secure."""
        # Make sure email isn't taken
        existing_user = db.query(User).filter(User.email == user_create.email).first()
        if existing_user:
            raise ValueError("Email already registered!")

        # Hash the password - super important for security!
        hashed_password = get_password_hash(user_create.password)
        new_user = User(
            email=user_create.email,
            name=user_create.name,
            password_hash=hashed_password,
            role=user_create.role
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    @staticmethod
    def authenticate_user(db: Session, login_request: LoginRequest) -> Optional[User]:
        """Authenticate user with email and password."""
        user = db.query(User).filter(User.email == login_request.email).first()
        if not user:
            return None
        if not verify_password(login_request.password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def create_tokens(user: User) -> Tuple[str, str]:
        """Create access and refresh tokens for user."""
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)
        
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=refresh_token_expires
        )
        
        return access_token, refresh_token
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token."""
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        
        return access_token
