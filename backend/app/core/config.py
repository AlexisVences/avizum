from datetime import date
from decimal import Decimal
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://localhost/avizum"
    jwt_secret_key: str = "development-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000"
    openai_api_key: SecretStr | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-5-mini"
    # Chat limits (spec section 2). Reasoning tokens count toward the output cap.
    chat_max_output_tokens: int = 1800  # measured: a 400-word answer used ~1,100 incl. reasoning; 1,200 was too tight
    chat_max_agent_steps: int = 6  # model calls per turn: up to 5 rounds of tools plus the final answer
    chat_context_messages: int = 12  # history sent to the model; the full history is still stored and shown
    # UMA (Unidad de Medida y Actualización): fines are expressed as "N veces la UMA". INEGI publishes the value each
    # January in the DOF and it applies from 1 February to 31 January. The tool warns when this window has passed.
    uma_value: Decimal = Decimal("117.31")
    uma_valid_from: date = date(2026, 2, 1)
    uma_valid_until: date = date(2027, 1, 31)
    uma_source: str = "INEGI, publicada en el DOF el 9 de enero de 2026 (https://www.inegi.org.mx/temas/uma/)"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
