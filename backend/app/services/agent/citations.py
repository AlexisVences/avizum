"""Turns the model's `[n]` markers into the citations the user can open, and catches the ones that point nowhere.

The model only ever sees numbers; the registry knows what each number is. Nothing the model writes is trusted:
a marker with no matching fragment is removed and reported, so the interface never shows a citation that does not
exist, and an answer that used the tools but cites nothing is flagged for review.
"""
import re
from dataclasses import dataclass

from app.services.agent.context import CitationRegistry

_GROUP = re.compile(r"\[(\d{1,3}(?:\s*[,;]\s*\d{1,3})+)\]")  # "[1, 2]" and "[1; 2]" become "[1][2]"
_MARKER = re.compile(r"\s?\[(\d{1,3})\]")  # takes the space before it so removing a marker leaves no gap


@dataclass
class ResolvedAnswer:
    text: str  # the answer without invalid markers; valid ones are untouched so streamed text stays consistent
    citations: list[dict]  # only the citations the text uses, in order of first appearance
    anomalies: list[dict]  # [{"tipo": "marca_invalida", "n": 99}, {"tipo": "sin_citas"}]


def resolve_citations(text: str, registry: CitationRegistry) -> ResolvedAnswer:
    text = _GROUP.sub(lambda m: "".join(f"[{n}]" for n in re.split(r"\s*[,;]\s*", m.group(1))), text)
    known = {citation.n: citation for citation in registry.all()}
    used: list[int] = []
    invalid: list[int] = []

    def check(match: re.Match) -> str:
        n = int(match.group(1))
        if n in known:
            if n not in used:
                used.append(n)
            return match.group(0)
        if n not in invalid:
            invalid.append(n)
        return ""

    cleaned = _MARKER.sub(check, text).strip()
    citations = [
        {
            "n": n, "orden": position, "source_slug": known[n].source_slug, "source_title": known[n].source_title,
            "article": known[n].article, "fraction": known[n].fraction, "page": known[n].page, "url": known[n].url,
        }
        for position, n in enumerate(used, start=1)
    ]
    anomalies: list[dict] = [{"tipo": "marca_invalida", "n": n} for n in invalid]
    if known and not used:
        anomalies.append({"tipo": "sin_citas"})
    return ResolvedAnswer(text=cleaned, citations=citations, anomalies=anomalies)
