"""Application configuration management."""

from typing import Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(default="sqlite:///./data/asml-link.db")

    # OAuth Providers
    oauth_providers: str = Field(default="google,github")

    # Google OAuth
    google_client_id: Optional[str] = Field(default=None)
    google_client_secret: Optional[str] = Field(default=None)
    google_redirect_uri: Optional[str] = Field(default=None)

    # GitHub OAuth
    github_client_id: Optional[str] = Field(default=None)
    github_client_secret: Optional[str] = Field(default=None)
    github_redirect_uri: Optional[str] = Field(default=None)

    # JWT/Security
    jwt_secret_key: str = Field(default="dev-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_seconds: int = Field(default=3600)  # 1 hour
    refresh_token_expiration_days: int = Field(default=7)

    # CSRF Protection
    csrf_secret_key: str = Field(default="dev-csrf-secret-change-in-production")
    csrf_token_expiration_minutes: int = Field(default=60)  # 1 hour

    # Security Headers
    enable_https_redirect: bool = Field(default=False)
    enable_hsts: bool = Field(default=True)
    hsts_max_age: int = Field(default=31536000)  # 1 year

    # Session Security
    session_secure_cookies: bool = Field(default=False)  # Set to True in production
    session_httponly: bool = Field(default=True)
    session_samesite: str = Field(default="Lax")  # Strict, Lax, or None

    # Application Settings
    instance_name: str = Field(default="My Short Links")
    allow_private_links_only: bool = Field(default=False)
    enable_allow_list_mode: bool = Field(default=False)

    # Server
    debug: bool = Field(default=True)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=5000)

    # Logging
    log_level: str = Field(default="INFO")

    def get_oauth_providers(self) -> list[str]:
        """Parse comma-separated OAuth providers."""
        return [p.strip().lower() for p in self.oauth_providers.split(",")]

    def get_oauth_config(self, provider: str) -> dict[str, Optional[str]]:
        """Get OAuth configuration for a specific provider."""
        provider = provider.lower()

        if provider == "google":
            return {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "redirect_uri": self.google_redirect_uri,
                "authorize_url": "https://accounts.google.com/o/oauth2/auth",
                "access_token_url": "https://oauth2.googleapis.com/token",
                "userinfo_endpoint": "https://www.googleapis.com/oauth2/v1/userinfo",
            }
        elif provider == "github":
            return {
                "client_id": self.github_client_id,
                "client_secret": self.github_client_secret,
                "redirect_uri": self.github_redirect_uri,
                "authorize_url": "https://github.com/login/oauth/authorize",
                "access_token_url": "https://github.com/login/oauth/access_token",
                "userinfo_endpoint": "https://api.github.com/user",
            }

        return {
            "client_id": None,
            "client_secret": None,
            "redirect_uri": None,
            "authorize_url": None,
            "access_token_url": None,
            "userinfo_endpoint": None,
        }

    def get_database_url(self) -> str:
        """Get properly formatted database URL."""
        # For PostgreSQL, ensure async driver
        if self.database_url.startswith("postgresql"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        # For SQLite, use aiosqlite driver
        if self.database_url.startswith("sqlite"):
            return self.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        return self.database_url


# Global settings instance
settings = Settings()
