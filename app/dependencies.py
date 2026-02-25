"""Dependency injection container for services and database session.

This module provides factory functions and context managers for injecting
services and database sessions into route handlers and other components.

Usage:
    from app.dependencies import get_link_service, get_user_service

    @app.route('/api/links')
    async def create_link(link_service: LinkService = Depends(get_link_service)):
        return await link_service.create_link(...)
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService
from app.services.link_service import LinkService
from app.services.user_service import UserService


async def get_link_service(db: AsyncSession) -> AsyncGenerator[LinkService, None]:
    """Dependency for getting LinkService with database session.

    Usage in route handlers:
        @app.route('/api/links')
        async def example(service: LinkService = Depends(get_link_service)):
            ...
    """
    service = LinkService(db)
    try:
        yield service
    finally:
        # Services are stateless, no cleanup needed
        pass


async def get_user_service(db: AsyncSession) -> AsyncGenerator[UserService, None]:
    """Dependency for getting UserService with database session.

    Usage in route handlers:
        @app.route('/api/users')
        async def example(service: UserService = Depends(get_user_service)):
            ...
    """
    service = UserService(db)
    try:
        yield service
    finally:
        # Services are stateless, no cleanup needed
        pass


async def get_auth_service(db: AsyncSession) -> AsyncGenerator[AuthService, None]:
    """Dependency for getting AuthService with database session.

    Usage in route handlers:
        @app.route('/auth/callback')
        async def example(service: AuthService = Depends(get_auth_service)):
            ...
    """
    service = AuthService(db)
    try:
        yield service
    finally:
        # Services are stateless, no cleanup needed
        pass
