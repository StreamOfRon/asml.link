"""Statistics service for dashboard functionality."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.models.user import User


class StatsService:
    """Service for calculating dashboard statistics."""

    def __init__(self, session: AsyncSession):
        """Initialize stats service with database session.

        Args:
            session: Async database session
        """
        self.session = session

    # ====== System-wide Statistics ======

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

    async def get_active_users_count(self) -> int:
        """Get number of users with at least one link in last 7 days.

        Returns:
            Count of active users
        """
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        result = await self.session.execute(
            select(func.count(func.distinct(Link.user_id))).where(
                Link.last_hit_at >= seven_days_ago
            )
        )
        return result.scalar() or 0

    async def get_admin_count(self) -> int:
        """Get count of admin users.

        Returns:
            Admin user count
        """
        result = await self.session.execute(
            select(func.count(User.id)).where(User.is_admin.is_(True))
        )
        return result.scalar() or 0

    async def get_blocked_users_count(self) -> int:
        """Get count of blocked users.

        Returns:
            Blocked user count
        """
        result = await self.session.execute(
            select(func.count(User.id)).where(User.is_blocked.is_(True))
        )
        return result.scalar() or 0

    async def get_public_links_count(self) -> int:
        """Get count of public links.

        Returns:
            Count of public links
        """
        result = await self.session.execute(
            select(func.count(Link.id)).where(Link.is_public.is_(True))
        )
        return result.scalar() or 0

    async def get_private_links_count(self) -> int:
        """Get count of private links.

        Returns:
            Count of private links
        """
        result = await self.session.execute(
            select(func.count(Link.id)).where(Link.is_public.is_(False))
        )
        return result.scalar() or 0

    async def get_average_links_per_user(self) -> float:
        """Get average number of links per user.

        Returns:
            Average links per user
        """
        total_links = await self.get_total_links()
        total_users = await self.get_total_users()

        if total_users == 0:
            return 0.0
        return round(total_links / total_users, 2)

    async def get_average_hits_per_link(self) -> float:
        """Get average number of hits per link.

        Returns:
            Average hits per link
        """
        total_hits = await self.get_total_hits()
        total_links = await self.get_total_links()

        if total_links == 0:
            return 0.0
        return round(total_hits / total_links, 2)

    # ====== Per-User Statistics ======

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

    async def get_user_average_hits_per_link(self, user_id: int) -> float:
        """Get average hits per link for a user.

        Args:
            user_id: User ID

        Returns:
            Average hits per link for user
        """
        total_hits = await self.get_user_total_hits(user_id)
        link_count = await self.get_user_link_count(user_id)

        if link_count == 0:
            return 0.0
        return round(total_hits / link_count, 2)

    async def get_user_public_links_count(self, user_id: int) -> int:
        """Get count of public links for a user.

        Args:
            user_id: User ID

        Returns:
            Count of user's public links
        """
        result = await self.session.execute(
            select(func.count(Link.id)).where(Link.user_id == user_id, Link.is_public.is_(True))
        )
        return result.scalar() or 0

    async def get_user_private_links_count(self, user_id: int) -> int:
        """Get count of private links for a user.

        Args:
            user_id: User ID

        Returns:
            Count of user's private links
        """
        result = await self.session.execute(
            select(func.count(Link.id)).where(Link.user_id == user_id, Link.is_public.is_(False))
        )
        return result.scalar() or 0

    async def get_user_most_popular_links(self, user_id: int, limit: int = 5) -> list[tuple]:
        """Get a user's most popular links.

        Args:
            user_id: User ID
            limit: Number of links to return

        Returns:
            List of (slug, hit_count) tuples, ordered by hits descending
        """
        result = await self.session.execute(
            select(Link.slug, Link.hit_count)
            .where(Link.user_id == user_id)
            .order_by(Link.hit_count.desc())
            .limit(limit)
        )
        return result.all()

    # ====== Per-Link Statistics ======

    async def get_link_stats(self, slug: str) -> dict:
        """Get statistics for a specific link.

        Args:
            slug: Link slug

        Returns:
            Dictionary with link statistics
        """
        stmt = select(Link).where(Link.slug == slug)
        result = await self.session.execute(stmt)
        link = result.scalar_one_or_none()

        if link is None:
            return {}

        return {
            "slug": link.slug,
            "original_url": link.original_url,
            "hit_count": link.hit_count,
            "is_public": link.is_public,
            "created_at": link.created_at,
            "last_hit_at": link.last_hit_at,
            "owner_id": link.user_id,
        }

    # ====== Helper Methods for Admin Views ======

    async def get_recent_users(self, limit: int = 10) -> list[User]:
        """Get recently created users.

        Args:
            limit: Number of users to return

        Returns:
            List of recent User objects
        """
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def get_recent_links(self, limit: int = 10) -> list[Link]:
        """Get recently created links.

        Args:
            limit: Number of links to return

        Returns:
            List of recent Link objects
        """
        result = await self.session.execute(
            select(Link).order_by(Link.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def get_most_active_users(self, limit: int = 10) -> list[tuple]:
        """Get most active users (by total hits).

        Args:
            limit: Number of users to return

        Returns:
            List of (user_email, total_hits) tuples
        """
        result = await self.session.execute(
            select(User.email, func.sum(Link.hit_count).label("total_hits"))
            .join(Link, User.id == Link.user_id)
            .group_by(User.id)
            .order_by(func.sum(Link.hit_count).desc())
            .limit(limit)
        )
        return result.all()

    async def get_most_popular_links_globally(self, limit: int = 10) -> list[tuple]:
        """Get most popular links globally.

        Args:
            limit: Number of links to return

        Returns:
            List of (slug, hit_count, owner_email) tuples
        """
        result = await self.session.execute(
            select(Link.slug, Link.hit_count, User.email)
            .join(User, Link.user_id == User.id)
            .order_by(Link.hit_count.desc())
            .limit(limit)
        )
        return result.all()

    # Backwards compatibility aliases for Phase 9 tests
    async def get_active_users(self) -> int:
        """Get count of active users (users with at least one link).

        This counts users with at least one link in the system,
        not users with recent activity.
        """
        result = await self.session.execute(select(func.count(func.distinct(Link.user_id))))
        return result.scalar() or 0

    async def get_total_admins(self) -> int:
        """Get count of admin users.

        Backwards compatibility alias for get_admin_count().
        """
        return await self.get_admin_count()

    async def get_total_blocked_users(self) -> int:
        """Get count of blocked users.

        Backwards compatibility alias for get_blocked_users_count().
        """
        return await self.get_blocked_users_count()
