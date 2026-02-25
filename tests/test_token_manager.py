"""Tests for JWT token management utilities."""

import asyncio
from datetime import timedelta, datetime, timezone

import pytest
import jwt

from app.config import settings
from app.utils.token_manager import TokenManager, TokenPayload


class TestTokenPayload:
    """Tests for TokenPayload class."""

    def test_token_payload_creation(self):
        """Test creating a token payload."""
        payload = TokenPayload(
            user_id=1,
            email="user@example.com",
            is_admin=False,
            token_type="access",
        )

        assert payload.user_id == 1
        assert payload.email == "user@example.com"
        assert payload.is_admin is False
        assert payload.token_type == "access"

    def test_token_payload_to_dict(self):
        """Test converting payload to dictionary."""
        payload = TokenPayload(
            user_id=1,
            email="user@example.com",
            is_admin=True,
            token_type="refresh",
        )

        payload_dict = payload.to_dict()
        assert payload_dict["user_id"] == 1
        assert payload_dict["email"] == "user@example.com"
        assert payload_dict["is_admin"] is True
        assert payload_dict["token_type"] == "refresh"


class TestAccessTokenCreation:
    """Tests for access token creation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        token = TokenManager.create_access_token(
            user_id=1,
            email="user@example.com",
            is_admin=False,
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_user_info(self):
        """Test that access token contains user information."""
        token = TokenManager.create_access_token(
            user_id=42,
            email="test@example.com",
            is_admin=True,
        )

        # Decode without verification to check payload
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["user_id"] == 42
        assert payload["email"] == "test@example.com"
        assert payload["is_admin"] is True
        assert payload["token_type"] == "access"

    def test_access_token_has_expiration(self):
        """Test that access token has proper expiration."""
        now = datetime.now(timezone.utc)
        token = TokenManager.create_access_token(user_id=1, email="user@example.com")

        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = now + timedelta(seconds=settings.jwt_expiration_seconds)

        # Allow 5 second tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_multiple_access_tokens_are_different(self):
        """Test that creating multiple tokens generates different values."""
        token1 = TokenManager.create_access_token(user_id=1, email="user1@example.com")
        token2 = TokenManager.create_access_token(user_id=2, email="user2@example.com")

        assert token1 != token2


class TestRefreshTokenCreation:
    """Tests for refresh token creation."""

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        token = TokenManager.create_refresh_token(
            user_id=1,
            email="user@example.com",
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_contains_user_info(self):
        """Test that refresh token contains user information."""
        token = TokenManager.create_refresh_token(
            user_id=99,
            email="refresh@example.com",
        )

        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["user_id"] == 99
        assert payload["email"] == "refresh@example.com"
        assert payload["is_admin"] is False
        assert payload["token_type"] == "refresh"

    def test_refresh_token_has_longer_expiration(self):
        """Test that refresh token has longer expiration than access token."""
        now = datetime.now(timezone.utc)
        refresh_token = TokenManager.create_refresh_token(user_id=1, email="user@example.com")

        payload = jwt.decode(
            refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = now + timedelta(days=settings.refresh_token_expiration_days)

        # Allow 5 second tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 5


class TestTokenVerification:
    """Tests for token verification."""

    def test_verify_valid_access_token(self):
        """Test verifying a valid access token."""
        token = TokenManager.create_access_token(
            user_id=1,
            email="user@example.com",
            is_admin=False,
        )

        payload = TokenManager.verify_token(token)

        assert payload is not None
        assert payload.user_id == 1
        assert payload.email == "user@example.com"
        assert payload.is_admin is False
        assert payload.token_type == "access"

    def test_verify_valid_refresh_token(self):
        """Test verifying a valid refresh token."""
        token = TokenManager.create_refresh_token(
            user_id=2,
            email="refresh@example.com",
        )

        payload = TokenManager.verify_token(token)

        assert payload is not None
        assert payload.user_id == 2
        assert payload.email == "refresh@example.com"
        assert payload.token_type == "refresh"

    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.string"
        payload = TokenManager.verify_token(invalid_token)

        assert payload is None

    def test_verify_tampered_token(self):
        """Test verifying a tampered token."""
        token = TokenManager.create_access_token(user_id=1, email="user@example.com")

        # Tamper with the token by changing a character
        tampered_token = token[:-5] + "xxxxx"
        payload = TokenManager.verify_token(tampered_token)

        assert payload is None

    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        # Create a token with immediate expiration
        now = datetime.now(timezone.utc)
        exp = now - timedelta(seconds=1)

        token_dict = {
            "user_id": 1,
            "email": "user@example.com",
            "is_admin": False,
            "token_type": "access",
            "exp": exp,
            "iat": now,
        }

        expired_token = jwt.encode(
            token_dict,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        payload = TokenManager.verify_token(expired_token)
        assert payload is None


class TestTokenTypeChecking:
    """Tests for checking token types."""

    def test_is_access_token(self):
        """Test checking if token is access token."""
        access_token = TokenManager.create_access_token(user_id=1, email="user@example.com")

        assert TokenManager.is_access_token(access_token) is True

    def test_is_access_token_false_for_refresh(self):
        """Test that refresh token is not identified as access token."""
        refresh_token = TokenManager.create_refresh_token(user_id=1, email="user@example.com")

        assert TokenManager.is_access_token(refresh_token) is False

    def test_is_refresh_token(self):
        """Test checking if token is refresh token."""
        refresh_token = TokenManager.create_refresh_token(user_id=1, email="user@example.com")

        assert TokenManager.is_refresh_token(refresh_token) is True

    def test_is_refresh_token_false_for_access(self):
        """Test that access token is not identified as refresh token."""
        access_token = TokenManager.create_access_token(user_id=1, email="user@example.com")

        assert TokenManager.is_refresh_token(access_token) is False

    def test_is_access_token_false_for_invalid(self):
        """Test that invalid token is not identified as access token."""
        assert TokenManager.is_access_token("invalid.token") is False

    def test_is_refresh_token_false_for_invalid(self):
        """Test that invalid token is not identified as refresh token."""
        assert TokenManager.is_refresh_token("invalid.token") is False


class TestCreateTokens:
    """Tests for creating both access and refresh tokens."""

    def test_create_tokens(self):
        """Test creating both tokens."""
        tokens = TokenManager.create_tokens(
            user_id=1,
            email="user@example.com",
            is_admin=False,
        )

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)

    def test_create_tokens_are_different(self):
        """Test that created tokens are different."""
        tokens = TokenManager.create_tokens(
            user_id=1,
            email="user@example.com",
        )

        assert tokens["access_token"] != tokens["refresh_token"]

    def test_create_tokens_verify_correctly(self):
        """Test that both created tokens verify correctly."""
        tokens = TokenManager.create_tokens(
            user_id=42,
            email="test@example.com",
            is_admin=True,
        )

        access_payload = TokenManager.verify_token(tokens["access_token"])
        assert access_payload is not None
        assert access_payload.token_type == "access"
        assert access_payload.user_id == 42

        refresh_payload = TokenManager.verify_token(tokens["refresh_token"])
        assert refresh_payload is not None
        assert refresh_payload.token_type == "refresh"
        assert refresh_payload.user_id == 42
