"""Integration tests for redirect endpoint and access control."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.link import Link
from app.services.link_service import LinkService


class TestRedirectEndpoint:
    """Tests for the redirect endpoint."""

    async def test_redirect_public_link(self, db_session: AsyncSession, test_user: User):
        """Test redirect to public link."""
        service = LinkService(db_session)

        original_url = "https://example.com/target"
        link = await service.create_link(
            user_id=test_user.id,
            original_url=original_url,
            slug="public123",
            is_public=True,
        )

        # Verify link was created
        assert link.id is not None
        assert link.original_url == original_url
        assert link.is_public is True

    async def test_redirect_private_link_accessible(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that private link can be accessed by allowed user."""
        service = LinkService(db_session)

        email = "allowed@example.com"
        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="private123",
            is_public=False,
            allowed_emails=[email],
        )

        # Verify access is granted
        access = await service.check_link_access(link, user_email=email)
        assert access is True

    async def test_redirect_private_link_denied(self, db_session: AsyncSession, test_user: User):
        """Test that private link denies access to non-allowed user."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="private456",
            is_public=False,
            allowed_emails=["allowed@example.com"],
        )

        # Verify access is denied
        access = await service.check_link_access(link, user_email="denied@example.com")
        assert access is False

    async def test_redirect_unauthenticated_to_private(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that unauthenticated users cannot access private links."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="private789",
            is_public=False,
            allowed_emails=["user@example.com"],
        )

        # Verify access is denied for unauthenticated
        access = await service.check_link_access(link, user_email=None)
        assert access is False

    async def test_redirect_increments_hit_count(self, db_session: AsyncSession, test_user: User):
        """Test that redirect increments hit count."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/target",
            slug="hits123",
            is_public=True,
        )

        initial_count = link.hit_count
        assert initial_count == 0

        # Simulate redirect by incrementing hit count
        updated = await service.increment_hit_count(link.slug)
        assert updated.hit_count == initial_count + 1
        assert updated.last_hit_at is not None

    async def test_redirect_nonexistent_slug(self, db_session: AsyncSession):
        """Test redirect to non-existent slug returns 404."""
        service = LinkService(db_session)

        # Try to get non-existent link
        link = await service.get_link_by_slug("nonexistent123")
        assert link is None

    async def test_redirect_multiple_hits(self, db_session: AsyncSession, test_user: User):
        """Test that multiple redirects accumulate hit count."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/target",
            slug="multihit",
            is_public=True,
        )

        # Simulate multiple redirects
        for i in range(5):
            updated = await service.increment_hit_count(link.slug)
            assert updated.hit_count == i + 1

        # Final verification
        final_link = await service.get_link_by_slug("multihit")
        assert final_link.hit_count == 5

    async def test_redirect_case_insensitive_email(self, db_session: AsyncSession, test_user: User):
        """Test that email matching is case-insensitive."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="casetest",
            is_public=False,
            allowed_emails=["User@Example.com"],
        )

        # Test various case combinations
        assert await service.check_link_access(link, user_email="user@example.com") is True
        assert await service.check_link_access(link, user_email="USER@EXAMPLE.COM") is True
        assert await service.check_link_access(link, user_email="User@Example.com") is True

    async def test_redirect_empty_allowlist(self, db_session: AsyncSession, test_user: User):
        """Test private link with no allowed emails denies all access."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="noallow",
            is_public=False,
            allowed_emails=[],
        )

        # No one should have access
        assert await service.check_link_access(link) is False
        assert await service.check_link_access(link, user_email="anyone@example.com") is False

    async def test_redirect_preserves_url_parameters(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that original URL with query parameters is preserved."""
        service = LinkService(db_session)

        url_with_params = "https://example.com/search?q=test&page=1&utm_source=shortlink"
        link = await service.create_link(
            user_id=test_user.id,
            original_url=url_with_params,
            slug="params123",
            is_public=True,
        )

        # Verify URL is stored as-is
        assert link.original_url == url_with_params

    async def test_redirect_long_url(self, db_session: AsyncSession, test_user: User):
        """Test that very long URLs are handled correctly."""
        service = LinkService(db_session)

        long_url = "https://example.com/" + "a" * 1000 + "?q=test&param2=value"
        link = await service.create_link(
            user_id=test_user.id,
            original_url=long_url,
            slug="longurl123",
            is_public=True,
        )

        # Verify long URL is stored correctly
        assert link.original_url == long_url
        assert len(link.original_url) > 1000


class TestAccessControlScenarios:
    """Tests for complex access control scenarios."""

    async def test_public_link_anyone_can_access(self, db_session: AsyncSession, test_user: User):
        """Test that public links are accessible to anyone."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/public",
            slug="pubanyc",
            is_public=True,
        )

        # Unauthenticated
        assert await service.check_link_access(link) is True

        # Random authenticated user
        assert await service.check_link_access(link, user_email="random@example.com") is True

        # Admin user
        assert await service.check_link_access(link, user_email="admin@example.com") is True

    async def test_private_link_only_allowlist(self, db_session: AsyncSession, test_user: User):
        """Test that private links only allow emails in allowlist."""
        service = LinkService(db_session)

        allowed = ["alice@example.com", "bob@example.com"]
        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="priallow",
            is_public=False,
            allowed_emails=allowed,
        )

        # Allowed users
        for email in allowed:
            assert await service.check_link_access(link, user_email=email) is True

        # Denied users
        for email in ["charlie@example.com", "denied@example.com"]:
            assert await service.check_link_access(link, user_email=email) is False

        # Unauthenticated
        assert await service.check_link_access(link, user_email=None) is False

    async def test_private_link_multiple_allowlist_updates(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating allowlist multiple times."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="multiupd",
            is_public=False,
            allowed_emails=["alice@example.com"],
        )

        # Initial state
        assert await service.check_link_access(link, user_email="alice@example.com") is True
        assert await service.check_link_access(link, user_email="bob@example.com") is False

        # Update allowlist
        updated = await service.update_link(
            link_id=link.id,
            user_id=test_user.id,
            allowed_emails=["alice@example.com", "bob@example.com", "charlie@example.com"],
        )

        # All three should now have access
        assert await service.check_link_access(updated, user_email="alice@example.com") is True
        assert await service.check_link_access(updated, user_email="bob@example.com") is True
        assert await service.check_link_access(updated, user_email="charlie@example.com") is True

    async def test_switch_public_to_private(self, db_session: AsyncSession, test_user: User):
        """Test changing link from public to private."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/target",
            slug="pubpriv",
            is_public=True,
        )

        # Initially public - accessible to all
        assert await service.check_link_access(link) is True
        assert await service.check_link_access(link, user_email="anyone@example.com") is True

        # Change to private with allowlist
        updated = await service.update_link(
            link_id=link.id,
            user_id=test_user.id,
            is_public=False,
            allowed_emails=["alice@example.com"],
        )

        # Now only allowlisted emails can access
        assert await service.check_link_access(updated, user_email="alice@example.com") is True
        assert await service.check_link_access(updated, user_email="bob@example.com") is False

    async def test_switch_private_to_public(self, db_session: AsyncSession, test_user: User):
        """Test changing link from private to public."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/target",
            slug="privpub",
            is_public=False,
            allowed_emails=["alice@example.com"],
        )

        # Initially private - only allowlisted users
        assert await service.check_link_access(link, user_email="alice@example.com") is True
        assert await service.check_link_access(link, user_email="bob@example.com") is False

        # Change to public
        updated = await service.update_link(
            link_id=link.id,
            user_id=test_user.id,
            is_public=True,
        )

        # Now everyone can access
        assert await service.check_link_access(updated) is True
        assert await service.check_link_access(updated, user_email="bob@example.com") is True
