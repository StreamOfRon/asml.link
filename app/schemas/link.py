"""Pydantic schemas for Link API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LinkCreateRequest(BaseModel):
    """Request body for creating a new link."""

    original_url: str = Field(
        ..., min_length=1, max_length=2048, description="Original URL to shorten"
    )
    slug: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Custom slug (optional)"
    )
    is_public: bool = Field(True, description="Whether the link is publicly accessible")
    allowed_emails: Optional[list[str]] = Field(
        None, description="Email addresses allowed to access private links"
    )


class LinkUpdateRequest(BaseModel):
    """Request body for updating a link."""

    original_url: Optional[str] = Field(
        None, min_length=1, max_length=2048, description="Original URL to shorten"
    )
    is_public: Optional[bool] = Field(None, description="Whether the link is publicly accessible")
    allowed_emails: Optional[list[str]] = Field(
        None, description="Email addresses allowed to access private links"
    )


class LinkResponse(BaseModel):
    """Response for link operations."""

    id: int = Field(..., description="Unique link ID")
    user_id: int = Field(..., description="ID of the user who created the link")
    original_url: str = Field(..., description="Original URL")
    slug: str = Field(..., description="Shortened slug")
    is_public: bool = Field(..., description="Whether the link is publicly accessible")
    allowed_emails: Optional[list[str]] = Field(
        None, description="Allowed emails for private links"
    )
    hit_count: int = Field(..., description="Number of times the link has been accessed")
    last_hit_at: Optional[datetime] = Field(None, description="Timestamp of last access")
    created_at: datetime = Field(..., description="Timestamp when link was created")
    updated_at: datetime = Field(..., description="Timestamp when link was last updated")

    model_config = {"from_attributes": True}


class LinkListResponse(BaseModel):
    """Response for listing links."""

    items: list[LinkResponse] = Field(..., description="List of links")
    total: int = Field(..., description="Total number of links")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
