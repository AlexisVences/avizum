"""legal_sanctions.applies_to: penalties that the text restricts to a kind of vehicle or situation

Revision ID: 20261015_08
Revises: 20261015_07
Create Date: 2026-10-15
"""
from alembic import op
import sqlalchemy as sa

revision = "20261015_08"
down_revision = "20261015_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("legal_sanctions", sa.Column("applies_to", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("legal_sanctions", "applies_to")
