import hashlib
import re
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.api.deps import get_db  # noqa: F401
from app.core.config import TERMS_VERSION
from app.models.domain import EmailToken, EmailTokenPurpose, User
from app.services.mailer import MailDeliveryError, get_mailer

PASSWORD = "a secure password"
NEW_PASSWORD = "another secure password"


def register(http, email="ana@example.com", **extra):
    body = {"first_name": "Ana", "last_name": "López", "email": email, "password": PASSWORD, "accepted_terms": True}
    body.update(extra)
    return http.post("/api/v1/auth/register", json=body)


def login(http, email="ana@example.com", password=PASSWORD):
    return http.post("/api/v1/auth/login", json={"email": email, "password": password})


def headers_for(http, email="ana@example.com", password=PASSWORD):
    return {"Authorization": f"Bearer {login(http, email, password).json()['access_token']}"}


def token_in(message) -> str:
    return re.search(r"token=([A-Za-z0-9_\-]+)", message.text).group(1)


# ---- terms -----------------------------------------------------------------------------------------------------

def test_register_requires_accepted_terms(client):
    http, _ = client
    body = {"first_name": "A", "last_name": "B", "email": "a@example.com", "password": PASSWORD}
    assert http.post("/api/v1/auth/register", json=body).status_code == 422
    assert http.post("/api/v1/auth/register", json={**body, "accepted_terms": False}).status_code == 422


def test_register_records_terms_consent(client):
    http, factory = client
    assert register(http).status_code == 201
    with factory() as db:
        user = db.scalar(select(User))
        assert user.terms_accepted_at is not None
        assert user.terms_version == TERMS_VERSION == "2026-10-29-borrador"


# ---- verification ----------------------------------------------------------------------------------------------

def test_register_sends_verification_and_token_is_stored_hashed(client, outbox):
    http, factory = client
    register(http)
    assert len(outbox.messages) == 1
    message = outbox.messages[0]
    assert message.to == "ana@example.com"
    raw = token_in(message)
    assert "/verificar-correo?token=" in message.text and "/verificar-correo?token=" in message.html
    assert raw not in message.subject
    with factory() as db:
        row = db.scalar(select(EmailToken))
        assert row.purpose == EmailTokenPurpose.VERIFY
        assert row.token_hash == hashlib.sha256(raw.encode()).hexdigest()
        assert raw not in row.token_hash
        assert row.used_at is None
        assert timedelta(hours=23) < row.expires_at - datetime.now(timezone.utc) <= timedelta(hours=24)


def test_verify_email_happy_path_and_token_is_single_use(client, outbox):
    http, factory = client
    register(http)
    raw = token_in(outbox.messages[0])
    assert http.post("/api/v1/auth/verify-email", json={"token": raw}).status_code == 200
    with factory() as db:
        assert db.scalar(select(User)).email_verified_at is not None
    again = http.post("/api/v1/auth/verify-email", json={"token": raw})
    assert again.status_code == 400
    unknown = http.post("/api/v1/auth/verify-email", json={"token": "x" * 43})
    assert unknown.status_code == 400
    assert again.json() == unknown.json()


def test_verify_email_rejects_expired_token(client, outbox):
    http, factory = client
    register(http)
    with factory() as db:
        row = db.scalar(select(EmailToken))
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    expired = http.post("/api/v1/auth/verify-email", json={"token": token_in(outbox.messages[0])})
    assert expired.status_code == 400
    assert expired.json() == http.post("/api/v1/auth/verify-email", json={"token": "y" * 43}).json()


def test_resend_verification_requires_auth(client):
    http, _ = client
    assert http.post("/api/v1/auth/resend-verification").status_code == 401


def test_resend_verification_invalidates_previous_token(client, outbox):
    http, _ = client
    register(http)
    first = token_in(outbox.messages[0])
    assert http.post("/api/v1/auth/resend-verification", headers=headers_for(http)).status_code == 202
    assert len(outbox.messages) == 2
    second = token_in(outbox.messages[1])
    assert http.post("/api/v1/auth/verify-email", json={"token": first}).status_code == 400
    assert http.post("/api/v1/auth/verify-email", json={"token": second}).status_code == 200


def test_resend_verification_is_noop_when_verified(client, outbox):
    http, _ = client
    register(http)
    http.post("/api/v1/auth/verify-email", json={"token": token_in(outbox.messages[0])})
    assert http.post("/api/v1/auth/resend-verification", headers=headers_for(http)).status_code == 202
    assert len(outbox.messages) == 1


def test_changing_email_sends_verification_to_new_address(client, outbox):
    http, factory = client
    register(http)
    response = http.patch(
        "/api/v1/users/me", headers=headers_for(http),
        json={"email": "new@example.com", "current_password": PASSWORD},
    )
    assert response.status_code == 200
    assert outbox.messages[-1].to == "new@example.com"
    assert http.post("/api/v1/auth/verify-email", json={"token": token_in(outbox.messages[-1])}).status_code == 200
    with factory() as db:
        assert db.scalar(select(User)).email_verified_at is not None


# ---- password reset --------------------------------------------------------------------------------------------

def test_forgot_password_answers_identically_for_known_and_unknown_emails(client, outbox):
    http, _ = client
    register(http)
    outbox.messages.clear()
    known = http.post("/api/v1/auth/forgot-password", json={"email": "ana@example.com"})
    unknown = http.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert [m.to for m in outbox.messages] == ["ana@example.com"]
    assert "/restablecer-contrasena?token=" in outbox.messages[0].text


def test_forgot_password_for_google_only_account_explains_instead_of_linking(client, outbox):
    http, factory = client
    with factory() as db:
        db.add(User(first_name="G", last_name="U", email="g@example.com", password_hash=None, google_sub="sub-1"))
        db.commit()
    response = http.post("/api/v1/auth/forgot-password", json={"email": "G@example.com"})
    assert response.status_code == 202
    assert len(outbox.messages) == 1
    assert "Google" in outbox.messages[0].text
    assert "token=" not in outbox.messages[0].text and "token=" not in outbox.messages[0].html
    with factory() as db:
        assert db.scalar(select(EmailToken)) is None


def test_reset_password_happy_path_revokes_sessions(client, outbox):
    http, factory = client
    register(http)
    old = headers_for(http)
    http.post("/api/v1/auth/forgot-password", json={"email": "ana@example.com"})
    raw = token_in(outbox.messages[-1])
    with factory() as db:
        reset_row = db.scalar(select(EmailToken).where(EmailToken.purpose == EmailTokenPurpose.RESET))
        assert timedelta(minutes=59) < reset_row.expires_at - datetime.now(timezone.utc) <= timedelta(hours=1)
        assert raw not in reset_row.token_hash
    assert http.post("/api/v1/auth/reset-password", json={"token": raw, "password": NEW_PASSWORD}).status_code == 200
    assert http.get("/api/v1/users/me", headers=old).status_code == 401
    assert login(http, password=PASSWORD).status_code == 401
    assert login(http, password=NEW_PASSWORD).status_code == 200
    with factory() as db:
        user = db.scalar(select(User))
        assert user.token_version == 1
        assert user.email_verified_at is not None  # the mailbox is proven
    assert http.post("/api/v1/auth/reset-password", json={"token": raw, "password": NEW_PASSWORD}).status_code == 400


def test_reset_password_validates_password_and_keeps_token_usable(client, outbox):
    http, _ = client
    register(http)
    http.post("/api/v1/auth/forgot-password", json={"email": "ana@example.com"})
    raw = token_in(outbox.messages[-1])
    assert http.post("/api/v1/auth/reset-password", json={"token": raw, "password": "short"}).status_code == 422
    assert http.post("/api/v1/auth/reset-password", json={"token": raw, "password": NEW_PASSWORD}).status_code == 200


def test_reset_password_rejects_unknown_expired_and_superseded_tokens(client, outbox):
    http, factory = client
    register(http)
    http.post("/api/v1/auth/forgot-password", json={"email": "ana@example.com"})
    first = token_in(outbox.messages[-1])
    http.post("/api/v1/auth/forgot-password", json={"email": "ana@example.com"})
    second = token_in(outbox.messages[-1])
    body = lambda t: {"token": t, "password": NEW_PASSWORD}  # noqa: E731
    unknown = http.post("/api/v1/auth/reset-password", json=body("z" * 43))
    assert unknown.status_code == 400
    superseded = http.post("/api/v1/auth/reset-password", json=body(first))
    assert superseded.status_code == 400 and superseded.json() == unknown.json()
    with factory() as db:
        for row in db.scalars(select(EmailToken).where(EmailToken.purpose == EmailTokenPurpose.RESET)):
            row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert http.post("/api/v1/auth/reset-password", json=body(second)).status_code == 400


def test_a_verify_token_cannot_reset_a_password(client, outbox):
    http, _ = client
    register(http)
    raw = token_in(outbox.messages[0])
    assert http.post("/api/v1/auth/reset-password", json={"token": raw, "password": NEW_PASSWORD}).status_code == 400


# ---- mail failures and rate limits -----------------------------------------------------------------------------

class ExplodingMailer:
    def send(self, to, subject, html, text, idempotency_key):
        raise MailDeliveryError("boom")


class CrashingMailer:
    def send(self, to, subject, html, text, idempotency_key):
        raise RuntimeError("unexpected")


@pytest.mark.parametrize("mailer", [ExplodingMailer(), CrashingMailer()])
def test_a_failing_mailer_does_not_break_register_or_forgot_password(client, mailer):
    http, _ = client
    http.app.dependency_overrides[get_mailer] = lambda: mailer
    assert register(http).status_code == 201
    assert login(http).status_code == 200
    assert http.post("/api/v1/auth/forgot-password", json={"email": "ana@example.com"}).status_code == 202


def test_failure_log_does_not_leak_address(client, caplog):
    http, _ = client
    http.app.dependency_overrides[get_mailer] = lambda: ExplodingMailer()
    with caplog.at_level("DEBUG"):
        register(http, "secret.person@example.com")
    assert "secret.person@example.com" not in caplog.text
    assert "mail" in caplog.text.lower()


def test_verify_email_is_rate_limited(client):
    http, _ = client
    codes = [http.post("/api/v1/auth/verify-email", json={"token": f"{i:043d}"}).status_code for i in range(12)]
    assert codes[-1] == 429


def test_forgot_password_is_rate_limited_per_target(client):
    http, _ = client
    codes = [http.post("/api/v1/auth/forgot-password", json={"email": "ana@example.com"}).status_code for _ in range(5)]
    assert codes[:3] == [202, 202, 202] and 429 in codes


def test_reset_password_is_rate_limited(client):
    http, _ = client
    codes = [
        http.post("/api/v1/auth/reset-password", json={"token": f"{i:043d}", "password": NEW_PASSWORD}).status_code
        for i in range(12)
    ]
    assert codes[-1] == 429


def test_resend_verification_is_rate_limited(client):
    http, _ = client
    register(http)
    headers = headers_for(http)
    codes = [http.post("/api/v1/auth/resend-verification", headers=headers).status_code for _ in range(6)]
    assert codes[-1] == 429


# ---- optional verified-email requirement -----------------------------------------------------------------------

def test_verified_user_dependency_only_blocks_when_setting_is_on(client, monkeypatch):
    from fastapi import HTTPException
    from app.api.deps import verified_user
    from app.core.config import get_settings

    user = User(first_name="A", last_name="B", email="a@example.com")
    assert verified_user(user) is user  # default: not required
    monkeypatch.setattr(get_settings(), "require_verified_email", True)
    with pytest.raises(HTTPException) as err:
        verified_user(user)
    assert err.value.status_code == 403
    user.email_verified_at = datetime.now(timezone.utc)
    assert verified_user(user) is user


def test_resend_mailer_is_selected_from_settings():
    from app.core.config import Settings
    from app.services.mailer import ConsoleMailer, ResendMailer, build_mailer

    assert isinstance(build_mailer(Settings(resend_api_key=None)), ConsoleMailer)
    assert isinstance(build_mailer(Settings(resend_api_key="re_x")), ResendMailer)
