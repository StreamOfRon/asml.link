"""Integration tests for link API endpoints."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.models.user import User
from app.services.link_service import LinkService


class TestLinkServiceIntegration:
    """Tests for link service integration with routes."""

    async def test_link_response_format(self, db_session: AsyncSession, test_user: User):
        """Test that link responses have correct format."""
        # Create a link via service
        service = LinkService(db_session)
        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/test",
            slug="test123",
            is_public=True,
        )

        # Verify the link has all required fields
        assert link.id is not None
        assert link.user_id == test_user.id
        assert link.original_url == "https://example.com/test"
        assert link.slug == "test123"
        assert link.is_public is True
        assert link.hit_count == 0
        assert link.last_hit_at is None
        assert link.created_at is not None
        assert link.updated_at is not None

    async def test_link_allowed_emails_serialization(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that allowed emails are properly serialized/deserialized."""
        service = LinkService(db_session)
        emails = ["alice@example.com", "bob@example.com"]

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            is_public=False,
            allowed_emails=emails,
        )

        # Verify emails are stored and retrievable
        assert link.get_allowed_emails() == emails

    async def test_get_user_links_pagination(self, db_session: AsyncSession, test_user: User):
        """Test pagination of user links."""
        service = LinkService(db_session)

        # Create multiple links
        for i in range(5):
            await service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/url{i}",
                slug=f"slug{i}",
            )

        # Get all user links
        links = await service.get_user_links(test_user.id, include_private=True)
        assert len(links) == 5

    async def test_update_link_validation(self, db_session: AsyncSession, test_user: User):
        """Test that update_link validates input."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/test",
        )

        # Test updating with invalid URL
        from app.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await service.update_link(
                link_id=link.id,
                user_id=test_user.id,
                original_url="not a valid url",
            )

    async def test_delete_link_not_found(self, db_session: AsyncSession, test_user: User):
        """Test deleting non-existent link raises NotFoundError."""
        service = LinkService(db_session)

        from app.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await service.delete_link(link_id=999, user_id=test_user.id)

    async def test_delete_link_forbidden(self, db_session: AsyncSession, test_user: User):
        """Test deleting another user's link raises ForbiddenError."""
        service = LinkService(db_session)

        # Create link for test_user
        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/test",
        )

        # Try to delete as different user
        from app.exceptions import ForbiddenError

        with pytest.raises(ForbiddenError):
            await service.delete_link(link_id=link.id, user_id=test_user.id + 1)

    async def test_increment_hit_count(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ):
        """Test incrementing hit count."""
        service = LinkService(db_session)

        initial_count = test_link.hit_count
        updated_link = await service.increment_hit_count(test_link.slug)

        assert updated_link.hit_count == initial_count + 1
        assert updated_link.last_hit_at is not None

    async def test_check_link_access_public(self, test_link: Link):
        """Test access check for public link."""
        service = LinkService(None)  # No DB needed for this check
        assert await service.check_link_access(test_link) is True
        assert await service.check_link_access(test_link, user_email="anyone@example.com") is True

    async def test_check_link_access_private_no_email(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test access check for private link without email."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            is_public=False,
            allowed_emails=["alice@example.com"],
        )

        assert await service.check_link_access(link) is False
        assert await service.check_link_access(link, user_email=None) is False

    async def test_check_link_access_private_allowed_email(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test access check for private link with allowed email."""
        service = LinkService(db_session)

        email = "alice@example.com"
        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            is_public=False,
            allowed_emails=[email],
        )

        assert await service.check_link_access(link, user_email=email) is True

    async def test_check_link_access_private_forbidden_email(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test access check for private link with non-allowed email."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            is_public=False,
            allowed_emails=["alice@example.com"],
        )

        assert await service.check_link_access(link, user_email="bob@example.com") is False

    async def test_check_link_access_case_insensitive(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that email access check is case-insensitive."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            is_public=False,
            allowed_emails=["Alice@Example.com"],
        )

        assert await service.check_link_access(link, user_email="alice@example.com") is True
        assert await service.check_link_access(link, user_email="ALICE@EXAMPLE.COM") is True
