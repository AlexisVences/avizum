from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.domain import (
    AgentLookup, Conversation, Message, MessageFeedback, MessageRole, MessageStatus, User,
)
from app.schemas.admin import DayPoint, Overview
from app.services.admin.attention import collect_attention
from app.services.chat_limits import MEXICO_CITY

_ZONE_NAME = "America/Mexico_City"


def _day_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=MEXICO_CITY)


def _cost(tokens_input: int, tokens_output: int) -> Decimal:
    settings = get_settings()
    total = (
        tokens_input * settings.llm_price_input_per_million
        + tokens_output * settings.llm_price_output_per_million
    ) / Decimal(1_000_000)
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _ratio(part: int, whole: int) -> float | None:
    return part / whole if whole else None


def build_overview(
    db: Session, *, days: Literal[7, 30, 90], now: datetime | None = None
) -> Overview:
    today = (now or datetime.now(MEXICO_CITY)).astimezone(MEXICO_CITY).date()
    first_day = today - timedelta(days=days - 1)
    since, until = _day_start(first_day), _day_start(today + timedelta(days=1))

    def in_window(column):
        return (column >= since) & (column < until)

    is_question = Message.role == MessageRole.USER
    is_answer = Message.role == MessageRole.ASSISTANT

    questions, active_users = db.execute(
        select(func.count(Message.id), func.count(func.distinct(Conversation.user_id)))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(is_question, in_window(Message.created_at))
    ).one()
    answers, answers_with_error, tokens_input, tokens_output = db.execute(
        select(
            func.count(Message.id),
            func.count(case((Message.status == MessageStatus.ERROR, 1))),
            func.coalesce(func.sum(Message.input_tokens), 0),
            func.coalesce(func.sum(Message.output_tokens), 0),
        ).where(is_answer, in_window(Message.created_at))
    ).one()
    new_users = db.scalar(select(func.count(User.id)).where(in_window(User.created_at)))
    feedback_up, feedback_down = db.execute(
        select(
            func.count(case((MessageFeedback.value == 1, 1))),
            func.count(case((MessageFeedback.value == -1, 1))),
        ).where(in_window(MessageFeedback.created_at))
    ).one()
    agent_lookups = db.scalar(
        select(func.count(AgentLookup.id)).where(in_window(AgentLookup.created_at))
    )

    local_day = func.date(func.timezone(_ZONE_NAME, Message.created_at))
    per_day = dict(
        db.execute(
            select(local_day, func.count(Message.id))
            .where(is_question, in_window(Message.created_at))
            .group_by(local_day)
        ).all()
    )
    series = [
        DayPoint(date=day, questions=per_day.get(day, 0))
        for day in (first_day + timedelta(days=i) for i in range(days))
    ]

    tokens_input, tokens_output = int(tokens_input), int(tokens_output)
    rated = feedback_up + feedback_down
    return Overview(
        days=days,
        since=since,
        questions=questions,
        active_users=active_users,
        new_users=new_users,
        answers_with_error=answers_with_error,
        error_rate=_ratio(answers_with_error, answers),
        feedback_up=feedback_up,
        feedback_down=feedback_down,
        feedback_rate=_ratio(feedback_up, rated),
        feedback_rated=rated,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        cost_usd=_cost(tokens_input, tokens_output),
        agent_lookups=agent_lookups,
        series=series,
        attention=collect_attention(db),
    )
