import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models.domain import Conversation, Message, MessageFeedback, MessageRole, MessageStatus, User


def make_user(db, email="ana@example.com") -> User:
    user = User(first_name="Ana", last_name="López", email=email, password_hash="x")
    db.add(user)
    db.flush()
    return user


def make_conversation(db, user: User, title: str | None = None) -> Conversation:
    conversation = Conversation(user_id=user.id, title=title)
    db.add(conversation)
    db.flush()
    return conversation


def make_message(db, conversation: Conversation, role=MessageRole.USER, content="hola", **extra) -> Message:
    message = Message(conversation_id=conversation.id, role=role, content=content, **extra)
    db.add(message)
    db.flush()
    return message


def test_a_message_keeps_citations_tool_calls_and_usage_as_json(client):
    _, factory = client
    with factory() as db:
        conversation = make_conversation(db, make_user(db))
        message = make_message(
            db, conversation, MessageRole.ASSISTANT, "Respuesta [1]",
            citations=[{"n": 1, "article": "30", "page": 31}],
            tool_calls=[{"name": "buscar_legislacion", "args": {"consulta": "placas"}}],
            model="gpt-5-mini", input_tokens=1200, output_tokens=180,
        )
        db.commit()
        db.refresh(message)
        assert message.status == MessageStatus.COMPLETE
        assert message.citations[0]["page"] == 31 and message.tool_calls[0]["name"] == "buscar_legislacion"
        assert (message.input_tokens, message.output_tokens) == (1200, 180)


def test_deleting_a_conversation_deletes_its_messages_and_their_feedback(client):
    _, factory = client
    with factory() as db:
        user = make_user(db)
        conversation = make_conversation(db, user)
        reply = make_message(db, conversation, MessageRole.ASSISTANT, "Respuesta")
        db.add(MessageFeedback(message_id=reply.id, user_id=user.id, value=1))
        db.commit()

        db.delete(conversation)
        db.commit()
        assert db.scalar(select(func.count()).select_from(Message)) == 0
        assert db.scalar(select(func.count()).select_from(MessageFeedback)) == 0


def test_deleting_a_user_deletes_their_conversations(client):
    _, factory = client
    with factory() as db:
        user = make_user(db)
        make_message(db, make_conversation(db, user))
        db.commit()
        db.delete(user)
        db.commit()
        assert db.scalar(select(func.count()).select_from(Conversation)) == 0


def test_one_feedback_per_user_per_message_and_only_plus_or_minus_one(client):
    _, factory = client
    with factory() as db:
        user = make_user(db)
        reply = make_message(db, make_conversation(db, user), MessageRole.ASSISTANT, "Respuesta")
        db.add(MessageFeedback(message_id=reply.id, user_id=user.id, value=-1))
        db.commit()

        db.add(MessageFeedback(message_id=reply.id, user_id=user.id, value=1))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        other = make_user(db, "luis@example.com")
        db.add(MessageFeedback(message_id=reply.id, user_id=other.id, value=0))
        with pytest.raises(IntegrityError):
            db.commit()
