from typing import Literal

from sqlalchemy import Select, case, exists, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models.domain import Message, MessageFeedback, MessageReview, MessageRole, MessageStatus
from app.schemas.admin import ReviewItem

ReviewReason = Literal["negative", "error", "uncited"]


def _array_length(column):
    """Length of a JSONB array column; 0 for SQL NULL, JSON null or a non-array."""
    return case(
        (func.jsonb_typeof(column) == "array", func.jsonb_array_length(column)), else_=0
    )


def _conditions() -> dict[ReviewReason, object]:
    return {
        "negative": exists().where(
            MessageFeedback.message_id == Message.id, MessageFeedback.value == -1
        ),
        "error": Message.status == MessageStatus.ERROR,
        "uncited": (Message.status == MessageStatus.COMPLETE)
        & (_array_length(Message.citations) == 0)
        & (_array_length(Message.tool_calls) > 0),
    }


def _question_before() -> object:
    """Content of the nearest earlier USER message in the same conversation."""
    earlier = aliased(Message)
    return (
        select(earlier.content)
        .where(
            earlier.conversation_id == Message.conversation_id,
            earlier.role == MessageRole.USER,
            earlier.id < Message.id,
        )
        .order_by(earlier.id.desc())
        .limit(1)
        .scalar_subquery()
    )


def _tool_names(tool_calls: object) -> list[str]:
    names: list[str] = []
    if isinstance(tool_calls, list):
        for call in tool_calls:
            name = call.get("name") if isinstance(call, dict) else None
            if isinstance(name, str) and name not in names:
                names.append(name)
    return names


def _queue_query(reason: ReviewReason | None, reviewed: bool | None) -> Select:
    conditions = _conditions()
    wanted = [conditions[reason]] if reason else list(conditions.values())
    query = (
        select(Message)
        .outerjoin(MessageReview, MessageReview.message_id == Message.id)
        .where(Message.role == MessageRole.ASSISTANT, or_(*wanted))
    )
    if reviewed is True:
        query = query.where(MessageReview.id.is_not(None))
    elif reviewed is False:
        query = query.where(MessageReview.id.is_(None))
    return query


def list_review_queue(
    db: Session, *, reason: ReviewReason | None, reviewed: bool | None, page: int, page_size: int
) -> tuple[list[ReviewItem], int]:
    """Assistant answers that deserve a human look, newest first."""
    query = _queue_query(reason, reviewed)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.add_columns(
            _question_before().label("question"),
            MessageReview.id.label("review_id"),
            MessageReview.note.label("note"),
        )
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    ids = [row.Message.id for row in rows]
    negative_ids = set(
        db.scalars(
            select(MessageFeedback.message_id).where(
                MessageFeedback.message_id.in_(ids), MessageFeedback.value == -1
            )
        )
    )
    items = []
    for row in rows:
        message = row.Message
        reasons: list[ReviewReason] = []
        if message.id in negative_ids:
            reasons.append("negative")
        if message.status == MessageStatus.ERROR:
            reasons.append("error")
        if (
            message.status == MessageStatus.COMPLETE
            and not (message.citations or [])
            and _tool_names(message.tool_calls)
        ):
            reasons.append("uncited")
        items.append(
            ReviewItem(
                message_id=message.id,
                asked_at=message.created_at,
                reasons=reasons,
                question=row.question or "",
                answer=message.content,
                citations=message.citations if isinstance(message.citations, list) else [],
                tools=_tool_names(message.tool_calls),
                reviewed=row.review_id is not None,
                note=row.note,
            )
        )
    return items, total
