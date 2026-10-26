from datetime import datetime
from typing import Generic, TypeVar

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
