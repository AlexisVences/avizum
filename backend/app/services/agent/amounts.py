"""End-of-turn check: every amount in the answer must come from what the tools returned this turn.

The model is told to copy sanctions from the verified rows (or the article text) and never to do arithmetic. This
catches the failures that remain: a "10, 15 o 20 veces la UMA" that no fragment of the turn says, or a peso figure
that no row or calculation produced. It does not judge whether the sanction fits the person's conduct (that is the
evaluation's job); it only refuses to let an unsupported number pass silently.
"""
import re
from decimal import Decimal

from app.services.agent.context import AgentContext
from app.services.ingestion.sanctions import _trailing_number

_TRIPLE = re.compile(r"(?<![\d,])(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s+o\s+(\d+(?:\.\d+)?)\s*(?:veces|UMA)", re.I)
_UMA = re.compile(r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:veces\s+(?:la\s+)?(?:UMA|Unidad)|UMA\b)", re.I)
_PESOS = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)")


def _dec(text: str) -> Decimal:
    return Decimal(text.replace(",", "")).normalize()


_UMA_PHRASE = re.compile(r"veces\s+(?:la\s+)?Unidad(?:es)?\s+de\s+Medida", re.I)


def _written_multiples(texts: str) -> set[Decimal]:
    """Multiples the law writes in words ("quinientos a seiscientos ochenta veces la Unidad de Medida"): the model
    answers with digits, so they must count as supported."""
    found: set[Decimal] = set()
    for match in _UMA_PHRASE.finditer(texts):
        value, before = _trailing_number(texts[max(0, match.start() - 160): match.start()])
        if value is None:
            continue
        found.add(Decimal(value).normalize())
        if re.search(r"\b(?:a|hasta)$", before):  # the other end of a range
            low, _ = _trailing_number(re.sub(r"\s+(?:a|hasta)$", "", before))
            if low is not None:
                found.add(Decimal(low).normalize())
    return found


def check_amounts(answer: str, ctx: AgentContext) -> list[dict]:
    texts = " ".join(ctx.fragment_texts)
    known_triples = {tuple(_dec(x) for x in m.groups()) for m in _TRIPLE.finditer(texts)} | set(ctx.served_uma_triples)
    known_uma = {v for t in known_triples for v in t} | set(ctx.served_uma_values)
    known_uma |= {_dec(m.group(1)) for m in _UMA.finditer(texts)} | _written_multiples(texts)
    known_pesos = {_dec(m.group(1)) for m in _PESOS.finditer(texts)} | {a.normalize() for a in ctx.served_amounts}
    known_pesos.add(ctx.settings.uma_value.normalize())

    anomalies: list[dict] = []
    for match in _TRIPLE.finditer(answer):
        triple = tuple(_dec(x) for x in match.groups())
        if triple not in known_triples:
            anomalies.append({"tipo": "monto_no_respaldado", "clase": "uma_terna", "valor": match.group(0)})
    without_triples = _TRIPLE.sub(" ", answer)
    for match in _UMA.finditer(without_triples):
        if _dec(match.group(1)) not in known_uma:
            anomalies.append({"tipo": "monto_no_respaldado", "clase": "uma", "valor": match.group(0)})
    for match in _PESOS.finditer(answer):
        if _dec(match.group(1)) not in known_pesos:
            anomalies.append({"tipo": "monto_no_respaldado", "clase": "pesos", "valor": match.group(0)})
    return anomalies
