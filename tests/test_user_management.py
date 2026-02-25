"""Integration tests for user management API endpoints."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import create_app
from app.models.user import User
from app.services.user_service import UserService


@pytest.fixture
async def app():
    """Create a test application."""
    app = await create_app()
    yield app


@pytest.fixture
async def client(app):
    """Create a test client."""
    return app.test_client()


class TestUserManagementEndpoints:
    """Tests for user management API endpoints."""

    async def test_list_users_admin_only(
        self, client, db_session: AsyncSession, test_admin_user: User, test_user: User
    ):
        """Test that only admins can list users."""
        from sqlalchemy import select

        from app.models.user import User as UserModel

        service = UserService(db_session)

        # Create multiple users
        _user2 = await service.create_user(
            email="user2@example.com",
            full_name="User 2",
        )

        _user3 = await service.create_user(
            email="user3@example.com",
            full_name="User 3",
        )

        # Get all users (admin view)
        result = await db_session.execute(select(UserModel).order_by(UserModel.created_at))
        users = result.scalars().all()
        assert len(users) >= 4

    async def test_get_user_details_admin_only(
        self, db_session: AsyncSession, test_admin_user: User, test_user: User
    ):
        """Test that only admins can get user details."""
        service = UserService(db_session)

        # Get user details via service
        user = await service.get_user(test_user.id)
        assert user is not None
        assert user.email == test_user.email
        assert user.full_name == test_user.full_name
        assert user.is_admin == test_user.is_admin
        assert user.is_blocked == test_user.is_blocked

    async def test_promote_user_to_admin(
        self, db_session: AsyncSession, test_admin_user: User, test_user: User
    ):
        """Test promoting a regular user to admin."""
        service = UserService(db_session)

        # Verify user is not admin
        assert test_user.is_admin is False

        # Promote to admin
        promoted = await service.promote_to_admin(test_user.id)
        assert promoted.is_admin is True

        # Verify change persists
        fetched = await service.get_user(test_user.id)
        assert fetched.is_admin is True

    async def test_demote_admin_to_user(self, db_session: AsyncSession, test_admin_user: User):
        """Test demoting an admin to regular user."""
        service = UserService(db_session)

        # Verify user is admin
        assert test_admin_user.is_admin is True

        # Demote from admin
        demoted = await service.demote_from_admin(test_admin_user.id)
        assert demoted.is_admin is False

        # Verify change persists
        fetched = await service.get_user(test_admin_user.id)
        assert fetched.is_admin is False

    async def test_block_user(
        self, db_session: AsyncSession, test_admin_user: User, test_user: User
    ):
        """Test blocking a user."""
        service = UserService(db_session)

        # Verify user is not blocked
        assert test_user.is_blocked is False

        # Block user
        blocked = await service.block_user(test_user.id)
        assert blocked.is_blocked is True

        # Verify change persists
        fetched = await service.get_user(test_user.id)
        assert fetched.is_blocked is True

    async def test_unblock_user(
        self, db_session: AsyncSession, test_admin_user: User, test_user: User
    ):
        """Test unblocking a user."""
        service = UserService(db_session)

        # Block user first
        await service.block_user(test_user.id)
        assert test_user.is_blocked is True

        # Unblock user
        unblocked = await service.unblock_user(test_user.id)
        assert unblocked.is_blocked is False

        # Verify change persists
        fetched = await service.get_user(test_user.id)
        assert fetched.is_blocked is False

    async def test_delete_user(
        self, db_session: AsyncSession, test_admin_user: User, test_user: User
    ):
        """Test deleting a user."""
        service = UserService(db_session)

        user_id = test_user.id

        # Delete user
        await service.delete_user(user_id)

        # Verify user is deleted
        fetched = await service.get_user(user_id)
        assert fetched is None

    async def test_get_admin_users(
        self, db_session: AsyncSession, test_admin_user: User, test_user: User
    ):
        """Test getting list of admin users."""
        service = UserService(db_session)

        # Create another admin
        admin2 = await service.create_user(
            email="admin2@example.com",
            full_name="Admin 2",
        )
        await service.promote_to_admin(admin2.id)

        # Get all admin users
        admins = await service.get_admin_users()
        assert len(admins) >= 2
        admin_ids = {admin.id for admin in admins}
        assert test_admin_user.id in admin_ids
        assert admin2.id in admin_ids
        assert test_user.id not in admin_ids

    async def test_get_blocked_users(
        self, db_session: AsyncSession, test_admin_user: User, test_user: User
    ):
        """Test getting list of blocked users."""
        service = UserService(db_session)

        # Create another user
        user2 = await service.create_user(
            email="user2@example.com",
            full_name="User 2",
        )

        # Block one user
        await service.block_user(test_user.id)

        # Get all blocked users
        blocked = await service.get_blocked_users()
        assert len(blocked) >= 1
        blocked_ids = {user.id for user in blocked}
        assert test_user.id in blocked_ids
        assert user2.id not in blocked_ids
        assert test_admin_user.id not in blocked_ids

    async def test_user_not_found_error(self, db_session: AsyncSession, test_admin_user: User):
        """Test getting non-existent user returns None."""
        service = UserService(db_session)

        # Try to get non-existent user - should return None
        user = await service.get_user(99999)
        assert user is None

    async def test_delete_nonexistent_user_error(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test deleting non-existent user raises error."""
        service = UserService(db_session)

        from app.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await service.delete_user(99999)

    async def test_promote_already_admin(self, db_session: AsyncSession, test_admin_user: User):
        """Test promoting already-admin user (should be idempotent)."""
        service = UserService(db_session)

        # Verify is admin
        assert test_admin_user.is_admin is True

        # Try to promote again (should succeed, idempotent)
        promoted = await service.promote_to_admin(test_admin_user.id)
        assert promoted.is_admin is True

    async def test_demote_non_admin(self, db_session: AsyncSession, test_user: User):
        """Test demoting non-admin user (should be idempotent)."""
        service = UserService(db_session)

        # Verify is not admin
        assert test_user.is_admin is False

        # Try to demote again (should succeed, idempotent)
        demoted = await service.demote_from_admin(test_user.id)
        assert demoted.is_admin is False

    async def test_block_already_blocked(self, db_session: AsyncSession, test_user: User):
        """Test blocking already-blocked user (should be idempotent)."""
        service = UserService(db_session)

        # Block user
        await service.block_user(test_user.id)
        assert test_user.is_blocked is True

        # Try to block again (should succeed, idempotent)
        blocked = await service.block_user(test_user.id)
        assert blocked.is_blocked is True

    async def test_unblock_not_blocked(self, db_session: AsyncSession, test_user: User):
        """Test unblocking non-blocked user (should be idempotent)."""
        service = UserService(db_session)

        # Verify not blocked
        assert test_user.is_blocked is False

        # Try to unblock again (should succeed, idempotent)
        unblocked = await service.unblock_user(test_user.id)
        assert unblocked.is_blocked is False

    async def test_is_user_admin(
        self, db_session: AsyncSession, test_admin_user: User, test_user: User
    ):
        """Test checking if user is admin."""
        service = UserService(db_session)

        assert await service.is_user_admin(test_admin_user.id) is True
        assert await service.is_user_admin(test_user.id) is False

    async def test_is_user_blocked(self, db_session: AsyncSession, test_user: User):
        """Test checking if user is blocked."""
        service = UserService(db_session)

        # Not blocked initially
        assert await service.is_user_blocked(test_user.id) is False

        # Block user
        await service.block_user(test_user.id)
        assert await service.is_user_blocked(test_user.id) is True

    async def test_user_timestamps(self, db_session: AsyncSession, test_user: User):
        """Test that user has creation and update timestamps."""
        service = UserService(db_session)

        user = await service.get_user(test_user.id)
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at <= user.updated_at

    async def test_update_user_profile(self, db_session: AsyncSession, test_user: User):
        """Test updating user profile information."""
        service = UserService(db_session)

        new_name = "Updated Name"
        new_avatar = "https://example.com/avatar.jpg"

        updated = await service.update_user(
            test_user.id,
            full_name=new_name,
            avatar_url=new_avatar,
        )

        assert updated.full_name == new_name
        assert updated.avatar_url == new_avatar

        # Verify change persists
        fetched = await service.get_user(test_user.id)
        assert fetched.full_name == new_name
        assert fetched.avatar_url == new_avatar

    async def test_get_user_by_email(self, db_session: AsyncSession, test_user: User):
        """Test getting user by email."""
        service = UserService(db_session)

        user = await service.get_user_by_email(test_user.email)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    async def test_get_user_by_email_case_insensitive(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test getting user by email is case-insensitive."""
        service = UserService(db_session)

        # Try different case variations
        user1 = await service.get_user_by_email(test_user.email.upper())
        user2 = await service.get_user_by_email(test_user.email.lower())
        user3 = await service.get_user_by_email(test_user.email.title())

        assert user1 is not None
        assert user2 is not None
        assert user3 is not None
        assert user1.id == user2.id == user3.id == test_user.id

    async def test_get_user_by_email_not_found(self, db_session: AsyncSession):
        """Test getting non-existent user by email returns None."""
        service = UserService(db_session)

        user = await service.get_user_by_email("nonexistent@example.com")
        assert user is None
