from app.core.security import create_access_token, hash_password
from app.models.domain import AuthorizedAgent, Consultation, LegalResponse, User, UserRole


def register(client, username="ana", email="ana@example.com"):
    return client.post("/api/v1/auth/register", json={"username": username, "first_name": "Ana", "last_name": "López", "email": email, "password": "a secure password"})


def auth_headers(client):
    login = client.post("/api/v1/auth/login", json={"username": "ana", "password": "a secure password"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_health(client):
    http, _ = client
    assert http.get("/api/v1/health").json() == {"status": "ok"}


def test_registration_login_and_no_self_assigned_admin(client):
    http, _ = client
    result = register(http)
    assert result.status_code == 201
    assert result.json()["role"] == "user"
    assert http.post("/api/v1/auth/login", json={"username": "ana", "password": "wrong"}).status_code == 401
    assert http.post("/api/v1/auth/login", json={"username": "ana", "password": "a secure password"}).status_code == 200
    assert http.get("/api/v1/admin/users", headers=auth_headers(http)).status_code == 403


def test_profile_requires_authentication_and_can_be_updated(client):
    http, _ = client
    assert http.get("/api/v1/users/me").status_code == 401
    register(http)
    response = http.patch("/api/v1/users/me", headers=auth_headers(http), json={"first_name": "Ana María"})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Ana María"


def test_agent_lookup_is_authenticated_and_recorded(client):
    http, factory = client
    register(http)
    with factory() as db:
        db.add(AuthorizedAgent(plate="ABC123", name="Oficial Ejemplo"))
        db.commit()
    assert http.get("/api/v1/agents/ABC123").status_code == 401
    response = http.get("/api/v1/agents/abc123", headers=auth_headers(http))
    assert response.status_code == 200
    assert response.json()["plate"] == "ABC123"


def test_feedback_only_for_response_owner_and_valid_rating(client):
    http, factory = client
    register(http)
    register(http, "other", "other@example.com")
    with factory() as db:
        owner = db.query(User).filter_by(username="ana").one()
        consultation = Consultation(user_id=owner.id, question="Pregunta")
        db.add(consultation); db.flush()
        response = LegalResponse(consultation_id=consultation.id, text="Respuesta", category="general")
        db.add(response); db.commit(); response_id = response.id
    other_login = http.post("/api/v1/auth/login", json={"username": "other", "password": "a secure password"}).json()
    headers = {"Authorization": f"Bearer {other_login['access_token']}"}
    assert http.put(f"/api/v1/legal-responses/{response_id}/feedback", headers=headers, json={"response_id": response_id, "rating": 5}).status_code == 403
    assert http.put(f"/api/v1/legal-responses/{response_id}/feedback", headers=auth_headers(http), json={"response_id": response_id, "rating": 6}).status_code == 422
    assert http.put(f"/api/v1/legal-responses/{response_id}/feedback", headers=auth_headers(http), json={"response_id": response_id, "rating": 5}).status_code == 204
