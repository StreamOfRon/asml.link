"""Authentication service tests."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.oauth_account import OAuthAccount
from app.models.user import User


class TestUserCreationFromOAuth:
    """Test creating users from OAuth providers."""

    async def test_create_user_from_oauth_google(self, db_session: AsyncSession) -> None:
        """Test creating a user from Google OAuth."""
        user = User(
            email="user@gmail.com",
            full_name="Google User",
            avatar_url="https://example.com/avatar.jpg",
            is_admin=False,
            is_blocked=False,
        )
        db_session.add(user)
        await db_session.commit()

        oauth = OAuthAccount(
            user_id=user.id,
            provider="google",
            provider_user_id="google_12345",
            provider_email="user@gmail.com",
            access_token="google_token_xyz",
        )
        db_session.add(oauth)
        await db_session.commit()

        # Verify both records exist with eager loading
        stmt = select(User).where(User.id == user.id).options(selectinload(User.oauth_accounts))
        result = await db_session.execute(stmt)
        found_user = result.scalar_one_or_none()

        assert found_user is not None
        assert found_user.email == "user@gmail.com"
        assert len(found_user.oauth_accounts) == 1
        assert found_user.oauth_accounts[0].provider == "google"

    async def test_create_user_from_oauth_github(self, db_session: AsyncSession) -> None:
        """Test creating a user from GitHub OAuth."""
        user = User(
            email="user@github.com",
            full_name="GitHub User",
            is_admin=False,
            is_blocked=False,
        )
        db_session.add(user)
        await db_session.commit()

        oauth = OAuthAccount(
            user_id=user.id,
            provider="github",
            provider_user_id="github_67890",
            provider_email="user@github.com",
            access_token="github_token_abc",
            refresh_token="github_refresh_xyz",
        )
        db_session.add(oauth)
        await db_session.commit()

        stmt = select(User).where(User.id == user.id).options(selectinload(User.oauth_accounts))
        result = await db_session.execute(stmt)
        found_user = result.scalar_one_or_none()

        assert found_user.oauth_accounts[0].provider == "github"
        assert found_user.oauth_accounts[0].refresh_token == "github_refresh_xyz"


class TestOAuthAccountLinking:
    """Test OAuth account linking and unlinking."""

    async def test_link_oauth_account_to_existing_user(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test linking an OAuth account to an existing user."""
        oauth = OAuthAccount(
            user_id=test_user.id,
            provider="github",
            provider_user_id="github_123",
            provider_email="test@github.com",
        )
        db_session.add(oauth)
        await db_session.commit()

        # Reload with eager loading
        stmt = (
            select(User).where(User.id == test_user.id).options(selectinload(User.oauth_accounts))
        )
        result = await db_session.execute(stmt)
        found_user = result.scalar_one_or_none()

        assert len(found_user.oauth_accounts) == 1
        assert found_user.oauth_accounts[0].provider == "github"

    async def test_user_can_have_multiple_oauth_accounts(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test user can link multiple OAuth accounts."""
        oauth_google = OAuthAccount(
            user_id=test_user.id,
            provider="google",
            provider_user_id="google_123",
            provider_email="test@gmail.com",
        )
        oauth_github = OAuthAccount(
            user_id=test_user.id,
            provider="github",
            provider_user_id="github_456",
            provider_email="test@github.com",
        )
        db_session.add(oauth_google)
        db_session.add(oauth_github)
        await db_session.commit()

        stmt = (
            select(User).where(User.id == test_user.id).options(selectinload(User.oauth_accounts))
        )
        result = await db_session.execute(stmt)
        found_user = result.scalar_one_or_none()

        assert len(found_user.oauth_accounts) == 2
        providers = {acc.provider for acc in found_user.oauth_accounts}
        assert providers == {"google", "github"}

    async def test_delete_oauth_account_keeps_user(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test deleting OAuth account doesn't delete user."""
        oauth = OAuthAccount(
            user_id=test_user.id,
            provider="google",
            provider_user_id="google_123",
        )
        db_session.add(oauth)
        await db_session.commit()

        _oauth_id = oauth.id
        await db_session.delete(oauth)
        await db_session.commit()

        # User should still exist
        stmt = (
            select(User).where(User.id == test_user.id).options(selectinload(User.oauth_accounts))
        )
        result = await db_session.execute(stmt)
        found_user = result.scalar_one_or_none()

        assert found_user is not None
        assert found_user.id is not None
        assert len(found_user.oauth_accounts) == 0


class TestUserAuthenticationStatus:
    """Test user authentication status checks."""

    async def test_user_is_not_blocked_by_default(self, db_session: AsyncSession) -> None:
        """Test new user is not blocked by default."""
        user = User(email="newuser@example.com", full_name="New User")
        db_session.add(user)
        await db_session.commit()

        assert user.is_blocked is False

    async def test_user_is_not_admin_by_default(self, db_session: AsyncSession) -> None:
        """Test new user is not admin by default."""
        user = User(email="user@example.com", full_name="User")
        db_session.add(user)
        await db_session.commit()

        assert user.is_admin is False

    async def test_admin_user_can_be_created(self, db_session: AsyncSession) -> None:
        """Test creating an admin user."""
        user = User(
            email="admin@example.com",
            full_name="Admin",
            is_admin=True,
        )
        db_session.add(user)
        await db_session.commit()

        assert user.is_admin is True

    async def test_user_can_be_blocked(self, db_session: AsyncSession, test_user: User) -> None:
        """Test marking a user as blocked."""
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()

        user.is_blocked = True
        db_session.add(user)
        await db_session.commit()

        # Reload to verify
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        found_user = result.scalar_one()
        assert found_user.is_blocked is True

    async def test_user_status_can_be_toggled(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test toggling user blocked status."""
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()

        # Block user
        user.is_blocked = True
        db_session.add(user)
        await db_session.commit()

        # Verify blocked
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        found_user = result.scalar_one()
        assert found_user.is_blocked is True

        # Unblock user
        found_user.is_blocked = False
        db_session.add(found_user)
        await db_session.commit()

        # Verify unblocked
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        found_user = result.scalar_one()
        assert found_user.is_blocked is False


class TestUserLookup:
    """Test finding users by various criteria."""

    async def test_find_user_by_email(self, db_session: AsyncSession, test_user: User) -> None:
        """Test finding a user by email."""
        stmt = select(User).where(User.email == test_user.email)
        result = await db_session.execute(stmt)
        found_user = result.scalar_one_or_none()

        assert found_user is not None
        assert found_user.email == test_user.email
        assert found_user.id == test_user.id

    async def test_find_oauth_account_by_provider_id(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test finding OAuth account by provider user ID."""
        oauth = OAuthAccount(
            user_id=test_user.id,
            provider="google",
            provider_user_id="google_12345",
        )
        db_session.add(oauth)
        await db_session.commit()

        stmt = select(OAuthAccount).where(OAuthAccount.provider_user_id == "google_12345")
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.provider_user_id == "google_12345"
        assert found.user_id == test_user.id

    async def test_find_user_oauth_by_provider(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test finding user's OAuth account by provider."""
        oauth = OAuthAccount(
            user_id=test_user.id,
            provider="github",
            provider_user_id="github_xyz",
        )
        db_session.add(oauth)
        await db_session.commit()

        stmt = select(OAuthAccount).where(
            (OAuthAccount.user_id == test_user.id) & (OAuthAccount.provider == "github")
        )
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.provider == "github"


class TestOAuthAccountValidation:
    """Test OAuth account validation."""

    async def test_oauth_email_can_be_different_from_user_email(
        self, db_session: AsyncSession
    ) -> None:
        """Test OAuth provider email can differ from user email."""
        user = User(email="user@example.com", full_name="User")
        db_session.add(user)
        await db_session.commit()

        oauth = OAuthAccount(
            user_id=user.id,
            provider="github",
            provider_user_id="github_123",
            provider_email="user@github.com",  # Different from user email
        )
        db_session.add(oauth)
        await db_session.commit()

        assert oauth.provider_email != user.email

    async def test_oauth_account_without_email(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test OAuth account can be created without provider email."""
        oauth = OAuthAccount(
            user_id=test_user.id,
            provider="github",
            provider_user_id="github_123",
            provider_email=None,
        )
        db_session.add(oauth)
        await db_session.commit()

        assert oauth.provider_email is None

    async def test_oauth_account_stores_tokens(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test OAuth account can store access and refresh tokens."""
        oauth = OAuthAccount(
            user_id=test_user.id,
            provider="google",
            provider_user_id="google_123",
            access_token="access_token_xyz",
            refresh_token="refresh_token_abc",
        )
        db_session.add(oauth)
        await db_session.commit()

        # Reload to verify tokens
        stmt = select(OAuthAccount).where(OAuthAccount.id == oauth.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.access_token == "access_token_xyz"
        assert found.refresh_token == "refresh_token_abc"


class TestUserEmailValidation:
    """Test user email validation."""

    async def test_user_email_must_be_unique(self, db_session: AsyncSession) -> None:
        """Test creating two users with same email raises error."""
        user1 = User(email="duplicate@example.com", full_name="User 1")
        db_session.add(user1)
        await db_session.commit()

        user2 = User(email="duplicate@example.com", full_name="User 2")
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_user_email_can_be_none(self, db_session: AsyncSession) -> None:
        """Test creating user with None email should raise error (NOT NULL constraint)."""
        user = User(email=None, full_name="User")
        db_session.add(user)

        with pytest.raises(IntegrityError):
            await db_session.commit()
