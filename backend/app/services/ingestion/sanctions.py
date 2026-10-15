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

EXTRACTOR_VERSION = "det-1"
CONDUCT_CHARS = 1200

NUMBER_WORDS = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12}
_UMA = r"(?:veces\s+(?:la\s+)?Unidad(?:es)?\s+de\s+Medida|Unidades\s+de\s+Medida|veces\s+la\s+UMA)"
_UMA_RE = re.compile(_UMA)
_TRIPLE = re.compile(r"(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s+o\s+(\d+(?:\.\d+)?)\s+veces")
_POINTS = r"(?:de\s+penalizaci[oó]n\s+)?(?:a|en)\s+la\s+"
_POINTS_LICENSE = re.compile(r"(\w+)\s+puntos?\s+" + _POINTS + r"licencia", re.I)
_POINTS_PLATE = re.compile(r"(\w+(?:\s+a\s+\w+)?)\s+puntos?\s+" + _POINTS + r"matr[ií]cula", re.I)
_BOUNDARY = re.compile(r"[.;:]\s+(?:y\s+)?(?=[A-ZÁÉÍÓÚÑ¿])")
_SENTENCE_END = re.compile(r"\.(?=\s|$)")
_INCISO_LIST = re.compile(r"incisos?\s+((?:[a-z](?:\s+Bis)?\)\s*(?:,|\by\b|\bo\b|\bal\b)?\s*)+)", re.I)
_INCISO_LABEL = re.compile(r"\b([a-z](?:\s+Bis)?)\)", re.I)
_INCISO_MARK = re.compile(r"(?:^|[:;.,]\s+)(?:y\s+)?([a-z](?:\s+Bis)?)[.)]\s+(?=[A-ZÁÉÍÓÚÑ¿\"“])")
_ROMAN_MARK = re.compile(r"(?:^|[:;.]\s+)([IVXL]+)\.\s+(?=[A-ZÁÉÍÓÚÑ¿\"“])")
_QUALIFIER = re.compile(r"^(?:en el caso de|tratándose de|si se determina)\b", re.I)
_PENALTY_VERB = re.compile(r"serán sancionad|será sancionad|se sancionar|la multa será|multa equivalente", re.I)
_OTHER = re.compile(r"depósito|arresto|retenci[oó]n|inmoviliz|cancelaci[oó]n|suspensi[oó]n|remisi[oó]n|remit", re.I)
_PENALTY_WORD = re.compile(r"multa|sanci[oó]n|sancionad|sancionar|infracci", re.I)
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


def _fractions(flat: str, fraction: str | None) -> list[tuple[str | None, str]]:
    """Split a chunk into (fraction, text). A fraction chunk is one segment; an article chunk is split on its
    consecutive roman-numeral markers (I., II., ...). Anything irregular stays a single segment."""
    if fraction:
        marker = re.search(rf"(?:^|[:;.]\s+){re.escape(fraction)}\.\s+", flat)
        return [(fraction, flat[marker.end():] if marker else flat)]
    marks = [m for m in _ROMAN_MARK.finditer(flat)]
    valid: list[re.Match] = []
    for mark in marks:
        if _roman(mark.group(1)) == len(valid) + 1:
            valid.append(mark)
    if not valid:
        return [(None, flat)]
    segments = []
    for index, mark in enumerate(valid):
        end = valid[index + 1].start() if index + 1 < len(valid) else len(flat)
        segments.append((mark.group(1), flat[mark.end():end]))
    return segments


def _clauses(segment: str) -> list[tuple[int, int]]:
    """(start, end) of every sentence that states a penalty in UMA, in order."""
    spans: list[tuple[int, int]] = []
    for match in _UMA_RE.finditer(segment):
        starts = [b.end() for b in _BOUNDARY.finditer(segment, 0, match.start())]
        start = starts[-1] if starts else 0
        end_match = _SENTENCE_END.search(segment, match.end())
        end = end_match.end() if end_match else len(segment)
        if (start, end) not in spans:
            spans.append((start, end))
    return spans


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
        text = re.sub(r"[;,.]?\s*(?:y|o)?\s*$", "", text).strip()
        items[labels[index]] = text
    return items


def _points(clause: str) -> tuple[int | None, int | None, str | None, list[Issue]]:
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
    return license_points, plate_points, note, issues


def _scope(clause: str) -> tuple[str, list[str] | None]:
    """('qualifier' | 'incisos' | 'whole' | 'ambiguous', labels)."""
    if _QUALIFIER.match(clause.strip()):
        return "qualifier", None
    head = clause[: _PENALTY_VERB.search(clause).start()] if _PENALTY_VERB.search(clause) else clause
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
    verb = _PENALTY_VERB.search(clause)
    head = clause[: verb.start()] if verb else clause
    return head.strip(" ,;")[:300]


def _amount(clause: str) -> tuple[tuple[Decimal | None, Decimal | None, Decimal | None] | None, str | None]:
    triple = _TRIPLE.search(clause)
    if triple:
        low, mid, high = (Decimal(x) for x in triple.groups())
        return (low, mid, high), None
    uma = _UMA_RE.search(clause)
    if not uma:
        return None, "sin_monto"
    value, before = _trailing_number(clause[: uma.start()])
    if value is None:
        return None, "sin_monto"
    if re.search(r"\b(?:a|hasta)$", before):  # "de trescientos cincuenta a cuatrocientos cincuenta veces": a range
        return None, "rango"
    return (Decimal(value), None, None), None


def extract_sanctions(article: str, fraction: str | None, text: str) -> Extraction:
    """Candidate sanction rows (and what could not be resolved) for one chunk."""
    result = Extraction()
    flat = _flat(text)
    if "Sanción mínima" in flat and "Sanción máxima" in flat:
        result.issues.append(Issue("tabla", f"Art. {article}: penalidades en una tabla por tipo de vehículo; capturar a mano"))
        return result

    keyed: list[tuple[tuple[int, int, int, int], Sanction]] = []
    for seg_index, (seg_fraction, segment) in enumerate(_fractions(flat, fraction)):
        spans = _clauses(segment)
        if not spans:
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
            license_points, plate_points, note, issues = _points(clause)
            result.issues.extend(issues)
            kind, labels = _scope(clause)
            if kind == "ambiguous":
                result.issues.append(Issue("alcance_ambiguo", f"fracción {seg_fraction}: la cláusula nombra otras fracciones", clause))
                continue
            other = clause if _OTHER.search(clause) else note
            low, mid, high = amount  # type: ignore[misc]

            def row(inciso: str | None, conduct: str, applies_to: str | None = None) -> Sanction:
                return Sanction(
                    ordinal=0, fraction=seg_fraction, inciso=inciso, conduct_text=conduct[:CONDUCT_CHARS],
                    clause_text=clause, uma_min=low, uma_mid=mid, uma_max=high, points_license=license_points,
                    points_plate=plate_points, other_consequences=other, applies_to=applies_to,
                )

            clause_index = len(keyed)
            if kind == "qualifier":
                keyed.append(((seg_index, 1, 0, clause_index), row(None, body.strip(), _qualifier(clause))))
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
                keyed.append(((seg_index, 0, 0, clause_index), row(None, body.strip())))

        if covered and general_whole:
            result.issues.append(Issue("alcance_mixto", f"fracción {seg_fraction}: mezcla cláusulas de incisos con una general"))
        if covered and items and set(covered) != set(items):
            result.issues.append(Issue(
                "cobertura_incompleta", f"fracción {seg_fraction}: incisos sin cláusula: {sorted(set(items) - set(covered))}"
            ))

    # Rows are numbered in reading order: fraction, general before qualified, inciso position, clause order.
    keyed.sort(key=lambda pair: pair[0])
    result.sanctions = [Sanction(**{**sanction.__dict__, "ordinal": index}) for index, (_, sanction) in enumerate(keyed)]
    return result
