from datetime import datetime, timedelta, timezone

import pytest
from langchain_core.messages import AIMessage
from sqlalchemy import select

from app.core.config import Settings
from app.models.domain import Conversation, Message, MessageRole, MessageStatus, User
from app.services.agent.agent import build_agent
from app.services.chat import ChatRuntime, send_message
from app.services.chat_limits import ChatLimitError
from tests.test_agent import RecordingModel, tool_call
from tests.test_retrieval import FixedQuery, add_chunk, add_source, vec


def settings(**overrides) -> Settings:
    return Settings(_env_file=None, openai_api_key="test-key", **overrides)


def runtime(model, **cfg) -> tuple[ChatRuntime, Settings]:
    cfg = settings(**cfg)
    return ChatRuntime(agent=build_agent(cfg, model=model), embeddings=FixedQuery(vec(1, 0))), cfg


def scripted(*replies) -> RecordingModel:
    return RecordingModel(messages=iter(list(replies)), seen=[])


def make_conversation(db, email="ana@example.com") -> tuple[User, Conversation]:
    user = User(first_name="Ana", last_name="López", email=email, password_hash="x")
    db.add(user)
    db.flush()
    conversation = Conversation(user_id=user.id)
    db.add(conversation)
    db.flush()
    return user, conversation


def stored(db, conversation) -> list[Message]:
    return list(db.scalars(select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at, Message.id)))


def seed_law(db):
    source = add_source(db, "reglamento-transito", "a")
    add_chunk(db, source, "33", "Inmovilizador en vehículos estacionados", vec(1, 0), fraction="II", page=35)
    db.commit()


def test_a_turn_stores_the_question_then_the_answer_with_citations_trace_and_usage(client):
    _, factory = client
    with factory() as db:
        seed_law(db)
        user, conversation = make_conversation(db)
        rt, cfg = runtime(scripted(
            tool_call("buscar_legislacion", {"consulta": "candado inmovilizador"}),
            AIMessage(content="Se inmoviliza en estos casos [1]."),
        ))

        reply = send_message(db, user.id, conversation, "  me pusieron la araña  ", cfg, rt).assistant_message

        question, answer = stored(db, conversation)
        assert (question.role, question.content, question.status) == (MessageRole.USER, "me pusieron la araña", MessageStatus.COMPLETE)
        assert reply.id == answer.id and answer.role == MessageRole.ASSISTANT and answer.status == MessageStatus.COMPLETE
        assert answer.content == "Se inmoviliza en estos casos [1]."
        assert answer.citations[0]["article"] == "33" and answer.citations[0]["orden"] == 1
        assert answer.tool_calls[0]["name"] == "buscar_legislacion" and answer.model == cfg.openai_chat_model
        assert conversation.title == "me pusieron la araña"


def test_the_title_is_the_first_sixty_characters_of_the_first_question_and_never_changes(client):
    _, factory = client
    with factory() as db:
        user, conversation = make_conversation(db)
        rt, cfg = runtime(scripted(AIMessage(content="uno"), AIMessage(content="dos")))
        long = "¿Qué pasa si me detienen sin licencia y además traigo el seguro vencido hoy por la mañana?   "
        send_message(db, user.id, conversation, long, cfg, rt)
        assert conversation.title == " ".join(long.split())[:60]
        assert len(conversation.title) == 60 and conversation.title.endswith("traigo el seg")
        conversation.updated_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        send_message(db, user.id, conversation, "otra pregunta", cfg, rt)
        assert conversation.title.startswith("¿Qué pasa si me detienen")


def test_when_generation_fails_the_question_is_kept_and_the_answer_is_an_error_without_internals(client):
    _, factory = client

    class Down(RecordingModel):
        def _generate(self, *args, **kwargs):
            raise RuntimeError("401 invalid api key sk-SECRET-123")

    with factory() as db:
        user, conversation = make_conversation(db)
        rt, cfg = runtime(Down(messages=iter([]), seen=[]))
        reply = send_message(db, user.id, conversation, "hola", cfg, rt).assistant_message

        question, answer = stored(db, conversation)
        assert question.content == "hola" and answer.status == MessageStatus.ERROR
        assert reply.status == MessageStatus.ERROR
        assert "sk-SECRET" not in answer.content and "invalid api key" not in answer.content
        assert "intenta de nuevo" in answer.content.lower()


def test_a_turn_cut_off_by_the_step_limit_is_stored_as_an_error_answer(client):
    _, factory = client
    from itertools import cycle

    with factory() as db:
        add_source(db, "reglamento-transito", "a")
        db.commit()
        user, conversation = make_conversation(db)
        endless = cycle([tool_call("buscar_legislacion", {"consulta": f"tema {i} distinto"}, f"c{i}") for i in range(50)])
        rt, cfg = runtime(RecordingModel(messages=endless, seen=[]), chat_max_agent_steps=3)
        reply = send_message(db, user.id, conversation, "x", cfg, rt).assistant_message
        assert reply.status == MessageStatus.ERROR and "no pude completar" in reply.content.lower()


def test_history_sent_to_the_model_has_the_complete_earlier_messages_only(client):
    _, factory = client
    with factory() as db:
        user, conversation = make_conversation(db)
        base = datetime.now(timezone.utc) - timedelta(hours=1)
        for i, (role, text, status) in enumerate([
            (MessageRole.USER, "pregunta uno", MessageStatus.COMPLETE),
            (MessageRole.ASSISTANT, "respuesta uno", MessageStatus.COMPLETE),
            (MessageRole.USER, "pregunta dos", MessageStatus.COMPLETE),
            (MessageRole.ASSISTANT, "se cayó", MessageStatus.ERROR),
        ]):
            db.add(Message(conversation_id=conversation.id, role=role, content=text, status=status, created_at=base + timedelta(minutes=i)))
        db.commit()
        model = scripted(AIMessage(content="ok"))
        rt, cfg = runtime(model)

        send_message(db, user.id, conversation, "pregunta tres", cfg, rt)

        sent = [m.content for m in model.seen[0] if m.type in ("human", "ai")]
        assert sent == ["pregunta uno", "respuesta uno", "pregunta dos", "pregunta tres"]


def test_a_second_message_while_one_is_being_answered_is_rejected_until_it_goes_stale(client):
    _, factory = client
    with factory() as db:
        user, conversation = make_conversation(db)
        pending = Message(conversation_id=conversation.id, role=MessageRole.USER, content="sin respuesta")
        db.add(pending)
        db.commit()
        rt, cfg = runtime(scripted(AIMessage(content="ok")))

        with pytest.raises(ChatLimitError) as raised:
            send_message(db, user.id, conversation, "otra", cfg, rt)
        assert (raised.value.status_code, raised.value.code) == (409, "respuesta_en_curso")
        assert len(stored(db, conversation)) == 1  # the rejected message was not stored

        pending.created_at = datetime.now(timezone.utc) - timedelta(minutes=3)  # a crashed turn does not block forever
        db.commit()
        assert send_message(db, user.id, conversation, "otra", cfg, rt).assistant_message.content == "ok"


def test_the_limits_apply_before_anything_is_stored(client):
    _, factory = client
    with factory() as db:
        user, conversation = make_conversation(db)
        rt, cfg = runtime(scripted(AIMessage(content="ok")))
        with pytest.raises(ChatLimitError) as raised:
            send_message(db, user.id, conversation, "   ", cfg, rt)
        assert raised.value.status_code == 422 and stored(db, conversation) == []
