import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
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
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e]), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class AuthorizedAgent(Timestamped, Base):
    __tablename__ = "authorized_agents"
    id: Mapped[int] = mapped_column(primary_key=True)
    plate: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))


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
