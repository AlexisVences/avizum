from app.core.security import create_access_token, hash_password


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
