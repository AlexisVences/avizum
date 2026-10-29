from datetime import datetime, timezone

import pytest

from app.api.routes import google_verifier
from app.core.config import get_settings
from app.main import create_app
from app.models.domain import User
from app.services.google_auth import GoogleIdentity, InvalidGoogleToken

CREDENTIAL = "x" * 40


@pytest.fixture()
def google(client, monkeypatch):
    http, factory = client
    monkeypatch.setattr(get_settings(), "google_client_id", "client-id.apps.googleusercontent.com")
    state = {"identity": GoogleIdentity("sub-1", "ana@example.com", "Ana", "López")}

    def verifier(credential, client_id):
        assert client_id == "client-id.apps.googleusercontent.com"
        if state["identity"] is None:
            raise InvalidGoogleToken("bad")
        return state["identity"]

    http.app.dependency_overrides[google_verifier] = lambda: verifier
    return http, factory, state


def test_first_google_sign_in_creates_a_verified_account_without_password(google):
    http, factory, _ = google
    response = http.post("/api/v1/auth/google", json={"credential": CREDENTIAL})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "ana@example.com" and body["user"]["email_verified"] is True
    assert http.get("/api/v1/users/me", headers={"Authorization": f"Bearer {body['access_token']}"}).status_code == 200
    with factory() as db:
        user = db.query(User).one()
        assert user.password_hash is None and user.google_sub == "sub-1"


def test_second_sign_in_reuses_the_account(google):
    http, factory, _ = google
    http.post("/api/v1/auth/google", json={"credential": CREDENTIAL})
    http.post("/api/v1/auth/google", json={"credential": CREDENTIAL})
    with factory() as db:
        assert db.query(User).count() == 1


def test_unverified_password_account_loses_its_password_when_the_owner_links_google(google):
    http, factory, _ = google
    http.post("/api/v1/auth/register", json={"first_name": "Mal", "last_name": "Actor", "email": "ana@example.com", "password": "Contrase#a-1234", "accepted_terms": True})
    attacker = http.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "Contrase#a-1234"})
    assert attacker.status_code == 200
    attacker_headers = {"Authorization": f"Bearer {attacker.json()['access_token']}"}
    assert http.get("/api/v1/users/me", headers=attacker_headers).status_code == 200
    owner = http.post("/api/v1/auth/google", json={"credential": CREDENTIAL})
    assert owner.status_code == 200
    assert http.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "Contrase#a-1234"}).status_code == 401
    # the session the squatter already had is revoked, the owner's new one works
    assert http.get("/api/v1/users/me", headers=attacker_headers).status_code == 401
    assert http.get("/api/v1/users/me", headers={"Authorization": f"Bearer {owner.json()['access_token']}"}).status_code == 200
    with factory() as db:
        user = db.query(User).one()
        assert user.password_hash is None and user.email_verified_at is not None


def test_google_only_account_cannot_sign_in_with_a_password(google):
    http, _, _ = google
    http.post("/api/v1/auth/google", json={"credential": CREDENTIAL})
    assert http.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "anything-123"}).status_code == 401


def test_invalid_token_is_rejected(google):
    http, factory, state = google
    state["identity"] = None
    assert http.post("/api/v1/auth/google", json={"credential": CREDENTIAL}).status_code == 401
    with factory() as db:
        assert db.query(User).count() == 0


def test_inactive_account_cannot_sign_in(google):
    http, factory, _ = google
    http.post("/api/v1/auth/google", json={"credential": CREDENTIAL})
    with factory() as db:
        db.query(User).update({"is_active": False})
        db.commit()
    assert http.post("/api/v1/auth/google", json={"credential": CREDENTIAL}).status_code == 401


def test_disabled_when_no_client_id(client, monkeypatch):
    http, _ = client
    monkeypatch.setattr(get_settings(), "google_client_id", None)
    assert http.post("/api/v1/auth/google", json={"credential": CREDENTIAL}).status_code == 503


def test_changing_the_email_clears_verification(google):
    http, factory, _ = google
    token = http.post("/api/v1/auth/google", json={"credential": CREDENTIAL}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # A Google-only account has no password to prove ownership with, so it cannot change its email yet.
    assert http.patch("/api/v1/users/me", json={"email": "otro@example.com"}, headers=headers).status_code == 403
    assert http.patch("/api/v1/users/me", json={"password": "my first password"}, headers=headers).status_code == 200
    token = http.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "my first password"}).json()["access_token"]
    response = http.patch("/api/v1/users/me", json={"email": "otro@example.com", "current_password": "my first password"}, headers={"Authorization": f"Bearer {token}"})
    assert response.json()["email_verified"] is False


def test_verifier_rejects_tokens_without_a_verified_email(monkeypatch):
    from google.oauth2 import id_token

    from app.services import google_auth

    info = {"iss": "https://accounts.google.com", "sub": "1", "email": "a@b.mx", "email_verified": False}
    monkeypatch.setattr(id_token, "verify_oauth2_token", lambda *a, **k: info)
    with pytest.raises(InvalidGoogleToken):
        google_auth.verify_google_credential(CREDENTIAL, "cid")
    info.update(email_verified=True, iss="https://evil.example")
    with pytest.raises(InvalidGoogleToken):
        google_auth.verify_google_credential(CREDENTIAL, "cid")
    info.update(iss="accounts.google.com", given_name="Ana", family_name="López")
    assert google_auth.verify_google_credential(CREDENTIAL, "cid").first_name == "Ana"
