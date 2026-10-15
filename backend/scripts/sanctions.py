"""Structured sanctions: extract candidates, produce the review sheet, apply the reviewed decisions.

Usage (from backend/):
  uv run python -m scripts.sanctions extract            # candidates -> legal_sanctions (pending); also loads verified.json
  uv run python -m scripts.sanctions review             # writes data/sanctions/review/<slug>.md
  uv run python -m scripts.sanctions apply --reviewer "Nombre"   # reads the sheet, verifies/rejects, exports verified.json
  uv run python -m scripts.sanctions status             # counts by status
"""
import argparse
import json
import re
from pathlib import Path

from app.db.session import SessionLocal
from app.services.ingestion import sanction_store as store

ROOT = Path(__file__).resolve().parents[2] / "data" / "sanctions"
VERIFIED = ROOT / "verified.json"
MANUAL = ROOT / "manual.json"
DEFAULT_SLUG = "reglamento-transito"


def _sheet(slug: str) -> Path:
    return ROOT / "review" / f"{slug}.md"


def manual_rows(slug: str) -> list[dict]:
    if not MANUAL.exists():
        return []
    return [m for m in json.loads(MANUAL.read_text(encoding="utf-8")) if m["source_slug"] == slug]


def refresh(db, slug: str):
    """What `scripts.ingest_sources` also runs after indexing a source: see sanction_store.refresh_sanctions."""
    return store.refresh_sanctions(db, slug, manual_rows(slug), VERIFIED)


def print_refresh(result) -> None:
    report, loaded = result.sync, result.loaded
    print(f"{report.chunks} fragmentos · filas nuevas {report.created} · sin cambio {report.unchanged} · "
          f"reemplazadas {report.replaced} · retiradas {report.removed}")
    print(f"verificadas cargadas desde git: {loaded.loaded} · sin fragmento coincidente: {len(loaded.unmatched)} · "
          f"marcadas stale: {result.stale}")
    health = result.health
    print(f"salud: {health['verified']}/{health['total']} filas verificadas ({health['verified_pct']}%) · "
          f"pendientes {health['pending']} · stale {health['stale']} · rechazadas {health['rejected']}")
    for article, fraction, issue in report.issues:
        where = f"Art. {article}" + (f" fr. {fraction}" if fraction else "")
        print(f"  ⚠ {where}: {issue.kind}")


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cli.add_argument("command", choices=["extract", "review", "apply", "status"])
    cli.add_argument("--slug", default=DEFAULT_SLUG)
    cli.add_argument("--reviewer", help="name recorded on the rows you approve (apply)")
    cli.add_argument("--delta", action="store_true", help="review: only rows pending review, with what you approved before")
    cli.add_argument("--sheet", help="apply: the review sheet to read (default: the main one)")
    cli.add_argument("--force", action="store_true", help="review: overwrite a sheet that already has marks")
    args = cli.parse_args()

    with SessionLocal() as db:
        if args.command == "extract":
            result = refresh(db, args.slug)
            db.commit()
            print_refresh(result)
        elif args.command == "review":
            previous = json.loads(VERIFIED.read_text(encoding="utf-8")) if VERIFIED.exists() else []
            text, counts = store.render_review(db, args.slug, only_pending=args.delta, previous=previous)
            path = _sheet(args.slug).with_suffix(".cambios.md") if args.delta else _sheet(args.slug)
            if path.exists() and re.search(r"^- \[[xX!]\]", path.read_text(encoding="utf-8"), re.M) and not args.force:
                raise SystemExit(f"{path} ya tiene marcas tuyas: no se sobrescribe (usa --force si de verdad quieres perderlas)")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text + "\n", encoding="utf-8")
            print(f"{path}  (filas por tanda: {counts})")
        elif args.command == "apply":
            if not args.reviewer:
                raise SystemExit("--reviewer is required: it is recorded as the person who verified the rows")
            path = Path(args.sheet) if args.sheet else _sheet(args.slug)
            report = store.apply_review(db, args.slug, path.read_text(encoding="utf-8"), args.reviewer)
            exported = store.export_verified(db, args.slug, VERIFIED)
            db.commit()
            print(f"aprobadas {report.approved} · rechazadas {report.rejected} · sin marcar {report.unmarked} · "
                  f"exportadas a verified.json: {exported}")
            if report.unknown_ids:
                print(f"  ids que no existen (¿la hoja es de otra extracción?): {report.unknown_ids}")
        else:
            print(store.health(db, args.slug))


if __name__ == "__main__":
    main()
