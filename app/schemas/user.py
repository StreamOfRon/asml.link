"""Pydantic schemas for User API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """Response for user operations."""

    id: int = Field(..., description="Unique user ID")
    email: str = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    avatar_url: Optional[str] = Field(None, description="User's avatar URL")
    is_admin: bool = Field(..., description="Whether user is an administrator")
    is_blocked: bool = Field(..., description="Whether user is blocked")
    created_at: datetime = Field(..., description="Timestamp when user was created")
    updated_at: datetime = Field(..., description="Timestamp when user was last updated")

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Response for listing users."""

    items: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")


class UserUpdateRequest(BaseModel):
    """Request body for updating user profile."""

    full_name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="User's full name"
    )
    avatar_url: Optional[str] = Field(
        None, min_length=1, max_length=512, description="User's avatar URL"
    )


class AllowListEntryResponse(BaseModel):
    """Response for allow-list entries."""

    email: str = Field(..., description="Email address in allow-list")
    created_at: datetime = Field(..., description="Timestamp when entry was created")

    model_config = {"from_attributes": True}


class AllowListResponse(BaseModel):
    """Response for listing allow-list entries."""

    items: list[AllowListEntryResponse] = Field(..., description="List of allowed emails")
    total: int = Field(..., description="Total number of entries")


class AllowListAddRequest(BaseModel):
    """Request body for adding email to allow-list."""

    email: str = Field(..., min_length=1, max_length=255, description="Email to add to allow-list")
