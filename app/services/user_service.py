"""User service for managing user accounts."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.utils.validators import is_valid_email, is_valid_full_name, normalize_email
from app.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
)


class UserService:
    """Service for managing users."""

    def __init__(self, db_session: AsyncSession):
        """Initialize user service with database session."""
        self.db = db_session

    async def create_user(
        self,
        email: str,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        is_admin: bool = False,
    ) -> User:
        """
        Create a new user.

        Args:
            email: User's email address
            full_name: Optional full name
            avatar_url: Optional avatar URL
            is_admin: Whether user is an admin

        Returns:
            Created User object

        Raises:
            ValidationError: If validation fails
            ConflictError: If email already exists
        """
        # Validate email
        if not is_valid_email(email):
            raise ValidationError(f"Invalid email: {email}")

        # Normalize email
        email = normalize_email(email)

        # Validate full name if provided
        if full_name is not None and not is_valid_full_name(full_name):
            raise ValidationError(f"Invalid full name: {full_name}")

        # Check email uniqueness
        existing = await self._get_user_by_email(email)
        if existing is not None:
            raise ConflictError(f"User with email '{email}' already exists")

        # Create user
        user = User(
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
            is_admin=is_admin,
            is_blocked=False,
        )

        self.db.add(user)
        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise ConflictError(f"Failed to create user: {str(e)}")

        await self.db.refresh(user)
        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User's email

        Returns:
            User object or None if not found
        """
        email = normalize_email(email)
        return await self._get_user_by_email(email)

    async def update_user(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        """
        Update user profile.

        Args:
            user_id: User ID
            full_name: New full name
            avatar_url: New avatar URL

        Returns:
            Updated User object

        Raises:
            NotFoundError: If user not found
            ValidationError: If validation fails
        """
        user = await self.get_user(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")

        if full_name is not None:
            if not is_valid_full_name(full_name):
                raise ValidationError(f"Invalid full name: {full_name}")
            user.full_name = full_name

        if avatar_url is not None:
            user.avatar_url = avatar_url

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> None:
        """
        Delete a user and cascade to related data.

        Args:
            user_id: User ID

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")

        await self.db.delete(user)
        await self.db.commit()

    async def promote_to_admin(self, user_id: int) -> User:
        """
        Promote user to admin.

        Args:
            user_id: User ID

        Returns:
            Updated User object

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")

        user.is_admin = True
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def demote_from_admin(self, user_id: int) -> User:
        """
        Demote user from admin.

        Args:
            user_id: User ID

        Returns:
            Updated User object

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")

        user.is_admin = False
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def block_user(self, user_id: int) -> User:
        """
        Block a user.

        Args:
            user_id: User ID

        Returns:
            Updated User object

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")

        user.is_blocked = True
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def unblock_user(self, user_id: int) -> User:
        """
        Unblock a user.

        Args:
            user_id: User ID

        Returns:
            Updated User object

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")

        user.is_blocked = False
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def is_user_admin(self, user_id: int) -> bool:
        """
        Check if user is admin.

        Args:
            user_id: User ID

        Returns:
            True if user is admin, False otherwise
        """
        user = await self.get_user(user_id)
        return user is not None and user.is_admin

    async def is_user_blocked(self, user_id: int) -> bool:
        """
        Check if user is blocked.

        Args:
            user_id: User ID

        Returns:
            True if user is blocked, False otherwise
        """
        user = await self.get_user(user_id)
        return user is not None and user.is_blocked

    async def get_admin_users(self) -> list[User]:
        """
        Get all admin users.

        Returns:
            List of admin User objects
        """
        stmt = select(User).where(User.is_admin == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_blocked_users(self) -> list[User]:
        """
        Get all blocked users.

        Returns:
            List of blocked User objects
        """
        stmt = select(User).where(User.is_blocked == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # Private helper methods

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (internal)."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
