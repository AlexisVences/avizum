from sqlalchemy import func, select, text

from app.models.domain import EMBEDDING_DIMENSIONS, LegalChunk, OfficialSource


def _vector(*head: float) -> list[float]:
    return [*head, *([0.0] * (EMBEDDING_DIMENSIONS - len(head)))]


def _chunk(source_id: int, article: str, body: str, embedding: list[float]) -> LegalChunk:
    return LegalChunk(
        source_id=source_id, article=article, heading_path=f"Reglamento › Art. {article}", text=body,
        page_start=1, page_end=1, token_count=10, embedding=embedding,
    )


def test_vector_distance_orders_by_meaning_and_tsv_ignores_accents(client):
    _, factory = client
    with factory() as db:
        source = OfficialSource(slug="reglamento-transito", title="Reglamento", kind="reglamento", url="https://x.mx/r.pdf", sha256="a" * 64)
        db.add(source)
        db.flush()
        db.add_all([
            _chunk(source.id, "30", "Retención de placas de circulación", _vector(1.0, 0.0)),
            _chunk(source.id, "31", "Velocidad máxima en vías primarias", _vector(0.0, 1.0)),
        ])
        db.commit()

        nearest = db.scalars(
            select(LegalChunk).order_by(LegalChunk.embedding.cosine_distance(_vector(0.9, 0.1))).limit(1)
        ).one()
        assert nearest.article == "30"

        # "retencion" (no accent) must match "Retención" through the generated, unaccented tsvector.
        hits = db.scalars(
            select(LegalChunk).where(LegalChunk.tsv.op("@@")(func.websearch_to_tsquery(text("'spanish'"), "retencion placas")))
        ).all()
        assert [chunk.article for chunk in hits] == ["30"]
