"""One conversational turn: validate, store the question, run the agent, store the answer.

The question is committed BEFORE the model runs, so it survives any failure of the generation. Whatever happens
inside the agent, the user always ends up with a stored answer: the real one, or an error message without internals.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from langchain_core.embeddings import Embeddings
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.domain import Conversation, Message, MessageRole, MessageStatus
from app.services.agent.agent import run_agent
from app.services.agent.context import AgentContext
from app.services.chat_limits import check_can_send

logger = logging.getLogger(__name__)

TITLE_CHARS = 60
GENERATION_FAILED = "No pude generar la respuesta en este momento. Intenta de nuevo en unos minutos."


@dataclass
class ChatRuntime:
    agent: object  # the compiled LangChain agent; built once and reused
    embeddings: Embeddings


@dataclass
class TurnResult:
    user_message: Message
    assistant_message: Message


def _history(db: Session, conversation_id: int) -> list[tuple[str, str]]:
    rows = db.execute(
        select(Message.role, Message.content)
        .where(Message.conversation_id == conversation_id, Message.status == MessageStatus.COMPLETE)
        .order_by(Message.created_at, Message.id)
    ).all()
    return [(role.value, content) for role, content in rows]


def send_message(
    db: Session, user_id: int, conversation: Conversation, content: str, settings: Settings,
    runtime: ChatRuntime, now: datetime | None = None,
) -> TurnResult:
    """Raises `ChatLimitError` (nothing stored) when a limit applies; otherwise always returns both messages."""
    content = check_can_send(db, user_id, conversation.id, content, settings, now=now)
    history = _history(db, conversation.id)  # earlier turns only: taken before the new question is stored

    question = Message(conversation_id=conversation.id, role=MessageRole.USER, content=content)
    db.add(question)
    if conversation.title is None:
        conversation.title = " ".join(content.split())[:TITLE_CHARS].rstrip()
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()

    ctx = AgentContext(db=db, user_id=user_id, embeddings=runtime.embeddings, user_message=content, settings=settings)
    try:
        run = run_agent(runtime.agent, ctx, content, history, settings)
    except Exception:  # noqa: BLE001 - any provider/network/agent failure must still end in a stored answer
        logger.exception("agent turn failed for conversation %s", conversation.id)
        db.rollback()
        answer = Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=GENERATION_FAILED, status=MessageStatus.ERROR)
    else:
        if run.anomalies:
            logger.warning("citation anomalies in conversation %s: %s", conversation.id, run.anomalies)
        answer = Message(
            conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=run.answer,
            status=MessageStatus.ERROR if run.limit_reached else MessageStatus.COMPLETE,
            citations=run.citations or None, tool_calls=run.tool_calls or None,
            model=run.model, input_tokens=run.input_tokens, output_tokens=run.output_tokens,
        )
    db.add(answer)
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(question)
    db.refresh(answer)
    return TurnResult(user_message=question, assistant_message=answer)
