"""OAuth2 provider integration utilities.

This module provides utilities for OAuth2 provider integration,
including client setup and user info retrieval.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp

from app.config import settings


@dataclass
class OAuthUserInfo:
    """OAuth user information from provider."""

    provider_id: str  # User's ID at the OAuth provider
    email: Optional[str]  # Email address
    name: Optional[str]  # Full name
    avatar_url: Optional[str]  # Avatar/profile picture URL
    provider: str  # Provider name (google, github, etc)


class OAuthProvider:
    """Base class for OAuth2 providers."""

    def __init__(self, provider_name: str):
        """Initialize OAuth provider.

        Args:
            provider_name: Name of the provider (google, github, etc)
        """
        self.provider_name = provider_name.lower()
        self.config = settings.get_oauth_config(provider_name)

    def get_authorization_url(self, state: str, redirect_uri: Optional[str] = None) -> str:
        """Get OAuth authorization URL for user login.

        Args:
            state: CSRF protection state parameter
            redirect_uri: Custom redirect URI (uses config default if not provided)

        Returns:
            Full OAuth authorization URL
        """
        redirect_uri = redirect_uri or self.config.get("redirect_uri")

        params = {
            "client_id": self.config.get("client_id"),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": self._get_scope(),
        }

        # Add provider-specific parameters
        if self.provider_name == "google":
            params["access_type"] = "offline"
            params["prompt"] = "consent"

        param_str = "&".join(f"{k}={v}" for k, v in params.items() if v)
        return f"{self.config.get('authorize_url')}?{param_str}"

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from provider
            redirect_uri: Custom redirect URI (uses config default if not provided)

        Returns:
            Token response dictionary with access_token, etc
        """
        redirect_uri = redirect_uri or self.config.get("redirect_uri")

        payload = {
            "client_id": self.config.get("client_id"),
            "client_secret": self.config.get("client_secret"),
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.config.get("access_token_url"),
                data=payload,
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Token exchange failed: {response.status}")

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Retrieve user information from OAuth provider.

        Args:
            access_token: OAuth access token

        Returns:
            OAuthUserInfo with user details from provider
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.config.get("userinfo_endpoint"),
                headers=headers,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_user_info(data)
                else:
                    raise Exception(f"User info retrieval failed: {response.status}")

    def _get_scope(self) -> str:
        """Get OAuth scopes for provider.

        Returns:
            Scope string for OAuth request
        """
        if self.provider_name == "google":
            return "openid profile email"
        elif self.provider_name == "github":
            return "user:email"
        return ""

    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        """Parse user info from provider response.

        Args:
            data: User info response from provider

        Returns:
            OAuthUserInfo object
        """
        if self.provider_name == "google":
            return OAuthUserInfo(
                provider_id=data.get("id"),
                email=data.get("email"),
                name=data.get("name"),
                avatar_url=data.get("picture"),
                provider="google",
            )
        elif self.provider_name == "github":
            return OAuthUserInfo(
                provider_id=str(data.get("id")),
                email=data.get("email"),
                name=data.get("name"),
                avatar_url=data.get("avatar_url"),
                provider="github",
            )

        raise ValueError(f"Unknown provider: {self.provider_name}")


class OAuthManager:
    """Manager for multiple OAuth providers."""

    def __init__(self):
        """Initialize OAuth manager with configured providers."""
        self.providers: Dict[str, OAuthProvider] = {}

        for provider_name in settings.get_oauth_providers():
            self.providers[provider_name] = OAuthProvider(provider_name)

    def get_provider(self, provider_name: str) -> Optional[OAuthProvider]:
        """Get OAuth provider by name.

        Args:
            provider_name: Name of the provider

        Returns:
            OAuthProvider instance or None if not configured
        """
        return self.providers.get(provider_name.lower())

    def get_available_providers(self) -> list[str]:
        """Get list of available OAuth providers.

        Returns:
            List of provider names
        """
        return list(self.providers.keys())

    def is_provider_configured(self, provider_name: str) -> bool:
        """Check if a provider is configured.

        Args:
            provider_name: Name of the provider

        Returns:
            True if provider is configured with credentials
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return False

        # Check if provider has required credentials
        return bool(
            provider.config.get("client_id")
            and provider.config.get("client_secret")
            and provider.config.get("redirect_uri")
        )


# Global OAuth manager instance
oauth_manager = OAuthManager()
