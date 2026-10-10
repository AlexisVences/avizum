import enum
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, Computed, Date, DateTime, Enum, ForeignKey, Index, Integer, SmallInteger, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class User(Timestamped, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e]), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class AuthorizationType(str, enum.Enum):
    VIA_PUBLICA = "via_publica"
    SISTEMAS_TECNOLOGICOS = "sistemas_tecnologicos"


class OfficialSource(Base):
    """One downloaded version of an official document; exactly one version per slug is current."""

    __tablename__ = "official_sources"
    __table_args__ = (
        UniqueConstraint("slug", "sha256", name="uq_official_sources_slug_sha256"),
        Index("uq_official_sources_current_slug", "slug", unique=True, postgresql_where=text("is_current")),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(1000))
    sha256: Mapped[str] = mapped_column(String(64))
    last_reform_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_current: Mapped[bool] = mapped_column(default=True, server_default=text("true"), nullable=False)


EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small


class LegalChunk(Base):
    """A retrievable piece of an official source: one article, or one fraction of a long article."""

    __tablename__ = "legal_chunks"
    __table_args__ = (
        Index("ix_legal_chunks_source_article", "source_id", "article"),
        Index("ix_legal_chunks_tsv", "tsv", postgresql_using="gin"),
        Index(
            "ix_legal_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("official_sources.id", ondelete="CASCADE"), nullable=False)
    article: Mapped[str] = mapped_column(String(50))  # "30", "30 Bis"
    fraction: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "II"
    heading_path: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    page_start: Mapped[int] = mapped_column(Integer)
    page_end: Mapped[int] = mapped_column(Integer)
    token_count: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    tsv: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('spanish', immutable_unaccent(heading_path || ' ' || text))", persisted=True),
    )


class AuthorizedAgent(Timestamped, Base):
    __tablename__ = "authorized_agents"
    __table_args__ = (
        UniqueConstraint("plate", "authorization_type", name="uq_authorized_agents_plate_type"),
        Index(
            "ix_authorized_agents_name_search_trgm",
            "name_search",
            postgresql_using="gin",
            postgresql_ops={"name_search": "gin_trgm_ops"},
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    plate: Mapped[str] = mapped_column(String(50), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    name_search: Mapped[str] = mapped_column(String(255))
    authorization_type: Mapped[AuthorizationType] = mapped_column(
        Enum(AuthorizationType, name="agent_authorization_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    corporation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alcaldias: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)), nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("official_sources.id"), nullable=False, index=True)


class AgentLookup(Base):
    __tablename__ = "agent_lookups"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("authorized_agents.id", ondelete="SET NULL"), nullable=True, index=True)


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class MessageStatus(str, enum.Enum):
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


class Conversation(Timestamped, Base):
    __tablename__ = "conversations"
    __table_args__ = (Index("ix_conversations_user_updated", "user_id", "updated_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(80), nullable=True)


class Message(Base):
    """One turn of a conversation. Order by (created_at, id): both timestamps of a turn can be equal."""

    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at", "id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role", values_callable=lambda e: [m.value for m in e]), nullable=False
    )
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus, name="message_status", values_callable=lambda e: [m.value for m in e]),
        default=MessageStatus.COMPLETE, server_default=MessageStatus.COMPLETE.value, nullable=False,
    )
    citations: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{n, source_title, article, fraction, page, url}]
    tool_calls: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # what the agent consulted, for traces and evals
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MessageFeedback(Base):
    __tablename__ = "message_feedback"
    __table_args__ = (
        CheckConstraint("value IN (-1, 1)", name="ck_message_feedback_value"),
        UniqueConstraint("message_id", "user_id", name="uq_message_feedback_message_user"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    value: Mapped[int] = mapped_column(SmallInteger)  # 1 = 👍, -1 = 👎
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
