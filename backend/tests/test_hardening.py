from app.core.rate_limit import SlidingWindowLimiter


def test_window_slides_and_reports_the_wait():
    now = [0.0]
    limiter = SlidingWindowLimiter(clock=lambda: now[0])
    assert [limiter.hit("b", "ip", 3, 60) for _ in range(3)] == [None, None, None]
    now[0] = 10
    assert limiter.hit("b", "ip", 3, 60) == 50
    now[0] = 61
    assert limiter.hit("b", "ip", 3, 60) is None


def test_keys_and_buckets_are_independent():
    limiter = SlidingWindowLimiter(clock=lambda: 0.0)
    assert limiter.hit("a", "x", 1, 60) is None
    assert limiter.hit("a", "x", 1, 60) is not None
    assert limiter.hit("a", "y", 1, 60) is None
    assert limiter.hit("b", "x", 1, 60) is None


def test_agent_search_is_limited_per_address(client):
    http, _ = client
    codes = [http.get("/api/v1/agents/search", params={"q": "123456"}).status_code for _ in range(31)]
    assert codes[:30] == [200] * 30
    assert codes[30] == 429
    last = http.get("/api/v1/agents/search", params={"q": "123456"})
    assert last.headers["retry-after"].isdigit()
    assert "Intenta de nuevo" in last.json()["detail"]


def test_login_is_limited_per_address_and_per_account(client):
    http, _ = client
    body = {"email": "a@example.com", "password": "wrong-password-1"}
    assert [http.post("/api/v1/auth/login", json=body).status_code for _ in range(10)] == [401] * 10
    assert http.post("/api/v1/auth/login", json=body).status_code == 429


def test_register_is_limited_per_address(client):
    http, _ = client
    codes = [
        http.post("/api/v1/auth/register", json={"first_name": "A", "last_name": "B", "email": f"u{i}@example.com", "password": "Contrase#a-1234", "accepted_terms": True}).status_code
        for i in range(6)
    ]
    assert codes[5] == 429


def test_forwarded_header_is_ignored_unless_proxy_is_trusted(client, monkeypatch):
    http, _ = client
    for i in range(30):
        http.get("/api/v1/agents/search", params={"q": "123456"}, headers={"x-forwarded-for": f"9.9.9.{i}"})
    assert http.get("/api/v1/agents/search", params={"q": "123456"}, headers={"x-forwarded-for": "8.8.8.8"}).status_code == 429


def test_forwarded_header_is_used_when_the_proxy_is_trusted(client, monkeypatch):
    from types import SimpleNamespace

    import app.core.rate_limit as rate_limit

    monkeypatch.setattr(rate_limit, "get_settings", lambda: SimpleNamespace(trust_proxy_headers=True))  # legacy switch
    http, _ = client
    for _ in range(30):
        http.get("/api/v1/agents/search", params={"q": "123456"}, headers={"x-forwarded-for": "1.1.1.1, 7.7.7.7"})
    assert http.get("/api/v1/agents/search", params={"q": "123456"}, headers={"x-forwarded-for": "1.1.1.1, 7.7.7.7"}).status_code == 429
    assert http.get("/api/v1/agents/search", params={"q": "123456"}, headers={"x-forwarded-for": "1.1.1.1, 6.6.6.6"}).status_code == 200


def test_production_refuses_to_start_with_development_secrets():

    from app.core.config import Settings

    weak = Settings(environment="production", jwt_secret_key="development-only-change-me", cors_origins="http://localhost:3000")
    assert len(weak.production_problems()) == 2
    strong = Settings(environment="production", jwt_secret_key="x" * 40, cors_origins="https://avizum.example")
    assert strong.production_problems() == []


def test_responses_carry_security_headers(client):
    http, _ = client
    response = http.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"


def _request(forwarded: str | None, peer: str | None = "10.0.0.1"):
    from starlette.requests import Request

    headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded is not None else []
    scope = {"type": "http", "headers": headers, "client": (peer, 1234) if peer else None}
    return Request(scope)


def _with_count(monkeypatch, count: int):
    from types import SimpleNamespace

    import app.core.rate_limit as rate_limit

    monkeypatch.setattr(rate_limit, "get_settings", lambda: SimpleNamespace(trusted_proxy_count=count))
    return rate_limit.client_ip


def test_client_ip_ignores_forwarded_header_by_default(monkeypatch):
    client_ip = _with_count(monkeypatch, 0)
    assert client_ip(_request("1.2.3.4")) == "10.0.0.1"
    assert client_ip(_request(None, peer=None)) == "unknown"


def test_client_ip_takes_the_nth_entry_from_the_right(monkeypatch):
    # One proxy (Render): the last entry is what that proxy saw; a forged value stays on the left.
    one = _with_count(monkeypatch, 1)
    assert one(_request("6.6.6.6, 203.0.113.9")) == "203.0.113.9"
    # Two proxies (Cloudflare in front of Render): the real client is second from the right.
    two = _with_count(monkeypatch, 2)
    assert two(_request("6.6.6.6, 203.0.113.9, 172.70.1.1")) == "203.0.113.9"
    assert two(_request("203.0.113.9, 172.70.1.1")) == "203.0.113.9"


def test_client_ip_falls_back_to_the_socket_when_the_chain_is_shorter_than_configured(monkeypatch):
    two = _with_count(monkeypatch, 2)
    assert two(_request("6.6.6.6")) == "10.0.0.1"  # a request that skipped a proxy must not pick its own identity
    assert two(_request(None)) == "10.0.0.1"


def test_user_data_responses_are_not_cacheable_and_not_sniffable(client):
    http, _ = client
    http.post("/api/v1/auth/register", json={"first_name": "Ana", "last_name": "L", "email": "ana@example.com",
                                             "password": "a secure password", "accepted_terms": True})
    token = http.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "a secure password"}).json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    for response in (
        http.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "a secure password"}),
        http.get("/api/v1/users/me", headers=auth),
        http.get("/api/v1/conversations", headers=auth),
    ):
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert "strict-transport-security" not in response.headers  # HSTS is set at the edge (Cloudflare / Render)
