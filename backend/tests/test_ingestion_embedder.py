import pytest
from langchain_core.embeddings import Embeddings

from app.core.config import Settings
from app.models.domain import EMBEDDING_DIMENSIONS
from app.services.ingestion.chunker import ChunkDraft
from app.services.ingestion.embedder import build_embeddings, embed_chunks


class RecordingEmbeddings(Embeddings):
    def __init__(self) -> None:
        self.batches: list[list[str]] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.batches.append(texts)
        return [[float(len(text))] + [0.0] * (EMBEDDING_DIMENSIONS - 1) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def draft(n: int) -> ChunkDraft:
    return ChunkDraft(article=str(n), fraction=None, heading_path="Ley › Art. " + str(n), text="x" * n, page_start=1, page_end=1, token_count=n)


def test_embeds_the_contextual_text_in_batches_keeping_order():
    fake = RecordingEmbeddings()
    drafts = [draft(n) for n in range(1, 6)]
    vectors = embed_chunks(drafts, fake, batch_size=2)
    assert [len(batch) for batch in fake.batches] == [2, 2, 1]
    assert fake.batches[0][0] == drafts[0].embedding_text  # heading_path + text, not just text
    assert [v[0] for v in vectors] == [float(len(d.embedding_text)) for d in drafts]


def test_rejects_vectors_with_the_wrong_dimension():
    class Wrong(RecordingEmbeddings):
        def embed_documents(self, texts):
            return [[0.1, 0.2] for _ in texts]

    with pytest.raises(ValueError, match="1536"):
        embed_chunks([draft(1)], Wrong(), batch_size=10)


def test_build_embeddings_requires_an_api_key():
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        build_embeddings(Settings(openai_api_key=None, _env_file=None))
