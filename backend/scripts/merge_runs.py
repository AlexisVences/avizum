"""Replace the errored records of a run with the records of a re-run (no API calls).

Usage: uv run python -m scripts.merge_runs <base.jsonl> <rerun.jsonl>
Writes <base>.merged.jsonl: base records that succeeded + every successful record of the re-run. Case ids that still
have no successful record are listed so nothing is silently missing.
"""
import json
import sys
from pathlib import Path


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    base_path, rerun_path = Path(sys.argv[1]), Path(sys.argv[2])
    base, rerun = load(base_path), load(rerun_path)
    redone = {r["id"] for r in rerun if not r.get("error")}
    kept = [r for r in base if not r.get("error") and r["id"] not in redone]  # a re-run replaces the whole case
    merged = sorted(kept + [r for r in rerun if not r.get("error")], key=lambda r: (r["id"], r.get("attempt", 1)))
    out = base_path.with_suffix(".merged.jsonl")
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in merged), encoding="utf-8")
    missing = {r["id"] for r in base} - {r["id"] for r in merged}
    print(f"{len(merged)} records -> {out.name}; cases with no successful record: {sorted(missing) or 'none'}")


if __name__ == "__main__":
    main()
