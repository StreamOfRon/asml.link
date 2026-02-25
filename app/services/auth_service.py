"""Authentication service for OAuth and session management."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models.oauth_account import OAuthAccount
from app.models.user import User
from app.utils.validators import is_valid_email, normalize_email


class AuthService:
    """Service for authentication and OAuth operations."""

    def __init__(self, db_session: AsyncSession):
        """Initialize auth service with database session."""
        self.db = db_session

    async def link_oauth_account(
        self,
        user_id: int,
        provider: str,
        provider_user_id: str,
        provider_email: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> OAuthAccount:
        """
        Link an OAuth account to a user.

        Args:
            user_id: User ID
            provider: OAuth provider name (e.g., 'google', 'github')
            provider_user_id: User ID from the provider
            provider_email: Email from the provider
            access_token: OAuth access token
            refresh_token: OAuth refresh token

        Returns:
            Created OAuthAccount object

        Raises:
            ValidationError: If validation fails
            NotFoundError: If user not found
            ConflictError: If OAuth account already exists
        """
        # Validate user exists
        user = await self._get_user(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")

        # Validate provider and IDs
        if not provider or not provider_user_id:
            raise ValidationError("Provider and provider_user_id are required")

        # Check if OAuth account already exists
        existing = await self._get_oauth_account(provider, provider_user_id)
        if existing is not None:
            raise ConflictError(f"OAuth account for {provider}:{provider_user_id} already linked")

        # Create OAuth account
        oauth = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
            access_token=access_token,
            refresh_token=refresh_token,
        )

        self.db.add(oauth)
        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to link OAuth account: {str(e)}")

        await self.db.refresh(oauth)
        return oauth

    async def get_or_create_user_from_oauth(
        self,
        provider: str,
        provider_user_id: str,
        provider_email: Optional[str] = None,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one from OAuth provider.

        Args:
            provider: OAuth provider name
            provider_user_id: User ID from provider
            provider_email: Email from provider
            full_name: Full name from provider
            avatar_url: Avatar URL from provider

        Returns:
            Tuple of (User object, created_flag)

        Raises:
            ValidationError: If validation fails
        """
        # Check if OAuth account exists
        oauth = await self._get_oauth_account(provider, provider_user_id)
        if oauth is not None:
            user = await self._get_user(oauth.user_id)
            if user is not None:
                return user, False

        # Try to find user by email
        user = None
        if provider_email and is_valid_email(provider_email):
            email = normalize_email(provider_email)
            user = await self._get_user_by_email(email)

        # Create new user if not found
        if user is None:
            if not provider_email:
                raise ValidationError("provider_email required for new user")

            email = normalize_email(provider_email)

            # Check email not already used
            existing = await self._get_user_by_email(email)
            if existing is not None:
                raise ConflictError(f"Email {email} already registered")

            user = User(
                email=email,
                full_name=full_name,
                avatar_url=avatar_url,
                is_admin=False,
                is_blocked=False,
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

        # Link OAuth account
        await self.link_oauth_account(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
            access_token=None,
            refresh_token=None,
        )

        return user, True

    async def unlink_oauth_account(
        self,
        user_id: int,
        provider: str,
    ) -> None:
        """
        Unlink an OAuth account from user.

        Args:
            user_id: User ID
            provider: OAuth provider name

        Raises:
            NotFoundError: If user or OAuth account not found
        """
        user = await self._get_user(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")

        oauth = await self._get_user_oauth_account(user_id, provider)
        if oauth is None:
            raise NotFoundError(f"OAuth account for {provider} not found")

        await self.db.delete(oauth)
        await self.db.commit()

    async def update_oauth_tokens(
        self,
        user_id: int,
        provider: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> OAuthAccount:
        """
        Update OAuth tokens for a user's OAuth account.

        Args:
            user_id: User ID
            provider: OAuth provider name
            access_token: New access token
            refresh_token: New refresh token

        Returns:
            Updated OAuthAccount object

        Raises:
            NotFoundError: If user or OAuth account not found
        """
        oauth = await self._get_user_oauth_account(user_id, provider)
        if oauth is None:
            raise NotFoundError(
                f"OAuth account for user {user_id} with provider {provider} not found"
            )

        if access_token is not None:
            oauth.access_token = access_token

        if refresh_token is not None:
            oauth.refresh_token = refresh_token

        self.db.add(oauth)
        await self.db.commit()
        await self.db.refresh(oauth)
        return oauth

    async def get_user_oauth_accounts(self, user_id: int) -> list[OAuthAccount]:
        """
        Get all OAuth accounts for a user.

        Args:
            user_id: User ID

        Returns:
            List of OAuthAccount objects
        """
        stmt = select(OAuthAccount).where(OAuthAccount.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_user_by_oauth(
        self,
        provider: str,
        provider_user_id: str,
    ) -> Optional[User]:
        """
        Get user by OAuth provider credentials.

        Args:
            provider: OAuth provider name
            provider_user_id: User ID from provider

        Returns:
            User object or None if not found
        """
        oauth = await self._get_oauth_account(provider, provider_user_id)
        if oauth is None:
            return None

        return await self._get_user(oauth.user_id)

    # Private helper methods

    async def _get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_oauth_account(
        self,
        provider: str,
        provider_user_id: str,
    ) -> Optional[OAuthAccount]:
        """Get OAuth account by provider and provider_user_id."""
        stmt = select(OAuthAccount).where(
            (OAuthAccount.provider == provider)
            & (OAuthAccount.provider_user_id == provider_user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_oauth_account(
        self,
        user_id: int,
        provider: str,
    ) -> Optional[OAuthAccount]:
        """Get specific OAuth account for a user."""
        stmt = select(OAuthAccount).where(
            (OAuthAccount.user_id == user_id) & (OAuthAccount.provider == provider)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
