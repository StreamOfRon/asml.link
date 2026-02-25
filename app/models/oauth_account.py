"""OAuth Account model."""

from sqlalchemy import String, Integer, ForeignKey, Column
from sqlalchemy.orm import relationship

from app.models import BaseModel


class OAuthAccount(BaseModel):
    """OAuth account linking for external provider authentication."""

    __tablename__ = "oauth_accounts"
    __allow_unmapped__ = True

    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider: str = Column(String(50), nullable=False, index=True)
    provider_user_id: str = Column(String(255), nullable=False)
    provider_email: str = Column(String(255), nullable=True)
    access_token: str = Column(String(2048), nullable=True)
    refresh_token: str = Column(String(2048), nullable=True)

    # Relationships
    user = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        # Ensure unique combination of provider and provider_user_id
        {"indexes": ["user_id", "provider"]},
    )

    def __repr__(self) -> str:
        return f"<OAuthAccount(provider={self.provider!r}, provider_user_id={self.provider_user_id!r})>"
