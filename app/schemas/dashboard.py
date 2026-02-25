"""Pydantic schemas for dashboard endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LinkStatsResponse(BaseModel):
    """Statistics for a single link."""

    id: int
    slug: str
    original_url: str
    is_public: bool
    hit_count: int
    created_at: datetime
    last_hit_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLinkListResponse(BaseModel):
    """List of user's links with pagination."""

    links: list[LinkStatsResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserDashboardResponse(BaseModel):
    """User dashboard overview."""

    id: int
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    total_links: int
    total_hits: int
    created_at: datetime

    class Config:
        from_attributes = True


class AdminSystemStatsResponse(BaseModel):
    """System-wide statistics for admin dashboard."""

    total_users: int
    total_links: int
    total_hits: int
    active_users: int = Field(description="Users with at least one link")
    public_links: int
    private_links: int


class AdminRecentActivityResponse(BaseModel):
    """Recent activity item for admin dashboard."""

    type: str = Field(description="Activity type: link_created, user_joined, link_accessed")
    description: str
    timestamp: datetime
    user_email: Optional[str] = None


class AdminDashboardResponse(BaseModel):
    """Admin dashboard overview."""

    stats: AdminSystemStatsResponse
    recent_activity: list[AdminRecentActivityResponse] = Field(
        description="Last 10 activities", default_factory=list
    )
    system_config: dict = Field(description="Instance configuration")


class AdminConfigResponse(BaseModel):
    """Instance configuration display for admins."""

    instance_name: str
    allow_private_links_only: bool
    enable_allow_list_mode: bool
    total_admins: int
    total_blocked_users: int
    database_type: str = Field(description="sqlite or postgresql")
