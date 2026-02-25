"""OAuth Account model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class OAuthAccount(BaseModel):
    """OAuth account linking for external provider authentication."""

    __tablename__ = "oauth_accounts"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    access_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        # Ensure unique combination of provider and provider_user_id
        Index("ix_oauth_accounts_user_provider", "user_id", "provider"),
    )

    def __repr__(self) -> str:
        return (
            f"<OAuthAccount(provider={self.provider!r}, "
            f"provider_user_id={self.provider_user_id!r})>"
        )
