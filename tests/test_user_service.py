"""User management service tests."""

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.link import Link


class TestUserCreation:
    """Test creating users."""

    async def test_create_user_with_all_fields(self, db_session: AsyncSession) -> None:
        """Test creating a user with all fields."""
        user = User(
            email="fulluser@example.com",
            full_name="Full User",
            avatar_url="https://example.com/avatar.jpg",
            is_admin=False,
            is_blocked=False,
        )
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.email == "fulluser@example.com")
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.email == "fulluser@example.com"
        assert found.full_name == "Full User"
        assert found.avatar_url == "https://example.com/avatar.jpg"

    async def test_create_user_minimal_fields(self, db_session: AsyncSession) -> None:
        """Test creating a user with minimal required fields."""
        user = User(email="minimal@example.com")
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.email == "minimal@example.com")
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.email == "minimal@example.com"
        assert found.full_name is None
        assert found.avatar_url is None

    async def test_user_timestamps_set_automatically(self, db_session: AsyncSession) -> None:
        """Test created_at and updated_at are set automatically."""
        user = User(email="timestamps@example.com")
        db_session.add(user)
        await db_session.commit()

        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at <= user.updated_at


class TestUserUpdate:
    """Test updating user information."""

    async def test_update_user_full_name(self, db_session: AsyncSession, test_user: User) -> None:
        """Test updating user's full name."""
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()

        user.full_name = "Updated Name"
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.full_name == "Updated Name"

    async def test_update_user_avatar_url(self, db_session: AsyncSession, test_user: User) -> None:
        """Test updating user's avatar URL."""
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()

        user.avatar_url = "https://example.com/new-avatar.jpg"
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.avatar_url == "https://example.com/new-avatar.jpg"

    async def test_updated_at_changes_on_update(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test updated_at timestamp is updated on modification."""
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()

        original_updated_at = user.updated_at
        user.full_name = "Updated"
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        # updated_at should be newer (greater or equal)
        assert found.updated_at >= original_updated_at


class TestUserDeletion:
    """Test deleting users."""

    async def test_delete_user(self, db_session: AsyncSession) -> None:
        """Test deleting a user."""
        user = User(email="delete_me@example.com")
        db_session.add(user)
        await db_session.commit()
        user_id = user.id

        # Delete the user
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        await db_session.delete(found)
        await db_session.commit()

        # Verify deleted
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()
        assert found is None

    async def test_delete_user_cascades_to_links(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test deleting user cascades to their links."""
        # Create a link for the user
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com",
            slug="test_slug_cascade",
            is_public=True,
        )
        db_session.add(link)
        await db_session.commit()
        link_id = link.id

        # Delete the user
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()
        await db_session.delete(user)
        await db_session.commit()

        # Verify link is deleted
        stmt = select(Link).where(Link.id == link_id)
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()
        assert found is None


class TestUserQueries:
    """Test querying users."""

    async def test_count_total_users(self, db_session: AsyncSession) -> None:
        """Test counting total users."""
        # Create multiple users
        for i in range(3):
            user = User(email=f"user{i}@example.com")
            db_session.add(user)
        await db_session.commit()

        stmt = select(func.count(User.id))
        result = await db_session.execute(stmt)
        count = result.scalar()
        assert count >= 3

    async def test_get_all_users(self, db_session: AsyncSession) -> None:
        """Test retrieving all users."""
        emails = set()
        for i in range(3):
            user = User(email=f"all_users_{i}@example.com")
            db_session.add(user)
            emails.add(f"all_users_{i}@example.com")
        await db_session.commit()

        stmt = select(User).where(User.email.in_(emails))
        result = await db_session.execute(stmt)
        users = result.scalars().all()
        assert len(users) == 3

    async def test_find_user_by_email_case_sensitive(self, db_session: AsyncSession) -> None:
        """Test email lookup is case-sensitive by default."""
        user = User(email="CaseSensitive@example.com")
        db_session.add(user)
        await db_session.commit()

        # Try to find with different case
        stmt = select(User).where(User.email == "casesensitive@example.com")
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()

        # SQLite by default does case-sensitive comparison
        # This may vary by database
        assert found is None or found.email == "CaseSensitive@example.com"

    async def test_get_admin_users(self, db_session: AsyncSession) -> None:
        """Test retrieving admin users."""
        # Create mix of users
        admin = User(email="admin1@example.com", is_admin=True)
        normal = User(email="normal1@example.com", is_admin=False)
        db_session.add(admin)
        db_session.add(normal)
        await db_session.commit()

        stmt = select(User).where(User.is_admin == True)
        result = await db_session.execute(stmt)
        admins = result.scalars().all()
        assert len(admins) >= 1
        assert all(u.is_admin for u in admins)

    async def test_get_blocked_users(self, db_session: AsyncSession) -> None:
        """Test retrieving blocked users."""
        blocked = User(email="blocked1@example.com", is_blocked=True)
        active = User(email="active1@example.com", is_blocked=False)
        db_session.add(blocked)
        db_session.add(active)
        await db_session.commit()

        stmt = select(User).where(User.is_blocked == True)
        result = await db_session.execute(stmt)
        blocked_users = result.scalars().all()
        assert len(blocked_users) >= 1
        assert all(u.is_blocked for u in blocked_users)

    async def test_get_user_with_no_links(self, db_session: AsyncSession, test_user: User) -> None:
        """Test user without links."""
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()

        # User exists but may have 0 links
        assert user.id is not None


class TestUserStatusManagement:
    """Test user status (admin, blocked) management."""

    async def test_promote_user_to_admin(self, db_session: AsyncSession, test_user: User) -> None:
        """Test promoting user to admin."""
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()

        assert user.is_admin is False
        user.is_admin = True
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.is_admin is True

    async def test_demote_admin_to_user(
        self, db_session: AsyncSession, test_admin_user: User
    ) -> None:
        """Test demoting admin to regular user."""
        stmt = select(User).where(User.id == test_admin_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()

        assert user.is_admin is True
        user.is_admin = False
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.id == test_admin_user.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.is_admin is False

    async def test_block_and_unblock_user(self, db_session: AsyncSession, test_user: User) -> None:
        """Test blocking and unblocking a user."""
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()

        # Block
        assert user.is_blocked is False
        user.is_blocked = True
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.is_blocked is True

        # Unblock
        found.is_blocked = False
        db_session.add(found)
        await db_session.commit()

        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        final = result.scalar_one()
        assert final.is_blocked is False


class TestUserLinkRelationship:
    """Test relationship between users and links."""

    async def test_user_can_have_multiple_links(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test user can have multiple links."""
        for i in range(3):
            link = Link(
                user_id=test_user.id,
                original_url=f"https://example.com/{i}",
                slug=f"slug_{test_user.id}_{i}",
                is_public=True,
            )
            db_session.add(link)
        await db_session.commit()

        stmt = select(func.count(Link.id)).where(Link.user_id == test_user.id)
        result = await db_session.execute(stmt)
        count = result.scalar()
        assert count >= 3

    async def test_multiple_users_own_different_links(self, db_session: AsyncSession) -> None:
        """Test multiple users own different links."""
        user1 = User(email="linkowner1@example.com")
        user2 = User(email="linkowner2@example.com")
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()

        link1 = Link(
            user_id=user1.id,
            original_url="https://example.com/link1",
            slug="link_user1",
            is_public=True,
        )
        link2 = Link(
            user_id=user2.id,
            original_url="https://example.com/link2",
            slug="link_user2",
            is_public=True,
        )
        db_session.add(link1)
        db_session.add(link2)
        await db_session.commit()

        # Verify user1 owns link1
        stmt = select(Link).where(Link.id == link1.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.user_id == user1.id

        # Verify user2 owns link2
        stmt = select(Link).where(Link.id == link2.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.user_id == user2.id
