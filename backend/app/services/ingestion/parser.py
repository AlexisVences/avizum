"""Turns the text of an official PDF into whole articles with their position in the document.

Pure functions over page texts, so they are testable without a PDF; `parse_pdf` is the only place that
touches PyMuPDF (installed with `uv sync --group ingest`).
"""
import re
from dataclasses import dataclass
from pathlib import Path

# Case-sensitive on purpose: a lowercase "artículo 10; cuando…" at the start of a wrapped line is a cross-reference.
ARTICLE_RE = re.compile(r"^Artículo\s+(\d+)(?:\s+(Bis|Ter|Quáter))?\s*[.\-–—]")
HEADING_RE = re.compile(r"^(TÍTULO|TITULO|CAPÍTULO|CAPITULO|SECCIÓN|SECCION)\s+(\S+)$")
TRANSITORIOS_RE = re.compile(r"^TRANSITORIOS?\b")

_LEVEL = {"TÍTULO": "Título", "TITULO": "Título", "CAPÍTULO": "Capítulo", "CAPITULO": "Capítulo", "SECCIÓN": "Sección", "SECCION": "Sección"}


@dataclass(frozen=True)
class ParsedArticle:
    article: str  # "30" or "30 Bis"
    heading_path: str
    text: str  # the article's lines, one per line, exactly as printed
    page_start: int  # 1-based, matches the PDF viewer's #page=N
    page_end: int


def _sentence_case(name: str) -> str:
    return name[:1] + name[1:].lower()


def _label_case(label: str) -> str:
    return label if re.fullmatch(r"[IVXLC]+", label) else label.capitalize()  # "II" stays, "PRIMERO" -> "Primero"


def parse_articles(pages: list[str], doc_title: str) -> list[ParsedArticle]:
    headings: dict[str, tuple[str, list[str]]] = {}  # level -> (label, name lines); insertion order = hierarchy
    open_heading: str | None = None  # level whose name lines we are still collecting
    current: dict | None = None
    articles: list[ParsedArticle] = []

    def path_for(article: str) -> str:
        parts = [doc_title]
        for level, (label, name) in headings.items():
            parts.append(f"{level} {label}: {_sentence_case(' '.join(name))}" if name else f"{level} {label}")
        parts.append(f"Art. {article}")
        return " › ".join(parts)

    def close() -> None:
        if current:
            articles.append(ParsedArticle(current["article"], current["path"], "\n".join(current["lines"]), current["start"], current["end"]))

    for page_number, page in enumerate(pages, start=1):
        for line in (raw.strip() for raw in page.splitlines()):
            if not line:
                continue
            if TRANSITORIOS_RE.match(line):
                close()
                return articles
            heading = HEADING_RE.match(line)
            if heading:
                level = _LEVEL[heading.group(1)]
                # A new title resets its chapters; a new chapter resets its sections.
                order = ["Título", "Capítulo", "Sección"]
                for deeper in order[order.index(level):]:
                    headings.pop(deeper, None)
                headings[level] = (_label_case(heading.group(2)), [])
                open_heading = level
                continue
            if open_heading and line.isupper() and not ARTICLE_RE.match(line):
                headings[open_heading][1].append(line)
                continue
            open_heading = None
            match = ARTICLE_RE.match(line)
            if match:
                close()
                number = match.group(1) + (f" {match.group(2)}" if match.group(2) else "")
                current = {"article": number, "path": path_for(number), "lines": [line], "start": page_number, "end": page_number}
            elif current:
                current["lines"].append(line)
                current["end"] = page_number
    close()
    return articles


def parse_pdf(path: Path, doc_title: str) -> list[ParsedArticle]:
    import pymupdf

    with pymupdf.open(path) as doc:
        return parse_articles([page.get_text() for page in doc], doc_title)
