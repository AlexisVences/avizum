from datetime import date, datetime
from decimal import Decimal
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.domain import UserRole

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class AdminUserRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_activity_at: datetime | None
    questions_count: int


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class AdminUserDelete(BaseModel):
    confirm_email: str


class AuditRow(BaseModel):
    id: int
    created_at: datetime
    actor_name: str | None
    action: str
    target_user_id: int | None
    detail: dict[str, str | int | bool | None]


class AttentionItem(BaseModel):
    kind: str
    label: str
    count: int
    href: str


class DayPoint(BaseModel):
    date: date
    questions: int


class Overview(BaseModel):
    days: int
    since: datetime
    questions: int
    active_users: int
    new_users: int
    answers_with_error: int
    error_rate: float | None
    feedback_up: int
    feedback_down: int
    feedback_rate: float | None
    feedback_rated: int
    tokens_input: int
    tokens_output: int
    cost_usd: Decimal  # serialized as a string so the client never receives a float
    agent_lookups: int
    series: list[DayPoint]
    attention: list[AttentionItem]


class ReviewItem(BaseModel):
    """One answer in the quality queue. Nothing here identifies the person who asked."""
    message_id: int
    asked_at: datetime
    reasons: list[Literal["negative", "error", "uncited"]]
    question: str
    answer: str
    citations: list[dict]
    tools: list[str]
    reviewed: bool
    note: str | None
