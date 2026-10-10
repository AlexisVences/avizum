"""Measure retrieval quality on data/eval/retrieval.jsonl (spends a few embedding calls; not part of pytest).

Usage: uv run python -m scripts.eval_retrieval [--k 5] [--verbose] [--rewrite]
"""
import argparse
import hashlib
import json
from pathlib import Path

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.evaluation import first_relevant_rank, mean_reciprocal_rank, recall_at
from app.services.ingestion.embedder import build_embeddings
from app.services.query_rewrite import build_chat_model, rewrite_query
from app.services.rerank import RERANK_PROMPT, apply_ranking, ask_ranking
from app.services.retrieval import search_many

CASES = Path(__file__).resolve().parents[2] / "data" / "eval" / "retrieval.jsonl"
RERANKS = CASES.with_name("reranks.json")
REWRITES = CASES.with_name("rewrites.json")  # cache: the LLM rewrite is not deterministic, so runs must reuse it to be comparable
SEARCH_DEPTH = 10  # MRR is measured over the top 10


def cached_rewrite(llm, model: str, question: str, cache: dict[str, str]) -> str:
    from app.services.query_rewrite import REWRITE_PROMPT

    key = hashlib.sha256(f"{model}\n{REWRITE_PROMPT}\n{question}".encode()).hexdigest()[:16]
    if key not in cache:
        cache[key] = rewrite_query(llm, question)
    return cache[key]


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cli.add_argument("--k", type=int, default=5)
    cli.add_argument("--cases", default=str(CASES), help="JSONL file with the evaluation questions")
    cli.add_argument("--verbose", action="store_true", help="show the top hits of every case")
    cli.add_argument("--depth", type=int, default=SEARCH_DEPTH, help="how many results to retrieve per question")
    cli.add_argument("--rerank", action="store_true", help="retrieve --candidates and let an LLM reorder them")
    cli.add_argument("--candidates", type=int, default=20, help="candidates handed to the reranker")
    cli.add_argument("--rewrite", action="store_true", help="search with the question and an LLM rewrite in legal vocabulary, fused with RRF")
    args = cli.parse_args()

    cases = [json.loads(line) for line in Path(args.cases).read_text(encoding="utf-8").splitlines() if line.strip()]
    embeddings = build_embeddings(get_settings())
    llm = build_chat_model(get_settings()) if (args.rewrite or args.rerank) else None
    rewrite_on = args.rewrite
    rerank_cache = json.loads(RERANKS.read_text(encoding="utf-8")) if RERANKS.exists() else {}
    cache = json.loads(REWRITES.read_text(encoding="utf-8")) if REWRITES.exists() else {}
    ranks: list[int | None] = []
    rows = []
    with SessionLocal() as db:
        for case in cases:
            queries = [case["question"]]
            if rewrite_on:
                case["rewrite"] = cached_rewrite(llm, get_settings().openai_chat_model, case["question"], cache)
                queries.append(case["rewrite"])
            hits = search_many(db, queries, embeddings, k=max(args.depth, args.candidates) if args.rerank else args.depth)
            if args.rerank:
                key = hashlib.sha256(f"{get_settings().openai_chat_model}\n{RERANK_PROMPT}\n{case['question']}\n{[h.chunk_id for h in hits[:args.candidates]]}".encode()).hexdigest()[:16]
                if key not in rerank_cache:
                    rerank_cache[key] = ask_ranking(llm, case["question"], hits[: args.candidates])
                hits = apply_ranking(hits[: args.candidates], rerank_cache[key])
            expected = {(e["source"], e["article"]) for e in case["expected"]}
            rank = first_relevant_rank(expected, hits) if expected else None
            if expected:
                ranks.append(rank)
            top = hits[0] if hits else None
            best_ok = next((h for h in hits if (h.source_slug, h.article) in expected), None)
            rows.append((case, rank, top, best_ok, hits))

    print(f"{'id':4} {'cobertura':9} {'rank':>4}  {'sim top1':>8}  {'sim acierto':>11}  top1")
    for case, rank, top, best_ok, hits in rows:
        top1 = f"{top.source_slug[:10]} {top.article}{' fr ' + top.fraction if top.fraction else ''}" if top else "-"
        print(f"{case['id']:4} {case['coverage']:9} {str(rank or '-'):>4}  {top.similarity if top else 0:8.3f}  "
              f"{best_ok.similarity if best_ok else float('nan'):11.3f}  {top1}")
        if rewrite_on and (rank is None or args.verbose) and case.get("expected"):
            print(f"       reescritura: {case['rewrite'][:150]}")
        if args.verbose:
            for h in hits[:5]:
                print(f"       {h.source_slug[:18]:18} art {h.article:7} fr {str(h.fraction):7} sim {h.similarity:.3f}")

    print(f"\nPreguntas con respuesta esperada: {len(ranks)}")
    depths = sorted({args.k, 10, 20, 30} & set(range(1, args.depth + 1)))
    print("   ".join(f"recall@{d} = {recall_at(ranks, d):.2f}" for d in depths) + f"   MRR = {mean_reciprocal_rank(ranks):.3f}")
    verified = [r for (c, r, *_) in rows if c["expected"] and c.get("verified")]
    if verified:
        print(f"solo etiquetas verificadas leyendo el artículo ({len(verified)}): recall@{args.k} = {recall_at(verified, args.k):.2f}   recall@10 = {recall_at(verified, 10):.2f}")
    print("sin aparecer entre los", args.depth, "primeros:", [c["id"] for (c, r, *_), in [((c, r),) for c, r, *_ in rows if c["expected"] and r is None]])
    none_sims = [top.similarity for case, _, top, _, _ in rows if not case["expected"] and top]
    ok_sims = [best.similarity for _, _, _, best, _ in rows if best]
    if none_sims and ok_sims:
        print(f"similitud del mejor resultado en preguntas SIN respuesta en el corpus: {min(none_sims):.3f} a {max(none_sims):.3f}")
        print(f"similitud del primer acierto en preguntas CON respuesta:              {min(ok_sims):.3f} a {max(ok_sims):.3f}")

    if rewrite_on:
        REWRITES.write_text(json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    if args.rerank:
        RERANKS.write_text(json.dumps(rerank_cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
