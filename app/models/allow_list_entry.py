"""AllowListEntry model for allow-list mode management."""

from sqlalchemy import String, Column

from app.models import BaseModel


class AllowListEntry(BaseModel):
    """Allowed email entry for allow-list mode."""

    __tablename__ = "allow_list_entries"
    __allow_unmapped__ = True

    email: str = Column(String(255), unique=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AllowListEntry(email={self.email!r})>"
