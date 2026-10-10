from langchain_core.embeddings import Embeddings

from app.models.domain import EMBEDDING_DIMENSIONS, LegalChunk, OfficialSource
from app.services.retrieval import get_article, reciprocal_rank_fusion, search


def vec(*head: float) -> list[float]:
    return [*head, *([0.0] * (EMBEDDING_DIMENSIONS - len(head)))]


class FixedQuery(Embeddings):
    def __init__(self, vector: list[float]) -> None:
        self.vector = vector

    def embed_documents(self, texts):
        return [self.vector for _ in texts]

    def embed_query(self, text):
        return self.vector


def add_source(db, slug="reglamento-transito", sha="a", current=True) -> OfficialSource:
    source = OfficialSource(slug=slug, title=slug.title(), kind="reglamento", url=f"https://x.mx/{slug}.pdf", sha256=sha * 64, is_current=current)
    db.add(source)
    db.flush()
    return source


def add_chunk(db, source, article, text, embedding, fraction=None, page=1) -> LegalChunk:
    chunk = LegalChunk(
        source_id=source.id, article=article, fraction=fraction, heading_path=f"{source.title} › Art. {article}",
        text=text, page_start=page, page_end=page, token_count=10, embedding=embedding,
    )
    db.add(chunk)
    db.flush()
    return chunk


def test_rrf_rewards_items_that_both_searches_found():
    fused = reciprocal_rank_fusion([[1, 2, 3], [3, 4]])
    assert [chunk_id for chunk_id, _ in fused] == [3, 1, 2, 4]
    assert fused[0][1] > fused[1][1]


def test_hybrid_search_finds_by_meaning_and_by_exact_words(client):
    _, factory = client
    with factory() as db:
        source = add_source(db)
        add_chunk(db, source, "10", "Retención de placas por estacionarse en banqueta", vec(1, 0))
        add_chunk(db, source, "11", "Velocidad máxima en vías primarias", vec(0, 1))
        add_chunk(db, source, "12", "Almacenaje diario del vehículo en el depósito", vec(0, 0, 1))
        db.commit()
        # The query vector points at article 10, but the words "almacenaje" and "vehículo" only match article 12.
        hits = search(db, "almacenaje del vehículo", FixedQuery(vec(1, 0)), k=2)
        assert [h.article for h in hits] == ["12", "10"]


def test_natural_questions_match_any_word_not_all_of_them(client):
    _, factory = client
    with factory() as db:
        source = add_source(db)
        add_chunk(db, source, "10", "Prohibido estacionarse en banqueta", vec(1, 0))
        add_chunk(db, source, "11", "Velocidad máxima en vías primarias", vec(0, 1))
        add_chunk(db, source, "12", "Almacenaje diario del vehículo", vec(0, 0, 1))
        db.commit()
        # No chunk contains all of these words; websearch_to_tsquery would return nothing.
        hits = search(db, "banqueta almacenaje zzzz", FixedQuery(vec(0, 0, 0, 1)))
        assert hits[-1].article == "11"  # the two lexical matches outrank the chunk that matches nothing


def test_only_current_source_versions_are_searched(client):
    _, factory = client
    with factory() as db:
        old = add_source(db, sha="a", current=False)
        new = add_source(db, sha="b", current=True)
        add_chunk(db, old, "5", "Texto derogado sobre placas", vec(1))
        add_chunk(db, new, "5", "Texto vigente sobre placas", vec(1))
        db.commit()
        hits = search(db, "placas", FixedQuery(vec(1)))
        assert [h.text for h in hits] == ["Texto vigente sobre placas"]
        assert [h.text for h in get_article(db, "reglamento-transito", "5")] == ["Texto vigente sobre placas"]


def test_source_slugs_filter_and_hit_carries_citation_fields(client):
    _, factory = client
    with factory() as db:
        reglamento, ley = add_source(db, "reglamento-transito", "a"), add_source(db, "ley-movilidad", "b")
        add_chunk(db, reglamento, "30", "Estacionar en banqueta", vec(1), fraction="I", page=31)
        add_chunk(db, ley, "9", "Estacionar en banqueta", vec(1))
        db.commit()
        [hit] = search(db, "estacionar banqueta", FixedQuery(vec(1)), source_slugs=["reglamento-transito"])
        assert (hit.source_slug, hit.article, hit.fraction, hit.page_start) == ("reglamento-transito", "30", "I", 31)
        assert hit.similarity > 0.99


def test_get_article_returns_all_fractions_in_document_order(client):
    _, factory = client
    with factory() as db:
        source = add_source(db)
        add_chunk(db, source, "30", "Intro\nI. Banquetas", vec(1), fraction="I")
        add_chunk(db, source, "30", "Intro\nII. Doble fila", vec(1), fraction="II")
        add_chunk(db, source, "30 Bis", "Otro artículo", vec(1))
        db.commit()
        assert [h.fraction for h in get_article(db, "reglamento-transito", "30")] == ["I", "II"]
        assert [h.article for h in get_article(db, "reglamento-transito", " 30 bis ")] == ["30 Bis"]
        assert get_article(db, "reglamento-transito", "999") == []


class PerQuery(Embeddings):
    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self.vectors = vectors

    def embed_documents(self, texts):
        return [self.vectors[t] for t in texts]

    def embed_query(self, text):
        return self.vectors[text]


def test_search_many_fuses_phrasings_so_each_can_rescue_a_chunk(client):
    from app.services.retrieval import search_many

    _, factory = client
    with factory() as db:
        source = add_source(db)
        add_chunk(db, source, "33", "Candado inmovilizador en vehículos estacionados", vec(1, 0))
        add_chunk(db, source, "9", "Velocidad máxima en vías primarias", vec(0, 1))
        db.commit()
        embeddings = PerQuery({"la araña": vec(0, 1), "candado inmovilizador": vec(1, 0)})
        # Alone, the slang query points at the wrong chunk; with the rewrite fused in, article 33 is retrieved too.
        assert search(db, "la araña", embeddings, k=1)[0].article == "9"
        assert "33" in [h.article for h in search_many(db, ["la araña", "candado inmovilizador"], embeddings, k=2)]
        assert search_many(db, ["   "], embeddings) == []
