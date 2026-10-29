from sqlalchemy import select

from app.models.domain import User

PASSWORD = "a secure password"


def register(http, email="ana@example.com"):
    return http.post("/api/v1/auth/register", json={"first_name": "Ana", "last_name": "López", "email": email, "password": PASSWORD})


def login(http, email="ana@example.com", password=PASSWORD):
    return http.post("/api/v1/auth/login", json={"email": email, "password": password})


def headers_for(http, email="ana@example.com", password=PASSWORD):
    return {"Authorization": f"Bearer {login(http, email, password).json()['access_token']}"}


def patch(http, headers, **body):
    return http.patch("/api/v1/users/me", headers=headers, json=body)


# (a) case-insensitive email

def test_register_stores_the_email_lowercased_and_trimmed(client):
    http, factory = client
    response = register(http, "  Ana@Example.COM ")
    assert response.status_code == 201
    assert response.json()["email"] == "ana@example.com"
    with factory() as db:
        assert db.scalar(select(User.email)) == "ana@example.com"


def test_register_rejects_a_duplicate_that_differs_only_in_case(client):
    http, _ = client
    assert register(http, "ana@example.com").status_code == 201
    assert register(http, "ANA@example.com").status_code == 409


def test_login_ignores_email_case(client):
    http, _ = client
    register(http)
    assert login(http, " ANA@Example.com ").status_code == 200


def test_the_database_refuses_case_variants_of_an_email(client):
    import pytest
    from sqlalchemy.exc import IntegrityError

    http, factory = client
    register(http)
    with factory() as db:
        db.add(User(first_name="X", last_name="Y", email="Ana@example.com", password_hash=None))
        with pytest.raises(IntegrityError):
            db.commit()


def test_profile_email_is_normalised_and_checked_case_insensitively(client):
    http, _ = client
    register(http)
    register(http, "bob@example.com")
    headers = headers_for(http)
    assert patch(http, headers, email="BOB@example.com", current_password=PASSWORD).status_code == 409
    response = patch(http, headers, email=" New@Example.com ", current_password=PASSWORD)
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"


# (b) current password required

def test_changing_the_password_requires_the_current_password(client):
    http, _ = client
    register(http)
    headers = headers_for(http)
    assert patch(http, headers, password="another password").status_code == 403
    assert patch(http, headers, password="another password", current_password="wrong").status_code == 403
    assert login(http, password=PASSWORD).status_code == 200
    assert patch(http, headers, password="another password", current_password=PASSWORD).status_code == 200
    assert login(http, password="another password").status_code == 200


def test_changing_the_email_requires_the_current_password(client):
    http, _ = client
    register(http)
    headers = headers_for(http)
    assert patch(http, headers, email="new@example.com").status_code == 403
    assert patch(http, headers, email="new@example.com", current_password="wrong").status_code == 403
    assert http.get("/api/v1/users/me", headers=headers).json()["email"] == "ana@example.com"
    assert patch(http, headers, email="new@example.com", current_password=PASSWORD).status_code == 200


def test_resending_the_same_email_or_editing_the_name_needs_no_password(client):
    http, _ = client
    register(http)
    headers = headers_for(http)
    assert patch(http, headers, email="ANA@example.com", first_name="Ana María").status_code == 200


def test_new_password_still_has_a_minimum_length(client):
    http, _ = client
    register(http)
    assert patch(http, headers_for(http), password="short", current_password=PASSWORD).status_code == 422


def test_profile_update_still_requires_authentication(client):
    http, _ = client
    assert http.patch("/api/v1/users/me", json={"password": "another password", "current_password": "x"}).status_code == 401


def test_google_only_account_can_set_a_first_password_but_not_change_email(client):
    http, factory = client
    with factory() as db:
        user = User(first_name="G", last_name="U", email="g@example.com", password_hash=None, google_sub="sub-1")
        db.add(user)
        db.commit()
        user_id = user.id
    from app.core.security import create_access_token

    headers = {"Authorization": f"Bearer {create_access_token(str(user_id), 0)}"}
    assert patch(http, headers, email="other@example.com").status_code == 403
    assert patch(http, headers, email="other@example.com", current_password="whatever").status_code == 403
    assert patch(http, headers, password="my first password").status_code == 200
    assert login(http, "g@example.com", "my first password").status_code == 200
    # Once it has a password it is like any other account.
    headers = headers_for(http, "g@example.com", "my first password")
    assert patch(http, headers, email="other@example.com").status_code == 403
    assert patch(http, headers, email="other@example.com", current_password="my first password").status_code == 200


# (c) token revocation

def test_changing_the_password_revokes_older_tokens(client):
    http, _ = client
    register(http)
    old = headers_for(http)
    assert patch(http, old, password="another password", current_password=PASSWORD).status_code == 200
    assert http.get("/api/v1/users/me", headers=old).status_code == 401
    assert login(http, password=PASSWORD).status_code == 401
    new = headers_for(http, password="another password")
    assert http.get("/api/v1/users/me", headers=new).status_code == 200


def test_editing_only_the_name_keeps_tokens_valid(client):
    http, _ = client
    register(http)
    headers = headers_for(http)
    assert patch(http, headers, first_name="Nueva").status_code == 200
    assert http.get("/api/v1/users/me", headers=headers).status_code == 200


# has_password flag

def test_has_password_true_for_password_accounts(client):
    http, _ = client
    registered = register(http)
    assert registered.json()["has_password"] is True
    assert "password_hash" not in registered.json()
    logged = login(http)
    assert logged.json()["user"]["has_password"] is True
    assert "password_hash" not in logged.json()["user"]
    me = http.get("/api/v1/users/me", headers=headers_for(http))
    assert me.json()["has_password"] is True
    assert "password_hash" not in me.json()


def test_has_password_false_for_google_only_then_true_after_setting_one(client, monkeypatch):
    from app.api.routes import google_verifier
    from app.core.config import get_settings
    from app.services.google_auth import GoogleIdentity

    http, _ = client
    monkeypatch.setattr(get_settings(), "google_client_id", "client-id.apps.googleusercontent.com")
    http.app.dependency_overrides[google_verifier] = lambda: (
        lambda credential, client_id: GoogleIdentity("sub-1", "ana@example.com", "Ana", "López")
    )
    response = http.post("/api/v1/auth/google", json={"credential": "x" * 40})
    assert response.status_code == 200
    assert response.json()["user"]["has_password"] is False
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert http.get("/api/v1/users/me", headers=headers).json()["has_password"] is False

    updated = patch(http, headers, password="my first password")
    assert updated.status_code == 200
    assert updated.json()["has_password"] is True
    # Setting a password rotates the token version, so the old token is rejected; sign in again.
    assert http.get("/api/v1/users/me", headers=headers).status_code == 401
    fresh = headers_for(http, password="my first password")
    assert http.get("/api/v1/users/me", headers=fresh).json()["has_password"] is True
