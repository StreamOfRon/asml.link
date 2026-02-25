"""Unit tests for link service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.link import Link
from app.models.user import User
from app.utils.slug_generator import generate_random_slug
from app.utils.validators import is_valid_url


class TestLinkModel:
    """Test suite for Link model functionality."""

    @pytest.mark.asyncio
    async def test_link_creation(self, db_session: AsyncSession, test_user: User):
        """Test creating a new link."""
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com",
            slug="test123",
            is_public=True,
        )
        db_session.add(link)
        await db_session.commit()
        await db_session.refresh(link)

        assert link.id is not None
        assert link.original_url == "https://example.com"
        assert link.slug == "test123"
        assert link.is_public is True
        assert link.hit_count == 0

    @pytest.mark.asyncio
    async def test_link_relationships(self, test_link: Link, test_user: User):
        """Test link relationships."""
        assert test_link.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_link_statistics_increment(self, db_session: AsyncSession, test_link: Link):
        """Test incrementing link hit count."""
        original_count = test_link.hit_count
        test_link.hit_count += 1
        db_session.add(test_link)
        await db_session.commit()
        await db_session.refresh(test_link)

        assert test_link.hit_count == original_count + 1

    @pytest.mark.asyncio
    async def test_get_allowed_emails_empty(self, test_link: Link):
        """Test getting allowed emails when none set."""
        emails = test_link.get_allowed_emails()
        assert emails == []

    @pytest.mark.asyncio
    async def test_set_and_get_allowed_emails(self, db_session: AsyncSession, test_link: Link):
        """Test setting and getting allowed emails."""
        test_emails = ["user1@example.com", "user2@example.com"]
        test_link.set_allowed_emails(test_emails)
        db_session.add(test_link)
        await db_session.commit()
        await db_session.refresh(test_link)

        retrieved_emails = test_link.get_allowed_emails()
        assert set(retrieved_emails) == set(test_emails)

    @pytest.mark.asyncio
    async def test_set_empty_allowed_emails(self, db_session: AsyncSession, test_link: Link):
        """Test setting empty allowed emails list."""
        test_link.set_allowed_emails([])
        db_session.add(test_link)
        await db_session.commit()
        await db_session.refresh(test_link)

        assert test_link.allowed_emails is None

    @pytest.mark.asyncio
    async def test_link_repr(self, test_link: Link):
        """Test link string representation."""
        repr_str = repr(test_link)
        assert "Link" in repr_str
        assert test_link.slug in repr_str


class TestLinkOperations:
    """Test suite for common link operations."""

    @pytest.mark.asyncio
    async def test_create_public_link(self, db_session: AsyncSession, test_user: User):
        """Test creating a public link."""
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com/public",
            slug="public123",
            is_public=True,
        )
        db_session.add(link)
        await db_session.commit()
        await db_session.refresh(link)

        assert link.is_public is True

    @pytest.mark.asyncio
    async def test_create_private_link(self, db_session: AsyncSession, test_user: User):
        """Test creating a private link."""
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="private456",
            is_public=False,
        )
        db_session.add(link)
        await db_session.commit()
        await db_session.refresh(link)

        assert link.is_public is False

    @pytest.mark.asyncio
    async def test_create_link_with_allowed_emails(self, db_session: AsyncSession, test_user: User):
        """Test creating a private link with allowed emails."""
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com/restricted",
            slug="restricted789",
            is_public=False,
        )
        link.set_allowed_emails(["user1@example.com", "user2@example.com"])
        db_session.add(link)
        await db_session.commit()
        await db_session.refresh(link)

        assert link.is_public is False
        allowed = link.get_allowed_emails()
        assert len(allowed) == 2

    @pytest.mark.asyncio
    async def test_slug_uniqueness(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ):
        """Test that slug must be unique."""
        # Try to create link with same slug
        duplicate_link = Link(
            user_id=test_user.id,
            original_url="https://different.com",
            slug=test_link.slug,  # Same slug
            is_public=True,
        )
        db_session.add(duplicate_link)

        # This should raise an error due to unique constraint
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_retrieve_link_by_slug(self, db_session: AsyncSession, test_link: Link):
        """Test retrieving a link by slug."""
        stmt = select(Link).where(Link.slug == test_link.slug)
        result = await db_session.execute(stmt)
        retrieved_link = result.scalar_one_or_none()

        assert retrieved_link is not None
        assert retrieved_link.slug == test_link.slug
        assert retrieved_link.original_url == test_link.original_url

    @pytest.mark.asyncio
    async def test_delete_link(self, db_session: AsyncSession, test_link: Link):
        """Test deleting a link."""
        link_id = test_link.id
        await db_session.delete(test_link)
        await db_session.commit()

        stmt = select(Link).where(Link.id == link_id)
        result = await db_session.execute(stmt)
        deleted_link = result.scalar_one_or_none()

        assert deleted_link is None

    @pytest.mark.asyncio
    async def test_user_links_cascade_delete(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ):
        """Test that deleting user cascades to delete their links."""
        user_id = test_user.id
        link_id = test_link.id

        await db_session.delete(test_user)
        await db_session.commit()

        # Check user is deleted
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is None

        # Check link is deleted (cascade)
        stmt = select(Link).where(Link.id == link_id)
        result = await db_session.execute(stmt)
        deleted_link = result.scalar_one_or_none()
        assert deleted_link is None
