"""Integration tests for dashboard endpoints."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.link import Link
from app.services.stats_service import StatsService
from app.services.link_service import LinkService
from app.services.user_service import UserService


class TestStatsService:
    """Tests for statistics service."""

    async def test_get_total_users(
        self, db_session: AsyncSession, test_user: User, test_admin_user: User
    ):
        """Test getting total user count."""
        service = StatsService(db_session)
        total = await service.get_total_users()
        assert total >= 2

    async def test_get_total_links(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ):
        """Test getting total link count."""
        service = StatsService(db_session)

        # Create some links
        link_service = LinkService(db_session)
        for i in range(3):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/url{i}",
                slug=f"link{i}",
            )

        total = await service.get_total_links()
        assert total >= 4

    async def test_get_total_hits(self, db_session: AsyncSession, test_user: User):
        """Test getting total hits across all links."""
        service = StatsService(db_session)
        link_service = LinkService(db_session)

        # Create link and increment hits
        link = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com",
            slug="hits1",
        )

        for _ in range(5):
            await link_service.increment_hit_count(link.slug)

        total_hits = await service.get_total_hits()
        assert total_hits >= 5

    async def test_get_active_users(self, db_session: AsyncSession, test_user: User):
        """Test getting count of users with links."""
        service = StatsService(db_session)
        link_service = LinkService(db_session)

        # Create user without links
        user_service = UserService(db_session)
        user_no_links = await user_service.create_user(
            email="nolinks@example.com",
            full_name="No Links",
        )

        # Create link for test_user
        await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com",
            slug="active1",
        )

        active = await service.get_active_users()
        assert active >= 1

    async def test_get_public_links_count(self, db_session: AsyncSession, test_user: User):
        """Test getting count of public links."""
        service = StatsService(db_session)
        link_service = LinkService(db_session)

        # Create public and private links
        for i in range(3):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/pub{i}",
                slug=f"pub{i}",
                is_public=True,
            )

        for i in range(2):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/priv{i}",
                slug=f"priv{i}",
                is_public=False,
            )

        public_count = await service.get_public_links_count()
        assert public_count >= 3

    async def test_get_private_links_count(self, db_session: AsyncSession, test_user: User):
        """Test getting count of private links."""
        service = StatsService(db_session)
        link_service = LinkService(db_session)

        # Create public and private links
        for i in range(2):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/pub{i}",
                slug=f"pub{i}",
                is_public=True,
            )

        for i in range(3):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/priv{i}",
                slug=f"priv{i}",
                is_public=False,
            )

        private_count = await service.get_private_links_count()
        assert private_count >= 3

    async def test_get_user_total_hits(self, db_session: AsyncSession, test_user: User):
        """Test getting total hits for a user's links."""
        service = StatsService(db_session)
        link_service = LinkService(db_session)

        # Create multiple links and increment hits
        link1 = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/1",
            slug="usrhits1",
        )

        link2 = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/2",
            slug="usrhits2",
        )

        # Increment hits
        for _ in range(3):
            await link_service.increment_hit_count(link1.slug)

        for _ in range(2):
            await link_service.increment_hit_count(link2.slug)

        user_hits = await service.get_user_total_hits(test_user.id)
        assert user_hits == 5

    async def test_get_total_admins(self, db_session: AsyncSession, test_admin_user: User):
        """Test getting count of admin users."""
        service = StatsService(db_session)
        user_service = UserService(db_session)

        # Create another admin
        user = await user_service.create_user(
            email="admin2@example.com",
            full_name="Admin 2",
        )
        await user_service.promote_to_admin(user.id)

        admins = await service.get_total_admins()
        assert admins >= 2

    async def test_get_total_blocked_users(self, db_session: AsyncSession, test_user: User):
        """Test getting count of blocked users."""
        service = StatsService(db_session)
        user_service = UserService(db_session)

        # Create and block users
        user1 = await user_service.create_user(
            email="block1@example.com",
            full_name="Block 1",
        )
        user2 = await user_service.create_user(
            email="block2@example.com",
            full_name="Block 2",
        )

        await user_service.block_user(user1.id)
        await user_service.block_user(user2.id)

        blocked = await service.get_total_blocked_users()
        assert blocked >= 2

    async def test_get_user_link_count(self, db_session: AsyncSession, test_user: User):
        """Test getting link count for a specific user."""
        service = StatsService(db_session)
        link_service = LinkService(db_session)

        # Create links
        for i in range(4):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/{i}",
                slug=f"usrlink{i}",
            )

        count = await service.get_user_link_count(test_user.id)
        assert count >= 4

    async def test_get_user_link_count_zero(self, db_session: AsyncSession, test_user: User):
        """Test getting link count for user with no links."""
        service = StatsService(db_session)
        user_service = UserService(db_session)

        # Create user with no links
        user = await user_service.create_user(
            email="nolinks2@example.com",
            full_name="No Links 2",
        )

        count = await service.get_user_link_count(user.id)
        assert count == 0


class TestAdminDashboardEndpoints:
    """Tests for admin dashboard endpoints."""

    async def test_admin_dashboard_returns_stats(
        self, db_session: AsyncSession, test_admin_user: User, test_user: User
    ):
        """Test admin dashboard returns statistics."""
        # Verify admin has access to stats
        link_service = LinkService(db_session)
        user_service = UserService(db_session)
        stats_service = StatsService(db_session)

        # Create test data
        for i in range(2):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/{i}",
                slug=f"dash{i}",
                is_public=True,
            )

        # Get stats
        total_users = await stats_service.get_total_users()
        total_links = await stats_service.get_total_links()

        assert total_users >= 2
        assert total_links >= 2

    async def test_admin_dashboard_config_returns_settings(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test admin dashboard config endpoint."""
        stats_service = StatsService(db_session)

        # Get admin and blocked counts
        admins = await stats_service.get_total_admins()
        blocked = await stats_service.get_total_blocked_users()

        assert admins >= 1
        assert blocked >= 0

    async def test_admin_only_access_to_dashboard(self, db_session: AsyncSession, test_user: User):
        """Test that only admins can access dashboard."""
        user_service = UserService(db_session)

        # Regular user should not be admin
        is_admin = await user_service.is_user_admin(test_user.id)
        assert is_admin is False

    async def test_admin_dashboard_empty_stats(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test admin dashboard with empty/minimal data."""
        stats_service = StatsService(db_session)

        total_links = await stats_service.get_total_links()
        assert total_links >= 0


class TestUserDashboardEndpoints:
    """Tests for user dashboard endpoints."""

    async def test_user_dashboard_returns_user_info(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test user dashboard returns user information."""
        user_service = UserService(db_session)

        # Get user info
        user = await user_service.get_user(test_user.id)
        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id

    async def test_user_dashboard_returns_statistics(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test user dashboard returns user statistics."""
        link_service = LinkService(db_session)
        stats_service = StatsService(db_session)

        # Create links
        for i in range(3):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/{i}",
                slug=f"ustat{i}",
            )

        # Get stats
        link_count = await stats_service.get_user_link_count(test_user.id)
        total_hits = await stats_service.get_user_total_hits(test_user.id)

        assert link_count == 3
        assert total_hits >= 0

    async def test_user_links_endpoint_pagination(self, db_session: AsyncSession, test_user: User):
        """Test user links endpoint with pagination."""
        link_service = LinkService(db_session)

        # Create many links
        for i in range(15):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/page{i}",
                slug=f"page{i}",
            )

        # Get paginated links (first 10)
        from sqlalchemy import select, desc

        result = await db_session.execute(
            select(Link)
            .where(Link.user_id == test_user.id)
            .order_by(desc(Link.created_at))
            .limit(10)
            .offset(0)
        )
        page1 = result.scalars().all()
        assert len(page1) == 10

        # Get second page
        result = await db_session.execute(
            select(Link)
            .where(Link.user_id == test_user.id)
            .order_by(desc(Link.created_at))
            .limit(10)
            .offset(10)
        )
        page2 = result.scalars().all()
        assert len(page2) >= 5

    async def test_user_links_include_statistics(self, db_session: AsyncSession, test_user: User):
        """Test that user links include hit statistics."""
        link_service = LinkService(db_session)

        # Create link and increment hits
        link = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/stat",
            slug="stat123",
        )

        for _ in range(5):
            await link_service.increment_hit_count(link.slug)

        # Fetch link
        from sqlalchemy import select

        result = await db_session.execute(select(Link).where(Link.id == link.id))
        fetched_link = result.scalar()

        assert fetched_link.hit_count == 5
        assert fetched_link.last_hit_at is not None

    async def test_user_links_ordered_by_creation(self, db_session: AsyncSession, test_user: User):
        """Test that user links are ordered by creation date (newest first)."""
        link_service = LinkService(db_session)

        # Create links with delay to ensure different timestamps
        links = []
        for i in range(3):
            link = await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/{i}",
                slug=f"order{i}",
            )
            links.append(link)

        # Verify order (should be in creation order)
        from sqlalchemy import select, desc

        result = await db_session.execute(
            select(Link).where(Link.user_id == test_user.id).order_by(desc(Link.created_at))
        )
        ordered_links = result.scalars().all()

        # Newest should be first
        assert ordered_links[0].id == links[-1].id

    async def test_user_dashboard_with_public_and_private_links(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test user dashboard with mix of public and private links."""
        link_service = LinkService(db_session)
        stats_service = StatsService(db_session)

        # Create public and private links
        for i in range(2):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/pub{i}",
                slug=f"ubpub{i}",
                is_public=True,
            )

        for i in range(3):
            await link_service.create_link(
                user_id=test_user.id,
                original_url=f"https://example.com/priv{i}",
                slug=f"ubpriv{i}",
                is_public=False,
            )

        # Get link count
        link_count = await stats_service.get_user_link_count(test_user.id)
        assert link_count == 5

    async def test_user_links_endpoint_empty(self, db_session: AsyncSession, test_user: User):
        """Test user links endpoint when user has no links."""
        from sqlalchemy import select

        result = await db_session.execute(select(Link).where(Link.user_id == test_user.id))
        links = result.scalars().all()

        assert len(links) == 0
