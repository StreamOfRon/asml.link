"""Statistics service for dashboard functionality."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.link import Link
from app.config import settings


class StatsService:
    """Service for calculating dashboard statistics."""

    def __init__(self, session: AsyncSession):
        """Initialize stats service with database session.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_total_users(self) -> int:
        """Get total number of users.

        Returns:
            Total user count
        """
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar() or 0

    async def get_total_links(self) -> int:
        """Get total number of links.

        Returns:
            Total link count
        """
        result = await self.session.execute(select(func.count(Link.id)))
        return result.scalar() or 0

    async def get_total_hits(self) -> int:
        """Get total hits across all links.

        Returns:
            Sum of all link hit counts
        """
        result = await self.session.execute(select(func.sum(Link.hit_count)))
        return result.scalar() or 0

    async def get_active_users(self) -> int:
        """Get number of users with at least one link.

        Returns:
            Count of users with links
        """
        result = await self.session.execute(select(func.count(func.distinct(Link.user_id))))
        return result.scalar() or 0

    async def get_public_links_count(self) -> int:
        """Get count of public links.

        Returns:
            Count of public links
        """
        result = await self.session.execute(
            select(func.count(Link.id)).where(Link.is_public == True)
        )
        return result.scalar() or 0

    async def get_private_links_count(self) -> int:
        """Get count of private links.

        Returns:
            Count of private links
        """
        result = await self.session.execute(
            select(func.count(Link.id)).where(Link.is_public == False)
        )
        return result.scalar() or 0

    async def get_user_total_hits(self, user_id: int) -> int:
        """Get total hits for a user's links.

        Args:
            user_id: User ID

        Returns:
            Sum of hit counts for user's links
        """
        result = await self.session.execute(
            select(func.sum(Link.hit_count)).where(Link.user_id == user_id)
        )
        return result.scalar() or 0

    async def get_total_admins(self) -> int:
        """Get total number of admin users.

        Returns:
            Admin user count
        """
        result = await self.session.execute(
            select(func.count(User.id)).where(User.is_admin == True)
        )
        return result.scalar() or 0

    async def get_total_blocked_users(self) -> int:
        """Get total number of blocked users.

        Returns:
            Blocked user count
        """
        result = await self.session.execute(
            select(func.count(User.id)).where(User.is_blocked == True)
        )
        return result.scalar() or 0

    async def get_user_link_count(self, user_id: int) -> int:
        """Get count of links for a specific user.

        Args:
            user_id: User ID

        Returns:
            Count of user's links
        """
        result = await self.session.execute(
            select(func.count(Link.id)).where(Link.user_id == user_id)
        )
        return result.scalar() or 0
