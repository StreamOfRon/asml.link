"""Database models base configuration."""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import func, pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column

from app.config import settings


# Create async engine with connection pooling
def _create_engine() -> AsyncEngine:
    """Create async engine with proper connection pooling configuration."""
    db_url = settings.get_database_url()

    # SQLite doesn't support connection pooling, use StaticPool instead
    if db_url.startswith("sqlite"):
        pool_config = {
            "poolclass": pool.StaticPool,
            "connect_args": {"check_same_thread": False},
        }
    else:
        # PostgreSQL uses connection pooling
        pool_config = {
            "pool_size": 10,  # Number of connections to keep in the pool
            "max_overflow": 20,  # Maximum overflow connections
            "pool_pre_ping": True,  # Test connections before using them
            "pool_recycle": 3600,  # Recycle connections after 1 hour
        }

    return create_async_engine(
        db_url,
        echo=settings.debug,
        future=True,
        **pool_config,
    )


async_engine = _create_engine()

# Session factory with connection pooling management
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

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session.

    Usage in route handlers:
        @app.route('/example')
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database schema on application startup."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections on application shutdown."""
    await async_engine.dispose()
