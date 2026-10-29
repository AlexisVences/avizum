"""The usage limits that keep the chat's cost and abuse bounded (spec section 2).

They run before anything is stored or sent to the model, in this order: the message itself (422), the conversation
(409), the user's day (429) and the rolling 24 h cost budget, per user and optionally global (429). Each raises `ChatLimitError` with the HTTP status the route should answer.
"""
from decimal import Decimal
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.domain import Conversation, Message, MessageRole

MEXICO_CITY = ZoneInfo("America/Mexico_City")


class ChatLimitError(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, retry_after: int | None = None
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after  # seconds; the route sends it as the Retry-After header
        self.status_code = status_code
        self.code = code
        self.message = message


def start_of_today(now: datetime | None = None) -> datetime:
    local = (now or datetime.now(MEXICO_CITY)).astimezone(MEXICO_CITY)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def messages_sent_today(db: Session, user_id: int, now: datetime | None = None) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(
            Conversation.user_id == user_id,
            Message.role == MessageRole.USER,
            Message.created_at >= start_of_today(now),
        )
    ) or 0


BUDGET_WINDOW = timedelta(hours=24)
MIN_RETRY_SECONDS = 60


def estimated_cost_usd(db: Session, since: datetime, user_id: int | None, settings: Settings) -> tuple[Decimal, datetime | None]:
    """Estimated USD spent on assistant answers since `since` (all users when `user_id` is None), from the stored
    token usage and the configured prices, plus the time of the oldest answer counted. Read from the database, so it
    holds across processes and restarts. Per user it walks the user's conversations (ix_conversations_user_updated)
    and then messages by conversation and date (ix_messages_conversation_created)."""
    query = select(
        func.coalesce(func.sum(Message.input_tokens), 0),
        func.coalesce(func.sum(Message.output_tokens), 0),
        func.min(Message.created_at),
    ).where(Message.role == MessageRole.ASSISTANT, Message.created_at >= since)
    if user_id is not None:
        query = query.join(Conversation, Conversation.id == Message.conversation_id).where(Conversation.user_id == user_id)
    tokens_in, tokens_out, oldest = db.execute(query).one()
    cost = (
        Decimal(tokens_in) * settings.llm_price_input_per_million + Decimal(tokens_out) * settings.llm_price_output_per_million
    ) / Decimal(1_000_000)
    return cost, oldest


def _retry_after(oldest: datetime | None, moment: datetime) -> int:
    """Seconds until the oldest counted answer leaves the window (it may take more than one to get under the cap)."""
    if oldest is None:
        return MIN_RETRY_SECONDS
    return max(MIN_RETRY_SECONDS, int((oldest + BUDGET_WINDOW - moment).total_seconds()) + 1)


def check_budget(db: Session, user_id: int, settings: Settings, now: datetime | None = None) -> None:
    moment = now or datetime.now(MEXICO_CITY)
    since = moment - BUDGET_WINDOW
    if settings.global_daily_cost_usd_limit > 0:
        spent, oldest = estimated_cost_usd(db, since, None, settings)
        if spent >= settings.global_daily_cost_usd_limit:
            raise ChatLimitError(
                429, "servicio_saturado",
                "El asistente está temporalmente fuera de servicio por alta demanda. Intenta de nuevo más tarde.",
                retry_after=_retry_after(oldest, moment),
            )
    if settings.daily_user_cost_usd_limit > 0:
        spent, oldest = estimated_cost_usd(db, since, user_id, settings)
        if spent >= settings.daily_user_cost_usd_limit:
            raise ChatLimitError(
                429, "presupuesto_diario",
                "Alcanzaste el límite de uso del asistente en las últimas 24 horas. Intenta de nuevo más tarde.",
                retry_after=_retry_after(oldest, moment),
            )


def check_can_send(
    db: Session, user_id: int, conversation_id: int, content: str, settings: Settings, now: datetime | None = None
) -> str:
    """Returns the message to store (trimmed) or raises `ChatLimitError`."""
    content = content.strip()
    if not content:
        raise ChatLimitError(422, "mensaje_vacio", "Escribe tu pregunta.")
    if len(content) > settings.chat_max_message_chars:
        raise ChatLimitError(
            422, "mensaje_demasiado_largo",
            f"El mensaje es demasiado largo (máximo {settings.chat_max_message_chars} caracteres).",
        )
    in_conversation = db.scalar(select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)) or 0
    if in_conversation >= settings.chat_max_messages_per_conversation:
        raise ChatLimitError(409, "conversacion_llena", "Esta conversación llegó a su límite. Inicia una conversación nueva.")
    if messages_sent_today(db, user_id, now) >= settings.chat_daily_message_limit:
        raise ChatLimitError(
            429, "limite_diario",
            f"Llegaste al límite de {settings.chat_daily_message_limit} mensajes por día. Vuelve mañana.",
            retry_after=max(1, int((start_of_today(now) + timedelta(days=1) - (now or datetime.now(MEXICO_CITY))).total_seconds())),
        )
    check_budget(db, user_id, settings, now)
    moment = now or datetime.now(MEXICO_CITY)
    last = db.execute(
        select(Message.role, Message.created_at)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(1)
    ).first()
    # The question is stored before the answer is generated, so "last message is a young unanswered question"
    # means a turn is in flight. A crashed turn stops blocking once the question is older than the window.
    if last and last.role == MessageRole.USER and last.created_at > moment - timedelta(seconds=settings.chat_in_flight_seconds):
        raise ChatLimitError(409, "respuesta_en_curso", "Espera a que termine la respuesta en curso antes de enviar otro mensaje.")
    return content
