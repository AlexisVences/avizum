import enum

from sqlalchemy.orm import Session

from app.models.domain import AdminAuditLog

FORBIDDEN_DETAIL_KEYS = frozenset({"password", "token", "email", "question", "answer", "content"})


class AuditAction(str, enum.Enum):
    USER_ROLE_CHANGED = "user.role_changed"
    USER_DEACTIVATED = "user.deactivated"
    USER_REACTIVATED = "user.reactivated"
    USER_DELETED = "user.deleted"
    REVIEW_MARKED = "review.marked"


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
    row = AdminAuditLog(
        actor_id=actor_id, action=action.value, target_user_id=target_user_id, detail=detail
    )
    db.add(row)
    db.flush()
    return row
