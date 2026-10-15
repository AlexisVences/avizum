"""Run the real agent over data/eval/agent_cases.jsonl and save one record per case (spends OpenAI tokens; not part of pytest).

It only COLLECTS what happened (answer, tools, citations, tokens, latency). Judging comes later: read the run file or
feed it to the judge. Every run writes its own file in data/eval/runs/. Cases with `dup_of` are skipped (another case
or the retrieval/held-out sets already cover them); the other eval files also work: --cases ../data/eval/heldout_fotocivicas.jsonl.

Usage: uv run python -m scripts.eval_agent [--category premisa_falsa] [--only c01,c45] [--limit 5] [--repeat 2]
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.agent.agent import build_agent, run_agent
from app.services.agent.context import AgentContext
from app.services.ingestion.embedder import build_embeddings
from app.services.sanction_eval import resolve_ref

CASES = Path(__file__).resolve().parents[2] / "data" / "eval" / "agent_cases.jsonl"
RUNS = CASES.parent / "runs"
# gpt-5-mini list prices per 1M tokens (assumed; same as scripts.ask): input 0.25, cached input 0.025, output 2.00
PRICE_IN, PRICE_CACHED, PRICE_OUT = 0.25, 0.025, 2.00


def load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


VERIFIED = CASES.parents[1] / "sanctions" / "verified.json"


def resolve_sanction_cases(cases: list[dict], uma) -> tuple[list[dict], list[str]]:
    """Fill the expected amounts of `sanction_ref` cases from the verified rows; skip the ones not verified yet."""
    entries = json.loads(VERIFIED.read_text(encoding="utf-8")) if VERIFIED.exists() else []
    ready, skipped = [], []
    for case in cases:
        ref = (case.get("expect") or {}).get("sanction_ref")
        if not ref:
            ready.append(case)
            continue
        resolved = resolve_ref(entries, ref, uma)
        if resolved is None:
            skipped.append(case["id"])
            continue
        ready.append({**case, "expect": {**case["expect"], "uma_expected": resolved["uma"], "pesos_expected": resolved["pesos"],
                                         "confusers": resolved["confusers"]}})
    return ready, skipped


def cost_usd(run) -> float:
    fresh = run.input_tokens - run.cached_input_tokens
    return (fresh * PRICE_IN + run.cached_input_tokens * PRICE_CACHED + run.output_tokens * PRICE_OUT) / 1e6


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cli.add_argument("--cases", default=str(CASES))
    cli.add_argument("--category", help="only this category")
    cli.add_argument("--only", help="comma-separated case ids")
    cli.add_argument("--include-dups", action="store_true", help="also run cases marked dup_of (already covered elsewhere)")
    cli.add_argument("--limit", type=int, help="first N cases after filtering")
    cli.add_argument("--repeat", type=int, default=1, help="runs per case (the model is not deterministic)")
    args = cli.parse_args()

    cases = load_cases(Path(args.cases))
    if not args.include_dups:
        cases = [c for c in cases if "dup_of" not in c]
    if args.category:
        cases = [c for c in cases if c.get("category") == args.category]
    if args.only:
        wanted = set(args.only.split(","))
        cases = [c for c in cases if c["id"] in wanted]
    if args.limit:
        cases = cases[: args.limit]
    settings = get_settings()
    cases, skipped = resolve_sanction_cases(cases, settings.uma_value)
    if skipped:
        print(f"saltados (su fila de sanción aún no está verificada en data/sanctions/verified.json): {', '.join(skipped)}")
    if not cases:
        raise SystemExit("no cases match the filters")

    agent = build_agent(settings)
    embeddings = build_embeddings(settings)
    RUNS.mkdir(exist_ok=True)
    out = RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-{settings.openai_chat_model}.jsonl"
    total = 0.0

    with out.open("w", encoding="utf-8") as sink:
        for case in cases:
            for attempt in range(1, args.repeat + 1):
                started = time.perf_counter()
                db = SessionLocal()  # one session per run: a failure in one cannot poison the next
                try:
                    ctx = AgentContext(db=db, user_id=None, embeddings=embeddings, user_message=case["question"], settings=settings)
                    run = run_agent(agent, ctx, case["question"], history=[], settings=settings)
                    record = {
                        "answer": run.answer,
                        "tools": [{"name": t["name"], "args": t["args"], "estado": t["estado"]} for t in run.tool_calls],
                        "citations": [
                            {k: c.get(k) for k in ("n", "orden", "source_slug", "article", "fraction", "page")} for c in run.citations
                        ],
                        "anomalies": run.anomalies,
                        "limit_reached": run.limit_reached,
                        "input_tokens": run.input_tokens,
                        "cached_input_tokens": run.cached_input_tokens,
                        "output_tokens": run.output_tokens,
                        "cost_usd": round(cost_usd(run), 5),
                        "error": None,
                    }
                except Exception as exc:  # one failing case must not lose the rest of an expensive run
                    record = {"error": f"{type(exc).__name__}: {exc}"}
                finally:
                    db.rollback()  # a terminal run must not leave agent lookups behind
                    db.close()
                record.update(
                    id=case["id"], category=case.get("category"), question=case["question"], expect=case.get("expect"),
                    attempt=attempt, seconds=round(time.perf_counter() - started, 1),
                )
                total += record.get("cost_usd", 0.0)
                sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                sink.flush()
                tools = ",".join(t["name"] for t in record.get("tools", [])) or "-"
                print(f"{case['id']} #{attempt} {record['seconds']:>5}s ${record.get('cost_usd', 0):.4f} [{tools}]"
                      + (f"  ERROR {record['error']}" if record["error"] else ""))

    print(f"\n{len(cases) * args.repeat} runs · ~USD {total:.3f} · saved to {out.relative_to(CASES.parents[2])}")


if __name__ == "__main__":
    main()
