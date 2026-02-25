"""Link model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Link(BaseModel):
    """Link model for shortened URLs."""

    __tablename__ = "links"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allowed_emails: Mapped[str | None] = mapped_column(
        String(4096), nullable=True
    )  # JSON-encoded list of emails
    hit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_hit_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="links")

    def __repr__(self) -> str:
        return (
            f"<Link(slug={self.slug!r}, original_url={self.original_url!r}, "
            f"is_public={self.is_public})>"
        )

    def get_allowed_emails(self) -> list[str]:
        """Parse allowed emails from JSON string."""
        if not self.allowed_emails:
            return []
        import json

        try:
            return json.loads(self.allowed_emails)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_allowed_emails(self, emails: list[str]) -> None:
        """Set allowed emails as JSON string."""
        import json

        self.allowed_emails = json.dumps(emails) if emails else None
