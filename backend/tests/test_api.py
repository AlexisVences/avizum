from app.core.security import create_access_token, hash_password
from datetime import datetime, timedelta, timezone

from app.models.domain import (
    AgentLookup, Conversation, Message, MessageFeedback, MessageRole, User, UserRole,
)


def register(client, email="ana@example.com"):
    return client.post("/api/v1/auth/register", json={"first_name": "Ana", "last_name": "López", "email": email, "password": "a secure password"})


def auth_headers(client):
    login = client.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "a secure password"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_health(client):
    http, _ = client
    assert http.get("/api/v1/health").json() == {"status": "ok"}


def test_registration_login_and_no_self_assigned_admin(client):
    http, _ = client
    result = register(http)
    assert result.status_code == 201
    assert result.json()["role"] == "user"
    assert "username" not in result.json()
    assert http.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "wrong"}).status_code == 401
    assert http.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "a secure password"}).status_code == 200
    assert http.get("/api/v1/admin/users", headers=auth_headers(http)).status_code == 403


def test_registration_rejects_duplicate_email(client):
    http, _ = client
    assert register(http).status_code == 201
    duplicate = register(http)
    assert duplicate.status_code == 409


def test_registration_rejects_short_password(client):
    http, _ = client
    response = http.post("/api/v1/auth/register", json={"first_name": "Ana", "last_name": "López", "email": "short@example.com", "password": "short1"})
    assert response.status_code == 422


def test_profile_requires_authentication_and_can_be_updated(client):
    http, _ = client
    assert http.get("/api/v1/users/me").status_code == 401
    register(http)
    response = http.patch("/api/v1/users/me", headers=auth_headers(http), json={"first_name": "Ana María"})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Ana María"


def test_the_old_consultation_and_feedback_endpoints_are_gone(client):
    http, _ = client
    register(http)
    headers = auth_headers(http)
    assert http.post("/api/v1/legal-consultations", headers=headers, json={"question": "hola mundo"}).status_code == 404
    assert http.put("/api/v1/legal-responses/1/feedback", headers=headers, json={"response_id": 1, "rating": 5}).status_code in (404, 405)


def test_statistics_require_an_admin_and_count_messages_conversations_and_feedback(client):
    http, factory = client
    register(http)
    headers = auth_headers(http)
    assert http.get("/api/v1/admin/statistics", headers=headers).status_code == 403

    with factory() as db:
        user = db.query(User).filter_by(email="ana@example.com").one()
        user.role = UserRole.ADMIN
        conversation = Conversation(user_id=user.id, title="Placas")
        db.add(conversation)
        db.flush()
        question = Message(conversation_id=conversation.id, role=MessageRole.USER, content="¿Placas?")
        answer = Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content="Sí [1]")
        old = Message(
            conversation_id=conversation.id, role=MessageRole.USER, content="antigua",
            created_at=datetime.now(timezone.utc) - timedelta(days=90),
        )
        db.add_all([question, answer, old])
        db.flush()
        db.add(MessageFeedback(message_id=answer.id, user_id=user.id, value=1))
        db.add(AgentLookup(user_id=user.id))
        db.commit()

    stats = http.get("/api/v1/admin/statistics", headers=headers).json()
    assert stats["messages_total"] == 2  # only the user's messages count, not the assistant's
    assert stats["messages_today"] == 1 and stats["messages_month"] == 1
    assert stats["conversations_total"] == 1
    assert stats["agent_lookups_month"] == 1
    assert (stats["feedback_positive"], stats["feedback_negative"], stats["feedback_positive_rate"]) == (1, 0, 1.0)


def test_statistics_without_any_feedback_report_no_rate(client):
    http, factory = client
    register(http)
    with factory() as db:
        db.query(User).filter_by(email="ana@example.com").one().role = UserRole.ADMIN
        db.commit()
    stats = http.get("/api/v1/admin/statistics", headers=auth_headers(http)).json()
    assert stats["feedback_positive_rate"] is None and stats["messages_total"] == 0
