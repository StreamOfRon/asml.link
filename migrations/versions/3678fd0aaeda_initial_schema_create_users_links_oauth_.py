"""Initial schema: create users, links, oauth_accounts, and allow_list_entries tables

Revision ID: 3678fd0aaeda
Revises:
Create Date: 2026-02-24 19:39:01.890249

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3678fd0aaeda"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # Create allow_list_entries table
    op.create_table(
        "allow_list_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(
        op.f("ix_allow_list_entries_email"), "allow_list_entries", ["email"], unique=True
    )

    # Create links table
    op.create_table(
        "links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("original_url", sa.String(2048), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("allowed_emails", sa.String(4096), nullable=True),
        sa.Column("hit_count", sa.Integer(), nullable=False),
        sa.Column("last_hit_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_links_slug"), "links", ["slug"], unique=True)
    op.create_index(op.f("ix_links_user_id"), "links", ["user_id"])

    # Create oauth_accounts table
    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column("provider_email", sa.String(255), nullable=True),
        sa.Column("access_token", sa.String(2048), nullable=True),
        sa.Column("refresh_token", sa.String(2048), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_oauth_accounts_provider"), "oauth_accounts", ["provider"])
    op.create_index(op.f("ix_oauth_accounts_user_id"), "oauth_accounts", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop oauth_accounts table
    op.drop_index(op.f("ix_oauth_accounts_user_id"), table_name="oauth_accounts")
    op.drop_index(op.f("ix_oauth_accounts_provider"), table_name="oauth_accounts")
    op.drop_table("oauth_accounts")

    # Drop links table
    op.drop_index(op.f("ix_links_user_id"), table_name="links")
    op.drop_index(op.f("ix_links_slug"), table_name="links")
    op.drop_table("links")

    # Drop allow_list_entries table
    op.drop_index(op.f("ix_allow_list_entries_email"), table_name="allow_list_entries")
    op.drop_table("allow_list_entries")

    # Drop users table
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
