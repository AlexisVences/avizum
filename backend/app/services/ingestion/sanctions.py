"""Deterministic extraction of the penalties written in a legal chunk (no network, no model).

An article lists conducts and then penalty clauses, and the clauses say which conducts they cover ("los incisos a),
b), d) y e) ... 5, 7 o 10 veces la UMA; el inciso c) ... 10, 15 o 20"). Reading that mapping out of prose is where the
agent made mistakes, so it is done here, once, with rules that can be tested and reviewed:

* numbers and points come from the verbatim clause with regular expressions, never from a model;
* a clause is attached to the conducts it names; if the text does not say which ones, it is NOT guessed: the clause
  is reported as an issue and no row is produced for it;
* every row carries the verbatim conduct and clause, so a person can check it against the source.

Rows are only candidates (`pending`). A person verifies them (see the plan 2026-10-15-sanciones-estructuradas).
"""
import hashlib
import re
from dataclasses import dataclass, field
from decimal import Decimal

EXTRACTOR_VERSION = "det-2"
CONDUCT_CHARS = 1200

NUMBER_WORDS = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12}
_UMA = r"(?:veces\s+(?:la\s+)?Unidad(?:es)?\s+de\s+Medida|Unidades\s+de\s+Medida|veces\s+la\s+UMA)"
_UMA_RE = re.compile(_UMA)
_TRIPLE = re.compile(r"(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s+o\s+(\d+(?:\.\d+)?)\s+veces")
_POINTS = r"(?:de\s+penalizaci[oó]n\s+)?(?:a|en)\s+la\s+"
_POINTS_LICENSE = re.compile(r"(\w+)\s+puntos?\s+" + _POINTS + r"licencia", re.I)
_POINTS_PLATE = re.compile(r"(\w+(?:\s+a\s+\w+)?)\s+puntos?\s+" + _POINTS + r"(?:placa\s+de\s+)?matr[ií]cula", re.I)
_BOUNDARY = re.compile(
    r"[.;:]\s+(?:y\s+)?(?=[A-ZÁÉÍÓÚÑ¿])"  # the usual sentence/fraction boundary
    r"|,\s+y\s+(?=(?:Los|Las|El|La)\s)"  # "...lo indique, y Los conductores que infrinjan..."
    r"|\s[óo]\s+(?=(?:El\s+incumplimiento|Los\s+conductores|El\s+motociclista)\b)"  # "...nociva ó El incumplimiento..."
)
_SENTENCE_END = re.compile(r"\.(?=\s|$)")
_INCISO_LIST = re.compile(r"incisos?\s+((?:[a-z](?:\s+Bis)?\)\s*(?:,|\by\b|\bo\b|\bal\b)?\s*)+)", re.I)
_INCISO_LABEL = re.compile(r"\b([a-z](?:\s+Bis)?)\)", re.I)
_INCISO_MARK = re.compile(r"(?:^|[:;.,]\s+)(?:y\s+)?([a-z](?:\s+Bis)?)[.)]\s+(?=[A-ZÁÉÍÓÚÑ¿\"“])")
# A roman marker only counts when it is the NEXT number in sequence (checked in _fractions) and the word before it
# is not "fracción", "y", "al"...: a note such as "G.O. CDMX 10/10/25 II. Abstenerse" still starts fraction II.
_ROMAN_MARK = re.compile(r"(?:^|(?<=\s))([IVXL]+)\.\s+(?=[A-ZÁÉÍÓÚÑ¿\"“])")
_ROMAN_GUARD = re.compile(r"(?:fracci[oó]n(?:es)?|\by\b|\bo\b|\bal\b|\ba\b|\bde\b|\bla\b|\bel\b|,)\s*$", re.I)
_HEADER = re.compile(r"^Art[ií]culo\s+\d+(?:\s*(?:Bis|Ter|Qu[aá]ter))?\s*\.?\s*-\s*", re.I)
_TRAILING_MARK = re.compile(r"\s*[IVXL]+\.\s*$")
_EXCEPTION = re.compile(r"\b(?:excepto|exceptuad[oa]s?|salvo|con\s+excepci[oó]n)\b", re.I)
_GENERIC = re.compile(
    r"presentes?\s+(?:disposici(?:[oó]n|ones)|art[ií]culo|fracci(?:[oó]n|ones))|est[ae]s?\s+(?:disposici(?:[oó]n|ones)|fracci(?:[oó]n|ones))"
    r"|este\s+art[ií]culo"
    r"|previsto\s+en\s+el\s+presente|lo\s+dispuesto\s+en\s+(?:esta|el\s+presente)",
    re.I,
)
_ARTICLE_WIDE = re.compile(r"presente\s+art[ií]culo|este\s+art[ií]culo", re.I)
_ALTERNATIVE_POINTS = re.compile(r"\bo\s+en\s+caso\s+de\s+infracciones\s+captadas", re.I)
_OTHER_PHRASE = re.compile(
    r"(?:\bo\s+)?arresto\s+administrativo[^,;.]*"
    r"|remisi[oó]n\s+del\s+veh[ií]culo\s+al\s+dep[oó]sito(?:\s+vehicular)?"
    r"|remitid[oa]\s+al\s+dep[oó]sito(?:\s+vehicular)?"
    r"|retenci[oó]n\s+de\s+(?:las\s+)?placas?(?:\s+de\s+circulaci[oó]n)?"
    r"|cancelaci[oó]n\s+de\s+(?:la\s+)?licencia|suspensi[oó]n\s+de\s+(?:la\s+)?licencia",
    re.I,
)
_ARREST = re.compile(r"\barresto\s+administrativo\b", re.I)  # the Reglamento's wording; Cultura Cívica says "arresto de…"
_PENALTY_VERB = re.compile(
    r"ser[aá]n? sancionad|se sancionar|la multa ser[aá]|multa equivalente|deber[aá] cubrir|una multa de|se impondr", re.I
)
_QUALIFIER = re.compile(r"^(?:en el caso de|tratándose de|si se determina)\b", re.I)
_PENALTY_WORD = re.compile(r"multa|sanci[oó]n|sancionad|sancionar|infracci|arresto", re.I)
_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50}


_UNITS = {
    "cero": 0, "uno": 1, "un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
    "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
    "dieciséis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiuno": 21,
    "veintidós": 22, "veintitrés": 23, "veinticuatro": 24, "veinticinco": 25, "veintiséis": 26, "veintisiete": 27,
    "veintiocho": 28, "veintinueve": 29,
}
_TENS = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90}
_HUNDREDS = {
    "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300, "cuatrocientos": 400, "quinientos": 500,
    "seiscientos": 600, "setecientos": 700, "ochocientos": 800, "novecientos": 900,
}


def _number(words: list[str]) -> int | None:
    """A Spanish number written in words or digits ("ciento ochenta", "180"); None if the words are not a number."""
    if not words:
        return None
    if len(words) == 1 and re.fullmatch(r"\d+", words[0]):
        return int(words[0])
    lowered = [w.lower() for w in words]
    if "mil" in lowered:  # "mil", "cincuenta mil", "dos mil quinientos"
        at = lowered.index("mil")
        thousands = _number(words[:at]) if at else 1
        rest = _number(words[at + 1:]) if at + 1 < len(words) else 0
        if thousands is None or rest is None:
            return None
        return thousands * 1000 + rest
    total = 0
    for word in lowered:
        if word == "y":
            continue
        if word in _HUNDREDS:
            total += _HUNDREDS[word]
        elif word in _TENS:
            total += _TENS[word]
        elif word in _UNITS:
            total += _UNITS[word]
        else:
            return None
    return total or None


def _trailing_number(text: str) -> tuple[int | None, str]:
    """The longest number at the end of `text` and the words that come before it."""
    tokens = re.findall(r"[\wáéíóúñÁÉÍÓÚÑ]+", text)
    for size in range(min(6, len(tokens)), 0, -1):
        value = _number(tokens[-size:])
        if value is not None:
            return value, " ".join(tokens[: len(tokens) - size])
    return None, text


@dataclass(frozen=True)
class Sanction:
    ordinal: int
    fraction: str | None
    inciso: str | None
    conduct_text: str
    clause_text: str
    uma_min: Decimal | None
    uma_mid: Decimal | None
    uma_max: Decimal | None
    points_license: int | None
    points_plate: int | None
    other_consequences: str | None
    applies_to: str | None
    lead_text: str | None = None  # the article's own wording before its list ("Se prohíbe estacionar cualquier vehículo:")
    points_mode: str | None = None  # 'alternativos_por_via' (licencia o matrícula) | 'acumulativos' (ambos)
    article_wide: bool = False  # the clause says "el presente artículo": it covers fractions that have none of their own


@dataclass(frozen=True)
class Issue:
    kind: str  # rango | tabla | sin_monto | alcance_ambiguo | inciso_desconocido | cobertura_incompleta | ...
    detail: str
    clause_text: str = ""


@dataclass
class Extraction:
    sanctions: list[Sanction] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)


def chunk_hash(text: str) -> str:
    """Ties a row to the exact stored text it was extracted from; if the chunk changes the row goes stale."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _roman(label: str) -> int:
    total, previous = 0, 0
    for char in reversed(label):
        value = _ROMAN_VALUES[char]
        total += value if value >= previous else -value
        previous = max(previous, value)
    return total


def _lead(raw: str) -> str:
    """The article's own wording that introduces its list, without "Artículo N.-" and without the trailing marker."""
    return _HEADER.sub("", _TRAILING_MARK.sub("", raw), count=1).strip()[:400]


def _fractions(flat: str, fraction: str | None) -> tuple[str, list[tuple[str | None, str]]]:
    """(lead, [(fraction, text)]). A fraction chunk is one segment; an article chunk is split on its consecutive
    roman-numeral markers (I., II., ...), where a marker counts only as the NEXT number in sequence. Anything
    irregular stays a single segment."""
    if fraction:
        marker = re.search(rf"(?:^|[:;.]\s+){re.escape(fraction)}\.\s+", flat)
        if marker:
            return _lead(flat[: marker.end()]), [(fraction, flat[marker.end():])]
        return "", [(fraction, _HEADER.sub("", flat, count=1))]
    valid: list[re.Match] = []
    for mark in _ROMAN_MARK.finditer(flat):
        if _roman(mark.group(1)) == len(valid) + 1 and not _ROMAN_GUARD.search(flat[: mark.start()]):
            valid.append(mark)
    if not valid:
        return "", [(None, _HEADER.sub("", flat, count=1))]
    segments = []
    for index, mark in enumerate(valid):
        end = valid[index + 1].start() if index + 1 < len(valid) else len(flat)
        segments.append((mark.group(1), flat[mark.end():end]))
    return _lead(flat[: valid[0].end()]), segments


def _sentence(segment: str, position: int, end_search_from: int) -> tuple[int, int]:
    starts = [b.end() for b in _BOUNDARY.finditer(segment, 0, position)]
    start = starts[-1] if starts else 0
    end_match = _SENTENCE_END.search(segment, end_search_from)
    return start, (end_match.end() if end_match else len(segment))


def _clauses(segment: str) -> list[tuple[int, int]]:
    """(start, end) of every sentence that states a penalty: in UMA, or an arrest, in order of appearance."""
    spans: list[tuple[int, int]] = []
    for match in _UMA_RE.finditer(segment):
        span = _sentence(segment, match.start(), match.end())
        if span not in spans:
            spans.append(span)
    for match in _ARREST.finditer(segment):  # arrest-only penalties (driving drunk): no UMA in the sentence
        span = _sentence(segment, match.start(), match.end())
        sentence = segment[span[0]:span[1]]
        overlaps = any(span[0] < other[1] and other[0] < span[1] for other in spans)
        inside_procedure = bool(_INCISO_MARK.search(segment[: span[0]]))  # Arts. 51-52 restate Art. 50 step by step
        if not overlaps and not inside_procedure and re.search(r"sancionar|sancionad|impondr", sentence, re.I) and re.search(r"horas", sentence, re.I):
            spans.append(span)
    return sorted(spans)


def _incisos(body: str) -> dict[str, str] | None:
    """{label: verbatim text} of the lettered items in the body, or None when the lettering is irregular."""
    marks = list(_INCISO_MARK.finditer(body))
    if not marks:
        return {}
    labels = [re.sub(r"\s+", " ", m.group(1)).lower().replace(" bis", " Bis") for m in marks]
    expected = "a"
    for label in labels:
        if label == expected:
            expected = chr(ord(expected) + 1)
        elif label == f"{chr(ord(expected) - 1)} Bis":
            continue
        else:
            return None
    items: dict[str, str] = {}
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(body)
        text = body[mark.end():end].strip()
        # Drop the list punctuation and a trailing connector WORD. (rstrip("; y o") ate the last letter of "propio".)
        text = re.sub(r"[;,.]\s*$", "", text)
        text = re.sub(r"[;,]?\s+(?:y|o)$", "", text)
        text = re.sub(r"[;,.]\s*$", "", text).strip()
        items[labels[index]] = text
    return items


def _points(clause: str) -> tuple[int | None, int | None, str | None, str | None, list[Issue]]:
    """(licence points, plate points, plate-range note, mode, issues)."""
    issues: list[Issue] = []
    note: str | None = None
    license_points = plate_points = None
    match = _POINTS_LICENSE.search(clause)
    if match:
        word = match.group(1).lower()
        license_points = int(word) if word.isdigit() else NUMBER_WORDS.get(word)
        if license_points is None:
            issues.append(Issue("puntos_no_reconocidos", match.group(0), clause))
    match = _POINTS_PLATE.search(clause)
    if match:
        word = match.group(1).lower()
        if " a " in word:  # "uno a cinco puntos a la matrícula": depends on the speed excess, not a single number
            note = f"puntos a la matrícula: {match.group(0)}"
        else:
            plate_points = int(word) if word.isdigit() else NUMBER_WORDS.get(word)
            if plate_points is None:
                issues.append(Issue("puntos_no_reconocidos", match.group(0), clause))
    mode = None
    if license_points is not None and (plate_points is not None or note):
        mode = "alternativos_por_via" if _ALTERNATIVE_POINTS.search(clause) else "acumulativos"
    elif _ALTERNATIVE_POINTS.search(clause) and (license_points is not None or plate_points is not None):
        mode = "alternativos_por_via"
    return license_points, plate_points, note, mode, issues


def _clean(conduct: str) -> str:
    """A conduct as the fraction wrote it, without the connector that joined it to the next one."""
    text = conduct.strip()
    text = re.sub(r"[;,.]?\s+(?:y|o|ó|u)$", "", text)
    return text.rstrip(" ;,")


def _head(clause: str) -> str:
    verb = _PENALTY_VERB.search(clause)
    return clause[: verb.start()] if verb else clause


def _scope(clause: str) -> tuple[str, list[str] | None]:
    """('qualifier' | 'incisos' | 'whole' | 'ambiguous', labels)."""
    if _QUALIFIER.match(clause.strip()):
        return "qualifier", None
    head = _head(clause)
    if re.search(r"fracciones\s+[IVXL]+", head):
        return "ambiguous", None
    listing = _INCISO_LIST.search(clause)
    if listing:
        labels = [re.sub(r"\s+", " ", x).lower().replace(" bis", " Bis") for x in _INCISO_LABEL.findall(listing.group(1))]
        span = re.search(r"\b([a-z])\)\s+al\s+([a-z])\)", listing.group(1), re.I)
        if span:  # "los incisos c) al f)" means c, d, e, f
            first, last = span.group(1).lower(), span.group(2).lower()
            expanded = [chr(c) for c in range(ord(first), ord(last) + 1)]
            labels = [x for x in labels if x not in (first, last)] + expanded
        return "incisos", labels
    return "whole", None


def _qualifier(clause: str) -> str:
    return _head(clause).strip(" ,;")[:300]


def _amount(clause: str) -> tuple[tuple[Decimal | None, Decimal | None, Decimal | None] | None, str | None]:
    triple = _TRIPLE.search(clause)
    if triple:
        low, mid, high = (Decimal(x) for x in triple.groups())
        return (low, mid, high), None
    uma = _UMA_RE.search(clause)
    if not uma:
        if _ARREST.search(clause):
            return (None, None, None), None  # an arrest-only penalty: no amount in UMA
        return None, "sin_monto"
    value, before = _trailing_number(clause[: uma.start()])
    if value is None:
        return None, "sin_monto"
    if re.search(r"\b(?:a|hasta)$", before):  # "de trescientos cincuenta a cuatrocientos cincuenta veces": a range
        return None, "rango"
    return (Decimal(value), None, None), None


def _other(clause: str) -> str | None:
    phrases: list[str] = []
    for match in _OTHER_PHRASE.finditer(clause):
        text = match.group(0).strip()
        if text and text not in phrases:
            phrases.append(text)
    return "; ".join(phrases) or None


def extract_sanctions(article: str, fraction: str | None, text: str) -> Extraction:
    """Candidate sanction rows (and what could not be resolved) for one chunk."""
    result = Extraction()
    flat = _flat(text)
    if "Sanción mínima" in flat and "Sanción máxima" in flat:
        result.issues.append(Issue("tabla", f"Art. {article}: penalidades en una tabla por tipo de vehículo; capturar a mano"))
        return result

    lead, segments = _fractions(flat, fraction)
    exception_mode = bool(lead) and bool(_EXCEPTION.search(lead[-220:]))
    if exception_mode:
        # "Se prohíbe X, excepto cuando: I... II...": the fractions are the exemptions, never the conduct.
        segments = [(None, _HEADER.sub("", flat, count=1))]

    keyed: list[tuple[tuple[int, int, int, int], Sanction]] = []
    seen_clauses: set[str] = set()
    without_clause: list[tuple[int, str | None, str]] = []
    wide_template: Sanction | None = None

    for seg_index, (seg_fraction, segment) in enumerate(segments):
        spans = _clauses(segment)
        if not spans:
            if segment.strip() and not exception_mode:
                without_clause.append((seg_index, seg_fraction, segment.strip()))
            continue
        body = segment[: spans[0][0]]
        items = _incisos(body)
        if items is None:
            result.issues.append(Issue("incisos_irregulares", f"fracción {seg_fraction}: la numeración de incisos no es consecutiva"))
            items = {}
        covered: list[str] = []
        general_whole = 0
        for start, end in spans:
            clause = re.sub(r"^y\s+", "", segment[start:end].strip())
            if not _PENALTY_WORD.search(clause):
                continue  # an amount in UMA that is not a penalty (e.g. the minimum insurance coverage of Art. 90)
            amount, problem = _amount(clause)
            if problem:
                result.issues.append(Issue(problem, f"fracción {seg_fraction}: no se pudo leer el monto", clause))
                continue
            license_points, plate_points, note, mode, issues = _points(clause)
            result.issues.extend(issues)
            kind, labels = _scope(clause)
            if kind == "ambiguous":
                result.issues.append(Issue("alcance_ambiguo", f"fracción {seg_fraction}: la cláusula nombra otras fracciones", clause))
                continue
            if exception_mode:
                if clause in seen_clauses:
                    continue  # the same clause repeated after every exemption
                seen_clauses.add(clause)
            other = _other(clause) or note
            low, mid, high = amount  # type: ignore[misc]
            head = _head(clause)
            wide = bool(_ARTICLE_WIDE.search(head)) or (not body.strip() and kind == "whole")

            def row(inciso: str | None, conduct: str, applies_to: str | None = None, wide_row: bool = False) -> Sanction:
                return Sanction(
                    ordinal=0, fraction=None if exception_mode else seg_fraction, inciso=inciso,
                    conduct_text=_clean(conduct)[:CONDUCT_CHARS], clause_text=clause, uma_min=low, uma_mid=mid, uma_max=high,
                    points_license=license_points, points_plate=plate_points, other_consequences=other,
                    applies_to=applies_to, lead_text=lead or None, points_mode=mode, article_wide=wide_row,
                )

            clause_index = len(keyed)
            if kind == "qualifier":
                keyed.append(((seg_index, 1, 0, clause_index), row(None, body.strip() or lead, _qualifier(clause))))
            elif kind == "incisos":
                for label in labels or []:
                    if label not in items:
                        result.issues.append(Issue("inciso_desconocido", f"fracción {seg_fraction}: la cláusula cita {label}) y la fracción no lo tiene", clause))
                        continue
                    if label in covered:
                        result.issues.append(Issue("cobertura_duplicada", f"fracción {seg_fraction}: el inciso {label}) tiene dos cláusulas", clause))
                        continue
                    covered.append(label)
                    keyed.append(((seg_index, 0, list(items).index(label), clause_index), row(label, items[label])))
            else:
                general_whole += 1
                if exception_mode:
                    conduct = lead or body.strip()
                elif not _GENERIC.search(head) and head.strip():
                    conduct = head.strip(" ,;")  # the clause names its own conduct ("Aquella persona que retire inmovilizadores…")
                else:
                    conduct = body.strip() or lead
                sanction = row(None, conduct, wide_row=wide)
                keyed.append(((seg_index, 0, 0, clause_index), sanction))
                if wide:
                    wide_template = sanction

        if covered and general_whole:
            result.issues.append(Issue("alcance_mixto", f"fracción {seg_fraction}: mezcla cláusulas de incisos con una general"))
        if covered and items and set(covered) != set(items):
            result.issues.append(Issue(
                "cobertura_incompleta", f"fracción {seg_fraction}: incisos sin cláusula: {sorted(set(items) - set(covered))}"
            ))

    if without_clause:
        if wide_template is not None:
            # "el presente artículo": fractions with no clause of their own are covered by the article-wide one.
            for seg_index, seg_fraction, body in without_clause:
                keyed.append(((seg_index, 0, 0, 10_000 + seg_index), Sanction(**{
                    **wide_template.__dict__, "fraction": seg_fraction, "conduct_text": body[:CONDUCT_CHARS],
                    "article_wide": False,
                })))
        elif keyed:
            where = ", ".join(str(f) for _, f, _ in without_clause)
            result.issues.append(Issue("fraccion_sin_sancion", f"fracciones sin sanción en el texto: {where}"))

    # Rows are numbered in reading order: fraction, general before qualified, inciso position, clause order.
    keyed.sort(key=lambda pair: pair[0])
    result.sanctions = [Sanction(**{**sanction.__dict__, "ordinal": index}) for index, (_, sanction) in enumerate(keyed)]
    return result


def fraction_body(article_text: str, fraction: str | None) -> str:
    """The text of one fraction chunk without the article header and the fraction marker."""
    _, segments = _fractions(_flat(article_text), fraction)
    return segments[0][1].strip()


def inherit_article_wide(template: Sanction, fraction: str | None, article_text: str) -> Sanction:
    """The row a fraction gets from an article-wide clause that sits in another fraction chunk of the same article."""
    return Sanction(**{
        **template.__dict__, "ordinal": 0, "fraction": fraction, "inciso": None, "applies_to": None,
        "conduct_text": fraction_body(article_text, fraction)[:CONDUCT_CHARS], "article_wide": False,
    })
