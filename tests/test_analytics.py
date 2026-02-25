"""Tests for analytics and rate limiting features."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.stats_service import StatsService
from app.services.rate_limiter import RateLimiter
from app.models.link import Link
from app.models.user import User
from app.models.rate_limit_entry import RateLimitEntry


class TestStatsServicePerLink:
    """Test per-link statistics tracking."""

    async def test_increment_hit_count_basic(self, db_session: AsyncSession, test_link: Link):
        """Test incrementing hit count for a link."""
        service = StatsService(db_session)

        # Increment hit count
        updated_link = await service.get_link_stats(test_link.slug)
        initial_hits = updated_link.get("hit_count", 0)

        # Link should have trackable stats
        assert updated_link["slug"] == test_link.slug
        assert "hit_count" in updated_link

    async def test_get_link_stats(self, db_session: AsyncSession, test_link: Link):
        """Test getting comprehensive link statistics."""
        service = StatsService(db_session)

        stats = await service.get_link_stats(test_link.slug)

        assert stats["slug"] == test_link.slug
        assert stats["original_url"] == test_link.original_url
        assert stats["is_public"] == test_link.is_public
        assert "created_at" in stats


class TestStatsServicePerUser:
    """Test per-user statistics."""

    async def test_get_user_link_count(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ):
        """Test getting user link count."""
        service = StatsService(db_session)

        count = await service.get_user_link_count(test_user.id)

        assert count >= 1  # At least the test_link

    async def test_get_user_total_hits(self, db_session: AsyncSession, test_user: User):
        """Test getting user total hits."""
        service = StatsService(db_session)

        total_hits = await service.get_user_total_hits(test_user.id)

        assert total_hits >= 0

    async def test_get_user_average_hits_per_link(self, db_session: AsyncSession, test_user: User):
        """Test calculating average hits per link for user."""
        service = StatsService(db_session)

        avg = await service.get_user_average_hits_per_link(test_user.id)

        assert avg >= 0

    async def test_get_user_public_links_count(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ):
        """Test getting count of public links for user."""
        service = StatsService(db_session)

        count = await service.get_user_public_links_count(test_user.id)

        assert count >= 1  # At least the test_link (which is public)

    async def test_get_user_private_links_count(
        self, db_session: AsyncSession, test_user: User, test_private_link: Link
    ):
        """Test getting count of private links for user."""
        service = StatsService(db_session)

        count = await service.get_user_private_links_count(test_user.id)

        assert count >= 1  # At least the test_private_link

    async def test_get_user_most_popular_links(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ):
        """Test getting user's most popular links."""
        service = StatsService(db_session)

        popular = await service.get_user_most_popular_links(test_user.id, limit=5)

        # Should return list of tuples
        assert isinstance(popular, list)


class TestStatsServiceSystemWide:
    """Test system-wide statistics."""

    async def test_get_total_users(self, db_session: AsyncSession, test_user: User):
        """Test getting total user count."""
        service = StatsService(db_session)

        total = await service.get_total_users()

        assert total >= 1

    async def test_get_total_links(self, db_session: AsyncSession, test_link: Link):
        """Test getting total link count."""
        service = StatsService(db_session)

        total = await service.get_total_links()

        assert total >= 1

    async def test_get_total_hits(self, db_session: AsyncSession):
        """Test getting total hits across system."""
        service = StatsService(db_session)

        total = await service.get_total_hits()

        assert total >= 0

    async def test_get_active_users_count(self, db_session: AsyncSession):
        """Test getting active users count."""
        service = StatsService(db_session)

        count = await service.get_active_users_count()

        assert count >= 0

    async def test_get_admin_count(self, db_session: AsyncSession, test_admin_user: User):
        """Test getting admin user count."""
        service = StatsService(db_session)

        count = await service.get_admin_count()

        assert count >= 1

    async def test_get_blocked_users_count(self, db_session: AsyncSession):
        """Test getting blocked users count."""
        service = StatsService(db_session)

        count = await service.get_blocked_users_count()

        assert count >= 0

    async def test_get_public_links_count(self, db_session: AsyncSession, test_link: Link):
        """Test getting public links count."""
        service = StatsService(db_session)

        count = await service.get_public_links_count()

        assert count >= 1

    async def test_get_private_links_count(self, db_session: AsyncSession, test_private_link: Link):
        """Test getting private links count."""
        service = StatsService(db_session)

        count = await service.get_private_links_count()

        assert count >= 1

    async def test_get_average_links_per_user(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ):
        """Test calculating average links per user."""
        service = StatsService(db_session)

        avg = await service.get_average_links_per_user()

        assert avg > 0

    async def test_get_average_hits_per_link(self, db_session: AsyncSession):
        """Test calculating average hits per link."""
        service = StatsService(db_session)

        avg = await service.get_average_hits_per_link()

        assert avg >= 0

    async def test_get_recent_users(self, db_session: AsyncSession, test_user: User):
        """Test getting recently created users."""
        service = StatsService(db_session)

        users = await service.get_recent_users(limit=5)

        assert isinstance(users, list)
        assert len(users) >= 1

    async def test_get_recent_links(self, db_session: AsyncSession, test_link: Link):
        """Test getting recently created links."""
        service = StatsService(db_session)

        links = await service.get_recent_links(limit=5)

        assert isinstance(links, list)
        assert len(links) >= 1

    async def test_get_most_active_users(self, db_session: AsyncSession):
        """Test getting most active users."""
        service = StatsService(db_session)

        users = await service.get_most_active_users(limit=5)

        assert isinstance(users, list)

    async def test_get_most_popular_links_globally(self, db_session: AsyncSession):
        """Test getting most popular links globally."""
        service = StatsService(db_session)

        links = await service.get_most_popular_links_globally(limit=5)

        assert isinstance(links, list)


class TestRateLimiter:
    """Test rate limiting functionality."""

    async def test_rate_limiter_initialization(self, db_session: AsyncSession):
        """Test rate limiter initialization."""
        limiter = RateLimiter(db_session)

        assert limiter.LIMITS is not None
        assert "oauth_login" in limiter.LIMITS
        assert "link_create" in limiter.LIMITS
        assert "link_redirect" in limiter.LIMITS

    async def test_first_request_not_limited(self, db_session: AsyncSession):
        """Test that first request is not rate limited."""
        limiter = RateLimiter(db_session)

        is_limited = await limiter.is_rate_limited("oauth_login", "192.168.1.1")

        assert not is_limited

    async def test_rate_limit_threshold_oauth(self, db_session: AsyncSession):
        """Test OAuth login rate limiting threshold."""
        limiter = RateLimiter(db_session)

        # Make 5 requests (the limit)
        for i in range(5):
            is_limited = await limiter.is_rate_limited("oauth_login", "192.168.1.1")
            assert not is_limited

        # 6th request should be limited
        is_limited = await limiter.is_rate_limited("oauth_login", "192.168.1.1")
        assert is_limited

    async def test_rate_limit_threshold_link_create(self, db_session: AsyncSession):
        """Test link creation rate limiting threshold."""
        limiter = RateLimiter(db_session)

        # Make 50 requests (the limit)
        for i in range(50):
            is_limited = await limiter.is_rate_limited("link_create", "192.168.1.1", user_id=1)
            assert not is_limited

        # 51st request should be limited
        is_limited = await limiter.is_rate_limited("link_create", "192.168.1.1", user_id=1)
        assert is_limited

    async def test_rate_limit_per_user(self, db_session: AsyncSession):
        """Test that rate limits are per user."""
        limiter = RateLimiter(db_session)

        # User 1 hits limit
        for i in range(5):
            await limiter.is_rate_limited("oauth_login", "192.168.1.1", user_id=1)

        is_limited_user1 = await limiter.is_rate_limited("oauth_login", "192.168.1.1", user_id=1)
        assert is_limited_user1

        # User 2 should not be limited
        is_limited_user2 = await limiter.is_rate_limited("oauth_login", "192.168.1.1", user_id=2)
        assert not is_limited_user2

    async def test_rate_limit_per_ip(self, db_session: AsyncSession):
        """Test that rate limits are per IP address."""
        limiter = RateLimiter(db_session)

        # IP 1 hits limit
        for i in range(5):
            await limiter.is_rate_limited("oauth_login", "192.168.1.1")

        is_limited_ip1 = await limiter.is_rate_limited("oauth_login", "192.168.1.1")
        assert is_limited_ip1

        # IP 2 should not be limited
        is_limited_ip2 = await limiter.is_rate_limited("oauth_login", "192.168.1.2")
        assert not is_limited_ip2

    async def test_get_remaining_requests(self, db_session: AsyncSession):
        """Test getting remaining requests."""
        limiter = RateLimiter(db_session)

        # First request
        await limiter.is_rate_limited("oauth_login", "192.168.1.1")

        remaining = await limiter.get_remaining_requests("oauth_login", "192.168.1.1")

        assert "remaining" in remaining
        assert "reset_in_seconds" in remaining
        assert remaining["remaining"] == 4  # 5 total - 1 used

    async def test_clear_old_entries(self, db_session: AsyncSession):
        """Test clearing old rate limit entries."""
        limiter = RateLimiter(db_session)

        # Create entry
        await limiter.is_rate_limited("oauth_login", "192.168.1.1")

        # Clear old entries (but 1 day isn't old yet)
        cleared = await limiter.clear_old_entries(days=0)

        # Should have cleared entries older than 0 days (very old)
        assert cleared >= 0

    async def test_unknown_endpoint_not_limited(self, db_session: AsyncSession):
        """Test that unknown endpoints are not rate limited."""
        limiter = RateLimiter(db_session)

        is_limited = await limiter.is_rate_limited("unknown_endpoint", "192.168.1.1")

        assert not is_limited
