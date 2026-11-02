"""Deterministic checks on the final answer, independent of what the model decided to do.

The prompt tells the model not to reveal its instructions and not to write links, and the security cases show it
obeys. These guards are the second layer for the day it does not: they act on the text, not on the model.
"""
import re
import unicodedata

from app.services.agent.prompt import SYSTEM_PROMPT

PROMPT_LEAK_WORDS = 20  # a run this long copied from the system prompt is not a coincidence; 12 flagged ordinary rule phrases ("aparece en la lista vigente (Acuerdo 30/2026)…")
LEAK_ANSWER = "No puedo compartir mis instrucciones internas. Puedo ayudarte con dudas de tránsito en la CDMX."

_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\((?:https?:)?//[^)]*\)", re.IGNORECASE)
_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_WORD = re.compile(r"\w+", re.UNICODE)


def _words(text: str) -> list[str]:
    folded = unicodedata.normalize("NFKD", text.casefold())
    return _WORD.findall("".join(c for c in folded if not unicodedata.combining(c)))


def _shingles(words: list[str], size: int) -> set[tuple[str, ...]]:
    return {tuple(words[i : i + size]) for i in range(len(words) - size + 1)}


# Lines the prompt orders the model to write word for word. Copying them is obeying the prompt, not leaking it, so
# they are left out of what counts as "the prompt": otherwise every legal answer would be replaced by LEAK_ANSWER.
REQUIRED_VERBATIM = (
    "Esta información es orientativa y no sustituye asesoría legal; para tu caso concreto consulta a la autoridad "
    "de tránsito o a un abogado.",
)


def _prompt_shingles() -> set[tuple[str, ...]]:
    segments = [_words(SYSTEM_PROMPT)]
    for line in REQUIRED_VERBATIM:
        needle = _words(line)
        remaining: list[list[str]] = []
        for words in segments:
            at = next((i for i in range(len(words) - len(needle) + 1) if words[i : i + len(needle)] == needle), None)
            remaining.extend([words] if at is None else [words[:at], words[at + len(needle) :]])
        segments = remaining
    return set().union(*(_shingles(words, PROMPT_LEAK_WORDS) for words in segments))


_PROMPT_SHINGLES = _prompt_shingles()


def leaks_system_prompt(text: str) -> bool:
    return bool(_shingles(_words(text), PROMPT_LEAK_WORDS) & _PROMPT_SHINGLES)


def strip_external_links(text: str) -> tuple[str, bool]:
    """Remove images, markdown links and bare URLs. Sources reach the person through the [n] citations, whose URLs
    the backend builds from the official documents, so an answer never needs a URL of its own."""
    cleaned = _IMAGE.sub("", text)
    cleaned = _LINK.sub(r"\1", cleaned)
    cleaned = _URL.sub("", cleaned)
    return cleaned, cleaned != text
