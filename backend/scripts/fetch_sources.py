"""Download official sources listed in data/sources.json and register their current versions.

TLS is always verified against the system/certifi roots. The Consejería server omits its Let's
Encrypt chain (YR2 → ISRG Root YR), so scripts/certs ships those two public certificates as
intermediates; partial-chain trust is disabled, so every connection must still end at ISRG Root X1.
"""
import argparse
import ssl
import sys
import urllib.request
from pathlib import Path

from app.db.session import SessionLocal
from app.services.sources import SourceSpec, load_manifest, local_path, register_source, sha256_of

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "data" / "sources.json"
SOURCES_DIR = REPO_ROOT / "data" / "legal-sources"
EXTRA_CHAIN = Path(__file__).resolve().parent / "certs" / "lets-encrypt-yr2-chain.pem"


def ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.verify_flags &= ~ssl.VERIFY_X509_PARTIAL_CHAIN
    context.load_verify_locations(cafile=str(EXTRA_CHAIN))
    return context


def download(spec: SourceSpec, dest: Path, context: ssl.SSLContext) -> None:
    request = urllib.request.Request(spec.url, headers={"User-Agent": "Avizum source sync"})
    with urllib.request.urlopen(request, context=context, timeout=300) as response:
        data = response.read()
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
