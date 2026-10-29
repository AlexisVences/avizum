"""message_reviews: answers an admin has reviewed in the quality queue

Revision ID: 20261025_13
Revises: 20261025_12
Create Date: 2026-10-26
"""
from alembic import op
import sqlalchemy as sa

revision = "20261025_13"
down_revision = "20261025_12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "message_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False, unique=True,
        ),
        sa.Column(
            "reviewer_id", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("message_reviews")
