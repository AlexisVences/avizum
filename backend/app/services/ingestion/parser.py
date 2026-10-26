"""Turns the text of an official PDF into whole articles with their position in the document.

Pure functions over page texts, so they are testable without a PDF; `parse_pdf` is the only place that
touches PyMuPDF (installed with `uv sync --group ingest`).
"""
import re
from dataclasses import dataclass
from functools import partial
from pathlib import Path

# Case-sensitive on purpose: a lowercase "artículo 10; cuando…" at the start of a wrapped line is a cross-reference.
# Also accepts "Articulo" (no accent), "1º"/"1°" ordinals and "BIS" in capitals, as printed by the other CDMX laws.
ARTICLE_RE = re.compile(r"^(?:Art[ií]culo|ARTÍCULO|ARTICULO)\s+(\d+)[º°o]?(?:\s+((?i:bis|ter|qu[aá]ter)))?\s*[.\-–—]")
# Fee schedules (Tesorería) head each article as a bare "Art. 219" line; only the "tarifas" layout reads those, because in a
# law a wrapped cross-reference could look the same.
SHORT_ARTICLE_RE = re.compile(r"^Art\.\s+(\d+)\s*$")
# In a fee schedule the amount is printed on its own line under the fraction; left like that the model pairs it with the
# wrong fraction (measured: "cambio de propietario" answered with the alta fee), so it is glued to the line it belongs to.
AMOUNT_LINE_RE = re.compile(r"^\$[\d,]+(?:\.\d{2})?$")
HEADING_RE = re.compile(r"^(TÍTULO|TITULO|CAPÍTULO|CAPITULO|SECCIÓN|SECCION)\s+(\S+)$")
# Editorial notes the Consejería prints between paragraphs ("Párrafo reformado en su cuota G.O. CDMX 19/12/25").
NOTE_RE = re.compile(r"^(?:Art[ií]culos?|P[aá]rrafos?|Fracci[oó]n(?:es)?|Incisos?|Numerales?)\s+(?:reformad|adicionad|derogad)")
MIN_HEADER_CHARS = 15
TRANSITORIOS_RE = re.compile(r"^TRANSI?TORIOS?\b")  # the 2014 Hoy No Circula decree prints "TRANSTORIOS"

_LEVEL = {"TÍTULO": "Título", "TITULO": "Título", "CAPÍTULO": "Capítulo", "CAPITULO": "Capítulo", "SECCIÓN": "Sección", "SECCION": "Sección"}


@dataclass(frozen=True)
class ParsedArticle:
    article: str  # "30" or "30 Bis"
    heading_path: str
    lines: tuple[str, ...]  # the article's lines exactly as printed
    line_pages: tuple[int, ...]  # 1-based page of each line, matches the PDF viewer's #page=N

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    @property
    def page_start(self) -> int:
        return self.line_pages[0]

    @property
    def page_end(self) -> int:
        return self.line_pages[-1]


def _sentence_case(name: str) -> str:
    return name[:1] + name[1:].lower()


def _label_case(label: str) -> str:
    return label if re.fullmatch(r"[IVXLC]+", label) else label.capitalize()  # "II" stays, "PRIMERO" -> "Primero"


def _running_headers(pages: list[str]) -> set[str]:
    """Long lines printed on at least half of the pages (page headers/footers); only meaningful for long documents.

    Short lines never count: labels like "I." or "II." repeat on most pages of a law and are real content.
    """
    if len(pages) < 10:
        return set()
    seen: dict[str, int] = {}
    for page in pages:
        for line in {raw.strip() for raw in page.splitlines() if len(raw.strip()) >= MIN_HEADER_CHARS}:
            seen[line] = seen.get(line, 0) + 1
    return {line for line, pages_with_line in seen.items() if pages_with_line >= len(pages) / 2}


def parse_articles(pages: list[str], doc_title: str, first_page: int = 1, short_headings: bool = False) -> list[ParsedArticle]:
    running_headers = _running_headers(pages)
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
            articles.append(ParsedArticle(current["article"], current["path"], tuple(current["lines"]), tuple(current["pages"])))

    for page_number, page in enumerate(pages, start=first_page):
        for line in (raw.strip() for raw in page.splitlines()):
            if not line or line in running_headers or NOTE_RE.match(line):
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
            match = ARTICLE_RE.match(line) or (SHORT_ARTICLE_RE.match(line) if short_headings else None)
            if match:
                close()
                suffix = match.group(2) if match.re is ARTICLE_RE else None
                number = match.group(1) + (f" {suffix.capitalize()}" if suffix else "")
                current = {"article": number, "path": path_for(number), "lines": [line], "pages": [page_number]}
            elif current and short_headings and AMOUNT_LINE_RE.match(line) and len(current["lines"]) > 1:
                current["lines"][-1] += f" {line}"
            elif current:
                current["lines"].append(line)
                current["pages"].append(page_number)
    close()
    return articles


SECTION_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\s+(\S.*)$")  # "4.5 DETENCIONES", "1.1 Principio de legalidad. El personal…"
CHAPTER_RE = re.compile(r"^CAPÍTULO\s+([A-ZÁÉÍÓÚ]+)\.\s*(.*)$")  # with a period; a bare "CAPÍTULO CUARTO" is a running header


def parse_sections(pages: list[str], doc_title: str, first_page: int = 1) -> list[ParsedArticle]:
    """Like `parse_articles` for documents organised in numbered sections (protocols, guides) instead of articles.

    A section id is a heading only if it is greater than the previous one, so a line that merely starts with
    "4.4 de este protocolo…" in the middle of section 4.5 stays part of the text.
    """
    running_headers = _running_headers(pages)
    chapter: tuple[str, list[str]] | None = None
    collecting_chapter = False
    last_id = (0, 0)
    current: dict | None = None
    sections: list[ParsedArticle] = []

    def close() -> None:
        if current:
            sections.append(ParsedArticle(current["id"], current["path"], tuple(current["lines"]), tuple(current["pages"])))

    for page_number, page in enumerate(pages, start=first_page):
        for line in (raw.strip() for raw in page.splitlines()):
            if not line or line in running_headers or line.isdigit():
                continue
            if TRANSITORIOS_RE.match(line):
                close()
                return sections
            heading = CHAPTER_RE.match(line)
            if heading:
                chapter = (_label_case(heading.group(1)), [heading.group(2)] if heading.group(2) else [])
                collecting_chapter = True
                continue
            section = SECTION_RE.match(line)
            if collecting_chapter and chapter and line.isupper() and not section:
                chapter[1].append(line)
                continue
            collecting_chapter = False
            if section and (int(section.group(1)), int(section.group(2))) > last_id:
                close()
                last_id = (int(section.group(1)), int(section.group(2)))
                section_id = f"{last_id[0]}.{last_id[1]}"
                title = section.group(3).split(". ")[0][:90].rstrip(".")
                title = _sentence_case(title) if title.isupper() else title
                parts = [doc_title]
                if chapter:
                    name = _sentence_case(" ".join(chapter[1]).strip())
                    parts.append(f"Capítulo {chapter[0].lower()}" + (f": {name}" if name else ""))
                parts.append(f"{section_id} {title}")
                current = {"id": section_id, "path": " › ".join(parts), "lines": [line], "pages": [page_number]}
            elif current:
                current["lines"].append(line)
                current["pages"].append(page_number)
    close()
    return sections


CHAPTER_TITLE_RE = re.compile(r"^(\d{1,2})\.\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9 ,;:()“”\"'/.\-–]*)$")  # "5. CALENDARIO PARA…"; "5.1.9." or "1. Haber…" are not


def parse_chapters(pages: list[str], doc_title: str, first_page: int = 1) -> list[ParsedArticle]:
    """Like `parse_articles` for programs organised in numbered chapters ("5. CALENDARIO…") with numerals inside.

    The chapter is the unit, so its inner numerals (5.1.9.) stay in the text for the answer to cite; the chunker splits
    long chapters by size. A chapter is an uppercase title with a number above the previous one, so "1. Haber obtenido…" list
    items and cross-references stay part of the text. A title printed over two lines is joined.
    """
    running_headers = _running_headers(pages)
    last_number = 0
    collecting_title = False
    current: dict | None = None
    chapters: list[ParsedArticle] = []

    def close() -> None:
        if current:
            chapters.append(ParsedArticle(current["id"], current["path"], tuple(current["lines"]), tuple(current["pages"])))

    for page_number, page in enumerate(pages, start=first_page):
        for line in (raw.strip() for raw in page.splitlines()):
            if not line or line in running_headers or line.isdigit():
                continue
            if TRANSITORIOS_RE.match(line):
                close()
                return chapters
            heading = CHAPTER_TITLE_RE.match(line)
            if heading and int(heading.group(1)) > last_number:
                close()
                last_number = int(heading.group(1))
                current = {"id": heading.group(1), "title": [heading.group(2)], "lines": [line], "pages": [page_number]}
                current["path"] = f"{doc_title} › {last_number} {_sentence_case(heading.group(2))}"
                collecting_title = True
                continue
            if not current:
                continue
            if collecting_title and line.isupper() and not re.match(r"^\d", line):
                current["title"].append(line)  # the title wraps onto this line
                current["path"] = f"{doc_title} › {last_number} {_sentence_case(' '.join(current['title']))}"
            else:
                collecting_title = False
            current["lines"].append(line)
            current["pages"].append(page_number)
    close()
    return chapters


DECREE_CHAPTER_RE = re.compile(r"^([IVXL]+)\.-\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9 ,;:()“”\"'/.\-–]*)$")  # "IV.- REGLAS APLICABLES…"
DECREE_SUBSECTION_RE = re.compile(r"^([IVXL]+)\.(\d{1,2})\.?\s+(\S.*)$")  # "IV.4. HOLOGRAMA “2”"; "VI. 1. Las fuentes…" is text
_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50}


def _roman_to_int(numeral: str) -> int:
    values = [_ROMAN[c] for c in numeral]
    return sum(-v if i + 1 < len(values) and v < values[i + 1] else v for i, v in enumerate(values))


def parse_decree(pages: list[str], doc_title: str, first_page: int = 1) -> list[ParsedArticle]:
    """Like `parse_chapters` for decrees whose chapters are roman ("IV.- REGLAS…") and have numbered subsections ("IV.4.").

    A chapter with subsections yields one unit for the chapter's own opening text and one per subsection (id "IV.4"),
    because each subsection (here, each hologram and its table) answers a different question. Roman items in sentence
    case ("I.- Días.") are lists inside a chapter, and a chapter number must rise, so neither opens a unit.
    """
    running_headers = _running_headers(pages)
    last_chapter = 0
    chapter_numeral, chapter_title, last_sub = "", [], 0
    collecting_title = False
    current: dict | None = None
    units: list[ParsedArticle] = []

    def close() -> None:
        if current:
            units.append(ParsedArticle(current["id"], current["path"], tuple(current["lines"]), tuple(current["pages"])))

    def chapter_path() -> str:
        return f"{doc_title} › {chapter_numeral} {_sentence_case(' '.join(chapter_title))}"

    for page_number, page in enumerate(pages, start=first_page):
        for line in (raw.strip() for raw in page.splitlines()):
            if not line or line in running_headers or line.isdigit():
                continue
            if TRANSITORIOS_RE.match(line):
                close()
                return units
            chapter = DECREE_CHAPTER_RE.match(line)
            if chapter and _roman_to_int(chapter.group(1)) > last_chapter:
                close()
                last_chapter, chapter_numeral, chapter_title, last_sub = _roman_to_int(chapter.group(1)), chapter.group(1), [chapter.group(2)], 0
                current = {"id": chapter_numeral, "path": chapter_path(), "lines": [line], "pages": [page_number]}
                collecting_title = True
                continue
            if not current:
                continue
            sub = DECREE_SUBSECTION_RE.match(line)
            if sub and sub.group(1) == chapter_numeral and int(sub.group(2)) > last_sub:
                close()
                last_sub = int(sub.group(2))
                title = sub.group(3)
                title = _sentence_case(title) if title.isupper() else title
                current = {"id": f"{chapter_numeral}.{last_sub}", "path": f"{chapter_path()} › {chapter_numeral}.{last_sub} {title}",
                           "lines": [line], "pages": [page_number]}
                collecting_title = False
                continue
            if collecting_title and line.isupper():
                chapter_title.append(line)  # the chapter title wraps onto this line
                current["path"] = chapter_path()
            else:
                collecting_title = False
            current["lines"].append(line)
            current["pages"].append(page_number)
    close()
    return units


def parse_ficha(text: str, doc_title: str) -> list[ParsedArticle]:
    """A transcribed official web page (a SEMOVI or Profeco ficha) in Markdown: one unit per "## Heading".

    Text before the first heading becomes the unit "Resumen". The "# Title", "Fuente:" and "Consultada:" lines are for the
    person who maintains the file and are not indexed. A web page has no pages, so every line is on page 0 and a citation
    opens the page itself.
    """
    units: list[tuple[str, list[str]]] = [("Resumen", [])]
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("# ") or line.startswith(("Fuente:", "Consultada:")):
            continue
        if line.startswith("## "):
            units.append((line[3:].strip(), [line[3:].strip()]))
        else:
            units[-1][1].append(line)
    return [
        ParsedArticle(heading if len(heading) <= 50 else heading[:49] + "…", f"{doc_title} › {heading}", tuple(lines), (0,) * len(lines))
        for heading, lines in units if lines
    ]


def parse_pdf(path: Path, doc_title: str, layout: str = "articles", pages: tuple[int, int] | None = None) -> list[ParsedArticle]:
    """`pages` is an inclusive 1-based range (e.g. to skip a table of contents); page numbers stay absolute."""
    import pymupdf

    with pymupdf.open(path) as doc:
        first, last = pages or (1, doc.page_count)
        texts = [doc[i].get_text() for i in range(first - 1, last)]
    parse = {"sections": parse_sections, "chapters": parse_chapters, "tarifas": partial(parse_articles, short_headings=True), "decreto": parse_decree}.get(layout, parse_articles)
    return parse(texts, doc_title, first_page=first)
