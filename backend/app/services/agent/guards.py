"""Deterministic checks on the final answer, independent of what the model decided to do.

The prompt tells the model not to reveal its instructions and not to write links, and the security cases show it
obeys. These guards are the second layer for the day it does not: they act on the text, not on the model.
"""
import re
import unicodedata

from app.services.agent.prompt import SYSTEM_PROMPT

PROMPT_LEAK_WORDS = 12  # a run this long copied from the system prompt is not a coincidence
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


_PROMPT_SHINGLES = _shingles(_words(SYSTEM_PROMPT), PROMPT_LEAK_WORDS)


def leaks_system_prompt(text: str) -> bool:
    return bool(_shingles(_words(text), PROMPT_LEAK_WORDS) & _PROMPT_SHINGLES)


def strip_external_links(text: str) -> tuple[str, bool]:
    """Remove images, markdown links and bare URLs. Sources reach the person through the [n] citations, whose URLs
    the backend builds from the official documents, so an answer never needs a URL of its own."""
    cleaned = _IMAGE.sub("", text)
    cleaned = _LINK.sub(r"\1", cleaned)
    cleaned = _URL.sub("", cleaned)
    return cleaned, cleaned != text
