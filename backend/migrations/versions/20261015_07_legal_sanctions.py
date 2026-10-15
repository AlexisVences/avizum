"""legal_sanctions: structured penalties per conduct, served only once a person verified them

Revision ID: 20261015_07
Revises: 20261010_06
Create Date: 2026-10-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261015_07"
down_revision = "20261010_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    status = postgresql.ENUM("pending", "verified", "rejected", "stale", name="sanction_status", create_type=False)
    status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "legal_sanctions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("chunk_id", sa.Integer(), sa.ForeignKey("legal_chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ordinal", sa.SmallInteger(), nullable=False),
        sa.Column("source_slug", sa.String(100), nullable=False),
        sa.Column("article", sa.String(50), nullable=False),
        sa.Column("fraction", sa.String(50), nullable=True),
        sa.Column("inciso", sa.String(20), nullable=True),
        sa.Column("conduct_text", sa.Text(), nullable=False),
        sa.Column("clause_text", sa.Text(), nullable=False),
        sa.Column("uma_min", sa.Numeric(8, 2), nullable=True),
        sa.Column("uma_mid", sa.Numeric(8, 2), nullable=True),
        sa.Column("uma_max", sa.Numeric(8, 2), nullable=True),
        sa.Column("points_license", sa.SmallInteger(), nullable=True),
        sa.Column("points_plate", sa.SmallInteger(), nullable=True),
        sa.Column("other_consequences", sa.Text(), nullable=True),
        sa.Column("chunk_hash", sa.String(64), nullable=False),
        sa.Column("extractor_version", sa.String(30), nullable=False),
        sa.Column("status", status, nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.String(100), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("chunk_id", "ordinal", name="uq_legal_sanctions_chunk_ordinal"),
        sa.CheckConstraint(
            "(uma_min IS NULL AND uma_mid IS NULL AND uma_max IS NULL) OR "
            "(uma_min IS NOT NULL AND uma_min > 0 AND (uma_mid IS NULL OR uma_mid >= uma_min) "
            "AND (uma_max IS NULL OR uma_max >= COALESCE(uma_mid, uma_min)))",
            name="ck_legal_sanctions_uma_ascending",
        ),
        sa.CheckConstraint("points_license IS NULL OR points_license >= 0", name="ck_legal_sanctions_points_license"),
        sa.CheckConstraint("points_plate IS NULL OR points_plate >= 0", name="ck_legal_sanctions_points_plate"),
        sa.CheckConstraint("char_length(chunk_hash) = 64", name="ck_legal_sanctions_chunk_hash_len"),
    )
    op.create_index("ix_legal_sanctions_chunk_status", "legal_sanctions", ["chunk_id", "status"])
    op.create_index("ix_legal_sanctions_article", "legal_sanctions", ["source_slug", "article", "fraction"])


def downgrade() -> None:
    op.drop_table("legal_sanctions")
    postgresql.ENUM(name="sanction_status").drop(op.get_bind(), checkfirst=True)
