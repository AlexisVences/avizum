"""legal_sanctions.context_text: the exemptions or the referenced paragraph a clause depends on

Revision ID: 20261016_10
Revises: 20261016_09
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa

revision = "20261016_10"
down_revision = "20261016_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("legal_sanctions", sa.Column("context_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("legal_sanctions", "context_text")
