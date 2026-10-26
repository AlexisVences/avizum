"""Official-source manifest and version registry. No network access lives here."""
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import OfficialSource

KINDS = {"ley", "reglamento", "codigo", "acuerdo", "decreto", "guia", "protocolo", "programa", "tarifas", "ficha"}
LAYOUTS = {"articles", "sections", "chapters", "tarifas", "decreto", "ficha"}
SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True)
class SourceSpec:
    slug: str
    title: str
    kind: str
    url: str
    last_reform_date: date | None
    manual: bool = False
    expected_counts: dict[str, int] | None = None
    pages: tuple[int, int] | None = None
    articles: tuple[str, ...] | None = None  # index only these articles/sections (e.g. the fee articles of a huge code)
    watch: bool = True  # false for documents the client reviews by hand once a year (see scripts.sources)
    max_chunk_tokens: int | None = None  # smaller than the default to cut a fee table into one chunk per fraction
    layout: str = "articles"  # "sections" for documents numbered 4.5, 4.6…, "chapters" for "5. TÍTULO" programs, "tarifas" for fee schedules headed "Art. 219", "decreto" for roman chapters with "IV.4." subsections, "ficha" for a transcribed web page, instead of "Artículo N"


def _parse_entry(raw: dict) -> SourceSpec:
    slug = raw["slug"]
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError(f"Slug inválido: {slug!r}")
    if raw["kind"] not in KINDS:
        raise ValueError(f"Tipo inválido en {slug}: {raw['kind']!r}")
    if not raw["url"].startswith("https://"):
        raise ValueError(f"La URL de {slug} debe ser https")
    layout = raw.get("layout", "articles")
    if layout not in LAYOUTS:
        raise ValueError(f"Layout inválido en {slug}: {layout!r}")
    reform = raw.get("last_reform_date")
    pages = raw.get("pages")
    if pages is not None and not (len(pages) == 2 and 1 <= pages[0] <= pages[1]):
        raise ValueError(f"Rango de páginas inválido en {slug}: {pages!r}")
    max_chunk_tokens = raw.get("max_chunk_tokens")
    if max_chunk_tokens is not None and (not isinstance(max_chunk_tokens, int) or max_chunk_tokens < 1):
        raise ValueError(f"max_chunk_tokens inválido en {slug}: {max_chunk_tokens!r}")
    return SourceSpec(
        slug=slug,
        title=raw["title"],
        kind=raw["kind"],
        url=raw["url"],
        last_reform_date=date.fromisoformat(reform) if reform else None,
        manual=bool(raw.get("manual", False)),
        expected_counts=raw.get("expected_counts"),
        pages=tuple(pages) if pages else None,
        articles=tuple(str(a) for a in raw["articles"]) if raw.get("articles") else None,
        layout=layout,
        max_chunk_tokens=max_chunk_tokens,
        watch=bool(raw.get("watch", True)),
    )


def load_manifest(path: Path) -> list[SourceSpec]:
    specs = [_parse_entry(raw) for raw in json.loads(path.read_text(encoding="utf-8"))["sources"]]
    slugs = [spec.slug for spec in specs]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Slugs duplicados en el manifiesto")
    return specs


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def local_path(spec: SourceSpec, directory: Path) -> Path:
    return directory / f"{spec.slug}.{'md' if spec.layout == 'ficha' else 'pdf'}"  # a ficha is the transcription of a web page


def _apply_metadata(source: OfficialSource, spec: SourceSpec) -> None:
    source.title = spec.title
    source.kind = spec.kind
    source.url = spec.url
    source.last_reform_date = spec.last_reform_date


def register_source(db: Session, spec: SourceSpec, sha256: str) -> tuple[OfficialSource, bool]:
    """Make the file with `sha256` the current version of `spec.slug`. Caller commits."""
    current = db.scalar(
        select(OfficialSource).where(OfficialSource.slug == spec.slug, OfficialSource.is_current)
    )
    if current is not None and current.sha256 == sha256:
        _apply_metadata(current, spec)
        return current, False
    if current is not None:
        current.is_current = False
        db.flush()
    source = db.scalar(
        select(OfficialSource).where(OfficialSource.slug == spec.slug, OfficialSource.sha256 == sha256)
    )
    if source is None:
        source = OfficialSource(slug=spec.slug, sha256=sha256, is_current=True)
        db.add(source)
    source.is_current = True
    _apply_metadata(source, spec)
    db.flush()
    return source, True
