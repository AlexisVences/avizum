from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.models.domain import Conversation, Message, MessageFeedback, MessageRole, MessageStatus, User


def signup(http, email: str) -> dict:
    http.post("/api/v1/auth/register", json={"first_name": "Ana", "last_name": "López", "email": email, "password": "a secure password", "accepted_terms": True})
    token = http.post("/api/v1/auth/login", json={"email": email, "password": "a secure password"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def user_id(factory, email: str) -> int:
    with factory() as db:
        return db.scalar(select(User.id).where(User.email == email))


def seed_conversation(factory, owner_email: str, title: str | None = None) -> int:
    with factory() as db:
        conversation = Conversation(user_id=user_id(factory, owner_email), title=title)
        db.add(conversation)
        db.commit()
        return conversation.id


def seed_message(factory, conversation_id: int, role: MessageRole, content: str, **fields) -> int:
    with factory() as db:
        message = Message(conversation_id=conversation_id, role=role, content=content, **fields)
        db.add(message)
        db.commit()
        return message.id


def test_every_chat_route_requires_authentication(client):
    http, _ = client
    for method, path in [
        ("get", "/api/v1/conversations"), ("post", "/api/v1/conversations"),
        ("patch", "/api/v1/conversations/1"), ("delete", "/api/v1/conversations/1"),
        ("get", "/api/v1/conversations/1/messages"),
        ("put", "/api/v1/messages/1/feedback"), ("delete", "/api/v1/messages/1/feedback"),
    ]:
        assert getattr(http, method)(path).status_code == 401, (method, path)


def test_creating_and_listing_conversations_shows_only_the_users_own_most_recent_first(client):
    http, factory = client
    ana, luis = signup(http, "ana@example.com"), signup(http, "luis@example.com")

    first = http.post("/api/v1/conversations", headers=ana)
    assert first.status_code == 201 and first.json()["title"] is None
    second = http.post("/api/v1/conversations", headers=ana).json()
    http.post("/api/v1/conversations", headers=luis)

    http.patch(f"/api/v1/conversations/{first.json()['id']}", headers=ana, json={"title": "Placas"})  # touches updated_at
    listing = http.get("/api/v1/conversations", headers=ana).json()
    assert [c["id"] for c in listing] == [first.json()["id"], second["id"]]
    assert len(http.get("/api/v1/conversations", headers=luis).json()) == 1


def test_a_conversation_that_belongs_to_someone_else_is_not_found_not_forbidden(client):
    http, factory = client
    signup(http, "ana@example.com")
    luis = signup(http, "luis@example.com")
    conversation_id = seed_conversation(factory, "ana@example.com", "Privada")
    message_id = seed_message(factory, conversation_id, MessageRole.ASSISTANT, "Respuesta")

    assert http.get(f"/api/v1/conversations/{conversation_id}/messages", headers=luis).status_code == 404
    assert http.patch(f"/api/v1/conversations/{conversation_id}", headers=luis, json={"title": "x"}).status_code == 404
    assert http.delete(f"/api/v1/conversations/{conversation_id}", headers=luis).status_code == 404
    assert http.put(f"/api/v1/messages/{message_id}/feedback", headers=luis, json={"value": 1}).status_code == 404
    assert http.get("/api/v1/conversations/99999/messages", headers=luis).status_code == 404  # missing looks identical


def test_renaming_validates_and_trims_the_title(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    conversation_id = seed_conversation(factory, "ana@example.com")
    url = f"/api/v1/conversations/{conversation_id}"

    for bad in ["", "   ", "x" * 81]:
        assert http.patch(url, headers=ana, json={"title": bad}).status_code == 422, repr(bad)
    ok = http.patch(url, headers=ana, json={"title": "  Multa por celular  "})
    assert ok.status_code == 200 and ok.json()["title"] == "Multa por celular"
    assert http.patch(url, headers=ana, json={"title": "x" * 80}).status_code == 200


def test_deleting_a_conversation_removes_its_messages_and_feedback(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    conversation_id = seed_conversation(factory, "ana@example.com")
    message_id = seed_message(factory, conversation_id, MessageRole.ASSISTANT, "Respuesta")
    assert http.put(f"/api/v1/messages/{message_id}/feedback", headers=ana, json={"value": 1}).status_code == 204

    assert http.delete(f"/api/v1/conversations/{conversation_id}", headers=ana).status_code == 204
    assert http.get(f"/api/v1/conversations/{conversation_id}/messages", headers=ana).status_code == 404
    with factory() as db:
        assert db.scalar(select(Message.id)) is None and db.scalar(select(MessageFeedback.id)) is None


def test_messages_come_in_order_with_citations_and_only_the_viewers_own_feedback(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    luis = signup(http, "luis@example.com")
    conversation_id = seed_conversation(factory, "ana@example.com")
    now = datetime.now(timezone.utc)
    question = seed_message(factory, conversation_id, MessageRole.USER, "¿Placas?", created_at=now - timedelta(seconds=5))
    answer = seed_message(
        factory, conversation_id, MessageRole.ASSISTANT, "Sí [1]",
        created_at=now, citations=[{"n": 1, "orden": 1, "article": "33", "url": "https://x.mx/r.pdf#page=41"}],
        tool_calls=[{"name": "buscar_legislacion"}], model="gpt-5-mini", input_tokens=900, output_tokens=120,
    )
    with factory() as db:  # feedback from two different people: each sees only their own
        db.add_all([
            MessageFeedback(message_id=answer, user_id=user_id(factory, "ana@example.com"), value=-1),
            MessageFeedback(message_id=answer, user_id=user_id(factory, "luis@example.com"), value=1),
        ])
        db.commit()

    messages = http.get(f"/api/v1/conversations/{conversation_id}/messages", headers=ana).json()
    assert [m["id"] for m in messages] == [question, answer]
    assert messages[0]["feedback"] is None and messages[1]["feedback"] == -1
    assert messages[1]["citations"][0]["url"].endswith("#page=41") and messages[1]["status"] == "complete"
    # the trace and the token accounting are internal: not part of the public message
    assert not {"tool_calls", "model", "input_tokens", "output_tokens"} & set(messages[1])
    del luis  # (luis never opens ana's conversation; his feedback exists only to prove it is not leaked)


def test_feedback_can_be_set_changed_and_removed_and_only_on_the_users_own_assistant_messages(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    conversation_id = seed_conversation(factory, "ana@example.com")
    question = seed_message(factory, conversation_id, MessageRole.USER, "Pregunta")
    answer = seed_message(factory, conversation_id, MessageRole.ASSISTANT, "Respuesta")
    url = f"/api/v1/messages/{answer}/feedback"

    assert http.put(url, headers=ana, json={"value": 1}).status_code == 204
    assert http.put(url, headers=ana, json={"value": -1}).status_code == 204  # changes it, does not duplicate
    with factory() as db:
        rows = db.scalars(select(MessageFeedback)).all()
        assert [r.value for r in rows] == [-1]
    assert http.get(f"/api/v1/conversations/{conversation_id}/messages", headers=ana).json()[1]["feedback"] == -1

    for bad in [0, 2, "up", None]:
        assert http.put(url, headers=ana, json={"value": bad}).status_code == 422, bad
    assert http.put(f"/api/v1/messages/{question}/feedback", headers=ana, json={"value": 1}).status_code == 404  # the user's own question
    assert http.put("/api/v1/messages/99999/feedback", headers=ana, json={"value": 1}).status_code == 404

    assert http.delete(url, headers=ana).status_code == 204
    assert http.delete(url, headers=ana).status_code == 204  # idempotent
    with factory() as db:
        assert db.scalar(select(MessageFeedback.id)) is None


def test_the_conversation_list_can_be_limited(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    for _ in range(3):
        http.post("/api/v1/conversations", headers=ana)
    assert len(http.get("/api/v1/conversations?limit=2", headers=ana).json()) == 2
    assert http.get("/api/v1/conversations?limit=0", headers=ana).status_code == 422


# ---------- POST /conversations/{id}/messages (JSON; the streaming version is step 12c)

from langchain_core.messages import AIMessage

from app.api.conversations import get_chat_runtime
from app.core.config import Settings
from app.services.agent.agent import build_agent
from app.services.chat import ChatRuntime
from tests.test_retrieval import FixedQuery, vec


def install_runtime(http, *replies):
    from tests.test_agent import RecordingModel

    cfg = Settings(_env_file=None, openai_api_key="test-key")
    model = RecordingModel(messages=iter(list(replies)), seen=[])
    http.app.dependency_overrides[get_chat_runtime] = lambda: ChatRuntime(agent=build_agent(cfg, model=model), embeddings=FixedQuery(vec(1)))


def test_posting_a_message_returns_the_question_and_the_stored_answer(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="Respuesta de prueba."))
    conversation_id = http.post("/api/v1/conversations", headers=ana).json()["id"]

    response = http.post(f"/api/v1/conversations/{conversation_id}/messages", headers=ana, json={"content": "¿Qué hago?"})

    assert response.status_code == 201
    body = response.json()
    assert body["user_message"]["content"] == "¿Qué hago?" and body["user_message"]["role"] == "user"
    assert body["assistant_message"]["content"] == "Respuesta de prueba." and body["assistant_message"]["status"] == "complete"
    listed = http.get(f"/api/v1/conversations/{conversation_id}/messages", headers=ana).json()
    assert [m["role"] for m in listed] == ["user", "assistant"]
    assert http.get("/api/v1/conversations", headers=ana).json()[0]["title"] == "¿Qué hago?"


def test_posting_to_someone_elses_conversation_is_404_and_runs_nothing(client):
    http, factory = client
    signup(http, "ana@example.com")
    luis = signup(http, "luis@example.com")
    install_runtime(http, AIMessage(content="no debe salir"))
    conversation_id = seed_conversation(factory, "ana@example.com")
    assert http.post(f"/api/v1/conversations/{conversation_id}/messages", headers=luis, json={"content": "hola"}).status_code == 404
    with factory() as db:
        assert db.scalar(select(Message.id)) is None


def test_limit_errors_map_to_their_status_codes_with_a_code_and_a_message(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="ok"))
    conversation_id = seed_conversation(factory, "ana@example.com")
    url = f"/api/v1/conversations/{conversation_id}/messages"

    empty = http.post(url, headers=ana, json={"content": "   "})
    assert empty.status_code == 422 and empty.json()["detail"]["code"] == "mensaje_vacio"
    assert http.post(url, headers=ana, json={"content": "x" * 2001}).status_code == 422
    assert http.post(url, headers=ana, json={}).status_code == 422  # missing field: FastAPI validation

    seed_message(factory, conversation_id, MessageRole.USER, "esperando respuesta")
    busy = http.post(url, headers=ana, json={"content": "otra"})
    assert busy.status_code == 409 and busy.json()["detail"]["code"] == "respuesta_en_curso"


def test_the_assistant_is_unavailable_not_broken_when_it_cannot_be_built(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    conversation_id = seed_conversation(factory, "ana@example.com")
    http.app.dependency_overrides.pop(get_chat_runtime, None)  # real dependency; the test environment has no OpenAI key
    response = http.post(f"/api/v1/conversations/{conversation_id}/messages", headers=ana, json={"content": "hola"})
    assert response.status_code == 503 and "no está disponible" in response.json()["detail"]["message"]


# ---------- el mismo endpoint como flujo SSE (Accept: text/event-stream)

import json as _json

from tests.fakes import FakeStreaming, tool_call as streaming_tool_call


def install_streaming_runtime(http, script, **model_fields):
    cfg = Settings(_env_file=None, openai_api_key="test-key")
    model = FakeStreaming(script=script, **model_fields)
    http.app.dependency_overrides[get_chat_runtime] = lambda: ChatRuntime(agent=build_agent(cfg, model=model), embeddings=FixedQuery(vec(1)))


def read_sse(response) -> list[tuple[str, dict]]:
    events, event = [], None
    for line in response.iter_lines():
        if line.startswith("event: "):
            event = line[7:]
        elif line.startswith("data: "):
            events.append((event, _json.loads(line[6:])))
    return events


def test_streaming_the_same_endpoint_emits_the_events_in_order_and_stores_the_turn(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    with factory() as db:
        from tests.test_retrieval import add_chunk, add_source
        source = add_source(db, "reglamento-transito", "a")
        add_chunk(db, source, "33", "Inmovilizador en vehículos estacionados", vec(1), fraction="II", page=35)
        db.commit()
    install_streaming_runtime(http, [
        streaming_tool_call("buscar_legislacion", {"consulta": "candado inmovilizador"}),
        AIMessage(content="Se inmoviliza en estos casos [1] según el Reglamento."),
    ])
    conversation_id = seed_conversation(factory, "ana@example.com")

    with http.stream("POST", f"/api/v1/conversations/{conversation_id}/messages", headers={**ana, "accept": "text/event-stream"},
                     json={"content": "me pusieron la araña"}) as response:
        assert response.status_code == 200 and response.headers["content-type"].startswith("text/event-stream")
        assert response.headers["cache-control"] == "no-cache"
        events = read_sse(response)

    names = [name for name, _ in events]
    assert names[0] == "message_start" and names[1:3] == ["tool_start", "tool_end"]
    assert names[-2:] == ["citations", "done"] and names.count("token") >= 3
    start, done = events[0][1], events[-1][1]
    stored = http.get(f"/api/v1/conversations/{conversation_id}/messages", headers=ana).json()
    assert [m["id"] for m in stored] == [start["user_message_id"], done["assistant_message_id"]]
    assert stored[1]["content"] == done["text"] == "Se inmoviliza en estos casos [1] según el Reglamento."
    assert stored[1]["citations"][0]["article"] == "33"


def test_limit_errors_come_back_as_plain_http_before_any_stream_opens(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_streaming_runtime(http, [AIMessage(content="ok")])
    conversation_id = seed_conversation(factory, "ana@example.com")
    url = f"/api/v1/conversations/{conversation_id}/messages"
    headers = {**ana, "accept": "text/event-stream"}

    empty = http.post(url, headers=headers, json={"content": "   "})
    assert empty.status_code == 422 and empty.headers["content-type"].startswith("application/json")
    assert empty.json()["detail"]["code"] == "mensaje_vacio"
    seed_message(factory, conversation_id, MessageRole.USER, "esperando respuesta")
    assert http.post(url, headers=headers, json={"content": "otra"}).status_code == 409
    other = signup(http, "luis@example.com")
    assert http.post(url, headers={**other, "accept": "text/event-stream"}, json={"content": "hola"}).status_code == 404


def test_a_failure_while_streaming_ends_with_an_error_event_and_a_stored_error_message(client):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_streaming_runtime(http, [AIMessage(content="Una respuesta que se corta a la mitad del camino")], fail_after_words=2)
    conversation_id = seed_conversation(factory, "ana@example.com")

    with http.stream("POST", f"/api/v1/conversations/{conversation_id}/messages", headers={**ana, "accept": "text/event-stream"},
                     json={"content": "hola"}) as response:
        events = read_sse(response)

    assert events[-1][0] == "error" and "sk-SECRET" not in _json.dumps(events)
    stored = http.get(f"/api/v1/conversations/{conversation_id}/messages", headers=ana).json()
    assert [(m["role"], m["status"]) for m in stored] == [("user", "complete"), ("assistant", "error")]


# ---------- durable budget and verified-email requirement

from app.core.config import get_settings



def budget_settings(monkeypatch, **values):
    settings = get_settings()
    for key, value in values.items():
        monkeypatch.setattr(settings, key, value)


def spend(factory, owner_email: str, conversation_id: int, *, tokens_in=0, tokens_out=0, age=timedelta(0)):
    seed_message(
        factory, conversation_id, MessageRole.ASSISTANT, "r",
        input_tokens=tokens_in, output_tokens=tokens_out, created_at=datetime.now(timezone.utc) - age,
    )


def post(http, headers, conversation_id, text="¿Qué hago?"):
    return http.post(f"/api/v1/conversations/{conversation_id}/messages", headers=headers, json={"content": text})


def count_messages(factory):
    with factory() as db:
        return len(db.scalars(select(Message.id)).all())


def test_under_the_user_budget_the_answer_is_generated(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="ok"))
    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("1"))
    conversation_id = seed_conversation(factory, "ana@example.com")
    spend(factory, "ana@example.com", conversation_id, tokens_in=1_000_000)  # 0.25 USD of 1
    assert post(http, ana, conversation_id).status_code == 201


def test_over_the_user_budget_is_429_with_retry_after_and_the_model_never_runs(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="no debe salir"))
    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("0.25"))
    conversation_id = seed_conversation(factory, "ana@example.com")
    spend(factory, "ana@example.com", conversation_id, tokens_in=500_000, tokens_out=62_500, age=timedelta(hours=2))  # 0.25
    before = count_messages(factory)

    response = post(http, ana, conversation_id)

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "presupuesto_diario"
    assert "24 horas" in response.json()["detail"]["message"]
    retry = int(response.headers["Retry-After"])
    assert 21 * 3600 < retry <= 22 * 3600  # the 2 h old answer leaves the window in ~22 h
    assert count_messages(factory) == before  # no question stored, nothing consumed
    assert post(http, ana, conversation_id).status_code == 429  # and a refusal does not change the outcome


def test_usage_older_than_24_hours_does_not_count(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="ok"))
    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("0.25"))
    conversation_id = seed_conversation(factory, "ana@example.com")
    spend(factory, "ana@example.com", conversation_id, tokens_in=10_000_000, age=timedelta(hours=25))
    assert post(http, ana, conversation_id).status_code == 201


def test_one_users_usage_does_not_affect_another(client, monkeypatch):
    http, factory = client
    signup(http, "ana@example.com")
    luis = signup(http, "luis@example.com")
    install_runtime(http, AIMessage(content="ok"))
    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("0.25"))
    spend(factory, "ana@example.com", seed_conversation(factory, "ana@example.com"), tokens_in=10_000_000)
    assert post(http, luis, seed_conversation(factory, "luis@example.com")).status_code == 201


def test_the_user_budget_can_be_disabled_with_zero(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="ok"))
    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("0"))
    conversation_id = seed_conversation(factory, "ana@example.com")
    spend(factory, "ana@example.com", conversation_id, tokens_in=100_000_000)
    assert post(http, ana, conversation_id).status_code == 201


def test_global_breaker_blocks_everyone_when_on_and_does_nothing_when_off(client, monkeypatch):
    http, factory = client
    signup(http, "ana@example.com")
    luis = signup(http, "luis@example.com")
    install_runtime(http, AIMessage(content="ok"))
    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("0"))
    spend(factory, "ana@example.com", seed_conversation(factory, "ana@example.com"), tokens_in=4_000_000)  # 1 USD
    luis_conversation = seed_conversation(factory, "luis@example.com")

    budget_settings(monkeypatch, global_daily_cost_usd_limit=Decimal("0"))  # off
    assert post(http, luis, luis_conversation).status_code == 201

    budget_settings(monkeypatch, global_daily_cost_usd_limit=Decimal("1"))  # on, reached
    before = count_messages(factory)
    response = post(http, luis, luis_conversation)
    assert response.status_code == 429 and response.json()["detail"]["code"] == "servicio_saturado"
    assert int(response.headers["Retry-After"]) >= 60
    assert count_messages(factory) == before

    budget_settings(monkeypatch, global_daily_cost_usd_limit=Decimal("2"))  # on, not reached
    install_runtime(http, AIMessage(content="ok"))
    assert post(http, luis, luis_conversation).status_code == 201


def test_streaming_requests_are_refused_by_the_budget_before_any_stream_opens(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="no debe salir"))
    budget_settings(monkeypatch, daily_user_cost_usd_limit=Decimal("0.25"))
    conversation_id = seed_conversation(factory, "ana@example.com")
    spend(factory, "ana@example.com", conversation_id, tokens_in=2_000_000)
    response = http.post(
        f"/api/v1/conversations/{conversation_id}/messages", headers={**ana, "Accept": "text/event-stream"},
        json={"content": "hola"},
    )
    assert response.status_code == 429 and "Retry-After" in response.headers


def test_the_daily_message_limit_also_sends_retry_after(client, monkeypatch):
    http, factory = client
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="ok"))
    budget_settings(monkeypatch, chat_daily_message_limit=0)
    response = post(http, ana, seed_conversation(factory, "ana@example.com"))
    assert response.status_code == 429 and int(response.headers["Retry-After"]) >= 1


def _unverified_user_chat(http, factory, monkeypatch, required: bool, verify: bool = False):
    ana = signup(http, "ana@example.com")
    install_runtime(http, AIMessage(content="ok"))
    budget_settings(monkeypatch, require_verified_email=required)
    if verify:
        with factory() as db:
            user = db.scalar(select(User).where(User.email == "ana@example.com"))
            user.email_verified_at = datetime.now(timezone.utc)
            db.commit()
    conversation_id = seed_conversation(factory, "ana@example.com")
    return ana, conversation_id


def test_verification_off_lets_an_unverified_user_chat(client, monkeypatch):
    http, factory = client
    ana, conversation_id = _unverified_user_chat(http, factory, monkeypatch, required=False)
    assert post(http, ana, conversation_id).status_code == 201


def test_verification_on_blocks_an_unverified_user_before_anything_runs(client, monkeypatch):
    http, factory = client
    ana, conversation_id = _unverified_user_chat(http, factory, monkeypatch, required=True)
    response = post(http, ana, conversation_id)
    assert response.status_code == 403 and response.json()["detail"] == "Verifica tu correo para continuar"
    assert count_messages(factory) == 0
    streamed = http.post(
        f"/api/v1/conversations/{conversation_id}/messages", headers={**ana, "Accept": "text/event-stream"},
        json={"content": "hola"},
    )
    assert streamed.status_code == 403
    assert http.get("/api/v1/conversations", headers=ana).status_code == 200  # read-only routes stay open


def test_verification_on_lets_a_verified_user_chat(client, monkeypatch):
    http, factory = client
    ana, conversation_id = _unverified_user_chat(http, factory, monkeypatch, required=True, verify=True)
    assert post(http, ana, conversation_id).status_code == 201
