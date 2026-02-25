"""Rate limiting service for API endpoints."""

from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rate_limit_entry import RateLimitEntry


class RateLimiter:
    """Service for rate limiting API endpoints."""

    # Rate limit configurations (requests per time window)
    LIMITS = {
        "oauth_login": {"requests": 5, "window_minutes": 15},  # 5 attempts per 15 minutes
        "link_create": {"requests": 50, "window_minutes": 60},  # 50 links per hour per user
        "link_redirect": {"requests": 1000, "window_minutes": 60},  # 1000 hits per hour per link
    }

    def __init__(self, session: AsyncSession):
        """Initialize rate limiter with database session.

        Args:
            session: Async database session
        """
        self.session = session

    async def is_rate_limited(
        self,
        endpoint: str,
        ip_address: str,
        user_id: Optional[int] = None,
    ) -> bool:
        """Check if a request should be rate limited.

        Args:
            endpoint: API endpoint identifier
            ip_address: Client IP address
            user_id: Optional user ID for per-user limiting

        Returns:
            True if rate limited, False otherwise
        """
        if endpoint not in self.LIMITS:
            return False

        limit_config = self.LIMITS[endpoint]
        window_minutes = limit_config["window_minutes"]
        max_requests = limit_config["requests"]

        # Get limit entry for this request
        limit_entry = await self._get_limit_entry(endpoint, ip_address, user_id)

        if limit_entry is None:
            # No entry yet, create one
            await self._create_limit_entry(endpoint, ip_address, user_id)
            return False

        # Check if window has expired
        # Convert naive datetime from DB to UTC-aware for comparison
        first_hit_at = (
            limit_entry.first_hit_at.replace(tzinfo=UTC)
            if limit_entry.first_hit_at.tzinfo is None
            else limit_entry.first_hit_at
        )
        time_since_first = datetime.now(UTC) - first_hit_at
        if time_since_first > timedelta(minutes=window_minutes):
            # Window expired, reset counter
            await self._reset_limit_entry(limit_entry)
            return False

        # Check if limit exceeded
        if limit_entry.hit_count >= max_requests:
            return True

        # Increment counter
        await self._increment_hit_count(limit_entry)
        return False

    async def get_remaining_requests(
        self,
        endpoint: str,
        ip_address: str,
        user_id: Optional[int] = None,
    ) -> dict:
        """Get remaining requests for an endpoint.

        Args:
            endpoint: API endpoint identifier
            ip_address: Client IP address
            user_id: Optional user ID for per-user limiting

        Returns:
            Dictionary with remaining requests and reset time
        """
        if endpoint not in self.LIMITS:
            return {"remaining": -1, "reset_in_seconds": 0}

        limit_config = self.LIMITS[endpoint]
        window_minutes = limit_config["window_minutes"]
        max_requests = limit_config["requests"]

        limit_entry = await self._get_limit_entry(endpoint, ip_address, user_id)

        if limit_entry is None:
            return {
                "remaining": max_requests,
                "reset_in_seconds": window_minutes * 60,
            }

        # Convert naive datetime from DB to UTC-aware for comparison
        first_hit_at = (
            limit_entry.first_hit_at.replace(tzinfo=UTC)
            if limit_entry.first_hit_at.tzinfo is None
            else limit_entry.first_hit_at
        )
        time_since_first = datetime.now(UTC) - first_hit_at
        time_remaining = timedelta(minutes=window_minutes) - time_since_first

        if time_remaining.total_seconds() <= 0:
            return {
                "remaining": max_requests,
                "reset_in_seconds": 0,
            }

        remaining = max(0, max_requests - limit_entry.hit_count)
        return {
            "remaining": remaining,
            "reset_in_seconds": int(time_remaining.total_seconds()),
        }

    async def clear_old_entries(self, days: int = 7) -> int:
        """Clear rate limit entries older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of entries deleted
        """
        # Use naive datetime for DB comparison since DB stores naive datetimes
        cutoff_time = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
        stmt = delete(RateLimitEntry).where(RateLimitEntry.last_hit_at < cutoff_time)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    # Private helper methods

    async def _get_limit_entry(
        self,
        endpoint: str,
        ip_address: str,
        user_id: Optional[int] = None,
    ) -> Optional[RateLimitEntry]:
        """Get rate limit entry for a request."""
        stmt = select(RateLimitEntry).where(
            RateLimitEntry.endpoint == endpoint,
            RateLimitEntry.ip_address == ip_address,
        )

        if user_id is not None:
            stmt = stmt.where(RateLimitEntry.user_id == user_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_limit_entry(
        self,
        endpoint: str,
        ip_address: str,
        user_id: Optional[int] = None,
    ) -> RateLimitEntry:
        """Create a new rate limit entry."""
        entry = RateLimitEntry(
            endpoint=endpoint,
            ip_address=ip_address,
            user_id=user_id,
            hit_count=1,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def _increment_hit_count(self, entry: RateLimitEntry) -> None:
        """Increment hit count for an entry."""
        entry.hit_count += 1
        entry.last_hit_at = datetime.now(UTC)
        self.session.add(entry)
        await self.session.commit()

    async def _reset_limit_entry(self, entry: RateLimitEntry) -> None:
        """Reset hit count for an entry."""
        entry.hit_count = 1
        entry.first_hit_at = datetime.now(UTC)
        entry.last_hit_at = datetime.now(UTC)
        self.session.add(entry)
        await self.session.commit()
