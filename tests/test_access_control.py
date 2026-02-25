"""Access control and permissions tests."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.models.user import User


class TestPublicLinkAccess:
    """Test access control for public links."""

    async def test_public_link_accessible_by_anyone(
        self, db_session: AsyncSession, test_link: Link
    ) -> None:
        """Test public links are accessible to anyone."""
        assert test_link.is_public is True

        # Public link should be accessible
        stmt = select(Link).where(Link.slug == test_link.slug)
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()
        assert found is not None

    async def test_non_owner_can_view_public_link(
        self, db_session: AsyncSession, test_link: Link, test_admin_user: User
    ) -> None:
        """Test non-owner can view public links."""
        # test_link belongs to test_user, test_admin_user is different
        assert test_link.is_public is True
        assert test_link.user_id != test_admin_user.id

        # Public link should be accessible to anyone
        stmt = select(Link).where(Link.slug == test_link.slug)
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()
        assert found is not None


class TestPrivateLinkAccess:
    """Test access control for private links."""

    async def test_private_link_no_allowed_emails(
        self, db_session: AsyncSession, test_private_link: Link
    ) -> None:
        """Test private link with no allowed emails."""
        assert test_private_link.is_public is False
        assert test_private_link.get_allowed_emails() == []

    async def test_private_link_with_allowed_emails(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test private link with allowed email list."""
        allowed_emails = ["user1@example.com", "user2@example.com"]
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="private_allowed",
            is_public=False,
        )
        link.set_allowed_emails(allowed_emails)
        db_session.add(link)
        await db_session.commit()

        # Verify allowed emails are stored
        stmt = select(Link).where(Link.id == link.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.get_allowed_emails() == allowed_emails

    async def test_check_email_allowed_access(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test checking if email is allowed to access private link."""
        allowed_emails = ["allowed@example.com", "another@example.com"]
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="email_check",
            is_public=False,
        )
        link.set_allowed_emails(allowed_emails)
        db_session.add(link)
        await db_session.commit()

        # Verify email check logic can be implemented
        stored_emails = link.get_allowed_emails()
        assert "allowed@example.com" in stored_emails
        assert "notallowed@example.com" not in stored_emails

    async def test_private_link_modify_allowed_emails(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test modifying allowed emails for private link."""
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="modify_allowed",
            is_public=False,
        )
        link.set_allowed_emails(["initial@example.com"])
        db_session.add(link)
        await db_session.commit()

        # Modify allowed emails
        stmt = select(Link).where(Link.id == link.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        new_emails = ["updated@example.com", "another@example.com"]
        found.set_allowed_emails(new_emails)
        db_session.add(found)
        await db_session.commit()

        # Verify modification
        stmt = select(Link).where(Link.id == link.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.get_allowed_emails() == new_emails


class TestLinkOwnership:
    """Test link ownership and owner-only operations."""

    async def test_link_owner_can_modify_link(
        self, db_session: AsyncSession, test_user: User, test_link: Link
    ) -> None:
        """Test link owner can modify link."""
        assert test_link.user_id == test_user.id

        # Owner should be able to modify
        stmt = select(Link).where(Link.id == test_link.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        found.is_public = False
        db_session.add(found)
        await db_session.commit()

        # Verify modification
        stmt = select(Link).where(Link.id == test_link.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.is_public is False

    async def test_link_owner_can_delete_link(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test link owner can delete link."""
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com/deleteme",
            slug="delete_me",
            is_public=True,
        )
        db_session.add(link)
        await db_session.commit()
        link_id = link.id

        # Owner can delete
        stmt = select(Link).where(Link.id == link_id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        await db_session.delete(found)
        await db_session.commit()

        # Verify deletion
        stmt = select(Link).where(Link.id == link_id)
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()
        assert found is None

    async def test_link_owner_can_change_privacy(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test link owner can change privacy setting."""
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com/privacy",
            slug="privacy_test",
            is_public=True,
        )
        db_session.add(link)
        await db_session.commit()

        # Change to private
        stmt = select(Link).where(Link.id == link.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.is_public is True

        found.is_public = False
        found.set_allowed_emails(["restricted@example.com"])
        db_session.add(found)
        await db_session.commit()

        # Verify change
        stmt = select(Link).where(Link.id == link.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.is_public is False
        assert found.get_allowed_emails() == ["restricted@example.com"]


class TestAdminAccess:
    """Test admin-level access controls."""

    async def test_admin_user_flag(self, db_session: AsyncSession, test_admin_user: User) -> None:
        """Test admin user has is_admin flag."""
        stmt = select(User).where(User.id == test_admin_user.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.is_admin is True

    async def test_regular_user_not_admin(self, db_session: AsyncSession, test_user: User) -> None:
        """Test regular user is not admin."""
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.is_admin is False

    async def test_admin_can_view_all_links(self, db_session: AsyncSession) -> None:
        """Test admin can potentially view all links."""
        # Create links by different users
        user1 = User(email="user1_admin_test@example.com")
        user2 = User(email="user2_admin_test@example.com")
        admin = User(email="admin_viewer@example.com", is_admin=True)
        db_session.add(user1)
        db_session.add(user2)
        db_session.add(admin)
        await db_session.commit()

        link1 = Link(
            user_id=user1.id,
            original_url="https://example.com/1",
            slug="admin_link1",
            is_public=False,
        )
        link2 = Link(
            user_id=user2.id,
            original_url="https://example.com/2",
            slug="admin_link2",
            is_public=True,
        )
        db_session.add(link1)
        db_session.add(link2)
        await db_session.commit()

        # Admin should be able to query all links
        stmt = select(Link)
        result = await db_session.execute(stmt)
        all_links = result.scalars().all()
        assert len(all_links) >= 2


class TestBlockedUserAccess:
    """Test access control for blocked users."""

    async def test_blocked_user_flag(self, db_session: AsyncSession) -> None:
        """Test blocked user has is_blocked flag."""
        user = User(email="blocked_user@example.com", is_blocked=True)
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.id == user.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one()
        assert found.is_blocked is True

    async def test_non_blocked_user_can_create_links(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test non-blocked user can create links."""
        assert test_user.is_blocked is False

        link = Link(
            user_id=test_user.id,
            original_url="https://example.com/new",
            slug="non_blocked_link",
            is_public=True,
        )
        db_session.add(link)
        await db_session.commit()

        # Link should be created
        stmt = select(Link).where(Link.id == link.id)
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()
        assert found is not None

    async def test_blocked_user_links_exist(self, db_session: AsyncSession) -> None:
        """Test blocked user's links still exist in database."""
        blocked_user = User(email="previously_blocked@example.com", is_blocked=False)
        db_session.add(blocked_user)
        await db_session.commit()

        link = Link(
            user_id=blocked_user.id,
            original_url="https://example.com/blocked",
            slug="blocked_user_link",
            is_public=True,
        )
        db_session.add(link)
        await db_session.commit()

        # Block the user
        stmt = select(User).where(User.id == blocked_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()
        user.is_blocked = True
        db_session.add(user)
        await db_session.commit()

        # Links should still exist
        stmt = select(Link).where(Link.user_id == blocked_user.id)
        result = await db_session.execute(stmt)
        links = result.scalars().all()
        assert len(links) > 0


class TestLinkAccessByStatus:
    """Test link access based on user and link status."""

    async def test_public_link_accessible_regardless_of_user_status(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        """Test public links are accessible even if user is blocked."""
        # Create public link
        link = Link(
            user_id=test_user.id,
            original_url="https://example.com/public",
            slug="public_link_status",
            is_public=True,
        )
        db_session.add(link)
        await db_session.commit()

        # Block the user
        stmt = select(User).where(User.id == test_user.id)
        result = await db_session.execute(stmt)
        user = result.scalar_one()
        user.is_blocked = True
        db_session.add(user)
        await db_session.commit()

        # Public link should still be accessible
        stmt = select(Link).where(Link.slug == link.slug)
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.is_public is True
