"""Conversations, their messages and per-message feedback. Ownership always comes from the token's user;
a conversation or message that is not yours looks exactly like one that does not exist (404)."""
import logging
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models.domain import Conversation, Message, MessageFeedback, MessageRole
from app.schemas.chat import (
    ConversationPublic, ConversationRename, FeedbackRequest, MessagePublic, SendMessageRequest, SendMessageResponse,
)
from app.services.chat import ChatRuntime, send_message
from app.services.chat_limits import ChatLimitError

logger = logging.getLogger(__name__)

router = APIRouter()

NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")


@lru_cache
def _build_runtime() -> ChatRuntime:
    from app.services.agent.agent import build_agent
    from app.services.ingestion.embedder import build_embeddings

    settings = get_settings()
    return ChatRuntime(agent=build_agent(settings), embeddings=build_embeddings(settings))


def get_chat_runtime() -> ChatRuntime:
    """The agent is built once, on first use. Without an API key the chat is unavailable (fails closed)."""
    try:
        return _build_runtime()
    except RuntimeError as error:
        logger.error("chat runtime unavailable: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "asistente_no_disponible", "message": "El asistente no está disponible en este momento."},
        ) from error


def owned_conversation(db: DbSession, user_id: int, conversation_id: int) -> Conversation:
    conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id))
    if conversation is None:
        raise NOT_FOUND
    return conversation


def owned_assistant_message(db: DbSession, user_id: int, message_id: int) -> Message:
    message = db.scalar(
        select(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Message.id == message_id, Message.role == MessageRole.ASSISTANT, Conversation.user_id == user_id)
    )
    if message is None:
        raise NOT_FOUND
    return message


@router.get("/conversations", response_model=list[ConversationPublic])
def list_conversations(
    user: CurrentUser, db: DbSession, limit: Annotated[int, Query(ge=1, le=500)] = 100
) -> list[Conversation]:
    return list(db.scalars(
        select(Conversation).where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc()).limit(limit)
    ))


@router.post("/conversations", response_model=ConversationPublic, status_code=status.HTTP_201_CREATED)
def create_conversation(user: CurrentUser, db: DbSession) -> Conversation:
    conversation = Conversation(user_id=user.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.patch("/conversations/{conversation_id}", response_model=ConversationPublic)
def rename_conversation(conversation_id: int, payload: ConversationRename, user: CurrentUser, db: DbSession) -> Conversation:
    conversation = owned_conversation(db, user.id, conversation_id)
    conversation.title = payload.title
    db.commit()
    db.refresh(conversation)
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: int, user: CurrentUser, db: DbSession) -> Response:
    db.delete(owned_conversation(db, user.id, conversation_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessagePublic])
def list_messages(conversation_id: int, user: CurrentUser, db: DbSession) -> list[MessagePublic]:
    owned_conversation(db, user.id, conversation_id)
    rows = db.execute(
        select(Message, MessageFeedback.value)
        .outerjoin(MessageFeedback, (MessageFeedback.message_id == Message.id) & (MessageFeedback.user_id == user.id))
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at, Message.id)
    ).all()
    return [
        MessagePublic(
            id=m.id, role=m.role, content=m.content, status=m.status, citations=m.citations,
            created_at=m.created_at, feedback=value,
        )
        for m, value in rows
    ]


@router.put("/messages/{message_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
def set_feedback(message_id: int, payload: FeedbackRequest, user: CurrentUser, db: DbSession) -> Response:
    message = owned_assistant_message(db, user.id, message_id)
    vote = db.scalar(select(MessageFeedback).where(MessageFeedback.message_id == message.id, MessageFeedback.user_id == user.id))
    if vote:
        vote.value = payload.value
    else:
        db.add(MessageFeedback(message_id=message.id, user_id=user.id, value=payload.value))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/messages/{message_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
def clear_feedback(message_id: int, user: CurrentUser, db: DbSession) -> Response:
    message = owned_assistant_message(db, user.id, message_id)
    vote = db.scalar(select(MessageFeedback).where(MessageFeedback.message_id == message.id, MessageFeedback.user_id == user.id))
    if vote:
        db.delete(vote)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/conversations/{conversation_id}/messages", response_model=SendMessageResponse, status_code=status.HTTP_201_CREATED)
def post_message(
    conversation_id: int, payload: SendMessageRequest, user: CurrentUser, db: DbSession,
    runtime: Annotated[ChatRuntime, Depends(get_chat_runtime)],
) -> SendMessageResponse:
    conversation = owned_conversation(db, user.id, conversation_id)
    try:
        turn = send_message(db, user.id, conversation, payload.content, get_settings(), runtime)
    except ChatLimitError as error:
        raise HTTPException(status_code=error.status_code, detail={"code": error.code, "message": error.message}) from error

    def public(message: Message) -> MessagePublic:
        return MessagePublic(
            id=message.id, role=message.role, content=message.content, status=message.status,
            citations=message.citations, created_at=message.created_at, feedback=None,
        )

    return SendMessageResponse(user_message=public(turn.user_message), assistant_message=public(turn.assistant_message))
