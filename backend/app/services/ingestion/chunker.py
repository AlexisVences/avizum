"""Cuts parsed articles into retrievable chunks: whole article when small, one chunk per fraction when large."""
import re
from collections.abc import Callable
from dataclasses import dataclass

from app.services.ingestion.parser import ParsedArticle

MAX_CHUNK_TOKENS = 800
# Cutting long fractions by their incisos (a), b), c)… is implemented but DISABLED (threshold above any real fraction).
# Experiment 2026-10-09 with threshold 350: recall@5 fell 0.80 -> 0.60 (rewrite+RRF) and 0.72 -> 0.64 (raw), because many
# near-duplicate siblings (same intro + fraction header) crowd the top results. Do not enable without re-measuring.
INCISO_MIN_TOKENS = 100_000
# An article whose introduction alone is this long (e.g. the points regime of Reglamento art. 64) keeps it as ONE chunk;
# repeating it inside every fraction produced several near-identical ~1,000-token chunks.
HEAVY_INTRO_TOKENS = 400
FRACTION_RE = re.compile(r"^([IVXLC]+)(?:\s+((?i:bis|ter|qu[aá]ter)))?\s*[.\-–—]")  # "II.", "IV Bis.", "V BIS.", "III.-"

INCISO_RE = re.compile(r"^([a-z])\)\s")  # "a) Indicará al conductor…"

TokenCounter = Callable[[str], int]


@dataclass(frozen=True)
class ChunkDraft:
    article: str
    fraction: str | None
    heading_path: str
    text: str
    page_start: int
    page_end: int
    token_count: int  # of `embedding_text`, i.e. what is actually sent to the embedding model

    @property
    def embedding_text(self) -> str:
        # Contextual retrieval: the vector also "knows" which law, title and article it belongs to.
        return f"{self.heading_path}\n{self.text}"


def openai_token_counter(model: str = "text-embedding-3-small") -> TokenCounter:
    import tiktoken

    encoding = tiktoken.encoding_for_model(model)
    return lambda text: len(encoding.encode(text))


def _draft(article: ParsedArticle, fraction: str | None, lines: list[str], pages: list[int], count_tokens: TokenCounter) -> ChunkDraft:
    heading_path = article.heading_path + (f", fr. {fraction}" if fraction else "")
    text = "\n".join(lines)
    return ChunkDraft(
        article=article.article, fraction=fraction, heading_path=heading_path, text=text,
        page_start=min(pages), page_end=max(pages), token_count=count_tokens(f"{heading_path}\n{text}"),
    )


def chunk_article(
    article: ParsedArticle,
    max_tokens: int = MAX_CHUNK_TOKENS,
    count_tokens: TokenCounter | None = None,
    inciso_min_tokens: int = INCISO_MIN_TOKENS,
    heavy_intro_tokens: int = HEAVY_INTRO_TOKENS,
) -> list[ChunkDraft]:
    count_tokens = count_tokens or openai_token_counter()
    lines, pages = list(article.lines), list(article.line_pages)

    whole = _draft(article, None, lines, pages, count_tokens)
    if whole.token_count <= max_tokens:
        return [whole]

    starts = [i for i, line in enumerate(lines) if i > 0 and FRACTION_RE.match(line)]
    if starts:
        return _by_fraction(article, lines, pages, starts, count_tokens, inciso_min_tokens, heavy_intro_tokens)
    return _by_lines(article, lines, pages, max_tokens, count_tokens)


def _split_incisos(label: str, block: list[str], pages: list[int], count_tokens: TokenCounter, min_tokens: int):
    """Yield (label, lines, pages) parts of one fraction: whole, or one part per inciso plus a closing paragraph.

    Every part repeats the fraction's own header lines, so "e) Solicitará licencia…" still says which fraction and
    which kind of person it is about. The paragraph that follows the last inciso (typically the sanction) becomes its
    own part instead of being pinned to the last inciso.
    """
    starts = [i for i, line in enumerate(block) if i > 0 and INCISO_RE.match(line)]
    if len(starts) < 3 or count_tokens("\n".join(block)) <= min_tokens:
        return [(label, block, pages)]
    head, head_pages = block[: starts[0]], pages[: starts[0]]
    parts = []
    for begin, end in zip(starts, [*starts[1:], len(block)]):
        segment, segment_pages = block[begin:end], pages[begin:end]
        closing = None
        if end == len(block):
            cut = next((k for k in range(1, len(segment)) if segment[k][:1].isupper() and segment[k - 1].rstrip().endswith((".", ";", ":"))), None)
            if cut:
                closing, segment, segment_pages = (segment[cut:], segment_pages[cut:]), segment[:cut], segment_pages[:cut]
        letter = INCISO_RE.match(segment[0]).group(1)
        parts.append((f"{label}, inc. {letter})", head + segment, head_pages + segment_pages))
        if closing:
            parts.append((f"{label}, párrafo final", head + closing[0], head_pages + closing[1]))
    return parts


def _by_fraction(
    article: ParsedArticle, lines: list[str], pages: list[int], starts: list[int], count_tokens: TokenCounter,
    inciso_min_tokens: int, heavy_intro_tokens: int,
) -> list[ChunkDraft]:
    intro_lines, intro_pages = lines[: starts[0]], pages[: starts[0]]
    chunks = []
    if len(intro_lines) > 1 and count_tokens("\n".join(intro_lines)) > heavy_intro_tokens:
        chunks.append(_draft(article, None, intro_lines, intro_pages, count_tokens))
        intro_lines, intro_pages = intro_lines[:1], intro_pages[:1]  # fractions keep only the article's opening line
    for begin, end in zip(starts, [*starts[1:], len(lines)]):
        numeral, suffix = FRACTION_RE.match(lines[begin]).groups()
        label = f"{numeral} {suffix.capitalize()}" if suffix else numeral
        # The fraction line plus everything until the next one, penalty paragraph included.
        for part_label, part_lines, part_pages in _split_incisos(label, lines[begin:end], pages[begin:end], count_tokens, inciso_min_tokens):
            draft = _draft(article, part_label, intro_lines + part_lines, intro_pages + part_pages, count_tokens)
            # Cite the pages where the fraction itself is printed, not the page of the article's intro.
            chunks.append(ChunkDraft(**{**draft.__dict__, "page_start": min(part_pages), "page_end": max(part_pages)}))
    return chunks


def _by_lines(article: ParsedArticle, lines: list[str], pages: list[int], max_tokens: int, count_tokens: TokenCounter) -> list[ChunkDraft]:
    header = lines[0]  # "Artículo N.- …" repeated on every part
    chunks, group, group_pages = [], [], []

    def flush() -> None:
        if group:
            chunks.append(_draft(article, None, [header, *group], [pages[0], *group_pages], count_tokens))

    for line, page in zip(lines[1:], pages[1:]):
        candidate = _draft(article, None, [header, *group, line], [pages[0], *group_pages, page], count_tokens)
        if group and candidate.token_count > max_tokens:
            flush()
            group, group_pages = [], []
        group.append(line)
        group_pages.append(page)
    flush()
    return chunks
