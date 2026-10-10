from sqlalchemy import func, select

from app.models.domain import EMBEDDING_DIMENSIONS, LegalChunk, OfficialSource
from app.services.ingestion.parser import ParsedArticle
from app.services.ingestion.pipeline import ingest_articles
from tests.test_ingestion_embedder import RecordingEmbeddings


def words(text: str) -> int:
    return len(text.split())


def source(db) -> OfficialSource:
    src = OfficialSource(slug="reglamento-transito", title="Reglamento", kind="reglamento", url="https://x.mx/r.pdf", sha256="a" * 64)
    db.add(src)
    db.flush()
    return src


def article(number: str, line: str, page: int) -> ParsedArticle:
    return ParsedArticle(article=number, heading_path=f"Reglamento › Art. {number}", lines=(line,), line_pages=(page,))


def count(db, src) -> int:
    return db.scalar(select(func.count()).select_from(LegalChunk).where(LegalChunk.source_id == src.id))


def test_writes_chunks_with_vectors_and_skips_a_source_that_is_already_indexed(client):
    _, factory = client
    with factory() as db:
        src = source(db)
        arts = [article("1", "Artículo 1.- Uno.", 1), article("2", "Artículo 2.- Dos.", 2)]
        assert ingest_articles(db, src, arts, RecordingEmbeddings(), words) == 2
        db.commit()
        row = db.scalars(select(LegalChunk).where(LegalChunk.article == "2")).one()
        assert (row.page_start, len(row.embedding)) == (2, EMBEDDING_DIMENSIONS)

        fake = RecordingEmbeddings()
        assert ingest_articles(db, src, arts, fake, words) == 0
        assert fake.batches == []  # no API calls for an already-indexed source


def test_replace_rebuilds_the_chunks_of_that_source_only(client):
    _, factory = client
    with factory() as db:
        src, other = source(db), OfficialSource(slug="otra", title="Otra", kind="ley", url="https://x.mx/o.pdf", sha256="b" * 64)
        db.add(other)
        db.flush()
        ingest_articles(db, src, [article("1", "Artículo 1.- Uno.", 1)], RecordingEmbeddings(), words)
        ingest_articles(db, other, [article("9", "Artículo 9.- Nueve.", 1)], RecordingEmbeddings(), words)
        ingest_articles(db, src, [article("5", "Artículo 5.- Cinco.", 1), article("6", "Artículo 6.- Seis.", 1)], RecordingEmbeddings(), words, replace=True)
        db.commit()
        assert sorted(c.article for c in db.scalars(select(LegalChunk).where(LegalChunk.source_id == src.id))) == ["5", "6"]
        assert count(db, other) == 1
