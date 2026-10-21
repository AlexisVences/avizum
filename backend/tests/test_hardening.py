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
        http.post("/api/v1/auth/register", json={"first_name": "A", "last_name": "B", "email": f"u{i}@example.com", "password": "Contrase#a-1234"}).status_code
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

    monkeypatch.setattr(rate_limit, "get_settings", lambda: SimpleNamespace(trust_proxy_headers=True))
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
