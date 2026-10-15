"""Ground truth for sanction questions, taken from the rows a person verified (data/sanctions/verified.json).

An evaluation case says WHICH conduct it is about ({"article": "37", "fraction": "II", "inciso": "b"}); the expected
numbers are read from the verified row, so the label comes from the reviewed article text and never from the
retriever or the model. A case whose row is not verified is skipped, not guessed.
"""
import re
from decimal import ROUND_HALF_UP, Decimal


def _norm(value) -> Decimal:
    return Decimal(str(value)).normalize()


def _s(value: Decimal) -> str:
    return format(value.normalize(), "f")  # "10", not "1E+1"


def _levels(entry: dict) -> list[Decimal]:
    return [_norm(entry[k]) for k in ("uma_min", "uma_mid", "uma_max") if entry.get(k) is not None]


def resolve_ref(entries: list[dict], ref: dict, uma: Decimal) -> dict | None:
    """The verified row a case refers to, with expected UMA multiples, pesos and the 'confusers': the amounts of other
    rows of the same article that share the inciso letter or the conduct family and must NOT be given instead."""
    contains = (ref.get("applies_to_contains") or "").lower()

    def same_article(e: dict) -> bool:
        return e["source_slug"] == ref["source"] and e["article"] == ref["article"]

    def matches(e: dict) -> bool:
        if not same_article(e) or (ref.get("fraction") and e.get("fraction") != ref["fraction"]):
            return False
        if ref.get("inciso") and e.get("inciso") != ref["inciso"]:
            return False
        if contains:
            return contains in (e.get("applies_to") or "").lower()
        return not e.get("applies_to")

    found = [e for e in entries if matches(e)]
    if len(found) != 1:
        return None
    target = found[0]
    expected = _levels(target)
    if not expected:
        return None
    confusers = []
    for e in entries:
        if e is target or not same_article(e):
            continue
        levels = _levels(e)
        if levels and levels != expected and (e.get("inciso") == target.get("inciso") or e.get("fraction") != target.get("fraction")):
            if levels not in confusers:
                confusers.append(levels)
    return {
        "uma": [_s(v) for v in expected],
        "pesos": [str((v * uma).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) for v in expected],
        "confusers": [[_s(v) for v in levels] for levels in confusers],
        "points_license": target.get("points_license"),
    }


def _has_number(text: str, value: str) -> bool:
    plain = _norm(value)
    for match in re.finditer(r"(?<![\d.,])\d[\d,]*(?:\.\d+)?", text):
        try:
            if Decimal(match.group(0).replace(",", "")).normalize() == plain:
                return True
        except Exception:  # noqa: BLE001 - a stray "1,2,3" is not a number we care about
            continue
    return False


def amount_in_answer(answer: str, uma: list[str], pesos: list[str]) -> bool:
    """The expected multiples (5, 7, 10) or the three peso amounts appear in the answer."""
    return all(_has_number(answer, v) for v in uma) or all(_has_number(answer, v) for v in pesos)


def confuser_in_answer(answer: str, uma: list[str], confusers: list[list[str]]) -> list[list[str]]:
    """Confuser triples the answer states as a sequence ("10, 15 o 20") unless that is also the right amount."""
    found = []
    for triple in confusers:
        if triple == uma:
            continue
        pattern = r"\s*(?:,|/|o|y)\s*".join(re.escape(v) for v in triple)
        if re.search(rf"(?<![\d.]){pattern}(?![\d.])", answer):
            found.append(triple)
    return found
