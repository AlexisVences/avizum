from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AdminUser, DbSession
from app.models.domain import User, UserRole
from app.schemas.admin import AdminUserDelete, AdminUserRow, AdminUserUpdate, Page
from app.schemas.api import UserPublic
from app.services.admin.users import AdminRuleError, delete_user, list_users, update_user

router = APIRouter(prefix="/admin")


def _rule_conflict(exc: AdminRuleError) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, {"code": exc.code, "message": exc.message})


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
    page: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> Page[AdminUserRow]:
    items, total = list_users(
        db, q=q, role=role, active=active, verified=verified,
        sort=sort, descending=descending, page=page, page_size=page_size,
    )
    return Page[AdminUserRow](items=items, total=total, page=page, page_size=page_size)


@router.patch("/users/{user_id}", response_model=UserPublic)
def admin_update_user(
    user_id: int, payload: AdminUserUpdate, admin: AdminUser, db: DbSession
) -> User:
    try:
        return update_user(
            db, actor=admin, target_id=user_id, role=payload.role, is_active=payload.is_active
        )
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found") from None
    except AdminRuleError as exc:
        raise _rule_conflict(exc) from exc


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(
    user_id: int, payload: AdminUserDelete, admin: AdminUser, db: DbSession
) -> None:
    try:
        delete_user(db, actor=admin, target_id=user_id, confirm_email=payload.confirm_email)
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found") from None
    except AdminRuleError as exc:
        raise _rule_conflict(exc) from exc
