"""Import the authorized-agents acuerdo registered under AGENTS_SOURCE_SLUG; safe to re-run."""
import pymupdf

from app.db.session import SessionLocal
from app.services.acuerdo_parser import parse_acuerdo, validate_counts
from app.services.agents_import import replace_agents
from app.services.agents_registry import AGENTS_SOURCE_SLUG, current_agents_source
from app.services.sources import load_manifest, local_path, sha256_of
from scripts.fetch_sources import MANIFEST, SOURCES_DIR


def main() -> None:
    spec = next((s for s in load_manifest(MANIFEST) if s.slug == AGENTS_SOURCE_SLUG), None)
    if spec is None or not spec.expected_counts:
        raise SystemExit(f"Falta la entrada {AGENTS_SOURCE_SLUG} con expected_counts en {MANIFEST}")
    path = local_path(spec, SOURCES_DIR)
    with SessionLocal() as db:
        source = current_agents_source(db)
        if source is None or not path.exists() or source.sha256 != sha256_of(path):
            raise SystemExit("El PDF no está registrado o cambió; corre primero scripts.fetch_sources")
        document = pymupdf.open(path)
        first, last = spec.pages or (1, document.page_count)
        text = "\n".join(document[i].get_text() for i in range(first - 1, last))
        sections = parse_acuerdo(text)
        validate_counts(sections, spec.expected_counts)
        counts = replace_agents(db, source, sections)
        db.commit()
    print(f"Importados {counts} desde {source.title}")


if __name__ == "__main__":
    main()
