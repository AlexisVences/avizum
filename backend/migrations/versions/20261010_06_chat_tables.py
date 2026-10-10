"""chat: conversations, messages and message_feedback replace consultations, legal_responses and feedback

Destructive on purpose: the legacy consultation tables held no real data (spec "Datos previos"), and the new
assistant stores a whole conversation instead of one question and one answer.

Revision ID: 20261010_06
Revises: 20261010_05
Create Date: 2026-10-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261010_06"
down_revision = "20261010_05"
branch_labels = None
depends_on = None

message_role = postgresql.ENUM("user", "assistant", name="message_role", create_type=False)
message_status = postgresql.ENUM("complete", "error", "cancelled", name="message_status", create_type=False)


def upgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("legal_responses")
    op.drop_table("consultations")

    bind = op.get_bind()
    postgresql.ENUM("user", "assistant", name="message_role").create(bind, checkfirst=True)
    postgresql.ENUM("complete", "error", "cancelled", name="message_status").create(bind, checkfirst=True)

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_conversations_user_updated", "conversations", ["user_id", "updated_at"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", message_status, nullable=False, server_default="complete"),
        sa.Column("citations", postgresql.JSONB(), nullable=True),
        sa.Column("tool_calls", postgresql.JSONB(), nullable=True),
        sa.Column("model", sa.String(50), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at", "id"])

    op.create_table(
        "message_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("value IN (-1, 1)", name="ck_message_feedback_value"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_message_feedback_message_user"),
    )


def downgrade() -> None:
    op.drop_table("message_feedback")
    op.drop_table("messages")
    op.drop_table("conversations")
    bind = op.get_bind()
    postgresql.ENUM(name="message_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="message_role").drop(bind, checkfirst=True)

    op.create_table(
        "consultations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_consultations_user_id", "consultations", ["user_id"])
    op.create_table(
        "legal_responses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="general"),
        sa.Column("consultation_id", sa.Integer(), sa.ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, unique=True),
    )
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("response_id", sa.Integer(), sa.ForeignKey("legal_responses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating_range"),
        sa.UniqueConstraint("response_id", name="uq_feedback_response"),
    )
    op.create_index("ix_feedback_response_id", "feedback", ["response_id"])
