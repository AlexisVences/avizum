"""Keeps `legal_sanctions` in step with the indexed chunks and with the rows a person verified.

Flow: `sync_pending` extracts candidate rows (status `pending`, idempotent) -> a person reviews the sheet from
`render_review` -> `apply_review` marks approved rows `verified` and exports them to `data/sanctions/verified.json`
(git is the source of truth: `load_verified` rebuilds the verified rows after a database rebuild or a re-ingest).
Nothing here reaches the agent: only rows with status `verified` and a matching `chunk_hash` may be served.
"""
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import LegalChunk, LegalSanction, OfficialSource, SanctionStatus
from app.services.ingestion.sanctions import (
    EXTRACTOR_VERSION, Extraction, Issue, Sanction, chunk_hash, extract_sanctions, inherit_article_wide,
)

MANUAL_ORDINAL_BASE = 100  # hand-written rows (tables the extractor cannot read) never collide with extracted ones
CONTENT_FIELDS = (
    "fraction", "inciso", "applies_to", "conduct_text", "clause_text", "uma_min", "uma_mid", "uma_max",
    "points_license", "points_plate", "other_consequences",
)
TANDA_TITLES = {
    1: "Tanda 1 — cláusulas que asignan montos por inciso (donde nació el error del cinturón)",
    2: "Tanda 2 — sanciones que el texto limita a un tipo de vehículo o situación (`applies_to`)",
    3: "Tanda 3 — fragmentos con algo que el extractor no pudo resolver",
    4: "Tanda 4 — una cláusula por fracción, sin incisos (deterministas): revisa la muestra ★ y aprueba la tanda",
}
_DECISION = re.compile(r"^- \[(?P<mark>[ xX!])\] `(?P<id>[^`]+)`", re.M)
_SECTION = re.compile(r"^- \[(?P<mark>[ xX])\] \*\*APROBAR TODA LA TANDA (?P<tanda>\d)\*\*", re.M)


@dataclass
class SyncReport:
    chunks: int = 0
    created: int = 0
    unchanged: int = 0
    replaced: int = 0
    removed: int = 0
    issues: list[tuple[str, str | None, Issue]] = field(default_factory=list)


def _chunks(db: Session, slug: str) -> list[LegalChunk]:
    return list(db.scalars(
        select(LegalChunk).join(OfficialSource, OfficialSource.id == LegalChunk.source_id)
        .where(OfficialSource.slug == slug, OfficialSource.is_current).order_by(LegalChunk.id)
    ))


def row_id(slug: str, article: str, chunk_fraction: str | None, ordinal: int, digest: str) -> str:
    return f"{slug}:{article}:{chunk_fraction or '-'}:{ordinal}:{digest[:8]}"


SUPPLEMENTARY_FIELDS = ("lead_text", "points_mode")  # derived from the same text; updating them never un-verifies a row


def _content(obj) -> tuple:
    return tuple(getattr(obj, name) for name in CONTENT_FIELDS)


_ARTICLE_PREFIX = re.compile(r"^Art[ií]culo\s+\d+[^.\s]*\s*\.?\s*-\s*", re.I)


def _norm_text(value: str | None) -> str:
    text = _ARTICLE_PREFIX.sub("", (value or "").strip()).rstrip(" .;,")
    return re.sub(r"[;,]?\s+(?:y|o|ó|u)$", "", text).rstrip(" .;,")  # a dangling connector is not part of the conduct


def _equivalent(old, new) -> bool:
    """Same verified content. Tolerated, because a person verified the amount and the conduct, not the punctuation:
    trailing punctuation, the "Artículo N.-" prefix, a conduct whose last 1-2 characters the first extractor cut off,
    and `other_consequences` distilled to the phrases that were already inside the old, longer text."""
    for name in CONTENT_FIELDS:
        a, b = getattr(old, name), getattr(new, name)
        if a == b:
            continue
        if name in ("conduct_text", "clause_text") and _norm_text(a) == _norm_text(b):
            continue
        if name == "conduct_text" and a and b and _norm_text(b).startswith(_norm_text(a)) and 0 < len(_norm_text(b)) - len(_norm_text(a)) <= 2:
            continue
        if name == "other_consequences" and b and a and all(part in a for part in b.split("; ")):
            continue
        return False
    return True


def _from_manual(entry: dict, index: int) -> Sanction:
    def dec(key):
        return Decimal(str(entry[key])) if entry.get(key) is not None else None
    return Sanction(
        ordinal=MANUAL_ORDINAL_BASE + index, fraction=entry.get("fraction"), inciso=entry.get("inciso"),
        conduct_text=entry["conduct_text"], clause_text=entry["clause_text"], uma_min=dec("uma_min"),
        uma_mid=dec("uma_mid"), uma_max=dec("uma_max"), points_license=entry.get("points_license"),
        points_plate=entry.get("points_plate"), other_consequences=entry.get("other_consequences"),
        applies_to=entry.get("applies_to"),
    )


def sync_pending(db: Session, slug: str, manual: list[dict] | None = None) -> SyncReport:
    """Extract candidate rows for every current chunk of `slug`. Idempotent: rows whose verified content did not
    change keep their status (a verified row stays verified); changed rows go back to pending."""
    report = SyncReport()
    manual_by_chunk: dict[tuple[str, str | None], list[dict]] = {}
    for entry in manual or []:
        manual_by_chunk.setdefault((entry["article"], entry.get("chunk_fraction")), []).append(entry)

    chunks = _chunks(db, slug)
    extractions: dict[int, Extraction] = {c.id: extract_sanctions(c.article, c.fraction, c.text) for c in chunks}

    # An article-wide clause ("el presente artículo") written in one fraction chunk covers its sibling fractions.
    by_article: dict[str, list[LegalChunk]] = {}
    for chunk in chunks:
        by_article.setdefault(chunk.article, []).append(chunk)
    for siblings in by_article.values():
        template = next((s for c in siblings for s in extractions[c.id].sanctions if s.article_wide), None)
        if template is None:
            continue
        for chunk in siblings:
            if chunk.fraction and not extractions[chunk.id].sanctions and not extractions[chunk.id].issues:
                extractions[chunk.id].sanctions = [inherit_article_wide(template, chunk.fraction, chunk.text)]

    for chunk in chunks:
        report.chunks += 1
        digest = chunk_hash(chunk.text)
        extraction = extractions[chunk.id]
        candidates = list(extraction.sanctions)
        for index, entry in enumerate(manual_by_chunk.get((chunk.article, chunk.fraction), [])):
            candidates.append(_from_manual(entry, index))
            extraction.issues = [i for i in extraction.issues if i.kind != "tabla"]  # captured by hand
        report.issues.extend((chunk.article, chunk.fraction, issue) for issue in extraction.issues)

        existing = {row.ordinal: row for row in db.scalars(select(LegalSanction).where(LegalSanction.chunk_id == chunk.id))}
        for candidate in candidates:
            version = "manual" if candidate.ordinal >= MANUAL_ORDINAL_BASE else EXTRACTOR_VERSION
            old = existing.pop(candidate.ordinal, None)
            if old is not None and old.chunk_hash == digest and _equivalent(old, candidate):
                for name in SUPPLEMENTARY_FIELDS:
                    setattr(old, name, getattr(candidate, name))
                if candidate.conduct_text != old.conduct_text:
                    old.conduct_text = candidate.conduct_text  # the repaired, complete wording
                report.unchanged += 1
                continue
            values = {name: getattr(candidate, name) for name in (*CONTENT_FIELDS, *SUPPLEMENTARY_FIELDS)}
            if old is None:
                db.add(LegalSanction(
                    chunk_id=chunk.id, ordinal=candidate.ordinal, source_slug=slug, article=chunk.article,
                    chunk_hash=digest, extractor_version=version, status=SanctionStatus.PENDING, **values,
                ))
                report.created += 1
            else:
                for name, value in values.items():
                    setattr(old, name, value)
                old.chunk_hash, old.extractor_version = digest, version
                old.status, old.reviewed_by, old.reviewed_at = SanctionStatus.PENDING, None, None
                report.replaced += 1
        for orphan in existing.values():  # the text no longer yields this row
            db.delete(orphan)
            report.removed += 1
    db.flush()
    return report


def mark_stale(db: Session) -> int:
    """Verified rows whose chunk text changed, or whose source is no longer current, stop being served."""
    count = 0
    rows = db.execute(
        select(LegalSanction, LegalChunk, OfficialSource)
        .join(LegalChunk, LegalChunk.id == LegalSanction.chunk_id)
        .join(OfficialSource, OfficialSource.id == LegalChunk.source_id)
        .where(LegalSanction.status == SanctionStatus.VERIFIED)
    ).all()
    for row, chunk, source in rows:
        if not source.is_current or row.chunk_hash != chunk_hash(chunk.text):
            row.status = SanctionStatus.STALE
            count += 1
    db.flush()
    return count


def _uma(row: LegalSanction) -> str:
    values = [v for v in (row.uma_min, row.uma_mid, row.uma_max) if v is not None]
    if not values:
        return "sin monto en UMA"
    text = " / ".join(format(v.normalize(), "f") for v in values)
    return f"**{text} UMA**" if len(values) > 1 else f"**{text} UMA** (monto único)"


def _tanda(rows: list[LegalSanction], issues: list[Issue]) -> int:
    if issues:
        return 3
    if any(r.applies_to for r in rows):
        return 2
    if any(r.inciso for r in rows):
        return 1
    return 4


def _highlight(text: str, clauses: set[str]) -> str:
    flat = " ".join(text.split())
    if not clauses:
        return flat
    pattern = re.compile("|".join(re.escape(c) for c in sorted(clauses, key=len, reverse=True)))
    return pattern.sub(lambda m: f"⟦{m.group(0)}⟧", flat)  # one pass: a clause repeated in the text is never nested


def render_review(
    db: Session, slug: str, sample_every: int = 6, only_pending: bool = False, previous: list[dict] | None = None
) -> tuple[str, dict[int, int]]:
    """Markdown review sheet for the pending rows of `slug`, ordered by risk. Approve a row by changing `[ ]` to
    `[x]`; reject with `[!]`; approve a whole tanda with its master checkbox."""
    before = {(e["article"], e["chunk_fraction"], e["ordinal"]): e for e in (previous or [])}
    by_tanda: dict[int, list[str]] = {1: [], 2: [], 3: [], 4: []}
    counts = {1: 0, 2: 0, 3: 0, 4: 0}
    sampled = 0
    for chunk in _chunks(db, slug):
        rows = list(db.scalars(
            select(LegalSanction).where(LegalSanction.chunk_id == chunk.id).order_by(LegalSanction.ordinal)
        ))
        if only_pending:
            rows = [r for r in rows if r.status is SanctionStatus.PENDING]
            if not rows:
                continue
        issues = extract_sanctions(chunk.article, chunk.fraction, chunk.text).issues
        if any(r.extractor_version == "manual" for r in rows):
            issues = [i for i in issues if i.kind != "tabla"]
        if not rows and not issues:
            continue
        tanda = _tanda(rows, issues)
        counts[tanda] += len(rows)
        where = f"Art. {chunk.article}" + (f" · fracción {chunk.fraction}" if chunk.fraction else "")
        star = ""
        if tanda == 4:
            sampled += 1
            star = " ★" if sampled % sample_every == 1 else ""
        lines = [f"#### {where}{star}", ""]
        if tanda != 4:  # the full article only where the mapping of clauses to incisos has to be checked
            lines += ["> " + _highlight(chunk.text, {r.clause_text for r in rows}), ""]
        for row in rows:
            label = []
            if row.fraction and row.fraction != chunk.fraction:
                label.append(f"fracción {row.fraction}")
            if row.inciso:
                label.append(f"inciso {row.inciso})")
            who = " · ".join(label) or "toda la disposición"
            points = ", ".join(
                x for x in (
                    f"{row.points_license} pt licencia" if row.points_license is not None else "",
                    f"{row.points_plate} pt matrícula" if row.points_plate is not None else "",
                ) if x
            )
            qualifier = f" — **solo si:** {row.applies_to}" if row.applies_to else ""
            manual = " _(capturada a mano)_" if row.extractor_version == "manual" else ""
            lines.append(
                f"- [ ] `{row_id(slug, row.article, chunk.fraction, row.ordinal, row.chunk_hash)}` **{who}**{qualifier}{manual}"
            )
            old = before.get((row.article, chunk.fraction, row.ordinal))
            if only_pending and old is not None and old["chunk_hash"] == row.chunk_hash:
                old_amount = "/".join(str(Decimal(old[k]).normalize()) for k in ("uma_min", "uma_mid", "uma_max") if old[k]) or "sin monto"
                lines.append(f"  - **antes (lo que revisaste):** «{old['conduct_text'][:140]}» → {old_amount} UMA")
            if row.lead_text:
                lines.append(f"  - encabezado: «{row.lead_text[:160]}»")
            conduct = row.conduct_text if len(row.conduct_text) <= 200 else row.conduct_text[:200] + "…"
            lines.append(f"  - conducta: «{conduct}»")
            if tanda == 4:
                clause = row.clause_text if len(row.clause_text) <= 260 else row.clause_text[:260] + "…"
                lines.append(f"  - cláusula: «{clause}»")
            mode = {"alternativos_por_via": " (licencia O matrícula, según la vía)", "acumulativos": " (ambos se suman)"}.get(row.points_mode or "", "")
            lines.append(f"  - sanción: {_uma(row)}" + (f"; {points}{mode}" if points else "")
                         + (f"; otras: {row.other_consequences}" if row.other_consequences else ""))
        for issue in issues:
            lines.append(f"- ⚠️ **{issue.kind}:** {issue.detail}" + (f" — «{issue.clause_text[:200]}»" if issue.clause_text else ""))
        lines.append("")
        by_tanda[tanda].append("\n".join(lines))

    out = [
        f"# Revisión de sanciones — `{slug}`" + (" (solo lo que cambió)" if only_pending else ""), "",
        "Marca `[x]` en cada fila que coincida con el artículo, `[!]` en la que esté mal (y anota por qué debajo).",
        "Una fila que no marques **no se sirve** al agente. Lo resaltado `⟦…⟧` es la cláusula de la que salió el monto.", "",
    ]
    for tanda in (1, 2, 3, 4):
        if not by_tanda[tanda]:
            continue
        out += [f"## {TANDA_TITLES[tanda]}", f"_{counts[tanda]} filas en {len(by_tanda[tanda])} fragmentos._", ""]
        if tanda == 4:
            out += [f"- [ ] **APROBAR TODA LA TANDA 4** (revisé las marcadas con ★ y el resto sigue el mismo patrón)", ""]
        out += by_tanda[tanda]
    return "\n".join(out), counts


def parse_review(markdown: str) -> tuple[dict[str, str], set[int]]:
    """({row id: 'approve' | 'reject'}, tandas approved as a whole)."""
    decisions = {}
    for match in _DECISION.finditer(markdown):
        mark = match.group("mark")
        if mark in "xX":
            decisions[match.group("id")] = "approve"
        elif mark == "!":
            decisions[match.group("id")] = "reject"
    tandas = {int(m.group("tanda")) for m in _SECTION.finditer(markdown) if m.group("mark") in "xX"}
    return decisions, tandas


def _entry(row: LegalSanction, chunk: LegalChunk) -> dict:
    def dec(value):
        return None if value is None else str(value)
    return {
        "id": row_id(row.source_slug, row.article, chunk.fraction, row.ordinal, row.chunk_hash),
        "source_slug": row.source_slug, "article": row.article, "chunk_fraction": chunk.fraction,
        "ordinal": row.ordinal, "chunk_hash": row.chunk_hash, "fraction": row.fraction, "inciso": row.inciso,
        "applies_to": row.applies_to, "conduct_text": row.conduct_text, "clause_text": row.clause_text,
        "uma_min": dec(row.uma_min), "uma_mid": dec(row.uma_mid), "uma_max": dec(row.uma_max),
        "points_license": row.points_license, "points_plate": row.points_plate,
        "other_consequences": row.other_consequences, "extractor_version": row.extractor_version,
        "lead_text": row.lead_text, "points_mode": row.points_mode,
        "reviewed_by": row.reviewed_by, "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
    }


@dataclass
class ApplyReport:
    approved: int = 0
    rejected: int = 0
    unmarked: int = 0
    unknown_ids: list[str] = field(default_factory=list)
    exported: int = 0


def apply_review(db: Session, slug: str, markdown: str, reviewer: str, now: datetime | None = None) -> ApplyReport:
    """Mark approved rows `verified` (rejected ones `rejected`). Returns what happened; export separately."""
    now = now or datetime.now(timezone.utc)
    decisions, tandas = parse_review(markdown)
    report = ApplyReport()
    known: set[str] = set()
    for chunk in _chunks(db, slug):
        rows = list(db.scalars(select(LegalSanction).where(LegalSanction.chunk_id == chunk.id)))
        issues = extract_sanctions(chunk.article, chunk.fraction, chunk.text).issues
        if any(r.extractor_version == "manual" for r in rows):
            issues = [i for i in issues if i.kind != "tabla"]
        tanda = _tanda(rows, issues) if rows else None
        for row in rows:
            rid = row_id(slug, row.article, chunk.fraction, row.ordinal, row.chunk_hash)
            known.add(rid)
            decision = decisions.get(rid) or ("approve" if tanda in tandas and decisions.get(rid) != "reject" else None)
            if row.chunk_hash != chunk_hash(chunk.text):
                continue  # never verify a row against a text it was not extracted from
            if decision == "approve":
                row.status, row.reviewed_by, row.reviewed_at = SanctionStatus.VERIFIED, reviewer, now
                report.approved += 1
            elif decision == "reject":
                row.status, row.reviewed_by, row.reviewed_at = SanctionStatus.REJECTED, reviewer, now
                report.rejected += 1
            else:
                report.unmarked += 1
    report.unknown_ids = sorted(set(decisions) - known)
    db.flush()
    return report


def export_verified(db: Session, slug: str, path: Path) -> int:
    """Write the verified rows of `slug` to the git-tracked file (replacing that slug's entries, keeping others)."""
    rows = db.execute(
        select(LegalSanction, LegalChunk).join(LegalChunk, LegalChunk.id == LegalSanction.chunk_id)
        .where(LegalSanction.source_slug == slug, LegalSanction.status == SanctionStatus.VERIFIED)
        .order_by(LegalSanction.article, LegalChunk.id, LegalSanction.ordinal)
    ).all()
    entries = [_entry(row, chunk) for row, chunk in rows]
    others = []
    if path.exists():
        others = [e for e in json.loads(path.read_text(encoding="utf-8")) if e["source_slug"] != slug]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(others + entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return len(entries)


@dataclass
class LoadReport:
    loaded: int = 0
    unmatched: list[str] = field(default_factory=list)  # the chunk text changed or the chunk is gone: needs review
    diverged: list[str] = field(default_factory=list)  # the extractor now proposes other content: stays pending


class _Entry:
    """A verified entry from the git file, shaped like a row for `_equivalent`."""

    def __init__(self, entry: dict):
        def dec(key):
            return Decimal(entry[key]) if entry.get(key) else None
        self.fraction, self.inciso, self.applies_to = entry["fraction"], entry["inciso"], entry["applies_to"]
        self.conduct_text, self.clause_text = entry["conduct_text"], entry["clause_text"]
        self.uma_min, self.uma_mid, self.uma_max = dec("uma_min"), dec("uma_mid"), dec("uma_max")
        self.points_license, self.points_plate = entry["points_license"], entry["points_plate"]
        self.other_consequences = entry["other_consequences"]


def load_verified(db: Session, slug: str, path: Path) -> LoadReport:
    """Restore `verified` on the rows a person approved, from the git file, after a rebuild or a re-ingest.

    A row is restored only when the extractor still proposes what was verified (same chunk text hash and equivalent
    content). If the extractor now proposes something else, the row stays pending and is reported as diverged: the
    approval was for the old content, not for the new."""
    report = LoadReport()
    if not path.exists():
        return report
    entries = [e for e in json.loads(path.read_text(encoding="utf-8")) if e["source_slug"] == slug]
    index = {(c.article, c.fraction, chunk_hash(c.text)): c for c in _chunks(db, slug)}
    for entry in entries:
        chunk = index.get((entry["article"], entry["chunk_fraction"], entry["chunk_hash"]))
        row = None
        if chunk is not None:
            row = db.scalars(select(LegalSanction).where(
                LegalSanction.chunk_id == chunk.id, LegalSanction.ordinal == entry["ordinal"])).first()
        if row is None:
            report.unmatched.append(entry["id"])
            continue
        if not _equivalent(_Entry(entry), row):
            report.diverged.append(entry["id"])
            continue
        reviewed_at = datetime.fromisoformat(entry["reviewed_at"]) if entry["reviewed_at"] else None
        row.status, row.reviewed_by, row.reviewed_at = SanctionStatus.VERIFIED, entry["reviewed_by"], reviewed_at
        report.loaded += 1
    db.flush()
    return report


@dataclass
class RefreshReport:
    sync: SyncReport
    loaded: LoadReport
    stale: int
    health: dict


def health(db: Session, slug: str) -> dict:
    """How much of what the extractor found is actually servable. A drop after a re-ingest means rows are waiting
    for review and the agent is reading prose for those articles (safe, but less precise)."""
    counts = {status.value: 0 for status in SanctionStatus}
    for (status,) in db.execute(select(LegalSanction.status).where(LegalSanction.source_slug == slug)):
        counts[status.value] += 1
    total = sum(counts.values())
    return {**counts, "total": total, "verified_pct": round(100 * counts["verified"] / total, 1) if total else None}


def refresh_sanctions(db: Session, slug: str, manual: list[dict], verified_path: Path) -> RefreshReport:
    """Everything that must happen after a (re-)ingest of `slug`, idempotently: candidates for new or changed text,
    verified rows restored from git where the text did not change, and rows of changed text marked stale."""
    sync = sync_pending(db, slug, manual)
    loaded = load_verified(db, slug, verified_path)
    stale = mark_stale(db)
    return RefreshReport(sync=sync, loaded=loaded, stale=stale, health=health(db, slug))
