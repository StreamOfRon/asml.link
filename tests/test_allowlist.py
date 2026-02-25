"""Integration tests for allow-list management API endpoints."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allow_list_entry import AllowListEntry
from app.models.user import User
from app.services.link_service import LinkService
from app.utils.validators import is_valid_email, normalize_email


class TestAllowListEndpoints:
    """Tests for allow-list management API endpoints."""

    async def test_add_to_allowlist_basic(self, db_session: AsyncSession, test_admin_user: User):
        """Test adding a single email to the allow-list."""
        # Create allow-list entry
        email = normalize_email("alice@example.com")
        entry = AllowListEntry(email=email)
        db_session.add(entry)
        await db_session.commit()
        await db_session.refresh(entry)

        assert entry.id is not None
        assert entry.email == "alice@example.com"
        assert entry.created_at is not None

    async def test_add_to_allowlist_case_normalization(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test that emails are normalized to lowercase."""
        # Create allow-list entry with mixed case
        email = normalize_email("Alice@Example.COM")
        entry = AllowListEntry(email=email)
        db_session.add(entry)
        await db_session.commit()
        await db_session.refresh(entry)

        # Normalized should be lowercase
        assert entry.email == "alice@example.com"

    async def test_add_to_allowlist_whitespace_normalization(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test that whitespace is stripped from emails."""
        # Create allow-list entry with whitespace
        email = normalize_email("  alice@example.com  ")
        entry = AllowListEntry(email=email)
        db_session.add(entry)
        await db_session.commit()
        await db_session.refresh(entry)

        # Whitespace should be stripped
        assert entry.email == "alice@example.com"

    async def test_add_duplicate_to_allowlist(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test that adding duplicate email raises constraint error."""
        email = normalize_email("alice@example.com")

        # Add first entry
        entry1 = AllowListEntry(email=email)
        db_session.add(entry1)
        await db_session.commit()

        # Try to add duplicate
        entry2 = AllowListEntry(email=email)
        db_session.add(entry2)

        # This should fail with a constraint error
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_list_allowlist(self, db_session: AsyncSession, test_admin_user: User):
        """Test listing all emails in allow-list."""
        emails = ["alice@example.com", "bob@example.com", "charlie@example.com"]

        for email in emails:
            normalized = normalize_email(email)
            entry = AllowListEntry(email=normalized)
            db_session.add(entry)

        await db_session.commit()

        # Fetch all entries
        result = await db_session.execute(select(AllowListEntry))
        entries = result.scalars().all()

        assert len(entries) >= 3
        stored_emails = {e.email for e in entries}
        for email in emails:
            assert email in stored_emails

    async def test_remove_from_allowlist(self, db_session: AsyncSession, test_admin_user: User):
        """Test removing an email from allow-list."""
        email = normalize_email("alice@example.com")

        # Add entry
        entry = AllowListEntry(email=email)
        db_session.add(entry)
        await db_session.commit()
        entry_id = entry.id

        # Remove entry
        result = await db_session.execute(
            select(AllowListEntry).where(AllowListEntry.id == entry_id)
        )
        stored_entry = result.scalar()
        assert stored_entry is not None

        await db_session.delete(stored_entry)
        await db_session.commit()

        # Verify it's deleted
        result = await db_session.execute(
            select(AllowListEntry).where(AllowListEntry.id == entry_id)
        )
        deleted_entry = result.scalar()
        assert deleted_entry is None

    async def test_remove_nonexistent_from_allowlist(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test removing non-existent email from allow-list."""
        email = normalize_email("alice@example.com")

        # Try to remove email that doesn't exist
        result = await db_session.execute(
            select(AllowListEntry).where(AllowListEntry.email == email)
        )
        entry = result.scalar()
        assert entry is None  # Entry doesn't exist

    async def test_allowlist_used_for_private_links(
        self, db_session: AsyncSession, test_user: User, test_admin_user: User
    ):
        """Test that allow-list is used for private link access control."""
        service = LinkService(db_session)

        # Create private link
        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="priv123",
            is_public=False,
        )

        # Add email to allow-list for this link
        allowed_email = "alice@example.com"
        link = await service.update_link(
            link_id=link.id,
            user_id=test_user.id,
            allowed_emails=[allowed_email],
        )

        # Verify access is granted for allowed email
        access = await service.check_link_access(link, user_email=allowed_email)
        assert access is True

        # Verify access is denied for other email
        access = await service.check_link_access(link, user_email="bob@example.com")
        assert access is False

    async def test_allowlist_case_insensitive_lookup(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test that allow-list lookup is case-insensitive."""
        email = normalize_email("Alice@Example.COM")

        # Add entry
        entry = AllowListEntry(email=email)
        db_session.add(entry)
        await db_session.commit()

        # Look up with different cases
        result1 = await db_session.execute(
            select(AllowListEntry).where(AllowListEntry.email == email)
        )
        entry1 = result1.scalar()
        assert entry1 is not None

        result2 = await db_session.execute(
            select(AllowListEntry).where(AllowListEntry.email == "ALICE@EXAMPLE.COM".lower())
        )
        entry2 = result2.scalar()
        assert entry2 is not None

        assert entry1.id == entry2.id

    async def test_allowlist_pagination(self, db_session: AsyncSession, test_admin_user: User):
        """Test pagination of allow-list entries."""
        # Add many emails
        for i in range(15):
            entry = AllowListEntry(email=f"user{i}@example.com")
            db_session.add(entry)

        await db_session.commit()

        # Get first page (10 items)
        result = await db_session.execute(select(AllowListEntry).limit(10).offset(0))
        page1 = result.scalars().all()
        assert len(page1) == 10

        # Get second page (5 items)
        result = await db_session.execute(select(AllowListEntry).limit(10).offset(10))
        page2 = result.scalars().all()
        assert len(page2) >= 5

    async def test_allowlist_email_validation(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test that invalid emails are rejected."""
        # Invalid email formats
        invalid_emails = [
            "notanemail",
            "user@",
            "@example.com",
            "user @example.com",
            "user@.com",
        ]

        for email in invalid_emails:
            assert is_valid_email(email) is False

    async def test_allowlist_valid_email_formats(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test that valid emails are accepted."""
        # Valid email formats
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user123@sub.example.com",
        ]

        for email in valid_emails:
            assert is_valid_email(email) is True

    async def test_allowlist_timestamps(self, db_session: AsyncSession, test_admin_user: User):
        """Test that allow-list entries have creation timestamps."""
        entry = AllowListEntry(email=normalize_email("alice@example.com"))
        db_session.add(entry)
        await db_session.commit()
        await db_session.refresh(entry)

        assert entry.created_at is not None

    async def test_allowlist_multiple_emails_same_link(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test private link with multiple allowed emails."""
        service = LinkService(db_session)

        allowed_emails = ["alice@example.com", "bob@example.com", "charlie@example.com"]

        link = await service.create_link(
            user_id=test_user.id,
            original_url="https://example.com/private",
            slug="multi123",
            is_public=False,
            allowed_emails=allowed_emails,
        )

        # All allowed emails should have access
        for email in allowed_emails:
            access = await service.check_link_access(link, user_email=email)
            assert access is True

        # Others should not have access
        access = await service.check_link_access(link, user_email="denied@example.com")
        assert access is False

    async def test_allowlist_remove_and_readd(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test removing and re-adding an email to allow-list."""
        email = normalize_email("alice@example.com")

        # Add entry
        entry = AllowListEntry(email=email)
        db_session.add(entry)
        await db_session.commit()

        # Remove entry
        result = await db_session.execute(
            select(AllowListEntry).where(AllowListEntry.email == email)
        )
        stored_entry = result.scalar()
        await db_session.delete(stored_entry)
        await db_session.commit()

        # Re-add entry
        entry2 = AllowListEntry(email=email)
        db_session.add(entry2)
        await db_session.commit()
        await db_session.refresh(entry2)

        assert entry2.id is not None
        assert entry2.email == email

    async def test_allowlist_special_characters_in_email(
        self, db_session: AsyncSession, test_admin_user: User
    ):
        """Test allow-list with special characters in email."""
        email = normalize_email("user+tag@example.co.uk")

        entry = AllowListEntry(email=email)
        db_session.add(entry)
        await db_session.commit()
        await db_session.refresh(entry)

        assert entry.email == email
