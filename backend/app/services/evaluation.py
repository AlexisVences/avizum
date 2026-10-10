"""Retrieval metrics. Pure functions; the eval script supplies the cases and the real search."""
from app.services.retrieval import SearchHit

Expected = set[tuple[str, str]]  # (source slug, article); fractions are not required to match


def first_relevant_rank(expected: Expected, hits: list[SearchHit]) -> int | None:
    """1-based rank of the first hit whose (source, article) is acceptable, or None."""
    for rank, hit in enumerate(hits, start=1):
        if (hit.source_slug, hit.article) in expected:
            return rank
    return None


def recall_at(ranks: list[int | None], k: int) -> float:
    return sum(1 for rank in ranks if rank is not None and rank <= k) / len(ranks)


def mean_reciprocal_rank(ranks: list[int | None]) -> float:
    return sum(1 / rank for rank in ranks if rank is not None) / len(ranks)
