"""Rate limit entry model."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import BaseModel


class RateLimitEntry(BaseModel):
    """Rate limit entry for tracking API calls."""

    __tablename__ = "rate_limit_entries"

    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)  # IPv4 or IPv6
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_hit_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    last_hit_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<RateLimitEntry(ip={self.ip_address}, endpoint={self.endpoint}, hits={self.hit_count})>"
