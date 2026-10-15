"""Aggregate *.judged.jsonl files into one table per model and category (no API calls).

Usage: uv run python -m scripts.eval_report [--runs ../data/eval/runs] [--out ../docs/evaluation/report.md]
"""
import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path


def pct(values: list[bool]) -> str:
    return f"{100 * sum(values) / len(values):.0f}% ({sum(values)}/{len(values)})" if values else "-"


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))] if ordered else 0.0


def model_of(path: Path) -> str:
    return path.name.split("-", 2)[-1].removesuffix(".judged.jsonl")  # <date>-<time>-<model>.judged.jsonl


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cli.add_argument("--runs", default=str(Path(__file__).resolve().parents[2] / "data" / "eval" / "runs"))
    cli.add_argument("--out")
    args = cli.parse_args()

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for path in sorted(Path(args.runs).glob("*.judged.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                groups[(model_of(path), record.get("category") or "otros")].append(record)

    lines = ["| modelo | categoría | n | comportamiento | fiel | promete de más | cita esperada | tool correcta | s (media / p95) | USD/turno |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for (model, category), rows in sorted(groups.items()):
        judge = [r["judge"] for r in rows if "judge" in r and "error" not in r["judge"]]
        faithful = [j["faithful"] for j in judge if j.get("faithful") is not None]
        cite = [r["checks"]["citation_hit"] for r in rows if "citation_hit" in r.get("checks", {})]
        tools = [r["checks"]["tool_ok"] for r in rows if "tool_ok" in r.get("checks", {})]
        secs = [r["seconds"] for r in rows if r.get("seconds") is not None]
        cost = [r["cost_usd"] for r in rows if r.get("cost_usd") is not None]
        lines.append(
            f"| {model} | {category} | {len(rows)} | {pct([j['behavior_ok'] for j in judge])} | {pct(faithful)} | {sum(1 for j in judge if j.get('overpromises'))}/{len(judge)} | {pct(cite)} "
            f"| {pct(tools)} | {statistics.mean(secs):.1f} / {p95(secs):.1f} | {statistics.mean(cost) if cost else 0:.4f} |"
        )
    report = "\n".join(lines)
    print(report)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
