"""drop username from users

Revision ID: 20260906_02
Revises: 20260727_01
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = "20260906_02"
down_revision = "20260727_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_constraint("users_username_key", "users", type_="unique")
    op.drop_column("users", "username")


def downgrade() -> None:
    # nullable=True (not the original NOT NULL): a populated `users` table
    # has no username values to backfill, and this path would be paired
    # with reverting the application code anyway.
    op.add_column("users", sa.Column("username", sa.String(100), nullable=True))
    op.create_unique_constraint("users_username_key", "users", ["username"])
    op.create_index("ix_users_username", "users", ["username"])
