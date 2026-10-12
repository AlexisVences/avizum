from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models.domain import MessageRole, MessageStatus

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class ConversationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationRename(BaseModel):
    title: Title


class MessagePublic(BaseModel):
    """What the interface may see. The tool trace, model name and token counts stay internal."""

    id: int
    role: MessageRole
    content: str
    status: MessageStatus
    citations: list[dict] | None
    created_at: datetime
    feedback: Literal[1, -1] | None  # the viewer's own vote


class FeedbackRequest(BaseModel):
    value: Literal[1, -1]


class SendMessageRequest(BaseModel):
    # No max_length here on purpose: the limit check answers with our own 422 (code and message), not a generic one.
    content: str


class SendMessageResponse(BaseModel):
    user_message: MessagePublic
    assistant_message: MessagePublic
