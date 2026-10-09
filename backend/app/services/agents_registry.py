"""Authorized-agents registry: normalization and lookup against the official Gaceta list."""
import re
import unicodedata

AGENTS_SOURCE_SLUG = "acuerdo-agentes-transito"


def normalize_name(value: str) -> str:
    """Lowercase, strip accents (ñ → n) and punctuation, collapse whitespace."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    letters_only = re.sub(r"[^a-z\s]", " ", without_accents.lower())
    return " ".join(letters_only.split())


def normalize_plate(value: str) -> str:
    return re.sub(r"[\s\-]", "", value).upper()
