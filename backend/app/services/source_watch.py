"""Detect that an official document changed or stopped being in force. Reads, compares and reports; changes nothing.

Two kinds of signal, because the sources are of two kinds:
- Documents listed in the Consejería's public index (11 of our 13): the index gives, for each document, the PDF path
  (it changes with every version, e.g. ..._6.4.pdf) and the "Última reforma" date. A change in either, or the
  document no longer appearing, is a finding.
- Documents outside the index (SSC Acuerdo and Protocolo): the SHA-256 of the downloaded file.

The state of "what we last saw" is a small JSON file kept in the repository, so the check runs anywhere (a scheduled
GitHub Action) without the database. Pure functions here; the network is injected so tests use saved pages.
"""
import hashlib
import html
import json
import re
import time
import unicodedata
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from app.services.sources import SourceSpec

INDEX_HOST = "data.consejeria.cdmx.gob.mx"
INDEX_URL = "https://" + INDEX_HOST + "/index.php/leyes/{section}?start={start}"
SECTIONS = ("leyes", "reglamentos", "codigos")
PAGE_SIZE = 27
MAX_PAGES = 20  # a runaway loop guard: today the biggest section has 7 pages

MONTHS = {m: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"], 1)}
_REFORM = re.compile(r"ultima reforma[^0-9]{0,60}?(\d{1,2})\s+de\s+([a-z]+)\s+(?:de|del)\s+(\d{4})")
_ITEM = re.compile(r'(?=<div class="nn_sliders_item")')


class IndexStructureError(Exception):
    """The index page no longer looks like it did. Never read this as «nothing changed»."""


def fold(text: str) -> str:
    """Lowercase without accents and with single spaces, to compare titles and dates written inconsistently."""
    plain = "".join(c for c in unicodedata.normalize("NFKD", html.unescape(text).casefold()) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", plain).strip()


@dataclass(frozen=True)
class IndexEntry:
    section: str
    title: str
    pdf_path: str | None
    reform_date: str | None  # ISO; None when the index does not state one (e.g. a recent regulation)
    description: str


def parse_reform_date(text: str) -> str | None:
    match = _REFORM.search(fold(text))
    if not match or match.group(2) not in MONTHS:
        return None
    try:
        return date(int(match.group(3)), MONTHS[match.group(2)], int(match.group(1))).isoformat()
    except ValueError:
        return None


def parse_index(page: str, section: str) -> list[IndexEntry]:
    entries = []
    for block in _ITEM.split(page)[1:]:
        title = re.search(r"<h2[^>]*>(.*?)</h2>", block, re.S)
        if not title:
            raise IndexStructureError(f"un elemento del índice «{section}» no trae título")
        pdf = re.search(r'href="([^"]+\.pdf)"', block, re.I)
        body = re.split(r"<table", block, maxsplit=1)[-1]
        description = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()
        entries.append(IndexEntry(section, html.unescape(re.sub(r"<[^>]+>", "", title.group(1))).strip(),
                                  pdf.group(1) if pdf else None, parse_reform_date(description), description[:300]))
    return entries


def fetch_index(fetch: Callable[[str], str], pause: float = 1.0) -> list[IndexEntry]:
    entries: list[IndexEntry] = []
    for section in SECTIONS:
        for page_number in range(MAX_PAGES):
            page = parse_index(fetch(INDEX_URL.format(section=section, start=page_number * PAGE_SIZE)), section)
            if page_number == 0 and not page:
                raise IndexStructureError(f"el índice «{section}» no devolvió ningún documento")
            entries += page
            if len(page) < PAGE_SIZE:
                break
            if pause:
                time.sleep(pause)
        else:
            raise IndexStructureError(f"el índice «{section}» no termina en {MAX_PAGES} páginas")
    return entries


def is_indexed(spec: SourceSpec) -> bool:
    return urlsplit(spec.url).hostname == INDEX_HOST


def pdf_path_of(url: str) -> str:
    return urlsplit(url).path


@dataclass
class Watched:
    """What we last saw of one source."""

    slug: str
    mode: str  # "index" or "hash"
    title: str | None = None  # index title, to find the document again if its PDF path changes
    pdf_path: str | None = None
    reform_date: str | None = None
    sha256: str | None = None
    url: str | None = None


@dataclass
class Finding:
    slug: str
    kind: str  # nueva_version | reforma_nueva | no_encontrado | contenido_cambio | inaccesible | error
    detail: str
    new_url: str | None = None
    fingerprint: str = field(default="")

    def __post_init__(self) -> None:
        if not self.fingerprint:
            basis = f"{self.slug}|{self.kind}|{self.new_url or ''}|{self.detail}"
            if self.kind == "error":  # a failure that lasts should remind you weekly, not once forever
                basis += f"|{date.today().isocalendar()[:2]}"
            self.fingerprint = hashlib.sha256(basis.encode()).hexdigest()[:12]


def load_state(path: Path) -> dict[str, Watched]:
    return {item["slug"]: Watched(**item) for item in json.loads(path.read_text(encoding="utf-8"))["sources"]}


def save_state(path: Path, state: dict[str, Watched]) -> None:
    payload = {"sources": [asdict(state[slug]) for slug in sorted(state)]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _find_in_index(entries: list[IndexEntry], watched: Watched) -> IndexEntry | None:
    for entry in entries:
        if entry.pdf_path and entry.pdf_path == watched.pdf_path:
            return entry
    titled = [e for e in entries if watched.title and fold(e.title) == fold(watched.title)]
    return titled[0] if len(titled) == 1 else None  # two documents with the same title: do not guess


def snapshot(specs: list[SourceSpec], entries: list[IndexEntry], hashes: dict[str, str]) -> tuple[dict[str, Watched], list[str]]:
    """The first state: what the index says today about each source, found by the PDF path in the manifest."""
    state, problems = {}, []
    for spec in specs:
        if is_indexed(spec):
            entry = next((e for e in entries if e.pdf_path and spec.url.endswith(e.pdf_path)), None)
            if entry is None:
                problems.append(f"{spec.slug}: su PDF del manifiesto no aparece en el índice de la Consejería")
                continue
            state[spec.slug] = Watched(spec.slug, "index", entry.title, entry.pdf_path, entry.reform_date, url=spec.url)
            if entry.reform_date and spec.last_reform_date and entry.reform_date != spec.last_reform_date.isoformat():
                problems.append(f"{spec.slug}: el índice dice reforma {entry.reform_date} y el manifiesto {spec.last_reform_date}")
        else:
            state[spec.slug] = Watched(spec.slug, "hash", sha256=hashes[spec.slug], url=spec.url)
    return state, problems


def compare(state: dict[str, Watched], specs: list[SourceSpec], entries: list[IndexEntry], hashes: dict[str, str],
            errors: dict[str, str] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for spec in specs:
        watched = state.get(spec.slug)
        if watched is None:
            findings.append(Finding(spec.slug, "error", "la fuente no está en data/watch-state.json (ejecuta `sources init`)"))
            continue
        if watched.mode == "index":
            entry = _find_in_index(entries, watched)
            base = f"https://{INDEX_HOST}"
            if entry is None:
                findings.append(Finding(spec.slug, "no_encontrado",
                                        f"«{watched.title}» ya no aparece en el índice de la Consejería: posible pérdida de vigencia o cambio de título"))
            elif entry.pdf_path != watched.pdf_path:
                findings.append(Finding(spec.slug, "nueva_version",
                                        f"el PDF cambió de {watched.pdf_path} a {entry.pdf_path} (reforma {watched.reform_date} → {entry.reform_date})",
                                        new_url=base + (entry.pdf_path or "")))
            elif entry.reform_date != watched.reform_date:
                findings.append(Finding(spec.slug, "reforma_nueva",
                                        f"la fecha de última reforma cambió de {watched.reform_date} a {entry.reform_date}",
                                        new_url=base + (entry.pdf_path or "")))
        else:
            if errors and spec.slug in errors:
                # Not a change in the document: the site did not answer (some government hosts refuse cloud IPs).
                findings.append(Finding(spec.slug, "inaccesible", f"no se pudo descargar: {errors[spec.slug]}"))
            elif hashes.get(spec.slug) != watched.sha256:
                findings.append(Finding(spec.slug, "contenido_cambio",
                                        f"el archivo cambió (sha256 {str(watched.sha256)[:12]} → {str(hashes.get(spec.slug))[:12]}); "
                                        "puede ser una versión nueva o solo una re-exportación del mismo texto", new_url=spec.url))
    return findings


def accept(state: dict[str, Watched], slug: str, entries: list[IndexEntry], hashes: dict[str, str]) -> Watched:
    """Record the current index/hash as the new baseline once a change was handled."""
    watched = state[slug]
    if watched.mode == "index":
        entry = _find_in_index(entries, watched)
        if entry is None:
            raise ValueError(f"{slug}: no aparece en el índice, no hay nada que aceptar")
        watched.title, watched.pdf_path, watched.reform_date = entry.title, entry.pdf_path, entry.reform_date
    else:
        watched.sha256 = hashes[slug]
    return watched


def split_findings(findings: list[Finding]) -> tuple[list[Finding], list[Finding]]:
    """(changes, unreachable). A source that could not be read says nothing about whether it changed."""
    return [f for f in findings if f.kind != "inaccesible"], [f for f in findings if f.kind == "inaccesible"]


def render_report(findings: list[Finding]) -> str:
    changes, unreachable = split_findings(findings)
    note = ""
    if unreachable:
        note = ("\n\nNo se pudieron revisar (no es un cambio, es que el sitio no respondió): "
                + ", ".join(f.slug for f in unreachable) + ". Revísalas desde tu computadora con `uv run python -m scripts.sources check`.")
    if not changes:
        return "Sin cambios en las fuentes que se pudieron revisar." + note
    lines = ["Se detectaron cambios en las fuentes oficiales:", ""]
    for f in changes:
        lines.append(f"- **{f.slug}** · `{f.kind}` · {f.detail}" + (f"\n  - Nueva versión: {f.new_url}" if f.new_url else ""))
    lines += ["", "Qué sigue: revisar el cambio, descargar e indexar con `scripts.fetch_sources` / `scripts.ingest_sources`,",
              "revisar las sanciones `stale` y actualizar `data/watch-state.json` con `scripts.sources accept <slug>`."]
    return "\n".join(lines) + note
