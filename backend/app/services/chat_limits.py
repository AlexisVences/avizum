"""The usage limits that keep the chat's cost and abuse bounded (spec section 2).

They run before anything is stored or sent to the model, in this order: the message itself (422), the conversation
(409), a turn already in flight for the user (409), the user's day (429) and the rolling 24 h cost budget, per user and
optionally global (429). Each raises `ChatLimitError` with the HTTP status the route should answer.

Usage is read from the `chat_usage` ledger, never from messages, so deleting a conversation cannot reset a limit. The
checks and the reservation of the turn run under a per-user advisory lock in one transaction, so parallel requests of
one user cannot all pass before any spend is recorded; `settle_usage` closes the reservation afterwards.
"""
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.domain import ChatUsage, Message, MessageRole, UsageStatus

logger = logging.getLogger(__name__)

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


ADVISORY_LOCK_NAMESPACE = 0x41565A  # first int of pg_advisory_xact_lock(ns, user_id): one lock per user, chat only


def lock_user(db: Session, user_id: int) -> None:
    """Serialises the check-and-reserve step of one user's turns across all workers. Held until the transaction ends."""
    db.execute(select(func.pg_advisory_xact_lock(ADVISORY_LOCK_NAMESPACE, user_id)))


def messages_sent_today(db: Session, user_id: int, now: datetime | None = None) -> int:
    """Turns accepted today (Mexico City), from the ledger: deleting conversations does not lower it."""
    return db.scalar(
        select(func.count()).select_from(ChatUsage).where(
            ChatUsage.user_id == user_id, ChatUsage.created_at >= start_of_today(now)
        )
    ) or 0


BUDGET_WINDOW = timedelta(hours=24)
MIN_RETRY_SECONDS = 60


def estimate_tokens(content: str, settings: Settings) -> tuple[int, int]:
    """(input, output) tokens reserved for a turn: the question at ~3 characters per token (conservative for Spanish)
    plus a base for the system prompt, history and tool results; the output is the model's output cap."""
    return settings.chat_reserve_input_tokens + len(content) // 3 + 1, settings.chat_max_output_tokens


def _row_tokens():
    """SQL expressions (input, output) of what a ledger row counts: the actual tokens when it has any and it is no
    longer only reserved, otherwise the reserved estimate (reserved, crashed, cancelled or usage-less turns)."""
    use_actual = and_(ChatUsage.status != UsageStatus.RESERVED, ChatUsage.input_tokens + ChatUsage.output_tokens > 0)
    return (
        case((use_actual, ChatUsage.input_tokens), else_=ChatUsage.reserved_input_tokens),
        case((use_actual, ChatUsage.output_tokens), else_=ChatUsage.reserved_output_tokens),
    )


def _cost(tokens_in, tokens_out, settings: Settings) -> Decimal:
    return (
        Decimal(tokens_in) * settings.llm_price_input_per_million + Decimal(tokens_out) * settings.llm_price_output_per_million
    ) / Decimal(1_000_000)


def estimated_cost_usd(db: Session, since: datetime, user_id: int | None, settings: Settings) -> tuple[Decimal, datetime | None]:
    """Estimated USD spent on turns since `since` (all users when `user_id` is None), from the ledger, plus the time
    of the oldest row counted. Per user it uses ix_chat_usage_user_created, global ix_chat_usage_created."""
    tokens_in, tokens_out = _row_tokens()
    query = select(
        func.coalesce(func.sum(tokens_in), 0), func.coalesce(func.sum(tokens_out), 0), func.min(ChatUsage.created_at)
    ).where(ChatUsage.created_at >= since)
    if user_id is not None:
        query = query.where(ChatUsage.user_id == user_id)
    spent_in, spent_out, oldest = db.execute(query).one()
    return _cost(spent_in, spent_out, settings), oldest


def _retry_after(oldest: datetime | None, moment: datetime) -> int:
    """Seconds until the oldest counted turn leaves the window (it may take more than one to get under the cap)."""
    if oldest is None:
        return MIN_RETRY_SECONDS
    return max(MIN_RETRY_SECONDS, int((oldest + BUDGET_WINDOW - moment).total_seconds()) + 1)


def check_budget(
    db: Session, user_id: int, settings: Settings, now: datetime | None = None, extra_cost: Decimal = Decimal(0)
) -> None:
    """`extra_cost` is the estimate of the turn about to be reserved: a turn that would cross the cap is refused."""
    moment = now or datetime.now(MEXICO_CITY)
    since = moment - BUDGET_WINDOW
    if settings.global_daily_cost_usd_limit > 0:
        spent, oldest = estimated_cost_usd(db, since, None, settings)
        if spent >= settings.global_daily_cost_usd_limit or spent + extra_cost > settings.global_daily_cost_usd_limit:
            raise ChatLimitError(
                429, "servicio_saturado",
                "El asistente está temporalmente fuera de servicio por alta demanda. Intenta de nuevo más tarde.",
                retry_after=_retry_after(oldest, moment),
            )
    if settings.daily_user_cost_usd_limit > 0:
        spent, oldest = estimated_cost_usd(db, since, user_id, settings)
        if spent >= settings.daily_user_cost_usd_limit or spent + extra_cost > settings.daily_user_cost_usd_limit:
            raise ChatLimitError(
                429, "presupuesto_diario",
                "Alcanzaste el límite de uso del asistente en las últimas 24 horas. Intenta de nuevo más tarde.",
                retry_after=_retry_after(oldest, moment),
            )


def check_can_send(
    db: Session, user_id: int, conversation_id: int, content: str, settings: Settings, now: datetime | None = None
) -> str:
    """Returns the message to store (trimmed) or raises `ChatLimitError`.

    Takes the user's advisory lock, which stays held until the caller's transaction ends, so the caller must call
    `reserve_usage` and commit in the same transaction (`begin_turn` does)."""
    content = content.strip()
    if not content:
        raise ChatLimitError(422, "mensaje_vacio", "Escribe tu pregunta.")
    if len(content) > settings.chat_max_message_chars:
        raise ChatLimitError(
            422, "mensaje_demasiado_largo",
            f"El mensaje es demasiado largo (máximo {settings.chat_max_message_chars} caracteres).",
        )
    lock_user(db, user_id)
    moment = now or datetime.now(MEXICO_CITY)
    in_conversation = db.scalar(select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)) or 0
    if in_conversation >= settings.chat_max_messages_per_conversation:
        raise ChatLimitError(409, "conversacion_llena", "Esta conversación llegó a su límite. Inicia una conversación nueva.")
    busy = ChatLimitError(409, "respuesta_en_curso", "Espera a que termine la respuesta en curso antes de enviar otro mensaje.")
    window_start = moment - timedelta(seconds=settings.chat_in_flight_seconds)
    # Any young reservation of this user means a turn is in flight, in whatever conversation; a stale one stops
    # blocking (but still counts its estimate toward the budget).
    if db.scalar(
        select(ChatUsage.id).where(
            ChatUsage.user_id == user_id, ChatUsage.status == UsageStatus.RESERVED, ChatUsage.created_at > window_start
        ).limit(1)
    ) is not None:
        raise busy
    if messages_sent_today(db, user_id, now) >= settings.chat_daily_message_limit:
        raise ChatLimitError(
            429, "limite_diario",
            f"Llegaste al límite de {settings.chat_daily_message_limit} mensajes por día. Vuelve mañana.",
            retry_after=max(1, int((start_of_today(now) + timedelta(days=1) - moment).total_seconds())),
        )
    est_in, est_out = estimate_tokens(content, settings)
    check_budget(db, user_id, settings, now, extra_cost=_cost(est_in, est_out, settings))
    last = db.execute(
        select(Message.role, Message.created_at)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(1)
    ).first()
    # The question is stored before the answer is generated, so "last message is a young unanswered question"
    # means a turn is in flight. A crashed turn stops blocking once the question is older than the window.
    if last and last.role == MessageRole.USER and last.created_at > window_start:
        raise busy
    return content


def reserve_usage(db: Session, user_id: int, content: str, settings: Settings, now: datetime | None = None) -> ChatUsage:
    """Adds the reservation row (not committed: the caller commits it together with the stored question, before the
    model is called, which also releases the user's lock). Returns it with its id assigned."""
    est_in, est_out = estimate_tokens(content, settings)
    row = ChatUsage(
        user_id=user_id, created_at=now or datetime.now(MEXICO_CITY),
        reserved_input_tokens=est_in, reserved_output_tokens=est_out, status=UsageStatus.RESERVED,
    )
    db.add(row)
    db.flush()
    return row


def settle_usage(
    db, usage_id: int, status: UsageStatus, input_tokens: int | None = None, output_tokens: int | None = None
) -> None:
    """Closes a reservation with the real tokens when known (otherwise the estimate keeps counting). Never raises:
    if it fails the row stays reserved, which still counts its estimate and stops blocking after the in-flight window."""
    if usage_id is None:
        return
    try:
        db.rollback()  # whatever state the session is in after a failed turn
        row = db.get(ChatUsage, usage_id)
        if row is None:
            return
        row.status = status
        row.settled_at = datetime.now(MEXICO_CITY)
        if input_tokens or output_tokens:
            row.input_tokens, row.output_tokens = int(input_tokens or 0), int(output_tokens or 0)
        db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("could not settle chat usage %s as %s", usage_id, status)
        db.rollback()
