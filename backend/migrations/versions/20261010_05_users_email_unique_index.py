"""users.email: one unique index instead of a unique constraint plus a plain index

Revision ID: 20261010_05
Revises: 20261009_04
Create Date: 2026-10-10
"""
from alembic import op

revision = "20261010_05"
down_revision = "20261009_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The model declares unique=True, index=True, which SQLAlchemy emits as a single UNIQUE INDEX.
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.drop_index("ix_users_email", table_name="users")
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.create_index("ix_users_email", "users", ["email"])
    op.create_unique_constraint("users_email_key", "users", ["email"])
