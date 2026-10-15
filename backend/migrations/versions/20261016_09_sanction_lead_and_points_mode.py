"""legal_sanctions.lead_text and points_mode: polarity of the conduct and whether licence/plate points add up

Revision ID: 20261016_09
Revises: 20261015_08
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa

revision = "20261016_09"
down_revision = "20261015_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("legal_sanctions", sa.Column("lead_text", sa.Text(), nullable=True))
    op.add_column("legal_sanctions", sa.Column("points_mode", sa.String(30), nullable=True))


def downgrade() -> None:
    op.drop_column("legal_sanctions", "points_mode")
    op.drop_column("legal_sanctions", "lead_text")
