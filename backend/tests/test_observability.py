import json
import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.deps import get_db
from app.core.config import Settings
from app.core.logging import JsonFormatter
from app.core.observability import init_sentry, scrub_breadcrumb, scrub_event
from app.main import create_app

JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abcDEF123_-xyz"
TOKEN43 = "A" * 20 + "b" * 20 + "-_9"
EMAIL = "ciudadano@example.org"


def test_health_and_request_id(client):
    c, _ = client
    r = c.get("/api/v1/health")
    assert r.status_code == 200 and len(r.headers["x-request-id"]) >= 8
    r = c.get("/api/v1/health", headers={"X-Request-ID": "abc-12345678"})
    assert r.headers["x-request-id"] == "abc-12345678"
    r = c.get("/api/v1/health", headers={"X-Request-ID": "bad id\twith spaces <script>"})
    assert r.headers["x-request-id"] != "bad id\twith spaces <script>"


def test_ready_ok(client):
    c, _ = client
    r = c.get("/api/v1/health/ready")
    assert r.status_code == 200 and r.json() == {"status": "ready"}


def test_ready_503_hides_exception(client):
    c, _ = client

    def broken():
        class S:
            def execute(self, *a, **k):
                raise OperationalError("SELECT 1", {}, Exception("password=hunter2 host=db.internal"))
        yield S()

    c.app.dependency_overrides[get_db] = broken
    r = c.get("/api/v1/health/ready")
    assert r.status_code == 503
    assert r.json() == {"status": "unavailable"}
    assert "hunter2" not in r.text


def test_access_log_has_template_not_query_or_email(client, caplog):
    c, _ = client
    with caplog.at_level(logging.INFO, logger="app.access"):
        c.get(f"/api/v1/health?email={EMAIL}&token={TOKEN43}", headers={"Authorization": f"Bearer {JWT}"})
        c.get("/api/v1/nope-" + "x" * 5)
    recs = [r for r in caplog.records if r.name == "app.access"]
    assert len(recs) == 2
    assert recs[0].path == "/api/v1/health" and recs[0].status == 200 and recs[0].method == "GET"
    assert recs[1].path == "unmatched" and recs[1].status == 404
    dumped = json.dumps([JsonFormatter().format(r) for r in recs])
    for secret in (EMAIL, TOKEN43, JWT, "Bearer"):
        assert secret not in dumped


def test_access_log_templates_path_params(client, caplog):
    c, _ = client
    with caplog.at_level(logging.INFO, logger="app.access"):
        c.get("/api/v1/conversations/987654")
    rec = [r for r in caplog.records if r.name == "app.access"][-1]
    assert "987654" not in rec.path and "{" in rec.path


def test_unhandled_exception_generic_500_and_logged_without_message(client, caplog):
    c, _ = client
    app = c.app

    @app.get("/boom")
    def boom():
        raise RuntimeError("".join(["secret ", "chat text from ", EMAIL]))

    with caplog.at_level(logging.ERROR, logger="app.errors"):
        r = TestClient(app, raise_server_exceptions=False).get("/boom", headers={"X-Request-ID": "req-abcdef12"})
    assert r.status_code == 500
    assert r.json() == {"detail": "Internal server error", "request_id": "req-abcdef12"}
    assert r.headers["x-request-id"] == "req-abcdef12"
    rec = [x for x in caplog.records if x.name == "app.errors"][0]
    assert rec.request_id == "req-abcdef12"
    assert "secret chat text" not in JsonFormatter().format(rec)


def test_http_and_validation_errors_not_swallowed(client):
    c, _ = client
    r = c.get("/api/v1/auth/me-does-not-exist")
    assert r.status_code == 404 and r.json()["detail"] == "Not Found"
    r = c.post("/api/v1/auth/login", json={})
    assert r.status_code == 422
    r = c.get("/api/v1/conversations")
    assert r.status_code == 401


def test_scrub_event_removes_everything_sensitive():
    event = {
        "request": {
            "url": f"https://x.test/a?email={EMAIL}",
            "query_string": f"token={TOKEN43}",
            "data": {"content": "mi pregunta legal"},
            "cookies": {"s": "1"},
            "headers": {
                "Authorization": f"Bearer {JWT}", "Cookie": "a=b", "X-Api-Key": "k", "X-Reset-Token": TOKEN43,
                "User-Agent": f"ua {EMAIL}", "Accept": "json",
            },
        },
        "user": {"email": EMAIL, "ip_address": "1.2.3.4"},
        "exception": {"values": [{"type": "ValueError", "value": f"bad {EMAIL} {JWT}"}]},
        "extra": {"note": f"{TOKEN43} and {EMAIL}", "n": 3},
        "message": "chat text",
        "breadcrumbs": {"values": [{"message": f"q {JWT}", "data": {"x": EMAIL}}]},
    }
    out = json.dumps(scrub_event(event))
    for leaked in (EMAIL, JWT, TOKEN43, "mi pregunta legal", "chat text", "1.2.3.4", "a=b", "Bearer"):
        assert leaked not in out
    assert "ValueError" in out and "Accept" in out


def test_scrub_breadcrumb_drops_query_and_pii():
    crumb = scrub_breadcrumb({"category": "httplib", "message": f"GET {EMAIL}",
                              "data": {"url": f"https://api.test/x?email={EMAIL}", "method": "GET", "body": "x"}})
    out = json.dumps(crumb)
    assert EMAIL not in out and "body" not in out and "api.test/x" in out


def test_sentry_not_initialised_without_dsn(monkeypatch):
    import sentry_sdk

    called = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: called.append(kw))
    assert init_sentry(Settings(sentry_dsn=None, _env_file=None)) is False
    assert called == []


def test_sentry_init_options_when_dsn_set(monkeypatch):
    import sentry_sdk

    called = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: called.append(kw))
    s = Settings(sentry_dsn="https://k@o0.ingest.sentry.io/1", git_sha="abc123", _env_file=None)
    assert init_sentry(s) is True
    kw = called[0]
    assert kw["send_default_pii"] is False and kw["include_local_variables"] is False
    assert kw["max_request_body_size"] == "never" and kw["traces_sample_rate"] == 0.0
    assert kw["release"] == "abc123" and kw["before_send"] is scrub_event


@pytest.mark.parametrize("fmt,env,expected", [("auto", "production", True), ("auto", "development", False),
                                              ("json", "development", True), ("text", "production", False)])
def test_log_format_selection(fmt, env, expected):
    assert Settings(log_format=fmt, environment=env, _env_file=None).use_json_logs is expected
