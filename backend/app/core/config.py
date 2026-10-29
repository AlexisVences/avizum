from datetime import date
from decimal import Decimal
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# Version of the terms a user accepted at registration; bump it when the published text changes.
TERMS_VERSION = "2026-10-29-borrador"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://localhost/avizum"
    environment: str = "development"  # "production" turns the startup checks below into hard failures
    jwt_secret_key: str = "development-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000"
    # Set only behind a reverse proxy you control (it must overwrite X-Forwarded-For); otherwise anyone could forge it.
    trust_proxy_headers: bool = False
    google_client_id: str | None = None  # OAuth client ID (public) of the web app; unset disables Google sign-in
    frontend_url: str = "http://localhost:3000"  # base of the links in e-mails (no trailing slash)
    resend_api_key: SecretStr | None = None  # unset: mails are only logged (ConsoleMailer)
    mail_from: str = "Avizum <no-reply@example.com>"
    require_verified_email: bool = False  # when true, endpoints using `verified_user` answer 403 until verified
    log_level: str = "INFO"
    log_format: str = "auto"  # "json", "text" or "auto" (json in production, text otherwise)
    sentry_dsn: SecretStr | None = None  # unset: error tracking is off and nothing leaves the server
    sentry_environment: str | None = None  # defaults to ENVIRONMENT
    sentry_traces_sample_rate: float = 0.0
    git_sha: str | None = None  # reported as the Sentry release when set
    openai_api_key: SecretStr | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-5-mini"
    # Chat limits (spec section 2). Reasoning tokens count toward the output cap.
    chat_max_output_tokens: int = 1800  # measured: a 400-word answer used ~1,100 incl. reasoning; 1,200 was too tight
    # Tokens reserved per turn before the model runs (see app/services/chat_limits.py). Input: system prompt, history
    # and tool results of up to several model calls, plus the question itself (chars/3) on top of this base.
    # Output: chat_max_output_tokens is used as the output reservation.
    chat_reserve_input_tokens: int = 12000
    chat_max_agent_steps: int = 6  # model calls per turn: up to 5 rounds of tools plus the final answer
    chat_context_messages: int = 12  # history sent to the model; the full history is still stored and shown
    chat_daily_message_limit: int = 40  # user messages per day per user (Mexico City calendar)
    chat_max_message_chars: int = 2000
    chat_in_flight_seconds: int = 120  # an unanswered question this young means a reply is still being generated
    chat_max_messages_per_conversation: int = 200  # user + assistant; the UI then proposes a new conversation
    # List prices in USD per million tokens, used only for the cost estimate in the admin overview.
    llm_price_input_per_million: Decimal = Decimal("0.25")
    llm_price_output_per_million: Decimal = Decimal("2.00")
    # Durable cost budget over a rolling 24 h window, computed from stored token usage x the prices above.
    # 0 disables a limit. ~0.005 USD per normal answer, so 0.25 is roughly 50 questions per user.
    daily_user_cost_usd_limit: Decimal = Decimal("0.25")
    global_daily_cost_usd_limit: Decimal = Decimal("0")  # circuit breaker over all users; 0 = disabled
    # UMA (Unidad de Medida y Actualización): fines are expressed as "N veces la UMA". INEGI publishes the value each
    # January in the DOF and it applies from 1 February to 31 January. The tool warns when this window has passed.
    uma_value: Decimal = Decimal("117.31")
    uma_valid_from: date = date(2026, 2, 1)
    uma_valid_until: date = date(2027, 1, 31)
    uma_source: str = "INEGI, publicada en el DOF el 9 de enero de 2026 (https://www.inegi.org.mx/temas/uma/)"

    def production_problems(self) -> list[str]:
        problems = []
        if self.jwt_secret_key == "development-only-change-me" or len(self.jwt_secret_key) < 32:
            problems.append("JWT_SECRET_KEY must be a random value of at least 32 characters")
        if self.resend_api_key and "example.com" in self.mail_from:
            problems.append("MAIL_FROM still uses the example.com placeholder")
        if any("localhost" in origin for origin in self.cors_origin_list):
            problems.append("CORS_ORIGINS still allows localhost")
        return problems

    @property
    def use_json_logs(self) -> bool:
        if self.log_format == "auto":
            return self.environment == "production"
        return self.log_format == "json"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
