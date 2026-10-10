"""Ask the legal assistant one question from the terminal and see how it got to the answer (spends OpenAI tokens).

Usage: uv run python -m scripts.ask "¿cuánto es la multa por exceso de velocidad?"
"""
import argparse
import json
import time

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.agent.agent import build_agent, run_agent
from app.services.agent.context import AgentContext
from app.services.ingestion.embedder import build_embeddings


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cli.add_argument("question")
    args = cli.parse_args()

    settings = get_settings()
    agent = build_agent(settings)
    with SessionLocal() as db:
        ctx = AgentContext(db=db, user_id=None, embeddings=build_embeddings(settings), user_message=args.question, settings=settings)
        started = time.perf_counter()
        run = run_agent(agent, ctx, args.question, history=[], settings=settings)
        db.rollback()  # a terminal question must not leave an agent lookup behind
        elapsed = time.perf_counter() - started

    print(f"\n❓ {args.question}\n")
    for i, call in enumerate(run.tool_calls, 1):
        print(f"  🔧 {i}. {call['name']}({json.dumps(call['args'], ensure_ascii=False)}) → {call['estado']}")
    print(f"\n💬 {run.answer}\n")
    if run.citations:
        print("📎 fragmentos consultados:")
        for c in run.citations:
            where = f"{c.article}" + (f", fr. {c.fraction}" if c.fraction else "")
            print(f"   [{c.n}] {c.source_title[:48]} · art. {where} · pág. {c.page}")
    # gpt-5-mini list prices per 1M tokens (assumed; check the OpenAI pricing page): input 0.25, cached input 0.025, output 2.00
    fresh = run.input_tokens - run.cached_input_tokens
    cost = (fresh * 0.25 + run.cached_input_tokens * 0.025 + run.output_tokens * 2.0) / 1e6
    print(f"\n⏱  {elapsed:.1f} s · entrada {run.input_tokens} ({run.cached_input_tokens} en caché) + salida {run.output_tokens} (~USD {cost:.4f})"
          + ("  ⚠ tope de pasos" if run.limit_reached else ""))


if __name__ == "__main__":
    main()
