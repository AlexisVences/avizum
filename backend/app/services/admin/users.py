from typing import Literal

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models.domain import Conversation, Message, MessageRole, User, UserRole
from app.schemas.admin import AdminUserRow

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
    if q and q.strip():
        term = f"%{q.strip()}%"
        conditions.append(
            or_(
                *(
                    func.immutable_unaccent(column).ilike(func.immutable_unaccent(term))
                    for column in (User.first_name, User.last_name, User.email)
                )
            )
        )
    if role is not None:
        conditions.append(User.role == role)
    if active is not None:
        conditions.append(User.is_active == active)
    if verified is not None:
        conditions.append(User.email_verified_at.is_not(None) if verified else User.email_verified_at.is_(None))

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
