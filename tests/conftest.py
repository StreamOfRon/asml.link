"""Pytest configuration and shared fixtures."""

import asyncio
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings as app_settings
from app.models import Base
from app.models.link import Link
from app.models.oauth_account import OAuthAccount
from app.models.user import User


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_engine():
    """Create a fresh test database engine for each test."""
    # Use in-memory SQLite for tests - each gets its own connection
    test_url = "sqlite+aiosqlite:///:memory:"

    engine = create_async_engine(
        test_url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def test_settings():
    """Return test settings."""
    return app_settings


# Model fixtures


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        full_name="Test User",
        is_admin=False,
        is_blocked=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        is_admin=True,
        is_blocked=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_link(db_session: AsyncSession, test_user: User) -> Link:
    """Create a test link."""
    link = Link(
        user_id=test_user.id,
        original_url="https://example.com/very/long/url",
        slug="abc123",
        is_public=True,
        hit_count=0,
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)
    return link


@pytest.fixture
async def test_private_link(db_session: AsyncSession, test_user: User) -> Link:
    """Create a test private link."""
    link = Link(
        user_id=test_user.id,
        original_url="https://example.com/private",
        slug="private123",
        is_public=False,
        hit_count=0,
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)
    return link


@pytest.fixture
async def test_oauth_account(db_session: AsyncSession, test_user: User) -> OAuthAccount:
    """Create a test OAuth account."""
    oauth = OAuthAccount(
        user_id=test_user.id,
        provider="google",
        provider_user_id="google_123456",
        provider_email="test@gmail.com",
        access_token="test_access_token",
    )
    db_session.add(oauth)
    await db_session.commit()
    await db_session.refresh(oauth)
    return oauth
