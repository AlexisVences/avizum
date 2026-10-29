from typing import Literal

from pydantic import ValidationError
from sqlalchemy import Select, case, exists, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models.domain import (
    Message, MessageFeedback, MessageReview, MessageRole, MessageStatus, User,
)
from app.schemas.admin import ReviewCitation, ReviewItem
from app.services.admin.audit import AuditAction, record_audit

ReviewReason = Literal["negative", "error", "uncited"]
REASONS: tuple[ReviewReason, ...] = ("negative", "error", "uncited")


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


def _queue_query(
    reason: ReviewReason | None, reviewed: bool | None, message_id: int | None = None
) -> Select:
    """Queue selection. Each reason is also selected as a boolean column, so the reasons shown
    come from the very conditions that select the row (single source of truth)."""
    conditions = _conditions()
    wanted = [conditions[reason]] if reason else list(conditions.values())
    query = (
        select(Message, *(cond.label(f"r_{name}") for name, cond in conditions.items()))
        .outerjoin(MessageReview, MessageReview.message_id == Message.id)
        .where(Message.role == MessageRole.ASSISTANT, or_(*wanted))
    )
    if message_id is not None:
        query = query.where(Message.id == message_id)
    if reviewed is True:
        query = query.where(MessageReview.id.is_not(None))
    elif reviewed is False:
        query = query.where(MessageReview.id.is_(None))
    return query


def _citations(value: object) -> list[ReviewCitation]:
    found = []
    for raw in value if isinstance(value, list) else []:
        try:
            found.append(ReviewCitation.model_validate(raw))
        except ValidationError:
            continue
    return found


def _items(db: Session, query: Select) -> list[ReviewItem]:
    rows = db.execute(
        query.add_columns(
            _question_before().label("question"),
            MessageReview.id.label("review_id"),
            MessageReview.note.label("note"),
        )
    ).all()
    return [
        ReviewItem(
            message_id=row.Message.id,
            asked_at=row.Message.created_at,
            reasons=[name for name in REASONS if getattr(row, f"r_{name}")],
            question=row.question or "",
            answer=row.Message.content,
            citations=_citations(row.Message.citations),
            tools=_tool_names(row.Message.tool_calls),
            reviewed=row.review_id is not None,
            note=row.note,
        )
        for row in rows
    ]


def list_review_queue(
    db: Session, *, reason: ReviewReason | None, reviewed: bool | None, page: int, page_size: int
) -> tuple[list[ReviewItem], int]:
    """Assistant answers that deserve a human look, newest first."""
    query = _queue_query(reason, reviewed)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    page_query = (
        query.order_by(Message.created_at.desc(), Message.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return _items(db, page_query), total


def count_unreviewed(db: Session) -> int:
    query = _queue_query(None, reviewed=False)
    return db.scalar(select(func.count()).select_from(query.subquery())) or 0


def _queue_item(db: Session, message_id: int) -> ReviewItem:
    items = _items(db, _queue_query(None, None, message_id))
    if not items:
        raise NotInQueueError(message_id)
    return items[0]


class NotInQueueError(LookupError):
    """The message does not exist or is not an answer that is in the review queue."""


def mark_reviewed(
    db: Session, *, actor: User, message_id: int, note: str | None
) -> MessageReview:
    """Mark a queued answer as reviewed. Idempotent: a second mark updates the note and writes
    no second audit row."""
    _queue_item(db, message_id)
    review = db.scalar(select(MessageReview).where(MessageReview.message_id == message_id))
    if review is None:
        review = MessageReview(message_id=message_id, reviewer_id=actor.id, note=note)
        db.add(review)
        record_audit(
            db, actor_id=actor.id, action=AuditAction.REVIEW_MARKED,
            detail={"message_id": message_id},
        )
    else:
        review.note = note
    db.commit()
    return review


def eval_case_for(db: Session, message_id: int) -> dict:
    """A data/eval/*.jsonl case from a queued answer; labels come from its citations, unverified."""
    item = _queue_item(db, message_id)
    expected: list[dict[str, str | None]] = []
    for citation in item.citations:
        entry = {"source": citation.source_slug, "article": citation.article}
        if citation.source_slug and entry not in expected:
            expected.append(entry)
    return {
        "id": f"p{message_id}",
        "question": item.question,
        "coverage": "full",
        "expected": expected,
        "notes": "Exportado de producción; etiquetas por verificar",
        "verified": False,
    }
