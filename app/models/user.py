"""User model."""

from sqlalchemy import String, Boolean, Column
from sqlalchemy.orm import relationship

from app.models import BaseModel


class User(BaseModel):
    """User model for authentication and link management."""

    __tablename__ = "users"
    __allow_unmapped__ = True

    email: str = Column(String(255), unique=True, nullable=False, index=True)
    full_name: str = Column(String(255), nullable=True)
    avatar_url: str = Column(String(512), nullable=True)
    is_admin: bool = Column(Boolean, default=False, nullable=False)
    is_blocked: bool = Column(Boolean, default=False, nullable=False)

    # Relationships
    links = relationship("Link", back_populates="user", cascade="all, delete-orphan")
    oauth_accounts = relationship(
        "OAuthAccount", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<User(email={self.email!r}, is_admin={self.is_admin}, is_blocked={self.is_blocked})>"
        )
