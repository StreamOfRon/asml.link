"""Tests for OAuth2 provider integration utilities."""

import pytest

from app.utils.oauth import OAuthProvider, OAuthManager, OAuthUserInfo, oauth_manager
from app.config import settings


class TestOAuthUserInfo:
    """Tests for OAuthUserInfo dataclass."""

    def test_oauth_user_info_creation(self):
        """Test creating OAuth user info."""
        info = OAuthUserInfo(
            provider_id="12345",
            email="user@example.com",
            name="John Doe",
            avatar_url="https://example.com/avatar.jpg",
            provider="google",
        )

        assert info.provider_id == "12345"
        assert info.email == "user@example.com"
        assert info.name == "John Doe"
        assert info.provider == "google"


class TestOAuthProvider:
    """Tests for OAuthProvider class."""

    def test_provider_initialization_google(self):
        """Test initializing Google OAuth provider."""
        provider = OAuthProvider("google")

        assert provider.provider_name == "google"
        assert provider.config is not None
        assert "authorize_url" in provider.config
        assert "access_token_url" in provider.config
        assert "userinfo_endpoint" in provider.config

    def test_provider_initialization_github(self):
        """Test initializing GitHub OAuth provider."""
        provider = OAuthProvider("github")

        assert provider.provider_name == "github"
        assert provider.config is not None

    def test_provider_initialization_case_insensitive(self):
        """Test that provider name is case-insensitive."""
        provider1 = OAuthProvider("GOOGLE")
        provider2 = OAuthProvider("google")

        assert provider1.provider_name == provider2.provider_name

    def test_get_scope_google(self):
        """Test getting scopes for Google."""
        provider = OAuthProvider("google")
        scope = provider._get_scope()

        assert "openid" in scope
        assert "profile" in scope
        assert "email" in scope

    def test_get_scope_github(self):
        """Test getting scopes for GitHub."""
        provider = OAuthProvider("github")
        scope = provider._get_scope()

        assert "email" in scope

    def test_get_authorization_url_google(self):
        """Test generating authorization URL for Google."""
        provider = OAuthProvider("google")

        url = provider.get_authorization_url(
            state="test-state", redirect_uri="http://localhost:5000/auth/callback/google"
        )

        assert "https://accounts.google.com" in url
        assert "test-state" in url
        assert "offline" in url  # Google-specific
        assert "consent" in url  # Google-specific
        assert "response_type=code" in url
        assert "scope=" in url

    def test_get_authorization_url_github(self):
        """Test generating authorization URL for GitHub."""
        provider = OAuthProvider("github")

        url = provider.get_authorization_url(
            state="test-state", redirect_uri="http://localhost:5000/auth/callback/github"
        )

        assert "https://github.com/login/oauth/authorize" in url
        assert "test-state" in url
        assert "response_type=code" in url
        assert "scope=" in url

    def test_parse_user_info_google(self):
        """Test parsing Google user info response."""
        provider = OAuthProvider("google")

        google_response = {
            "id": "123456789",
            "email": "user@gmail.com",
            "name": "John Doe",
            "picture": "https://example.com/photo.jpg",
        }

        user_info = provider._parse_user_info(google_response)

        assert user_info.provider_id == "123456789"
        assert user_info.email == "user@gmail.com"
        assert user_info.name == "John Doe"
        assert user_info.avatar_url == "https://example.com/photo.jpg"
        assert user_info.provider == "google"

    def test_parse_user_info_github(self):
        """Test parsing GitHub user info response."""
        provider = OAuthProvider("github")

        github_response = {
            "id": 987654321,
            "email": "user@github.com",
            "name": "Jane Doe",
            "avatar_url": "https://github.com/avatar.jpg",
        }

        user_info = provider._parse_user_info(github_response)

        assert user_info.provider_id == "987654321"
        assert user_info.email == "user@github.com"
        assert user_info.name == "Jane Doe"
        assert user_info.avatar_url == "https://github.com/avatar.jpg"
        assert user_info.provider == "github"

    def test_parse_user_info_invalid_provider(self):
        """Test that parsing with invalid provider raises error."""
        provider = OAuthProvider("google")
        provider.provider_name = "invalid"

        with pytest.raises(ValueError):
            provider._parse_user_info({"id": "123"})


class TestOAuthManager:
    """Tests for OAuthManager class."""

    def test_oauth_manager_initialization(self):
        """Test initializing OAuth manager."""
        manager = OAuthManager()

        assert len(manager.providers) > 0
        assert "google" in manager.providers
        assert "github" in manager.providers

    def test_get_provider(self):
        """Test getting a provider."""
        manager = OAuthManager()

        provider = manager.get_provider("google")
        assert provider is not None
        assert provider.provider_name == "google"

    def test_get_provider_case_insensitive(self):
        """Test that get_provider is case-insensitive."""
        manager = OAuthManager()

        provider1 = manager.get_provider("GOOGLE")
        provider2 = manager.get_provider("google")

        assert provider1 is not None
        assert provider2 is not None
        assert provider1.provider_name == provider2.provider_name

    def test_get_provider_not_found(self):
        """Test getting non-existent provider."""
        manager = OAuthManager()

        provider = manager.get_provider("invalid")
        assert provider is None

    def test_get_available_providers(self):
        """Test getting available providers."""
        manager = OAuthManager()

        providers = manager.get_available_providers()
        assert "google" in providers
        assert "github" in providers

    def test_is_provider_configured(self):
        """Test checking if provider is configured."""
        manager = OAuthManager()

        # Just verify the method works and returns correct type
        result = manager.is_provider_configured("google")
        assert isinstance(result, bool)

    def test_is_provider_configured_invalid_provider(self):
        """Test that invalid provider returns False."""
        manager = OAuthManager()

        result = manager.is_provider_configured("nonexistent_provider")
        assert result is False

    def test_is_provider_configured_invalid(self):
        """Test checking invalid provider."""
        manager = OAuthManager()

        result = manager.is_provider_configured("invalid")
        assert result is False


class TestOAuthManagerGlobal:
    """Tests for global oauth_manager instance."""

    def test_global_oauth_manager_exists(self):
        """Test that global oauth_manager exists."""
        assert oauth_manager is not None
        assert isinstance(oauth_manager, OAuthManager)

    def test_global_oauth_manager_has_providers(self):
        """Test that global manager has providers."""
        providers = oauth_manager.get_available_providers()
        assert len(providers) > 0
