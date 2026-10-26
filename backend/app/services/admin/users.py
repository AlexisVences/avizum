from typing import Literal

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models.domain import Conversation, Message, MessageRole, User, UserRole
from app.schemas.admin import AdminUserRow
from app.services.admin.audit import AuditAction, record_audit

UserSort = Literal["name", "created", "activity", "questions"]


def list_users(
    db: Session,
    *,
    q: str | None = None,
    role: UserRole | None = None,
    active: bool | None = None,
    verified: bool | None = None,
    sort: UserSort = "created",
    descending: bool = True,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AdminUserRow], int]:
    """One aggregated query: per-user message stats outer-joined to users, filtered and paged."""
    stats = (
        select(
            Conversation.user_id.label("user_id"),
            func.max(Message.created_at).label("last_activity_at"),
            func.count(case((Message.role == MessageRole.USER, 1))).label("questions_count"),
        )
        .join(Message, Message.conversation_id == Conversation.id)
        .group_by(Conversation.user_id)
        .subquery()
    )
    questions = func.coalesce(stats.c.questions_count, 0)

    conditions = []
    for token in (q or "").split():
        escaped = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = func.immutable_unaccent(f"%{escaped}%")
        conditions.append(
            or_(
                *(
                    func.immutable_unaccent(column).ilike(pattern, escape="\\")
                    for column in (User.first_name, User.last_name, User.email)
                )
            )
        )
    if role is not None:
        conditions.append(User.role == role)
    if active is not None:
        conditions.append(User.is_active == active)
    if verified is not None:
        has_verified = User.email_verified_at.is_not(None)
        conditions.append(has_verified if verified else User.email_verified_at.is_(None))

    total = db.scalar(select(func.count()).select_from(User).where(*conditions)) or 0

    direction = (lambda c: c.desc()) if descending else (lambda c: c.asc())
    if sort == "name":
        order = [direction(func.lower(User.first_name)), direction(func.lower(User.last_name))]
    elif sort == "activity":
        order = [direction(stats.c.last_activity_at).nulls_last()]
    elif sort == "questions":
        order = [direction(questions)]
    else:
        order = [direction(User.created_at)]
    order.append(direction(User.id))

    rows = db.execute(
        select(User, stats.c.last_activity_at, questions.label("questions_count"))
        .outerjoin(stats, stats.c.user_id == User.id)
        .where(*conditions)
        .order_by(*order)
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    items = [
        AdminUserRow(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            email_verified=user.email_verified,
            created_at=user.created_at,
            last_activity_at=last_activity,
            questions_count=count,
        )
        for user, last_activity, count in rows
    ]
    return items, total


class AdminRuleError(Exception):
    """A rule that keeps the system safe (no self-lockout, always one active admin)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _load_target(db: Session, target_id: int) -> User:
    """Lock the target row; a missing one is a LookupError for the router to turn into 404."""
    target = db.scalar(select(User).where(User.id == target_id).with_for_update())
    if target is None:
        raise LookupError(target_id)
    return target


def _ensure_not_self(actor: User, target: User, message: str) -> None:
    if actor.id == target.id:
        raise AdminRuleError("cannot_modify_self", message)


def _ensure_another_active_admin(db: Session, target: User) -> None:
    """Refuse when `target` is an active admin and no other active admin would remain."""
    if target.role != UserRole.ADMIN or not target.is_active:
        return
    others = db.scalar(
        select(func.count()).select_from(User).where(
            User.role == UserRole.ADMIN, User.is_active.is_(True), User.id != target.id
        )
    )
    if not others:
        raise AdminRuleError(
            "last_admin", "Debe quedar al menos un administrador activo en Avizum."
        )


def update_user(
    db: Session, *, actor: User, target_id: int, role: UserRole | None, is_active: bool | None
) -> User:
    """Change role and/or active flag with guards; each real change is audited in one commit."""
    target = _load_target(db, target_id)
    role_changes = role is not None and role != target.role
    active_changes = is_active is not None and is_active != target.is_active
    if not role_changes and not active_changes:
        return target
    _ensure_not_self(
        actor, target, "No puedes cambiar tu propio rol ni desactivar tu propia cuenta."
    )
    demoting = role_changes and role != UserRole.ADMIN
    deactivating = active_changes and not is_active
    if demoting or deactivating:
        _ensure_another_active_admin(db, target)

    if role_changes:
        record_audit(
            db, actor_id=actor.id, action=AuditAction.USER_ROLE_CHANGED, target_user_id=target.id,
            detail={"from": target.role.value, "to": role.value},
        )
        target.role = role
    if active_changes:
        target.is_active = is_active
        if deactivating:
            target.token_version += 1  # revokes every token already issued
        record_audit(
            db, actor_id=actor.id, target_user_id=target.id,
            action=AuditAction.USER_DEACTIVATED if deactivating else AuditAction.USER_REACTIVATED,
        )
    db.commit()
    db.refresh(target)
    return target
