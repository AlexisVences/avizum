import enum
from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, Computed, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint, func, text
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
    password_hash: Mapped[str | None] = mapped_column(String(255))  # None: the account only signs in with Google
    google_sub: Mapped[str | None] = mapped_column(String(64), unique=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    token_version: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)  # bump to revoke every issued token
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e]), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None


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


class MessageReview(Base):
    """An admin marked an assistant answer as reviewed in the quality queue. One per message."""
    __tablename__ = "message_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SanctionStatus(str, enum.Enum):
    PENDING = "pending"  # extracted and validated by the machine, not reviewed by a person: never served
    VERIFIED = "verified"  # a person approved it against the source text: the only status the agent may serve
    REJECTED = "rejected"  # a person found it wrong
    STALE = "stale"  # the chunk it came from changed (hash mismatch) after it was verified


class LegalSanction(Timestamped, Base):
    """One sanctionable conduct of a legal chunk, with the penalty that applies to THAT conduct.

    Articles list several conducts and several penalty clauses ("los incisos a), b), d) y e) ... 5, 7 o 10 veces la
    UMA; el inciso c) ... 10, 15 o 20"), and mapping one to the other in prose is where the model made mistakes.
    The numbers come from the verbatim clause (regex), never from a model. `chunk_hash` ties the row to the exact
    text it was verified against: if the chunk changes, the row stops being served until it is reviewed again.
    """

    __tablename__ = "legal_sanctions"
    __table_args__ = (
        UniqueConstraint("chunk_id", "ordinal", name="uq_legal_sanctions_chunk_ordinal"),
        CheckConstraint(
            "(uma_min IS NULL AND uma_mid IS NULL AND uma_max IS NULL) OR "
            "(uma_min IS NOT NULL AND uma_min > 0 AND (uma_mid IS NULL OR uma_mid >= uma_min) "
            "AND (uma_max IS NULL OR uma_max >= COALESCE(uma_mid, uma_min)))",
            name="ck_legal_sanctions_uma_ascending",
        ),
        CheckConstraint("points_license IS NULL OR points_license >= 0", name="ck_legal_sanctions_points_license"),
        CheckConstraint("points_plate IS NULL OR points_plate >= 0", name="ck_legal_sanctions_points_plate"),
        CheckConstraint("char_length(chunk_hash) = 64", name="ck_legal_sanctions_chunk_hash_len"),
        Index("ix_legal_sanctions_chunk_status", "chunk_id", "status"),
        Index("ix_legal_sanctions_article", "source_slug", "article", "fraction"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("legal_chunks.id", ondelete="CASCADE"), nullable=False)
    ordinal: Mapped[int] = mapped_column(SmallInteger)  # position inside the chunk, stable for a given text
    # Denormalised so the reviewed file in git (data/sanctions/verified.json) can be matched without chunk ids.
    source_slug: Mapped[str] = mapped_column(String(100))
    article: Mapped[str] = mapped_column(String(50))
    fraction: Mapped[str | None] = mapped_column(String(50), nullable=True)  # the fraction this conduct sits in
    inciso: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "b", "e Bis"; null when the whole fraction
    # A qualifier the text puts on the penalty ("vehículos de transporte público de pasajeros y carga"): the same
    # conduct then has several rows and the agent must pick the one that matches the person's vehicle. Null = general.
    applies_to: Mapped[str | None] = mapped_column(Text, nullable=True)
    conduct_text: Mapped[str] = mapped_column(Text)  # verbatim from the chunk
    clause_text: Mapped[str] = mapped_column(Text)  # the verbatim penalty clause the numbers were read from
    uma_min: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    uma_mid: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    uma_max: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    points_license: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    points_plate: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)  # when caught by technological systems
    other_consequences: Mapped[str | None] = mapped_column(Text, nullable=True)  # depósito, arresto... as written
    # Context the extractor derives from the same text; it does not change what a person verified (amount, conduct):
    lead_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # the article's wording that introduces its list
    points_mode: Mapped[str | None] = mapped_column(String(30), nullable=True)  # alternativos_por_captacion | acumulativos
    # Verbatim text the clause depends on: the exemptions of "excepto cuando…", or the paragraph it points back to.
    context_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_hash: Mapped[str] = mapped_column(String(64))  # sha256 of the chunk text this row was extracted from
    extractor_version: Mapped[str] = mapped_column(String(30))
    status: Mapped[SanctionStatus] = mapped_column(
        Enum(SanctionStatus, name="sanction_status", values_callable=lambda e: [m.value for m in e]),
        default=SanctionStatus.PENDING, server_default=SanctionStatus.PENDING.value, nullable=False,
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminAuditLog(Base):
    """Who did what to whom in the admin console. Holds identifiers and state values only: never passwords,
    tokens, emails or the text of questions and answers. target_user_id has no foreign key on purpose, so the
    record outlives the deletion of the person it is about."""
    __tablename__ = "admin_audit_log"
    __table_args__ = (Index("ix_admin_audit_log_created_at", text("created_at DESC")),)
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(40))
    target_user_id: Mapped[int | None] = mapped_column(nullable=True)
    detail: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
