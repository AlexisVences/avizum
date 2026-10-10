"""Hybrid retrieval over legal_chunks: pgvector (meaning) + Postgres full-text (exact words), fused with RRF.

Knows nothing about the agent; the agent's tools call `search` and `get_article`.
"""
import re
from dataclasses import dataclass

from langchain_core.embeddings import Embeddings
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.domain import LegalChunk, OfficialSource

CANDIDATES = 20  # per search, before fusion
RRF_K = 60  # standard damping constant of Reciprocal Rank Fusion


@dataclass(frozen=True)
class SearchHit:
    chunk_id: int
    source_slug: str
    source_title: str
    article: str
    fraction: str | None
    heading_path: str
    text: str
    page_start: int
    page_end: int
    score: float  # RRF score; only meaningful to order this result list
    similarity: float | None  # cosine similarity to the query (None for get_article)
    source_url: str = ""  # the official PDF; a citation opens it at `#page=N`


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = RRF_K) -> list[tuple[int, float]]:
    """Merge ranked id lists using only positions, so unrelated score scales never have to be compared."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for position, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + position)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def _any_word_query(query: str) -> str | None:
    """'a | b | c': a chunk matches if it contains ANY word, and ts_rank_cd ranks more matches higher.

    websearch_to_tsquery requires ALL words, which returns nothing for a natural-language question.
    Only word characters survive, so the string cannot inject tsquery operators.
    """
    words = list(dict.fromkeys(re.findall(r"\w+", query)))
    return " | ".join(words) or None


def _current_chunks(source_slugs: list[str] | None):
    stmt = select(LegalChunk.id).join(OfficialSource, OfficialSource.id == LegalChunk.source_id).where(OfficialSource.is_current)
    return stmt.where(OfficialSource.slug.in_(source_slugs)) if source_slugs else stmt


def _hit(chunk: LegalChunk, source: OfficialSource, score: float, similarity: float | None) -> SearchHit:
    return SearchHit(
        chunk_id=chunk.id, source_slug=source.slug, source_title=source.title, article=chunk.article, fraction=chunk.fraction,
        heading_path=chunk.heading_path, text=chunk.text, page_start=chunk.page_start, page_end=chunk.page_end,
        score=score, similarity=similarity, source_url=source.url,
    )


def _rankings(db: Session, query: str, query_vector: list[float], base) -> list[list[int]]:
    """The two ranked id lists for one query: by meaning (vectors) and by words (full text)."""
    by_meaning = list(db.scalars(base.order_by(LegalChunk.embedding.cosine_distance(query_vector)).limit(CANDIDATES)).all())
    by_words: list[int] = []
    if words := _any_word_query(query):
        tsquery = func.to_tsquery(text("'spanish'"), func.immutable_unaccent(words))
        by_words = list(db.scalars(
            base.where(LegalChunk.tsv.op("@@")(tsquery))
            .order_by(func.ts_rank_cd(LegalChunk.tsv, tsquery).desc(), LegalChunk.id)
            .limit(CANDIDATES)
        ).all())
    return [by_meaning, by_words]


def search_many(db: Session, queries: list[str], embeddings: Embeddings, source_slugs: list[str] | None = None, k: int = 6) -> list[SearchHit]:
    """Several phrasings of the same need (e.g. the user's words + a legal-vocabulary rewrite), fused with RRF.

    `similarity` in each hit is the best cosine similarity over all the phrasings, so a relevance floor does not drop a
    chunk that one phrasing found just because another phrasing was poorly worded.
    """
    queries = [q.strip() for q in queries if q.strip()]
    if not queries:
        return []
    base = _current_chunks(source_slugs)
    vectors = [embeddings.embed_query(query) for query in queries]
    rankings = [ranking for query, vector in zip(queries, vectors) for ranking in _rankings(db, query, vector, base)]
    fused = reciprocal_rank_fusion(rankings)[:k]
    similarities = [1 - LegalChunk.embedding.cosine_distance(vector) for vector in vectors]
    best = similarities[0] if len(similarities) == 1 else func.greatest(*similarities)
    rows = db.execute(
        select(LegalChunk, OfficialSource, best.label("similarity"))
        .join(OfficialSource, OfficialSource.id == LegalChunk.source_id)
        .where(LegalChunk.id.in_([chunk_id for chunk_id, _ in fused]))
    ).all()
    by_id = {chunk.id: (chunk, source, similarity) for chunk, source, similarity in rows}
    return [_hit(by_id[chunk_id][0], by_id[chunk_id][1], score, float(by_id[chunk_id][2])) for chunk_id, score in fused]


def search(db: Session, query: str, embeddings: Embeddings, source_slugs: list[str] | None = None, k: int = 6) -> list[SearchHit]:
    return search_many(db, [query], embeddings, source_slugs, k)


def get_article(db: Session, source_slug: str, article: str) -> list[SearchHit]:
    """Every chunk of one article (all its fractions) in document order; used to follow cross-references."""
    rows = db.execute(
        select(LegalChunk, OfficialSource)
        .join(OfficialSource, OfficialSource.id == LegalChunk.source_id)
        .where(OfficialSource.is_current, OfficialSource.slug == source_slug, func.lower(LegalChunk.article) == " ".join(article.lower().split()))
        .order_by(LegalChunk.id)
    ).all()
    return [_hit(chunk, source, 0.0, None) for chunk, source in rows]
