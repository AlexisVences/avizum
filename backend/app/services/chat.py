"""One conversational turn: validate, store the question, run the agent, store the answer.

The question is committed BEFORE the model runs, so it survives any failure of the generation. Whatever happens
inside the agent, the user always ends up with a stored answer: the real one, or an error message without internals.
"""
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone

from langchain_core.embeddings import Embeddings
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.domain import Conversation, Message, MessageRole, MessageStatus
from app.services.agent.agent import AgentRun, run_agent, stream_agent
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


@dataclass
class PreparedTurn:
    """The question is already stored and committed; what is left is to generate and store the answer."""

    conversation_id: int
    user_message_id: int
    content: str
    history: list[tuple[str, str]]


def begin_turn(
    db: Session, user_id: int, conversation: Conversation, content: str, settings: Settings, now: datetime | None = None
) -> PreparedTurn:
    """Raises `ChatLimitError` (nothing stored) when a limit applies; otherwise stores the question and commits."""
    content = check_can_send(db, user_id, conversation.id, content, settings, now=now)
    history = _history(db, conversation.id)  # earlier turns only: taken before the new question is stored

    question = Message(conversation_id=conversation.id, role=MessageRole.USER, content=content)
    db.add(question)
    if conversation.title is None:
        conversation.title = " ".join(content.split())[:TITLE_CHARS].rstrip()
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    return PreparedTurn(conversation.id, question.id, content, history)


def _store_answer(
    db: Session, conversation_id: int, *, run: AgentRun | None = None, status: MessageStatus | None = None,
    content: str | None = None,
) -> Message:
    if run is not None:
        answer = Message(
            conversation_id=conversation_id, role=MessageRole.ASSISTANT, content=run.answer,
            status=status or (MessageStatus.ERROR if run.limit_reached else MessageStatus.COMPLETE),
            citations=run.citations or None, tool_calls=run.tool_calls or None,
            model=run.model, input_tokens=run.input_tokens, output_tokens=run.output_tokens,
        )
    else:
        answer = Message(
            conversation_id=conversation_id, role=MessageRole.ASSISTANT, content=content or GENERATION_FAILED,
            status=status or MessageStatus.ERROR,
        )
    db.add(answer)
    conversation = db.get(Conversation, conversation_id)
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(answer)
    return answer


def run_turn(db: Session, user_id: int, prepared: PreparedTurn, settings: Settings, runtime: ChatRuntime) -> Message:
    ctx = AgentContext(db=db, user_id=user_id, embeddings=runtime.embeddings, user_message=prepared.content, settings=settings)
    try:
        run = run_agent(runtime.agent, ctx, prepared.content, prepared.history, settings)
    except Exception:  # noqa: BLE001 - any provider/network/agent failure must still end in a stored answer
        logger.exception("agent turn failed for conversation %s", prepared.conversation_id)
        db.rollback()
        return _store_answer(db, prepared.conversation_id)
    if run.anomalies:
        logger.warning("citation anomalies in conversation %s: %s", prepared.conversation_id, run.anomalies)
    return _store_answer(db, prepared.conversation_id, run=run)


def send_message(
    db: Session, user_id: int, conversation: Conversation, content: str, settings: Settings,
    runtime: ChatRuntime, now: datetime | None = None,
) -> TurnResult:
    """Validate, store the question, run the agent, store the answer. Always returns both messages."""
    prepared = begin_turn(db, user_id, conversation, content, settings, now=now)
    answer = run_turn(db, user_id, prepared, settings, runtime)
    return TurnResult(user_message=db.get(Message, prepared.user_message_id), assistant_message=answer)


def stream_turn(
    session_factory, user_id: int, prepared: PreparedTurn, settings: Settings, runtime: ChatRuntime
) -> Iterator[tuple[str, dict]]:
    """Yields (event, data) pairs for the SSE layer. It opens its OWN database session: it keeps running after the
    request handler returned, when the request's session may already be closed.

    The turn always ends stored: `done` after a real answer, `error` after a failure, and if the consumer closes the
    stream early the partial text is saved as `cancelled`. The question was committed in `begin_turn`.
    """
    partial: list[str] = []
    with session_factory() as db:
        ctx = AgentContext(db=db, user_id=user_id, embeddings=runtime.embeddings, user_message=prepared.content, settings=settings)
        try:
            for kind, data in stream_agent(runtime.agent, ctx, prepared.content, prepared.history, settings):
                if kind == "run":
                    run = data
                    if run.anomalies:
                        logger.warning("citation anomalies in conversation %s: %s", prepared.conversation_id, run.anomalies)
                    answer = _store_answer(db, prepared.conversation_id, run=run)
                    yield "citations", run.citations
                    yield "done", {
                        "assistant_message_id": answer.id,
                        "text": answer.content,
                        "usage": {"input_tokens": run.input_tokens, "output_tokens": run.output_tokens},
                    }
                    return
                if kind == "token":
                    partial.append(data["text"])
                yield kind, data
        except GeneratorExit:
            # The client went away (browser aborted). Keep what was generated; the question is already stored.
            db.rollback()
            _store_answer(db, prepared.conversation_id, status=MessageStatus.CANCELLED, content="".join(partial).strip() or "(respuesta interrumpida)")
            raise
        except Exception:  # noqa: BLE001
            logger.exception("streamed turn failed for conversation %s", prepared.conversation_id)
            db.rollback()
            answer = _store_answer(db, prepared.conversation_id)
            yield "error", {"code": "generacion_fallida", "message": GENERATION_FAILED, "assistant_message_id": answer.id}
