from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://localhost/avizum"
    jwt_secret_key: str = "development-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000"
    ai_enabled: bool = False
    ai_ollama_base_url: str = "http://localhost:11434"
    ai_chat_model: str = "gemma2:2b"
    ai_embedding_model: str = "mxbai-embed-large"
    ai_index_path: Path = Path("../data/legal-embeddings")
    ai_allow_legacy_faiss_deserialization: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
