"""Parse, chunk and embed the current official sources into legal_chunks; safe to re-run.

Downloading and hashing is `scripts.fetch_sources`; this only reads the registered PDFs.
Usage: uv run python -m scripts.ingest_sources [--only <slug>] [--force]
"""
import argparse

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.domain import OfficialSource
from app.services.ingestion.chunker import openai_token_counter
from app.services.ingestion.embedder import build_embeddings
from app.services.ingestion.parser import parse_pdf
from app.services.ingestion.pipeline import ingest_articles
from app.services.sources import load_manifest, local_path, sha256_of
from scripts.fetch_sources import MANIFEST, SOURCES_DIR

INGESTIBLE_KINDS = {"ley", "reglamento", "codigo", "protocolo"}  # acuerdos feed the agents registry, not the RAG


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cli.add_argument("--only", help="slug of a single source")
    cli.add_argument("--force", action="store_true", help="re-ingest sources that already have chunks")
    args = cli.parse_args()

    specs = [s for s in load_manifest(MANIFEST) if s.kind in INGESTIBLE_KINDS and args.only in (None, s.slug)]
    if not specs:
        raise SystemExit(f"Ninguna fuente indexable coincide con {args.only!r}")
    embeddings, count_tokens = build_embeddings(get_settings()), openai_token_counter()

    with SessionLocal() as db:
        for spec in specs:
            source = db.scalar(select(OfficialSource).where(OfficialSource.slug == spec.slug, OfficialSource.is_current))
            path = local_path(spec, SOURCES_DIR)
            if source is None or not path.exists() or source.sha256 != sha256_of(path):
                raise SystemExit(f"{spec.slug}: el PDF no está registrado o cambió; corre primero scripts.fetch_sources")
            articles = parse_pdf(path, spec.title, layout=spec.layout, pages=spec.pages)
            if spec.articles:
                found = {a.article: a for a in articles}
                missing = [n for n in spec.articles if n not in found]
                if missing:
                    raise SystemExit(f"{spec.slug}: no se encontraron los artículos {missing}")
                articles = [found[n] for n in spec.articles]
            written = ingest_articles(db, source, articles, embeddings, count_tokens, replace=args.force)
            db.commit()
            print(f"{spec.slug}: {len(articles)} artículos -> {written} chunks" if written else f"{spec.slug}: ya indexado (usa --force)")


if __name__ == "__main__":
    main()
