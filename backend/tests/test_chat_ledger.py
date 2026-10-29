"""The usage ledger behind the chat limits: durable (deleting conversations does not reset it), counts cancelled and
failed turns, and a per-user lock + reservation closes the check-then-spend race."""
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from langchain_core.messages import AIMessage
from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.models.domain import ChatUsage, Conversation, Message, MessageRole, UsageStatus, User
from app.services import chat_limits
from app.services.chat import begin_turn, stream_turn
from app.services.chat_limits import ChatLimitError, estimate_tokens, estimated_cost_usd
from tests.fakes import FakeStreaming
from tests.test_conversations_api import (
    budget_settings, install_runtime, install_streaming_runtime, post, read_sse, seed_conversation, signup, user_id,
)
from tests.test_streaming import runtime as streaming_runtime

QUESTION = "¿Qué hago?"


def turn_cost() -> Decimal:
    cfg = get_settings()
    tokens_in, tokens_out = estimate_tokens(QUESTION, cfg)
    return (Decimal(tokens_in) * cfg.llm_price_input_per_million + Decimal(tokens_out) * cfg.llm_price_output_per_million) / Decimal(1_000_000)


def ledger(factory) -> list[ChatUsage]:
    with factory() as db:
        return list(db.scalars(select(ChatUsage).order_by(ChatUsage.id)))


def delete_conversation(http, headers, conversation_id):
    assert http.delete(f"/api/v1/conversations/{conversation_id}", headers=headers).status_code == 204


def test_deleting_the_conversation_does_not_reset_the_cost_cap(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    budget_settings(monkeypatch, daily_user_cost_usd_limit=turn_cost() * Decimal("2.5"))  # room for two turns
    install_runtime(http, *[AIMessage(content="ok")] * 5)
    first = seed_conversation(factory, "ana@example.com")
    assert post(http, ana, first, QUESTION).status_code == 201
    assert post(http, ana, first, QUESTION).status_code == 201
    third = post(http, ana, first, QUESTION)
    assert third.status_code == 429 and third.json()["detail"]["code"] == "presupuesto_diario"

    delete_conversation(http, ana, first)  # the old way of starting over
    again = post(http, ana, seed_conversation(factory, "ana@example.com"), QUESTION)
    assert again.status_code == 429 and again.json()["detail"]["code"] == "presupuesto_diario"
    assert int(again.headers["Retry-After"]) >= 60
    assert len(ledger(factory)) == 2  # the refusals left no ledger row, deleting left both


def test_deleting_the_conversation_does_not_reset_the_daily_message_cap(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("0"), chat_daily_message_limit=2)
    install_runtime(http, *[AIMessage(content="ok")] * 5)
    first = seed_conversation(factory, "ana@example.com")
    assert post(http, ana, first).status_code == 201 and post(http, ana, first).status_code == 201
    delete_conversation(http, ana, first)
    response = post(http, ana, seed_conversation(factory, "ana@example.com"))
    assert response.status_code == 429 and response.json()["detail"]["code"] == "limite_diario"
    with factory() as db:
        assert db.scalar(select(Message.id)) is None  # the messages are gone, the usage is not
    assert len(ledger(factory)) == 2


def test_a_turn_that_errors_while_streaming_still_counts_its_estimate(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    budget_settings(monkeypatch, daily_user_cost_usd_limit=turn_cost() * Decimal("1.5"))
    install_streaming_runtime(http, [AIMessage(content="Una respuesta que se corta a la mitad del camino")], fail_after_words=2)
    conversation_id = seed_conversation(factory, "ana@example.com")
    with http.stream("POST", f"/api/v1/conversations/{conversation_id}/messages", headers={**ana, "accept": "text/event-stream"},
                     json={"content": QUESTION}) as response:
        assert read_sse(response)[-1][0] == "error"

    (row,) = ledger(factory)
    assert row.status == UsageStatus.ERROR and row.input_tokens == 0 and row.settled_at is not None
    with factory() as db:
        spent, _ = estimated_cost_usd(db, datetime.now(timezone.utc) - timedelta(hours=24), user_id(factory, "ana@example.com"), get_settings())
    assert spent == turn_cost()
    assert post(http, ana, conversation_id, QUESTION).status_code == 429  # the failed turn used up the room


def test_a_cancelled_turn_counts_its_estimate_and_is_settled_as_cancelled(client, monkeypatch):
    _, factory = client
    from tests.test_streaming import seed

    with factory() as db:
        user, conversation = seed(db)
        cfg = Settings(_env_file=None, openai_api_key="test-key")
        prepared = begin_turn(db, user.id, conversation, QUESTION, cfg)
        model = FakeStreaming(script=[AIMessage(content="Primera parte de una respuesta larga que el usuario interrumpe")])
        stream = stream_turn(factory, user.id, prepared, cfg, streaming_runtime(model, cfg))
        received = 0
        for kind, _data in stream:
            received += 1
            if kind == "token" and received >= 3:
                break
        stream.close()

        (row,) = ledger(factory)
        assert row.id == prepared.usage_id and row.status == UsageStatus.CANCELLED and row.settled_at is not None
        spent, _ = estimated_cost_usd(db, datetime.now(timezone.utc) - timedelta(hours=24), user.id, get_settings())
        assert spent == turn_cost()


def test_a_turn_killed_by_an_unexpected_exception_is_never_left_reserved(client):
    _, factory = client
    from app.services.chat import run_turn, ChatRuntime
    from tests.test_streaming import seed

    class Boom(BaseException):
        pass

    class Agent:
        def invoke(self, *args, **kwargs):
            raise Boom()

    with factory() as db:
        user, conversation = seed(db)
        cfg = Settings(_env_file=None, openai_api_key="test-key")
        prepared = begin_turn(db, user.id, conversation, QUESTION, cfg)
        assert ledger(factory)[0].status == UsageStatus.RESERVED
        with pytest.raises(Boom):
            run_turn(db, user.id, prepared, cfg, ChatRuntime(agent=Agent(), embeddings=None))
        assert ledger(factory)[0].status == UsageStatus.ERROR


def test_settling_a_completed_turn_stores_the_real_tokens_and_status(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="ok", usage_metadata={"input_tokens": 700, "output_tokens": 90, "total_tokens": 790}))
    conversation_id = seed_conversation(factory, "ana@example.com")
    assert post(http, ana, conversation_id, QUESTION).status_code == 201

    (row,) = ledger(factory)
    assert (row.status, row.input_tokens, row.output_tokens) == (UsageStatus.SETTLED, 700, 90)
    assert row.settled_at is not None and row.reserved_input_tokens > 700 and row.reserved_output_tokens == 1800
    with factory() as db:  # with real tokens the actual cost counts, not the larger estimate
        spent, _ = estimated_cost_usd(db, datetime.now(timezone.utc) - timedelta(hours=24), row.user_id, get_settings())
    assert spent == (Decimal(700) * Decimal("0.25") + Decimal(90) * Decimal("2")) / Decimal(1_000_000)


def test_a_stale_reservation_stops_blocking_but_still_counts(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, *[AIMessage(content="ok")] * 3)
    other_conversation = seed_conversation(factory, "ana@example.com")
    uid = user_id(factory, "ana@example.com")

    def reserve(age: timedelta):
        with factory() as db:
            db.add(ChatUsage(
                user_id=uid, created_at=datetime.now(timezone.utc) - age, reserved_input_tokens=1_000_000,
                reserved_output_tokens=0, status=UsageStatus.RESERVED,
            ))
            db.commit()

    reserve(timedelta(seconds=5))  # young: a turn is in flight (in another conversation: the guard is per user)
    busy = post(http, ana, seed_conversation(factory, "ana@example.com"), QUESTION)
    assert busy.status_code == 409 and busy.json()["detail"]["code"] == "respuesta_en_curso"

    with factory() as db:
        db.execute(ChatUsage.__table__.update().values(created_at=datetime.now(timezone.utc) - timedelta(minutes=10)))
        db.commit()
    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("0.2"))  # the stale 1M tokens = 0.25 USD
    counted = post(http, ana, other_conversation, QUESTION)
    assert counted.status_code == 429 and counted.json()["detail"]["code"] == "presupuesto_diario"  # not 409: no longer blocks

    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("1"))
    assert post(http, ana, other_conversation, QUESTION).status_code == 201  # blocks nothing, and the room was enough


def test_another_user_is_unaffected_by_a_reservation_or_a_spent_budget(client, monkeypatch):
    http, factory = client
    signup(http, "ana@example.com")
    luis = signup(http, "luis@example.com")
    install_runtime(http, AIMessage(content="ok"))
    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("0.25"))
    with factory() as db:
        db.add(ChatUsage(user_id=user_id(factory, "ana@example.com"), reserved_input_tokens=9_000_000, reserved_output_tokens=0, status=UsageStatus.RESERVED))
        db.commit()
    assert post(http, luis, seed_conversation(factory, "luis@example.com"), QUESTION).status_code == 201


def test_a_refused_turn_creates_no_ledger_row(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="no debe salir"))
    budget_settings(monkeypatch, chat_daily_message_limit=0)
    assert post(http, ana, seed_conversation(factory, "ana@example.com"), QUESTION).status_code == 429
    assert post(http, ana, seed_conversation(factory, "ana@example.com"), "   ").status_code == 422
    assert ledger(factory) == []


# ---------- concurrency

def _race(factory, uid: int, conversation_ids: list[int], cfg: Settings, monkeypatch) -> list[str]:
    """Each thread opens its own session and tries to take a turn in its own conversation. The budget check is slowed
    so that without the per-user lock every thread would pass it before any reservation exists."""
    real = chat_limits.check_budget

    def slow_budget(*args, **kwargs):
        real(*args, **kwargs)
        threading.Event().wait(0.3)

    monkeypatch.setattr(chat_limits, "check_budget", slow_budget)
    barrier = threading.Barrier(len(conversation_ids))

    def attempt(conversation_id: int) -> str:
        with factory() as db:
            conversation = db.get(Conversation, conversation_id)
            barrier.wait()
            try:
                begin_turn(db, uid, conversation, QUESTION, cfg)
                return "ok"
            except ChatLimitError as error:
                db.rollback()
                return error.code

    with ThreadPoolExecutor(len(conversation_ids)) as pool:
        return list(pool.map(attempt, conversation_ids))


def test_parallel_turns_of_one_user_reserve_one_at_a_time_under_the_budget(client, monkeypatch):
    http, factory = client
    signup(http, "ana@example.com")
    uid = user_id(factory, "ana@example.com")
    cfg = Settings(_env_file=None, openai_api_key="test-key", chat_in_flight_seconds=0,  # budget alone must serialise
                   daily_user_cost_usd_limit=turn_cost() * Decimal("1.5"))  # room for exactly one turn
    conversations = [seed_conversation(factory, "ana@example.com") for _ in range(5)]

    outcomes = _race(factory, uid, conversations, cfg, monkeypatch)

    assert sorted(outcomes) == ["ok"] + ["presupuesto_diario"] * 4
    assert len(ledger(factory)) == 1


def test_parallel_turns_of_one_user_get_409_while_one_is_in_flight(client, monkeypatch):
    http, factory = client
    signup(http, "ana@example.com")
    uid = user_id(factory, "ana@example.com")
    cfg = Settings(_env_file=None, openai_api_key="test-key")
    conversations = [seed_conversation(factory, "ana@example.com") for _ in range(5)]
    outcomes = _race(factory, uid, conversations, cfg, monkeypatch)
    assert sorted(outcomes) == ["ok"] + ["respuesta_en_curso"] * 4


def test_parallel_turns_cannot_exceed_the_daily_message_cap(client, monkeypatch):
    http, factory = client
    signup(http, "ana@example.com")
    uid = user_id(factory, "ana@example.com")
    cfg = Settings(_env_file=None, openai_api_key="test-key", chat_in_flight_seconds=0, daily_user_cost_usd_limit=0, chat_daily_message_limit=2)
    conversations = [seed_conversation(factory, "ana@example.com") for _ in range(5)]
    outcomes = _race(factory, uid, conversations, cfg, monkeypatch)
    assert sorted(outcomes) == ["limite_diario"] * 3 + ["ok"] * 2


def test_parallel_http_requests_call_the_model_at_most_once_when_the_cap_leaves_room_for_one(client, monkeypatch):
    from tests.test_agent import RecordingModel
    from app.api.conversations import get_chat_runtime
    from app.services.agent.agent import build_agent
    from app.services.chat import ChatRuntime
    from tests.test_retrieval import FixedQuery, vec

    http, factory = client
    ana = signup(http, "ana@example.com")
    budget_settings(monkeypatch, daily_user_cost_usd_limit=turn_cost() * Decimal("1.5"), chat_in_flight_seconds=0)
    model = RecordingModel(messages=iter([AIMessage(content="ok")] * 20), seen=[])
    cfg = Settings(_env_file=None, openai_api_key="test-key")
    http.app.dependency_overrides[get_chat_runtime] = lambda: ChatRuntime(agent=build_agent(cfg, model=model), embeddings=FixedQuery(vec(1)))
    conversations = [seed_conversation(factory, "ana@example.com") for _ in range(6)]

    with ThreadPoolExecutor(6) as pool:
        statuses = list(pool.map(lambda cid: post(http, ana, cid, QUESTION).status_code, conversations))

    assert statuses.count(201) == 1 and statuses.count(429) == 5
    assert len(model.seen) == 1
    assert len(ledger(factory)) == 1
