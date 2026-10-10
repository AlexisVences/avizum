"""Turns chunk drafts into embedding vectors through LangChain's `Embeddings` interface."""
from langchain_core.embeddings import Embeddings

from app.core.config import Settings
from app.models.domain import EMBEDDING_DIMENSIONS
from app.services.ingestion.chunker import ChunkDraft

DEFAULT_BATCH_SIZE = 100


def build_embeddings(settings: Settings) -> Embeddings:
    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is not set; add it to backend/.env")
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
        dimensions=EMBEDDING_DIMENSIONS,
        max_retries=3,
    )


def embed_chunks(drafts: list[ChunkDraft], embeddings: Embeddings, batch_size: int = DEFAULT_BATCH_SIZE) -> list[list[float]]:
    """One vector per draft, in the same order. Embeds `embedding_text` (heading path + text)."""
    vectors: list[list[float]] = []
    for start in range(0, len(drafts), batch_size):
        batch = drafts[start : start + batch_size]
        vectors.extend(embeddings.embed_documents([draft.embedding_text for draft in batch]))
    for vector in vectors:
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise ValueError(f"Expected {EMBEDDING_DIMENSIONS}-dimensional embeddings, got {len(vector)}")
    return vectors
