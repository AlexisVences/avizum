"""legal_chunks: pgvector embeddings plus Spanish full-text search

Revision ID: 20261009_04
Revises: 20261008_03
Create Date: 2026-10-09
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "20261009_04"
down_revision = "20261008_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    # unaccent() is only STABLE; generated columns need IMMUTABLE, so wrap it with a pinned dictionary.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION immutable_unaccent(text) RETURNS text
        LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
        AS $$ SELECT public.unaccent('public.unaccent', $1) $$
        """
    )
    op.create_table(
        "legal_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("official_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("article", sa.String(50), nullable=False),
        sa.Column("fraction", sa.String(50), nullable=True),
        sa.Column("heading_path", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column(
            "tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('spanish', immutable_unaccent(heading_path || ' ' || text))", persisted=True),
            nullable=False,
        ),
    )
    op.create_index("ix_legal_chunks_source_article", "legal_chunks", ["source_id", "article"])
    op.create_index("ix_legal_chunks_tsv", "legal_chunks", ["tsv"], postgresql_using="gin")
    op.create_index(
        "ix_legal_chunks_embedding_hnsw", "legal_chunks", ["embedding"],
        postgresql_using="hnsw", postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_table("legal_chunks")
    op.execute("DROP FUNCTION IF EXISTS immutable_unaccent(text)")
