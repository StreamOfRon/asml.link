"""Database utilities for initialization, migration, and management.

This module provides utilities for database lifecycle management including
initialization, migration, and cleanup operations.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, wait_exponential

from app.models import Base, async_engine, async_session, close_db, init_db


async def initialize_database() -> None:
    """Initialize database schema on application startup.

    This creates all tables defined in the models if they don't exist.
    For production, use Alembic migrations instead:
        alembic upgrade head
    """
    await init_db()
    print("✓ Database initialized successfully")


async def get_session() -> AsyncSession:
    """Get a new database session.

    Returns:
        An async database session.

    Usage:
        session = await get_session()
        try:
            # Use session
            ...
        finally:
            await session.close()
    """
    return async_session()


async def verify_database_connection() -> bool:
    """Verify that the database connection is working.

    Returns:
        True if connection is successful, False otherwise.
    """
    try:
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
        print("✓ Database connection verified")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


@retry(wait=wait_exponential(min=1, max=60), reraise=True)
async def verify_database_connection_with_retry() -> bool:
    """Verify database connection with exponential backoff retry."""
    return await verify_database_connection()


async def cleanup_database() -> None:
    """Clean up database connections on shutdown.

    This should be called when the application is shutting down
    to properly close all connections.
    """
    await close_db()
    print("✓ Database connections closed")


async def reset_database() -> None:
    """Reset the database by dropping and recreating all tables.

    WARNING: This will delete all data. Use with caution!
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await init_db()
    print("✓ Database reset successfully (all data deleted)")


class DatabaseContext:
    """Context manager for database operations.

    Ensures proper cleanup of database connections and sessions.

    Usage:
        async with DatabaseContext() as db:
            # Use db session
            ...
    """

    def __init__(self):
        """Initialize context manager."""
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        """Enter context and return session."""
        self.session = async_session()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and close session."""
        if self.session:
            await self.session.close()
