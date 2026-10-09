import enum
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import ARRAY
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


class Consultation(Base):
    __tablename__ = "consultations"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    question: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)


class LegalResponse(Base):
    __tablename__ = "legal_responses"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    consultation_id: Mapped[int] = mapped_column(ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, unique=True)


class Feedback(Timestamped, Base):
    __tablename__ = "feedback"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating_range"), UniqueConstraint("response_id", name="uq_feedback_response"), Index("ix_feedback_response_id", "response_id"))
    id: Mapped[int] = mapped_column(primary_key=True)
    rating: Mapped[int] = mapped_column(Integer)
    response_id: Mapped[int] = mapped_column(ForeignKey("legal_responses.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
