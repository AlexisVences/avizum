import json

import pytest
from langchain_core.messages import AIMessage
from sqlalchemy import select

from app.core.config import Settings
from app.models.domain import Conversation, Message, MessageRole, MessageStatus, User
from app.services.agent.agent import build_agent, stream_agent
from app.services.agent.context import AgentContext
from app.services.chat import ChatRuntime, begin_turn, stream_turn
from tests.fakes import FakeStreaming, tool_call
from tests.test_retrieval import FixedQuery, add_chunk, add_source, vec

ANSWER = "Se inmoviliza en estos casos [1] y también [99]."
SCRIPT = [tool_call("buscar_legislacion", {"consulta": "candado inmovilizador"}), AIMessage(content=ANSWER)]


def settings(**overrides) -> Settings:
    return Settings(_env_file=None, openai_api_key="test-key", **overrides)


def seed(db):
    source = add_source(db, "reglamento-transito", "a")
    add_chunk(db, source, "33", "Inmovilizador en vehículos estacionados", vec(1, 0), fraction="II", page=35)
    user = User(first_name="Ana", last_name="López", email="ana@example.com", password_hash="x")
    db.add(user)
    db.flush()
    conversation = Conversation(user_id=user.id)
    db.add(conversation)
    db.commit()
    return user, conversation


def runtime(model, cfg) -> ChatRuntime:
    return ChatRuntime(agent=build_agent(cfg, model=model), embeddings=FixedQuery(vec(1, 0)))


def test_the_agent_stream_yields_tool_events_then_text_tokens_then_the_summary(client):
    _, factory = client
    with factory() as db:
        seed(db)
        cfg = settings()
        ctx = AgentContext(db=db, user_id=None, embeddings=FixedQuery(vec(1, 0)), user_message="araña", settings=cfg)
        agent = build_agent(cfg, model=FakeStreaming(script=SCRIPT))

        events = list(stream_agent(agent, ctx, "araña", [], cfg))

        kinds = [kind for kind, _ in events]
        assert kinds[0] == "tool_start" and events[0][1] == {"name": "buscar_legislacion", "args": {"consulta": "candado inmovilizador"}}
        assert kinds[1] == "tool_end" and events[1][1] == {"name": "buscar_legislacion", "ok": True}
        tokens = [data["text"] for kind, data in events if kind == "token"]
        assert "".join(tokens).strip() == ANSWER and len(tokens) > 3  # arrived piece by piece, not in one block
        assert kinds[-1] == "run"
        run = events[-1][1]
        assert run.answer == "Se inmoviliza en estos casos [1] y también." and run.anomalies == [{"tipo": "marca_invalida", "n": 99}]
        assert [c["article"] for c in run.citations] == ["33"] and run.input_tokens == 200  # two model calls of 100


def test_a_streamed_turn_stores_the_answer_and_ends_with_citations_then_done(client):
    _, factory = client
    with factory() as db:
        user, conversation = seed(db)
        cfg = settings()
        prepared = begin_turn(db, user.id, conversation, "me pusieron la araña", cfg)
        events = list(stream_turn(factory, user.id, prepared, cfg, runtime(FakeStreaming(script=SCRIPT), cfg)))

        kinds = [kind for kind, _ in events]
        assert kinds[0] == "tool_start" and kinds[-2:] == ["citations", "done"] and "error" not in kinds
        done = events[-1][1]
        assert done["text"] == "Se inmoviliza en estos casos [1] y también." and done["usage"] == {"input_tokens": 200, "output_tokens": 40}
        assert events[-2][1][0]["url"].endswith("#page=35")

        answer = db.scalar(select(Message).where(Message.id == done["assistant_message_id"]))
        assert (answer.status, answer.content) == (MessageStatus.COMPLETE, done["text"])
        assert answer.citations[0]["orden"] == 1 and answer.tool_calls[0]["name"] == "buscar_legislacion"
        assert db.scalar(select(Message.content).where(Message.id == prepared.user_message_id)) == "me pusieron la araña"


def test_a_failure_in_the_middle_of_the_stream_keeps_the_question_and_sends_a_clean_error(client):
    _, factory = client
    with factory() as db:
        user, conversation = seed(db)
        cfg = settings()
        prepared = begin_turn(db, user.id, conversation, "hola", cfg)
        model = FakeStreaming(script=[AIMessage(content="Una respuesta que se corta a la mitad del camino")], fail_after_words=3)

        events = list(stream_turn(factory, user.id, prepared, cfg, runtime(model, cfg)))

        kinds = [kind for kind, _ in events]
        assert kinds[-1] == "error" and "done" not in kinds
        error = events[-1][1]
        assert error["code"] == "generacion_fallida" and "sk-SECRET" not in json.dumps(error)
        stored = db.scalars(select(Message).where(Message.conversation_id == conversation.id).order_by(Message.id)).all()
        assert [(m.role, m.status) for m in stored] == [(MessageRole.USER, MessageStatus.COMPLETE), (MessageRole.ASSISTANT, MessageStatus.ERROR)]
        assert "sk-SECRET" not in stored[1].content


def test_closing_the_stream_early_saves_the_partial_answer_as_cancelled(client):
    _, factory = client
    with factory() as db:
        user, conversation = seed(db)
        cfg = settings()
        prepared = begin_turn(db, user.id, conversation, "hola", cfg)
        model = FakeStreaming(script=[AIMessage(content="Primera parte de una respuesta larga que el usuario interrumpe")])
        stream = stream_turn(factory, user.id, prepared, cfg, runtime(model, cfg))

        received = []
        for kind, data in stream:
            received.append((kind, data))
            if kind == "token" and len(received) >= 3:
                break
        stream.close()  # what happens when the browser aborts the request

        answer = db.scalars(select(Message).where(Message.role == MessageRole.ASSISTANT)).one()
        assert answer.status == MessageStatus.CANCELLED
        assert answer.content.startswith("Primera parte") and answer.content != model.script[0].content
        question = db.scalar(select(Message).where(Message.id == prepared.user_message_id))
        assert question.status == MessageStatus.COMPLETE  # the question is never lost
