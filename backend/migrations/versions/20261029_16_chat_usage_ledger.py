"""chat_usage: append-only ledger behind the chat limits (cost cap and daily messages)

Usage used to be derived from `messages`, which a user could delete together with the conversation. The ledger has no
foreign key to conversations or messages, so deleting those never deletes usage.

Backfill (best effort, so the limits do not reset at deploy): one 'settled' row per USER message of the last 48 hours,
dated at the message, carrying the tokens of the assistant message that answers it (the first assistant message after
it and before the user's next question) when there is one. A question with no stored answer, or an answer without
tokens (cancelled, errored), keeps 0 tokens and therefore counts the reservation below, which is the same estimate
the app uses (12000 input / 1800 output tokens).

Revision ID: 20261029_16
Revises: 20261029_15
Create Date: 2026-10-29
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261029_16"
down_revision = "20261029_15"
branch_labels = None
depends_on = None

status = postgresql.ENUM("reserved", "settled", "cancelled", "error", name="chat_usage_status", create_type=False)


def upgrade() -> None:
    status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "chat_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("input_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("output_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reserved_input_tokens", sa.Integer(), nullable=False),
        sa.Column("reserved_output_tokens", sa.Integer(), nullable=False),
        sa.Column("status", status, nullable=False),
    )
    op.create_index("ix_chat_usage_user_created", "chat_usage", ["user_id", "created_at"])
    op.create_index("ix_chat_usage_created", "chat_usage", ["created_at"])
    op.execute(
        """
        INSERT INTO chat_usage (
            user_id, created_at, settled_at, input_tokens, output_tokens,
            reserved_input_tokens, reserved_output_tokens, status
        )
        SELECT c.user_id, m.created_at, m.created_at,
               COALESCE(a.input_tokens, 0), COALESCE(a.output_tokens, 0), 12000, 1800, 'settled'
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        LEFT JOIN LATERAL (
            SELECT x.input_tokens, x.output_tokens
            FROM messages x
            WHERE x.conversation_id = m.conversation_id
              AND x.role = 'assistant'
              AND (x.created_at, x.id) > (m.created_at, m.id)
              AND NOT EXISTS (
                  SELECT 1 FROM messages u
                  WHERE u.conversation_id = m.conversation_id AND u.role = 'user'
                    AND (u.created_at, u.id) > (m.created_at, m.id)
                    AND (u.created_at, u.id) < (x.created_at, x.id)
              )
            ORDER BY x.created_at, x.id
            LIMIT 1
        ) a ON true
        WHERE m.role = 'user' AND m.created_at >= now() - interval '48 hours'
        """
    )


def downgrade() -> None:
    op.drop_index("ix_chat_usage_created", table_name="chat_usage")
    op.drop_index("ix_chat_usage_user_created", table_name="chat_usage")
    op.drop_table("chat_usage")
    status.drop(op.get_bind(), checkfirst=True)
