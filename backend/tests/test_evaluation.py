from app.services.evaluation import first_relevant_rank, mean_reciprocal_rank, recall_at
from app.services.retrieval import SearchHit


def hit(slug: str, article: str) -> SearchHit:
    return SearchHit(0, slug, "", article, None, "", "", 1, 1, 0.0, 0.5)


def test_rank_matches_source_and_article_not_fraction_or_other_laws():
    hits = [hit("ley-movilidad", "59"), hit("reglamento-transito", "9"), hit("reglamento-transito", "59")]
    assert first_relevant_rank({("reglamento-transito", "59")}, hits) == 3
    assert first_relevant_rank({("codigo-fiscal", "230")}, hits) is None


def test_recall_and_mrr():
    ranks = [1, 3, None, 6]
    assert recall_at(ranks, 5) == 0.5
    assert mean_reciprocal_rank(ranks) == (1 + 1 / 3 + 1 / 6) / 4
