"""Tests for LinkService implementation."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.link_service import LinkService
from app.models.user import User
from app.models.link import Link
from app.exceptions import (
    ValidationError,
    NotFoundError,
    ForbiddenError,
    ConflictError,
)


class TestLinkServiceCreate:
    """Test LinkService.create_link method."""

    async def test_create_link_with_generated_slug(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test creating a link with auto-generated slug."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com",
            is_public=True,
        )

        assert link.id is not None
        assert link.user_id == test_user.id
        assert link.original_url == "https://example.com"
        assert link.slug is not None
        assert link.is_public is True
        assert link.hit_count == 0

    async def test_create_link_with_custom_slug(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test creating a link with custom slug."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com",
            slug="customslug123",
            is_public=True,
        )

        assert link.slug == "customslug123"

    async def test_create_link_invalid_url(self, db_session: AsyncSession, test_user: User) -> None:
        """Test creating link with invalid URL raises error."""
        service = LinkService(db_session)

        with pytest.raises(ValidationError):
            await service.create_link(
                user_id=test_user.id,
                original_url="not a valid url",
                is_public=True,
            )

    async def test_create_link_duplicate_slug(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test creating link with duplicate slug raises error."""
        service = LinkService(db_session)

        link1 = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/1",
            slug="duplicate",
            is_public=True,
        )

        with pytest.raises(ConflictError):
            await service.create_link(
                user_id=test_user.id,
                original_url="https://example.com/2",
                slug="duplicate",
                is_public=True,
            )

    async def test_create_private_link_with_allowed_emails(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test creating private link with allowed emails."""
        service = LinkService(db_session)

        allowed = ["user1@example.com", "user2@example.com"]
        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="privatelink123",
            is_public=False,
            allowed_emails=allowed,
        )

        assert link.is_public is False
        assert link.get_allowed_emails() == allowed


class TestLinkServiceAccess:
    """Test LinkService access control methods."""

    async def test_get_link_by_slug(self, db_session: AsyncSession, test_link: Link) -> None:
        """Test retrieving link by slug."""
        service = LinkService(db_session)

        link = await service.get_link_by_slug(test_link.slug)

        assert link is not None
        assert link.id == test_link.id

    async def test_get_link_by_id_owner(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ) -> None:
        """Test link owner can get link."""
        service = LinkService(db_session)

        link = await service.get_link(test_link.id, user_id=test_user.id)

        assert link.id == test_link.id

    async def test_get_link_non_owner_forbidden(
        self, db_session: AsyncSession, test_user: User, test_admin_user: User, test_link: Link
    ) -> None:
        """Test non-owner cannot get link with permission check."""
        service = LinkService(db_session)

        with pytest.raises(ForbiddenError):
            await service.get_link(test_link.id, user_id=test_admin_user.id)

    async def test_check_public_link_access(
        self, db_session: AsyncSession, test_link: Link
    ) -> None:
        """Test public link is accessible to anyone."""
        service = LinkService(db_session)

        assert test_link.is_public is True
        assert await service.check_link_access(test_link, user_email=None) is True
        assert await service.check_link_access(test_link, user_email="anyone@example.com") is True

    async def test_check_private_link_no_email(
        self, db_session: AsyncSession, test_private_link: Link
    ) -> None:
        """Test private link inaccessible without email."""
        service = LinkService(db_session)

        assert test_private_link.is_public is False
        assert await service.check_link_access(test_private_link, user_email=None) is False

    async def test_check_private_link_allowed_email(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test private link accessible with allowed email."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="privateallowed123",
            is_public=False,
            allowed_emails=["allowed@example.com"],
        )

        assert await service.check_link_access(link, user_email="allowed@example.com") is True
        assert await service.check_link_access(link, user_email="denied@example.com") is False


class TestLinkServiceUpdate:
    """Test LinkService.update_link method."""

    async def test_update_link_url(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ) -> None:
        """Test updating link URL."""
        service = LinkService(db_session)

        updated = await service.update_link(
            link_id=test_link.id,
            user_id=test_user.id,
            original_url="https://newurl.com",
        )

        assert updated.original_url == "https://newurl.com"

    async def test_update_link_privacy(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ) -> None:
        """Test updating link privacy."""
        service = LinkService(db_session)

        updated = await service.update_link(
            link_id=test_link.id,
            user_id=test_user.id,
            is_public=False,
        )

        assert updated.is_public is False


class TestLinkServiceDelete:
    """Test LinkService.delete_link method."""

    async def test_delete_link_owner(self, db_session: AsyncSession, test_user: User) -> None:
        """Test link owner can delete link."""
        service = LinkService(db_session)

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/delete",
            slug="deleteme123",
            is_public=True,
        )
        link_id = link.id

        await service.delete_link(link_id, user_id=test_user.id)

        with pytest.raises(NotFoundError):
            await service.get_link(link_id)

    async def test_delete_link_non_owner_forbidden(
        self, db_session: AsyncSession, test_user: User, test_admin_user: User, test_link: Link
    ) -> None:
        """Test non-owner cannot delete link."""
        service = LinkService(db_session)

        with pytest.raises(ForbiddenError):
            await service.delete_link(test_link.id, user_id=test_admin_user.id)


class TestLinkServiceStats:
    """Test LinkService statistics methods."""

    async def test_increment_hit_count(self, db_session: AsyncSession, test_link: Link) -> None:
        """Test incrementing link hit count."""
        service = LinkService(db_session)

        original_count = test_link.hit_count
        updated = await service.increment_hit_count(test_link.slug)

        assert updated.hit_count == original_count + 1
        assert updated.last_hit_at is not None
