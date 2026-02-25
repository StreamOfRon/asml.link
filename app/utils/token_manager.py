"""JWT token generation and validation utilities.

This module provides utilities for creating and validating JWT tokens
for user authentication and session management.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt

from app.config import settings


class TokenPayload:
    """JWT token payload data class."""

    def __init__(
        self,
        user_id: int,
        email: str,
        is_admin: bool = False,
        token_type: str = "access",
    ):
        """Initialize token payload.

        Args:
            user_id: ID of the user
            email: Email of the user
            is_admin: Whether user is an admin
            token_type: Type of token ('access' or 'refresh')
        """
        self.user_id = user_id
        self.email = email
        self.is_admin = is_admin
        self.token_type = token_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JWT encoding."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "is_admin": self.is_admin,
            "token_type": self.token_type,
        }


class TokenManager:
    """Manager for JWT token operations."""

    @staticmethod
    def create_access_token(user_id: int, email: str, is_admin: bool = False) -> str:
        """Create an access token for a user.

        Args:
            user_id: ID of the user
            email: Email of the user
            is_admin: Whether user is an admin

        Returns:
            JWT access token string
        """
        payload = TokenPayload(
            user_id=user_id,
            email=email,
            is_admin=is_admin,
            token_type="access",
        )

        # Add expiration time
        now = datetime.now(timezone.utc)
        exp = now + timedelta(seconds=settings.jwt_expiration_seconds)

        token_dict = payload.to_dict()
        token_dict["exp"] = exp
        token_dict["iat"] = now

        token = jwt.encode(
            token_dict,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        return token

    @staticmethod
    def create_refresh_token(user_id: int, email: str) -> str:
        """Create a refresh token for a user.

        Args:
            user_id: ID of the user
            email: Email of the user

        Returns:
            JWT refresh token string
        """
        payload = TokenPayload(
            user_id=user_id,
            email=email,
            is_admin=False,
            token_type="refresh",
        )

        # Add longer expiration time for refresh token
        now = datetime.now(timezone.utc)
        exp = now + timedelta(days=settings.refresh_token_expiration_days)

        token_dict = payload.to_dict()
        token_dict["exp"] = exp
        token_dict["iat"] = now

        token = jwt.encode(
            token_dict,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        return token

    @staticmethod
    def verify_token(token: str) -> Optional[TokenPayload]:
        """Verify and decode a JWT token.

        Args:
            token: JWT token string to verify

        Returns:
            TokenPayload if valid, None if invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )

            return TokenPayload(
                user_id=payload.get("user_id"),
                email=payload.get("email"),
                is_admin=payload.get("is_admin", False),
                token_type=payload.get("token_type", "access"),
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def is_access_token(token: str) -> bool:
        """Check if a token is an access token.

        Args:
            token: JWT token string

        Returns:
            True if token is valid and is an access token
        """
        payload = TokenManager.verify_token(token)
        return payload is not None and payload.token_type == "access"

    @staticmethod
    def is_refresh_token(token: str) -> bool:
        """Check if a token is a refresh token.

        Args:
            token: JWT token string

        Returns:
            True if token is valid and is a refresh token
        """
        payload = TokenManager.verify_token(token)
        return payload is not None and payload.token_type == "refresh"

    @staticmethod
    def create_tokens(user_id: int, email: str, is_admin: bool = False) -> Dict[str, str]:
        """Create both access and refresh tokens for a user.

        Args:
            user_id: ID of the user
            email: Email of the user
            is_admin: Whether user is an admin

        Returns:
            Dictionary with 'access_token' and 'refresh_token' keys
        """
        return {
            "access_token": TokenManager.create_access_token(user_id, email, is_admin),
            "refresh_token": TokenManager.create_refresh_token(user_id, email),
        }
