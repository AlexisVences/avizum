from typing import Annotated, Literal

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.models.domain import UserRole
from app.schemas.admin import AdminUserRow, Page
from app.services.admin.users import list_users

router = APIRouter(prefix="/admin")


@router.get("/users", response_model=Page[AdminUserRow])
def admin_list_users(
    _: AdminUser,
    db: DbSession,
    q: str | None = None,
    role: UserRole | None = None,
    active: bool | None = None,
    verified: bool | None = None,
    sort: Literal["name", "created", "activity", "questions"] = "created",
    descending: bool = True,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> Page[AdminUserRow]:
    items, total = list_users(
        db, q=q, role=role, active=active, verified=verified,
        sort=sort, descending=descending, page=page, page_size=page_size,
    )
    return Page[AdminUserRow](items=items, total=total, page=page, page_size=page_size)
