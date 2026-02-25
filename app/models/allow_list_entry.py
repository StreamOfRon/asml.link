"""AllowListEntry model for allow-list mode management."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import BaseModel


class AllowListEntry(BaseModel):
    """Allowed email entry for allow-list mode."""

    __tablename__ = "allow_list_entries"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AllowListEntry(email={self.email!r})>"

    def __repr__(self) -> str:
        return f"<AllowListEntry(email={self.email!r})>"
