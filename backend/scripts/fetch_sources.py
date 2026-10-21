"""Download official sources listed in data/sources.json and register their current versions.

TLS and redirect rules live in app.services.source_http.
"""
import argparse
import ssl
import sys
from pathlib import Path

from app.db.session import SessionLocal
from app.services.source_http import MAX_PDF_BYTES, http_get, ssl_context
from app.services.sources import SourceSpec, load_manifest, local_path, register_source, sha256_of

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "data" / "sources.json"
SOURCES_DIR = REPO_ROOT / "data" / "legal-sources"


def download(spec: SourceSpec, dest: Path, context: ssl.SSLContext) -> None:
    try:
        data = http_get(spec.url, max_bytes=MAX_PDF_BYTES, timeout=300, context=context)
    except ValueError as exc:
        raise ValueError(f"{spec.slug}: {exc}") from exc
    if not data.startswith(b"%PDF"):
        raise ValueError(f"{spec.slug}: la respuesta no es un PDF")
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(data)
    tmp.replace(dest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="slug a procesar")
    parser.add_argument("--refresh", action="store_true", help="vuelve a descargar aunque exista el archivo")
    args = parser.parse_args()

    specs = [s for s in load_manifest(MANIFEST) if args.only in (None, s.slug)]
    if not specs:
        raise SystemExit(f"No hay fuentes con slug {args.only!r}")
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    context = ssl_context()
    missing: list[tuple[SourceSpec, Path]] = []
    with SessionLocal() as db:
        for spec in specs:
            path = local_path(spec, SOURCES_DIR)
            if not spec.manual and (args.refresh or not path.exists()):
                print(f"↓ {spec.slug}", flush=True)
                download(spec, path, context)
            if not path.exists():
                missing.append((spec, path))
                continue
            source, changed = register_source(db, spec, sha256_of(path))
            print(f"{'✓ nueva versión' if changed else '= sin cambios'} {spec.slug} ({source.sha256[:12]})")
        db.commit()
    for spec, path in missing:
        print(f"✗ Falta {spec.slug}: descárgalo desde {spec.url} y guárdalo como {path}", file=sys.stderr)
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
