"""LLM reranking of retrieval candidates.

Hybrid search finds the right article among the top 20 almost always but not always in the top 5. A model that
reads the question next to each candidate can reorder them much better than vector distance or word overlap.
"""
import logging
import re

from langchain_core.language_models import BaseChatModel

from app.services.retrieval import SearchHit

logger = logging.getLogger(__name__)

CANDIDATE_CHARS = 450
MAX_CHOSEN = 8

RERANK_PROMPT = (
    "Eres un revisor jurídico. Recibes la pregunta de una persona sobre tránsito en la Ciudad de México y una lista "
    "numerada de fragmentos de la legislación. Elige los fragmentos que ayudan a contestar la pregunta (la regla "
    "aplicable, la sanción, el procedimiento o el recurso para impugnar) y ordénalos del más al menos útil. Juzga "
    f"solo con base en los candidatos; no uses conocimiento externo. Responde únicamente con hasta {MAX_CHOSEN} "
    "números separados por comas, por ejemplo: 4, 1, 7."
)


def _render(hits: list[SearchHit]) -> str:
    return "\n\n".join(f"[{i}] {hit.heading_path}\n{' '.join(hit.text.split())[:CANDIDATE_CHARS]}" for i, hit in enumerate(hits, start=1))


def _numbers(content: str | list, count: int) -> list[int]:
    text = content if isinstance(content, str) else "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    chosen: list[int] = []
    for raw in re.findall(r"\d+", text):
        number = int(raw)
        if 1 <= number <= count and number not in chosen:
            chosen.append(number)
    return chosen[:MAX_CHOSEN]


def ask_ranking(llm: BaseChatModel, question: str, hits: list[SearchHit]) -> str:
    """The model's raw reply (a list of candidate numbers). Split from `apply_ranking` so evaluations can cache it."""
    reply = llm.invoke([("system", RERANK_PROMPT), ("human", f"Pregunta: {question}\n\nFragmentos:\n{_render(hits)}")])
    content = reply.content
    return content if isinstance(content, str) else "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)


def apply_ranking(hits: list[SearchHit], reply: str) -> list[SearchHit]:
    """Same hits, best first: the model's choices in its order, then the others in their original order."""
    chosen = _numbers(reply, len(hits))
    first = [hits[number - 1] for number in chosen]
    return first + [hit for i, hit in enumerate(hits, start=1) if i not in chosen]


def rerank(llm: BaseChatModel, question: str, hits: list[SearchHit]) -> list[SearchHit]:
    """Reorder with the model; if the call fails, degrade to the hybrid-search order instead of failing the search."""
    if not hits:
        return []
    try:
        return apply_ranking(hits, ask_ranking(llm, question, hits))
    except Exception:  # noqa: BLE001 - reranking is an optimisation, never a reason to lose the answer
        logger.warning("rerank failed; returning the fused order", exc_info=True)
        return hits
