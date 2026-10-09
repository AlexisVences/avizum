"""official sources registry and authorized agents rebuilt from Acuerdo 30/2026

Revision ID: 20261008_03
Revises: 20260906_02
Create Date: 2026-10-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261008_03"
down_revision = "20260906_02"
branch_labels = None
depends_on = None

authorization_type = postgresql.ENUM("via_publica", "sistemas_tecnologicos", name="agent_authorization_type", create_type=False)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "official_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("last_reform_date", sa.Date(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("slug", "sha256", name="uq_official_sources_slug_sha256"),
    )
    op.create_index("ix_official_sources_slug", "official_sources", ["slug"])
    op.create_index("uq_official_sources_current_slug", "official_sources", ["slug"], unique=True, postgresql_where=sa.text("is_current"))

    # The legacy registry (Acuerdo 40/2024, no source tracking) is discarded; lookups keep their history.
    op.drop_constraint("agent_lookups_agent_id_fkey", "agent_lookups", type_="foreignkey")
    op.execute("UPDATE agent_lookups SET agent_id = NULL")
    op.drop_index("ix_authorized_agents_plate", table_name="authorized_agents")
    op.drop_table("authorized_agents")

    bind = op.get_bind()
    postgresql.ENUM("via_publica", "sistemas_tecnologicos", name="agent_authorization_type").create(bind, checkfirst=True)
    op.create_table(
        "authorized_agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plate", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("name_search", sa.String(255), nullable=False),
        sa.Column("authorization_type", authorization_type, nullable=False),
        sa.Column("corporation", sa.String(100), nullable=True),
        sa.Column("alcaldias", postgresql.ARRAY(sa.String(100)), nullable=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("official_sources.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("plate", "authorization_type", name="uq_authorized_agents_plate_type"),
    )
    op.create_index("ix_authorized_agents_plate", "authorized_agents", ["plate"])
    op.create_index("ix_authorized_agents_source_id", "authorized_agents", ["source_id"])
    op.create_index(
        "ix_authorized_agents_name_search_trgm", "authorized_agents", ["name_search"],
        postgresql_using="gin", postgresql_ops={"name_search": "gin_trgm_ops"},
    )
    op.create_foreign_key("agent_lookups_agent_id_fkey", "agent_lookups", "authorized_agents", ["agent_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("agent_lookups_agent_id_fkey", "agent_lookups", type_="foreignkey")
    op.execute("UPDATE agent_lookups SET agent_id = NULL")
    op.drop_table("authorized_agents")
    postgresql.ENUM(name="agent_authorization_type").drop(op.get_bind(), checkfirst=True)
    op.drop_table("official_sources")
    op.create_table(
        "authorized_agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plate", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("plate"),
    )
    op.create_index("ix_authorized_agents_plate", "authorized_agents", ["plate"])
    op.create_foreign_key("agent_lookups_agent_id_fkey", "agent_lookups", "authorized_agents", ["agent_id"], ["id"], ondelete="SET NULL")
