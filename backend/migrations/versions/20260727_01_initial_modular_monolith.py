"""initial modular monolith schema

Revision ID: 20260727_01
Revises:
Create Date: 2026-07-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260727_01"
down_revision = None
branch_labels = None
depends_on = None

user_role = postgresql.ENUM("user", "admin", name="user_role", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM("user", "admin", name="user_role").create(bind, checkfirst=True)
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(100), nullable=False), sa.Column("first_name", sa.String(100), nullable=False), sa.Column("last_name", sa.String(100), nullable=False), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", user_role, nullable=False, server_default="user"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint("username"), sa.UniqueConstraint("email"))
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("authorized_agents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("plate", sa.String(50), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint("plate"))
    op.create_index("ix_authorized_agents_plate", "authorized_agents", ["plate"])
    op.create_table("agent_lookups", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("agent_id", sa.Integer(), sa.ForeignKey("authorized_agents.id", ondelete="SET NULL")))
    op.create_index("ix_agent_lookups_user_id", "agent_lookups", ["user_id"])
    op.create_index("ix_agent_lookups_agent_id", "agent_lookups", ["agent_id"])
    op.create_table("consultations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("question", sa.Text(), nullable=False), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")))
    op.create_index("ix_consultations_user_id", "consultations", ["user_id"])
    op.create_table("legal_responses", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("text", sa.Text(), nullable=False), sa.Column("category", sa.String(50), nullable=False, server_default="general"), sa.Column("consultation_id", sa.Integer(), sa.ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False), sa.UniqueConstraint("consultation_id"))
    op.create_table("feedback", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("rating", sa.Integer(), nullable=False), sa.Column("response_id", sa.Integer(), sa.ForeignKey("legal_responses.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating_range"), sa.UniqueConstraint("response_id", name="uq_feedback_response"))
    op.create_index("ix_feedback_response_id", "feedback", ["response_id"])


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("legal_responses")
    op.drop_table("consultations")
    op.drop_table("agent_lookups")
    op.drop_table("authorized_agents")
    op.drop_table("users")
    postgresql.ENUM("user", "admin", name="user_role").drop(op.get_bind(), checkfirst=True)
