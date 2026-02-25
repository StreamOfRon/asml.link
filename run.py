"""Application entry point."""

import asyncio
import os
from dotenv import load_dotenv

from app.config import settings
from app.models import async_engine, Base

# Load environment variables
load_dotenv()


async def create_all_tables():
    """Create all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    """Main entry point."""
    # Create tables
    await create_all_tables()
    print("Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(main())
