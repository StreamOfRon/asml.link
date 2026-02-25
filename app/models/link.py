"""Link model."""

from typing import Optional
from sqlalchemy import String, Boolean, Integer, ForeignKey, Column, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models import BaseModel


class Link(BaseModel):
    """Link model for shortened URLs."""

    __tablename__ = "links"
    __allow_unmapped__ = True

    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_url: str = Column(String(2048), nullable=False)
    slug: str = Column(String(255), unique=True, nullable=False, index=True)
    is_public: bool = Column(Boolean, default=True, nullable=False)
    allowed_emails: Optional[str] = Column(
        String(4096), nullable=True
    )  # JSON-encoded list of emails
    hit_count: int = Column(Integer, default=0, nullable=False)
    last_hit_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="links")

    def __repr__(self) -> str:
        return f"<Link(slug={self.slug!r}, original_url={self.original_url!r}, is_public={self.is_public})>"

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
