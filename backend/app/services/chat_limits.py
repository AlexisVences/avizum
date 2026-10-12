"""The usage limits that keep the chat's cost and abuse bounded (spec section 2).

They run before anything is stored or sent to the model, in this order: the message itself (422), the conversation
(409) and the user's day (429). Each raises `ChatLimitError` with the HTTP status the route should answer.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.domain import Conversation, Message, MessageRole

MEXICO_CITY = ZoneInfo("America/Mexico_City")


class ChatLimitError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
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
        )
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
