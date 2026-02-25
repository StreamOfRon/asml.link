"""Database models base configuration."""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Create async engine
async_engine = create_async_engine(
    settings.get_database_url(),
    echo=settings.debug,
    future=True,
)

# Session factory
async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base for all models
Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields for all models."""

    __abstract__ = True
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async with async_session() as session:
        yield session
