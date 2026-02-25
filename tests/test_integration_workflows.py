"""Phase 12: Integration and End-to-End Tests for complete user workflows."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import create_app
from app.models.user import User
from app.models.link import Link
from app.models.allow_list_entry import AllowListEntry
from app.services.link_service import LinkService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.exceptions import ValidationError, ForbiddenError, NotFoundError, ConflictError


# Module-level fixture for test client
@pytest.fixture
async def client():
    """Create a test client for the Quart app."""
    app = await create_app()
    app.config["SECRET_KEY"] = "test-secret-key"
    async with app.test_client() as client:
        yield client


# ============================================================================
# OAuth Flow Integration Tests
# ============================================================================


class TestOAuthFlowIntegration:
    """Test complete OAuth flows and user registration."""

    async def test_oauth_callback_with_new_user(self, db_session: AsyncSession):
        """Test OAuth callback creates a new user on first login."""
        auth_service = AuthService(db_session)

        # Create user from OAuth info
        user, created = await auth_service.get_or_create_user_from_oauth(
            provider="google",
            provider_user_id="google_12345",
            provider_email="newuser@gmail.com",
            full_name="New User",
            avatar_url="https://example.com/avatar.jpg",
        )

        assert user is not None
        assert user.email == "newuser@gmail.com"
        assert user.full_name == "New User"
        assert created is True

    async def test_oauth_callback_with_existing_user(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test OAuth callback retrieves existing user on subsequent login."""
        auth_service = AuthService(db_session)

        # Link OAuth account to existing user
        oauth_account = await auth_service.link_oauth_account(
            user_id=test_user.id,
            provider="google",
            provider_user_id="google_123",
            provider_email="test@gmail.com",
            access_token="token_123",
        )

        assert oauth_account is not None
        assert oauth_account.provider == "google"

        # Retrieve user via OAuth on subsequent login
        user, created = await auth_service.get_or_create_user_from_oauth(
            provider="google",
            provider_user_id="google_123",
            provider_email="test@gmail.com",
        )
        assert user.id == test_user.id
        assert created is False

    async def test_multiple_oauth_providers_per_user(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test a user can link multiple OAuth providers."""
        auth_service = AuthService(db_session)

        # Link Google
        google_account = await auth_service.link_oauth_account(
            user_id=test_user.id,
            provider="google",
            provider_user_id="google_123",
            provider_email="test@gmail.com",
            access_token="google_token",
        )

        # Link GitHub
        github_account = await auth_service.link_oauth_account(
            user_id=test_user.id,
            provider="github",
            provider_user_id="github_456",
            provider_email="test@github.com",
            access_token="github_token",
        )

        assert google_account.provider == "google"
        assert github_account.provider == "github"

        # Verify both accounts belong to same user
        accounts = await auth_service.get_user_oauth_accounts(test_user.id)
        assert len(accounts) == 2

    async def test_oauth_account_linking_fails_if_already_linked(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that linking same OAuth account twice fails with ConflictError."""
        auth_service = AuthService(db_session)

        # Link first time
        await auth_service.link_oauth_account(
            user_id=test_user.id,
            provider="google",
            provider_user_id="google_123",
            provider_email="test@gmail.com",
            access_token="token_123",
        )

        # Try to link again - should fail
        with pytest.raises(ConflictError):
            await auth_service.link_oauth_account(
                user_id=test_user.id,
                provider="google",
                provider_user_id="google_123",
                provider_email="test@gmail.com",
                access_token="token_456",
            )


# ============================================================================
# Link Creation & Redirect Workflow Tests
# ============================================================================


class TestLinkCreationAndRedirectWorkflow:
    """Test complete link creation and redirect workflows."""

    async def test_user_creates_public_link_and_retrieves(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test user can create a public link and retrieve it."""
        link_service = LinkService(db_session)

        # User creates a public link
        link = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/very/long/url",
            slug="mylink",
            is_public=True,
        )

        assert link.slug == "mylink"
        assert link.is_public is True
        assert link.hit_count == 0

        # Retrieve the link
        retrieved_link = await link_service.get_link_by_slug("mylink")
        assert retrieved_link is not None
        assert retrieved_link.original_url == "https://example.com/very/long/url"

        # Increment hit count
        updated_link = await link_service.increment_hit_count("mylink")
        assert updated_link.hit_count == 1

    async def test_user_creates_private_link_with_email_allowlist(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test user can create private link with email allowlist."""
        link_service = LinkService(db_session)

        allowed_emails = ["alice@example.com", "bob@example.com"]
        link = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            is_public=False,
            allowed_emails=allowed_emails,
        )

        assert link.is_public is False
        assert link.get_allowed_emails() == allowed_emails

    async def test_multiple_users_create_different_links(
        self, db_session: AsyncSession
    ):
        """Test multiple users can create links with different slugs."""
        user_service = UserService(db_session)
        link_service = LinkService(db_session)

        # Create user 1
        user1 = await user_service.create_user(
            email="user1@example.com", full_name="User One"
        )

        # Create user 2
        user2 = await user_service.create_user(
            email="user2@example.com", full_name="User Two"
        )

        # User 1 creates a link
        link1 = await link_service.create_link(
            user_id=user1.id,
            original_url="https://example.com/user1",
            slug="u1link",
            is_public=True,
        )

        # User 2 creates a different link
        link2 = await link_service.create_link(
            user_id=user2.id,
            original_url="https://example.com/user2",
            slug="u2link",
            is_public=True,
        )

        assert link1.user_id == user1.id
        assert link2.user_id == user2.id
        assert link1.slug != link2.slug

    async def test_duplicate_slug_rejected(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that duplicate slugs are rejected."""
        link_service = LinkService(db_session)

        # Create first link
        await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/url1",
            slug="duplicate",
            is_public=True,
        )

        # Try to create second link with same slug
        with pytest.raises(ConflictError):
            await link_service.create_link(
                user_id=test_user.id,
                original_url="https://example.com/url2",
                slug="duplicate",
                is_public=True,
            )

    async def test_user_can_update_own_link(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test user can update their own link."""
        link_service = LinkService(db_session)

        # Create link
        link = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/original",
            slug="mylink",
            is_public=True,
        )

        # Update the link
        updated_link = await link_service.update_link(
            link_id=link.id,
            user_id=test_user.id,
            original_url="https://example.com/updated",
            is_public=False,
        )

        assert updated_link.original_url == "https://example.com/updated"
        assert updated_link.is_public is False

    async def test_user_cannot_update_others_link(
        self, db_session: AsyncSession
    ):
        """Test user cannot update another user's link."""
        user_service = UserService(db_session)
        link_service = LinkService(db_session)

        # Create two users
        user1 = await user_service.create_user(
            email="user1@example.com", full_name="User 1"
        )
        user2 = await user_service.create_user(
            email="user2@example.com", full_name="User 2"
        )

        # User1 creates a link
        link = await link_service.create_link(
            user_id=user1.id,
            original_url="https://example.com/link",
            slug="link123",
            is_public=True,
        )

        # User2 tries to update user1's link
        with pytest.raises(ForbiddenError):
            await link_service.update_link(
                link_id=link.id,
                user_id=user2.id,
                original_url="https://example.com/hacked",
            )

    async def test_user_can_delete_own_link(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test user can delete their own link."""
        link_service = LinkService(db_session)

        # Create link
        link = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/deleteme",
            slug="delete123",
            is_public=True,
        )

        # Delete the link
        await link_service.delete_link(link_id=link.id, user_id=test_user.id)

        # Verify link is deleted
        deleted_link = await link_service.get_link_by_slug("delete123")
        assert deleted_link is None


# ============================================================================
# Private Link Access Control Tests
# ============================================================================


class TestPrivateLinkAccessControl:
    """Test access control for private links."""

    async def test_public_link_accessible_to_anyone(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test public links are accessible to anyone."""
        link_service = LinkService(db_session)

        # Create public link
        link = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/public",
            slug="public",
            is_public=True,
        )

        # Anyone can access
        can_access = await link_service.check_link_access(link, user_email=None)
        assert can_access is True

    async def test_private_link_requires_email_allowlist(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test private link with email allowlist enforcement."""
        link_service = LinkService(db_session)

        allowed_emails = ["alice@example.com", "bob@example.com"]
        link = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="private",
            is_public=False,
            allowed_emails=allowed_emails,
        )

        # Allowed user can access
        can_access_alice = await link_service.check_link_access(
            link, user_email="alice@example.com"
        )
        assert can_access_alice is True

        # Unallowed user cannot access
        can_access_charlie = await link_service.check_link_access(
            link, user_email="charlie@example.com"
        )
        assert can_access_charlie is False


# ============================================================================
# Admin Operations Integration Tests
# ============================================================================


class TestAdminOperationsIntegration:
    """Test admin operations and user management workflows."""

    async def test_admin_can_promote_user(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test admin can promote user to admin."""
        user_service = UserService(db_session)

        # Verify user is not admin
        user = await user_service.get_user(test_user.id)
        assert user.is_admin is False

        # Promote user
        promoted_user = await user_service.promote_to_admin(test_user.id)
        assert promoted_user.is_admin is True

    async def test_admin_can_demote_admin(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test admin can demote another admin."""
        user_service = UserService(db_session)

        # Verify user is admin
        user = await user_service.get_user(test_admin_user.id)
        assert user.is_admin is True

        # Demote admin
        demoted_user = await user_service.demote_from_admin(test_admin_user.id)
        assert demoted_user.is_admin is False

    async def test_admin_can_block_user(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test admin can block a user."""
        user_service = UserService(db_session)

        # Verify user is not blocked
        user = await user_service.get_user(test_user.id)
        assert user.is_blocked is False

        # Block user
        blocked_user = await user_service.block_user(test_user.id)
        assert blocked_user.is_blocked is True

    async def test_admin_can_unblock_user(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test admin can unblock a user."""
        user_service = UserService(db_session)

        # Block user first
        await user_service.block_user(test_user.id)

        # Unblock user
        unblocked_user = await user_service.unblock_user(test_user.id)
        assert unblocked_user.is_blocked is False

    async def test_admin_can_delete_user(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test admin can delete a user and cascade-delete their links."""
        user_service = UserService(db_session)
        link_service = LinkService(db_session)

        # Create a link for the user
        link = await link_service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/link",
            slug="link",
            is_public=True,
        )

        # Verify user and link exist
        user = await user_service.get_user(test_user.id)
        assert user is not None

        # Delete user
        await user_service.delete_user(test_user.id)

        # Verify user is deleted
        deleted_user = await user_service.get_user(test_user.id)
        assert deleted_user is None

        # Verify user's links are cascade-deleted
        deleted_link = await link_service.get_link_by_slug("link")
        assert deleted_link is None

    async def test_admin_can_manage_allow_list(self, db_session: AsyncSession):
        """Test admin can add emails to allow-list."""
        # Add to allow-list
        entry = AllowListEntry(email="test@example.com")
        db_session.add(entry)
        await db_session.commit()

        # Verify entry exists
        result = await db_session.get(AllowListEntry, entry.id)
        assert result is not None
        assert result.email == "test@example.com"


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================


class TestEndToEndUserWorkflow:
    """Test complete user workflows from signup to link creation."""

    async def test_complete_user_signup_and_link_creation_workflow(
        self, db_session: AsyncSession
    ):
        """Test: User registers via OAuth → Creates link → Link is retrieved."""
        auth_service = AuthService(db_session)
        link_service = LinkService(db_session)

        # Step 1: User logs in via OAuth (new user)
        user, created = await auth_service.get_or_create_user_from_oauth(
            provider="google",
            provider_user_id="google_workflow_1",
            provider_email="newworkflow@gmail.com",
            full_name="Workflow User",
        )

        assert user is not None
        assert user.email == "newworkflow@gmail.com"
        assert created is True

        # Step 2: User creates a link
        link = await link_service.create_link(
            user_id=user.id,
            original_url="https://github.com/anomalyco/opencode",
            slug="opencode",
            is_public=True,
        )

        assert link.slug == "opencode"
        assert link.user_id == user.id

        # Step 3: Anyone can access the link
        retrieved_link = await link_service.get_link_by_slug("opencode")
        assert retrieved_link is not None
        assert (
            retrieved_link.original_url == "https://github.com/anomalyco/opencode"
        )

        # Step 4: Track hit
        updated_link = await link_service.increment_hit_count("opencode")
        assert updated_link.hit_count == 1

    async def test_user_creates_multiple_links_with_different_access_levels(
        self, db_session: AsyncSession
    ):
        """Test: User creates public, private, and email-restricted links."""
        user_service = UserService(db_session)
        link_service = LinkService(db_session)

        # User registers
        user = await user_service.create_user(
            email="multilink@example.com", full_name="Multi Link User"
        )

        # Create public link
        public_link = await link_service.create_link(
            user_id=user.id,
            original_url="https://example.com/public",
            slug="pub",
            is_public=True,
        )

        # Create private link
        private_link = await link_service.create_link(
            user_id=user.id,
            original_url="https://example.com/private",
            slug="priv",
            is_public=False,
        )

        # Create email-restricted link
        restricted_link = await link_service.create_link(
            user_id=user.id,
            original_url="https://example.com/restricted",
            slug="restricted",
            is_public=False,
            allowed_emails=["vip@example.com"],
        )

        assert public_link.is_public is True
        assert private_link.is_public is False
        assert restricted_link.is_public is False
        assert restricted_link.get_allowed_emails() == ["vip@example.com"]

    async def test_admin_manages_users_and_their_links(
        self, db_session: AsyncSession
    ):
        """Test: Admin can view, manage, and delete users and their links."""
        user_service = UserService(db_session)
        link_service = LinkService(db_session)

        # Create admin and regular user
        admin = await user_service.create_user(
            email="admin@example.com", full_name="Admin User"
        )
        await user_service.promote_to_admin(admin.id)

        user = await user_service.create_user(
            email="regularuser@example.com", full_name="Regular User"
        )

        # User creates links
        link1 = await link_service.create_link(
            user_id=user.id,
            original_url="https://example.com/link1",
            slug="link1",
            is_public=True,
        )

        link2 = await link_service.create_link(
            user_id=user.id,
            original_url="https://example.com/link2",
            slug="link2",
            is_public=False,
        )

        # Admin gets all user links
        user_links = await link_service.get_user_links(
            user.id, include_private=True
        )
        assert len(user_links) == 2

        # Admin blocks user
        blocked_user = await user_service.block_user(user.id)
        assert blocked_user.is_blocked is True

        # Admin deletes user (cascade deletes links)
        await user_service.delete_user(user.id)

        # Verify user and links are deleted
        deleted_user = await user_service.get_user(user.id)
        assert deleted_user is None

        # Verify user's links are cascade-deleted
        deleted_link1 = await link_service.get_link_by_slug("link1")
        assert deleted_link1 is None


# ============================================================================
# Admin Workflow Tests
# ============================================================================


class TestAdminEndToEndWorkflow:
    """Test complete admin workflows."""

    async def test_admin_manages_allow_list_and_users(
        self, db_session: AsyncSession
    ):
        """Test: Admin adds emails to allow-list and manages users."""
        # Add emails to allow-list
        allowed_emails = ["user1@corp.com", "user2@corp.com", "user3@corp.com"]

        for email in allowed_emails:
            entry = AllowListEntry(email=email)
            db_session.add(entry)

        await db_session.commit()

        # Verify entries were added
        query_result = await db_session.get(AllowListEntry, 1)
        assert query_result is not None

    async def test_admin_views_system_statistics(
        self, db_session: AsyncSession
    ):
        """Test: Admin can view aggregate system statistics."""
        user_service = UserService(db_session)
        link_service = LinkService(db_session)

        # Create multiple users
        user1 = await user_service.create_user(
            email="user1stats@example.com", full_name="User 1"
        )
        user2 = await user_service.create_user(
            email="user2stats@example.com", full_name="User 2"
        )

        # Create multiple links
        link1 = await link_service.create_link(
            user_id=user1.id,
            original_url="https://example.com/u1l1",
            slug="u1l1",
            is_public=True,
        )

        link2 = await link_service.create_link(
            user_id=user2.id,
            original_url="https://example.com/u2l1",
            slug="u2l1",
            is_public=True,
        )

        # Get total links for each user
        user1_links = await link_service.get_user_links(user1.id)
        user2_links = await link_service.get_user_links(user2.id)
        assert len(user1_links) >= 1
        assert len(user2_links) >= 1
