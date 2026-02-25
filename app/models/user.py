"""User model."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel

if TYPE_CHECKING:
    from app.models.link import Link
    from app.models.oauth_account import OAuthAccount


class User(BaseModel):
    """User model for authentication and link management."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    links: Mapped[List["Link"]] = relationship(
        "Link", back_populates="user", cascade="all, delete-orphan"
    )
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        "OAuthAccount", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<User(email={self.email!r}, is_admin={self.is_admin}, is_blocked={self.is_blocked})>"
        )
