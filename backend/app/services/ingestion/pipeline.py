"""Writes the chunks of one official source: chunk -> embed -> insert, inside the caller's transaction."""
from langchain_core.embeddings import Embeddings
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.domain import LegalChunk, OfficialSource
from app.services.ingestion.chunker import TokenCounter, chunk_article
from app.services.ingestion.embedder import embed_chunks
from app.services.ingestion.parser import ParsedArticle


def ingest_articles(
    db: Session,
    source: OfficialSource,
    articles: list[ParsedArticle],
    embeddings: Embeddings,
    count_tokens: TokenCounter | None = None,
    replace: bool = False,
) -> int:
    """Returns the number of chunks written; 0 when the source already has chunks and `replace` is false."""
    existing = db.scalar(select(func.count()).select_from(LegalChunk).where(LegalChunk.source_id == source.id))
    if existing and not replace:
        return 0
    db.execute(delete(LegalChunk).where(LegalChunk.source_id == source.id))
    drafts = [draft for article in articles for draft in chunk_article(article, count_tokens=count_tokens)]
    vectors = embed_chunks(drafts, embeddings)  # all vectors are computed before inserting anything
    db.add_all(
        LegalChunk(
            source_id=source.id, article=draft.article, fraction=draft.fraction, heading_path=draft.heading_path,
            text=draft.text, page_start=draft.page_start, page_end=draft.page_end, token_count=draft.token_count,
            embedding=vector,
        )
        for draft, vector in zip(drafts, vectors)
    )
    return len(drafts)
