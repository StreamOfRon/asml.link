"""Link service for managing shortened links."""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models.link import Link
from app.models.user import User
from app.utils.slug_generator import generate_random_slug, validate_slug
from app.utils.validators import is_valid_url


class LinkService:
    """Service for managing links."""

    def __init__(self, db_session: AsyncSession):
        """Initialize link service with database session."""
        self.db = db_session

    async def create_link(
        self,
        user_id: int,
        original_url: str,
        slug: Optional[str] = None,
        is_public: bool = True,
        allowed_emails: Optional[list[str]] = None,
    ) -> Link:
        """
        Create a new shortened link.

        Args:
            user_id: ID of the user creating the link
            original_url: Original URL to shorten
            slug: Custom slug (optional, generates if not provided)
            is_public: Whether link is publicly accessible
            allowed_emails: List of allowed emails for private links

        Returns:
            Created Link object

        Raises:
            ValidationError: If validation fails
            ConflictError: If slug already exists
        """
        # Validate URL
        if not is_valid_url(original_url):
            raise ValidationError(f"Invalid URL: {original_url}")

        # Validate user exists
        user = await self._get_user(user_id)
        if user is None:
            raise ValidationError(f"User {user_id} not found")

        # Generate or validate slug
        if slug is None:
            slug = generate_random_slug()
        else:
            if not validate_slug(slug):
                raise ValidationError(f"Invalid slug format: {slug}")

        # Check slug uniqueness
        existing = await self._get_link_by_slug(slug)
        if existing is not None:
            raise ConflictError(f"Slug '{slug}' already exists")

        # Create link
        link = Link(
            user_id=user_id,
            original_url=original_url,
            slug=slug,
            is_public=is_public,
        )

        if allowed_emails and not is_public:
            link.set_allowed_emails(allowed_emails)

        self.db.add(link)
        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to create link: {str(e)}")

        await self.db.refresh(link)
        return link

    async def get_link_by_slug(self, slug: str) -> Optional[Link]:
        """
        Get link by slug without permission checks.

        Args:
            slug: The shortened slug

        Returns:
            Link object or None if not found
        """
        return await self._get_link_by_slug(slug)

    async def get_link(self, link_id: int, user_id: Optional[int] = None) -> Link:
        """
        Get link by ID with optional permission check.

        Args:
            link_id: Link ID
            user_id: Optional user ID for permission check

        Returns:
            Link object

        Raises:
            NotFoundError: If link not found
            ForbiddenError: If user doesn't own the link
        """
        link = await self._get_link(link_id)
        if link is None:
            raise NotFoundError(f"Link {link_id} not found")

        if user_id is not None and link.user_id != user_id:
            raise ForbiddenError("You don't own this link")

        return link

    async def update_link(
        self,
        link_id: int,
        user_id: int,
        original_url: Optional[str] = None,
        is_public: Optional[bool] = None,
        allowed_emails: Optional[list[str]] = None,
    ) -> Link:
        """
        Update a link.

        Args:
            link_id: Link ID
            user_id: ID of user making the update
            original_url: New original URL
            is_public: New public status
            allowed_emails: New allowed emails list

        Returns:
            Updated Link object

        Raises:
            NotFoundError: If link not found
            ForbiddenError: If user doesn't own the link
            ValidationError: If validation fails
        """
        link = await self.get_link(link_id, user_id)

        if original_url is not None:
            if not is_valid_url(original_url):
                raise ValidationError(f"Invalid URL: {original_url}")
            link.original_url = original_url

        if is_public is not None:
            link.is_public = is_public

        if allowed_emails is not None:
            if not is_public:
                link.set_allowed_emails(allowed_emails)
            else:
                raise ValidationError("Cannot set allowed emails for public links")

        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        return link

    async def delete_link(self, link_id: int, user_id: int) -> None:
        """
        Delete a link.

        Args:
            link_id: Link ID
            user_id: ID of user making the deletion

        Raises:
            NotFoundError: If link not found
            ForbiddenError: If user doesn't own the link
        """
        link = await self.get_link(link_id, user_id)
        await self.db.delete(link)
        await self.db.commit()

    async def increment_hit_count(self, slug: str) -> Link:
        """
        Increment hit count for a link.

        Args:
            slug: Link slug

        Returns:
            Updated Link object

        Raises:
            NotFoundError: If link not found
        """
        link = await self._get_link_by_slug(slug)
        if link is None:
            raise NotFoundError(f"Link with slug '{slug}' not found")

        link.hit_count += 1
        link.last_hit_at = datetime.now(UTC)
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        return link

    async def get_user_links(
        self,
        user_id: int,
        include_private: bool = False,
    ) -> list[Link]:
        """
        Get all links for a user.

        Args:
            user_id: User ID
            include_private: Whether to include private links

        Returns:
            List of Link objects
        """
        stmt = select(Link).where(Link.user_id == user_id)

        if not include_private:
            stmt = stmt.where(Link.is_public)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def check_link_access(
        self,
        link: Link,
        user_email: Optional[str] = None,
    ) -> bool:
        """
        Check if user can access a link.

        Args:
            link: Link object
            user_email: Optional email for private link checks

        Returns:
            True if user can access, False otherwise
        """
        if link.is_public:
            return True

        if user_email is None:
            return False

        allowed_emails = link.get_allowed_emails()
        return user_email.lower() in [e.lower() for e in allowed_emails]

    # Private helper methods

    async def _get_link(self, link_id: int) -> Optional[Link]:
        """Get link by ID."""
        stmt = select(Link).where(Link.id == link_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_link_by_slug(self, slug: str) -> Optional[Link]:
        """Get link by slug."""
        stmt = select(Link).where(Link.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
