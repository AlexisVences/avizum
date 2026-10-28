import enum

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.models.domain import AdminAuditLog, User
from app.schemas.admin import AuditRow

FORBIDDEN_DETAIL_KEYS = frozenset({"password", "token", "email", "question", "answer", "content"})


class AuditAction(str, enum.Enum):
    USER_ROLE_CHANGED = "user.role_changed"
    USER_DEACTIVATED = "user.deactivated"
    USER_REACTIVATED = "user.reactivated"
    USER_DELETED = "user.deleted"
    REVIEW_MARKED = "review.marked"


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, (str, int, bool))


def record_audit(
    db: Session,
    *,
    actor_id: int,
    action: AuditAction,
    target_user_id: int | None = None,
    detail: dict[str, str | int | bool | None] | None = None,
) -> AdminAuditLog:
    """Add an audit row in the caller's transaction (flush, no commit). Detail carries identifiers
    and state values only; keys that equal or contain a forbidden word (any case) are rejected."""
    detail = detail or {}
    forbidden = {
        key for key in detail if any(word in key.lower() for word in FORBIDDEN_DETAIL_KEYS)
    }
    if forbidden:
        raise ValueError(f"audit detail cannot include: {', '.join(sorted(forbidden))}")
    nested = sorted(key for key, value in detail.items() if not _is_scalar(value))
    if nested:
        raise ValueError(f"audit detail values must be scalars: {', '.join(nested)}")
    row = AdminAuditLog(
        actor_id=actor_id, action=action.value, target_user_id=target_user_id, detail=detail
    )
    db.add(row)
    db.flush()
    return row


def list_audit(
    db: Session,
    *,
    actor_id: int | None,
    action: AuditAction | None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AuditRow], int]:
    """Audit rows, newest first (id breaks ties); actor_name/target_name are null if gone."""
    filters = []
    if actor_id is not None:
        filters.append(AdminAuditLog.actor_id == actor_id)
    if action is not None:
        filters.append(AdminAuditLog.action == action.value)
    total = db.scalar(select(func.count()).select_from(AdminAuditLog).where(*filters)) or 0
    target = aliased(User)
    stmt = (
        select(
            AdminAuditLog, User.first_name, User.last_name, target.first_name, target.last_name
        )
        .outerjoin(User, User.id == AdminAuditLog.actor_id)
        .outerjoin(target, target.id == AdminAuditLog.target_user_id)
        .where(*filters)
        .order_by(AdminAuditLog.created_at.desc(), AdminAuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [
        AuditRow(
            id=row.id,
            created_at=row.created_at,
            actor_name=f"{first} {last}" if first is not None else None,
            action=row.action,
            target_user_id=row.target_user_id,
            target_name=f"{t_first} {t_last}" if t_first is not None else None,
            detail={k: v for k, v in (row.detail or {}).items() if _is_scalar(v)},
        )
        for row, first, last, t_first, t_last in db.execute(stmt)
    ]
    return items, total
