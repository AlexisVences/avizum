from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AdminUser, DbSession
from app.models.domain import User, UserRole
from app.schemas.admin import (
    AdminUserDelete, AdminUserRow, AdminUserUpdate, AuditRow, Overview, Page, ReviewItem,
    ReviewMark, ReviewMarkBody, SourcesStatus,
)
from app.schemas.api import UserPublic
from app.services.admin.audit import AuditAction, list_audit
from app.services.admin.overview import build_overview
from app.services.admin.review import (
    NotInQueueError, ReviewReason, eval_case_for, list_review_queue, mark_reviewed,
)
from app.services.admin.sources import list_sources, pending_sanctions
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


@router.get("/audit", response_model=Page[AuditRow])
def admin_list_audit(
    _: AdminUser,
    db: DbSession,
    actor_id: int | None = None,
    action: AuditAction | None = None,
    page: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> Page[AuditRow]:
    items, total = list_audit(db, actor_id=actor_id, action=action, page=page, page_size=page_size)
    return Page[AuditRow](items=items, total=total, page=page, page_size=page_size)


@router.get("/overview", response_model=Overview)
def admin_overview(
    _: AdminUser, db: DbSession, days: Literal[7, 30, 90] = 30
) -> Overview:
    return build_overview(db, days=days)


@router.get("/review-queue", response_model=Page[ReviewItem])
def admin_review_queue(
    _: AdminUser,
    db: DbSession,
    reason: ReviewReason | None = None,
    reviewed: bool | None = None,
    page: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> Page[ReviewItem]:
    items, total = list_review_queue(
        db, reason=reason, reviewed=reviewed, page=page, page_size=page_size
    )
    return Page[ReviewItem](items=items, total=total, page=page, page_size=page_size)


_NOT_IN_QUEUE = HTTPException(status.HTTP_404_NOT_FOUND, "Respuesta no encontrada en la cola")


@router.post("/review-queue/{message_id}/review", response_model=ReviewMark)
def admin_mark_reviewed(
    message_id: int, body: ReviewMarkBody, admin: AdminUser, db: DbSession
) -> ReviewMark:
    try:
        review = mark_reviewed(db, actor=admin, message_id=message_id, note=body.note)
    except NotInQueueError:
        raise _NOT_IN_QUEUE from None
    return ReviewMark(message_id=message_id, reviewed=True, note=review.note)


@router.get("/review-queue/{message_id}/eval-case")
def admin_eval_case(message_id: int, _: AdminUser, db: DbSession) -> dict:
    try:
        return eval_case_for(db, message_id)
    except NotInQueueError:
        raise _NOT_IN_QUEUE from None


@router.get("/sources", response_model=SourcesStatus)
def admin_sources(_: AdminUser, db: DbSession) -> SourcesStatus:
    return SourcesStatus(sources=list_sources(db), pending_sanctions=pending_sanctions(db))
