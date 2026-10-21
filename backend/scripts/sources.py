"""Watch the official sources for changes (read-only: it never edits the database or the indexed documents).

Usage (from backend/):
    uv run python -m scripts.sources init              # first time: record what the index says today
    uv run python -m scripts.sources check             # exit 0 = no changes, 2 = changes found, 1 = the check itself failed
    uv run python -m scripts.sources accept <slug>     # after handling a change, make today's state the baseline

`check --report-file report.md --findings-file findings.json` also writes the files the scheduled job uses.
The baseline lives in data/watch-state.json and is committed, so the check needs no database.
"""
import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

from app.services.source_http import MAX_PDF_BYTES, http_get
from app.services.source_watch import (IndexEntry, IndexStructureError, accept, compare, fetch_index, is_indexed,
                                       load_state, render_report, save_state, snapshot)
from app.services.sources import load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "data" / "sources.json"
STATE = REPO_ROOT / "data" / "watch-state.json"


def read_world(specs) -> tuple[list[IndexEntry], dict[str, str], dict[str, str]]:
    """The index (if any source needs it) and the hash of every source outside it."""
    entries = fetch_index(lambda url: http_get(url).decode("utf-8", errors="replace")) if any(is_indexed(s) for s in specs) else []
    hashes, errors = {}, {}
    for spec in specs:
        if is_indexed(spec):
            continue
        try:
            hashes[spec.slug] = hashlib.sha256(http_get(spec.url, max_bytes=MAX_PDF_BYTES, timeout=120)).hexdigest()
        except Exception as exc:  # network, TLS, size: reported as a finding, not as «no changes»
            errors[spec.slug] = str(exc)
    return entries, hashes, errors


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cli.add_argument("command", choices=["init", "check", "accept"])
    cli.add_argument("slug", nargs="?")
    cli.add_argument("--force", action="store_true", help="init: overwrite an existing state file")
    cli.add_argument("--report-file")
    cli.add_argument("--findings-file")
    args = cli.parse_args()

    specs = load_manifest(MANIFEST)
    try:
        entries, hashes, errors = read_world(specs)
    except IndexStructureError as exc:
        print(f"ERROR: la estructura del índice cambió y no se puede vigilar con seguridad: {exc}", file=sys.stderr)
        return 1

    if args.command == "init":
        if STATE.exists() and not args.force:
            print(f"{STATE} ya existe; usa --force para reemplazarlo", file=sys.stderr)
            return 1
        if errors:
            print("ERROR: no se pudieron descargar: " + "; ".join(f"{k}: {v}" for k, v in errors.items()), file=sys.stderr)
            return 1
        state, problems = snapshot(specs, entries, hashes)
        save_state(STATE, state)
        print(f"Estado guardado para {len(state)} fuentes en {STATE}")
        for problem in problems:
            print(f"AVISO: {problem}")
        return 1 if len(state) != len(specs) else 0

    state = load_state(STATE)
    if args.command == "accept":
        if args.slug not in state:
            print(f"{args.slug!r} no está en el estado", file=sys.stderr)
            return 1
        accept(state, args.slug, entries, hashes)
        save_state(STATE, state)
        print(f"{args.slug}: línea base actualizada")
        return 0

    findings = compare(state, specs, entries, hashes, errors)
    report = render_report(findings)
    print(report)
    if args.report_file:
        Path(args.report_file).write_text(report + "\n", encoding="utf-8")
    if args.findings_file:
        Path(args.findings_file).write_text(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 2 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
